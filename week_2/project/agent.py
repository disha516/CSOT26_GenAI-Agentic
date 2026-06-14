"""
ResearchBot — Week 2 Project
A full research agent with:
  - Web search (Serper), web fetch, and ArXiv tools
  - Agentic loop (iterates until model stops calling tools)
  - Textual TUI: chat panel + tool activity log
  - Shortcuts: Ctrl+L (clear display), Ctrl+K (clear history),
               Ctrl+Q (quit), Ctrl+S (save chat to file)
"""

import os
import re
import json
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv

from textual.app import App, ComposeResult
from textual import work
from textual.binding import Binding
from textual.widgets import Header, Footer, Input, RichLog, Static
from textual.containers import Horizontal, Vertical

load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ.get("OPENROUTER_API_KEY"),
)
MODEL = "google/gemini-2.5-flash"

# ─────────────────────────── TOOLS ────────────────────────────

def web_search(query: str) -> str:
    """Search the web using Serper API and return top results."""
    url = "https://google.serper.dev/search"
    headers = {
        "X-API-KEY": os.environ.get("SERPER_API_KEY", ""),
        "Content-Type": "application/json",
    }
    try:
        resp = requests.post(url, headers=headers, json={"q": query}, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        results = []
        if "answerBox" in data:
            ab = data["answerBox"]
            answer = ab.get("answer") or ab.get("snippet", "")
            if answer:
                results.append(f"[Quick Answer] {answer}")

        if "knowledgeGraph" in data:
            kg = data["knowledgeGraph"]
            desc = kg.get("description", "")
            if desc:
                results.append(f"[Knowledge] {desc}")

        for r in data.get("organic", [])[:4]:
            results.append(
                f"Title: {r.get('title','')}\n"
                f"URL: {r.get('link','')}\n"
                f"Snippet: {r.get('snippet','')}"
            )

        return "\n\n".join(results) if results else "No results found."
    except Exception as e:
        return f"Web search error: {e}"


def web_fetch(url: str) -> str:
    """Fetch and return key text content from a URL — capped and cleaned."""
    try:
        resp = requests.get(url, timeout=10, headers={"User-Agent": "ResearchBot/1.0"})
        resp.raise_for_status()
        text = resp.text

        # Strip styles, scripts, and tags
        text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL)
        text = re.sub(r"<script[^>]*>.*?</script>", "", text, flags=re.DOTALL)
        text = re.sub(r"<nav[^>]*>.*?</nav>", "", text, flags=re.DOTALL)
        text = re.sub(r"<footer[^>]*>.*?</footer>", "", text, flags=re.DOTALL)
        text = re.sub(r"<header[^>]*>.*?</header>", "", text, flags=re.DOTALL)
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"\s+", " ", text).strip()

        # Cap at 1500 chars — enough for the model to summarize without overload
        if len(text) > 1500:
            text = text[:1500] + "... [truncated — summarize what's available]"

        return text
    except Exception as e:
        return f"Fetch error: {e}"


def search_arxiv(query: str) -> str:
    """Search ArXiv for recent research papers."""
    url = (
        f"http://export.arxiv.org/api/query"
        f"?search_query=all:{requests.utils.quote(query)}"
        f"&start=0&max_results=5&sortBy=submittedDate&sortOrder=descending"
    )
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        root = ET.fromstring(resp.content)
        ns = "{http://www.w3.org/2005/Atom}"

        results = []
        for entry in root.findall(f"{ns}entry"):
            title     = entry.find(f"{ns}title").text.strip().replace("\n", " ")
            link      = entry.find(f"{ns}id").text.strip()
            summary   = entry.find(f"{ns}summary").text.strip().replace("\n", " ")[:200]
            authors   = [a.find(f"{ns}name").text for a in entry.findall(f"{ns}author")][:3]
            published = entry.find(f"{ns}published").text[:10]
            results.append(
                f"Title: {title}\n"
                f"Authors: {', '.join(authors)}\n"
                f"Published: {published}\n"
                f"URL: {link}\n"
                f"Summary: {summary}..."
            )

        return "\n\n".join(results) if results else "No papers found."
    except Exception as e:
        return f"ArXiv search error: {e}"


# ──────────────────── TOOL DEFINITIONS ────────────────────────

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": (
                "PRIMARY tool. Search the web for any real-time or current information: "
                "weather, temperature, news, events, prices, sports scores, stock data, "
                "people, products, or anything that changes over time. "
                "Always use this before answering questions about the current state of the world."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "A specific search query, e.g. 'current temperature Delhi today'"
                    }
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "web_fetch",
            "description": (
                "Fetch and read the text content of a specific URL. "
                "Use this after web_search to read a full article or page "
                "when the search snippet is not enough. "
                "Do NOT use on very large pages — prefer specific article URLs."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The full URL to fetch, e.g. https://example.com/article"
                    }
                },
                "required": ["url"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_arxiv",
            "description": (
                "Search ArXiv for recent peer-reviewed research papers. "
                "Use for academic queries: physics, electrodynamics, machine learning, "
                "mathematics, biology, economics, or any scientific research topic."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Research topic or keywords, e.g. 'electrodynamics quantum field theory'"
                    }
                },
                "required": ["query"],
            },
        },
    },
]

AVAILABLE_TOOLS = {
    "web_search": web_search,
    "web_fetch": web_fetch,
    "search_arxiv": search_arxiv,
}

# ─────────────────────── AGENT LOOP ───────────────────────────

def run_agent(messages: list, tool_log_callback=None) -> str:
    """
    Iterative agent loop.
    Keeps calling the model until it stops requesting tools.
    """
    MAX_ITERATIONS = 8

    for _ in range(MAX_ITERATIONS):
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=TOOLS,
            max_tokens=2000,
        )
        msg = response.choices[0].message

        # No tool calls → final answer
        if not msg.tool_calls:
            return msg.content or "(No response)"

        # Append assistant message with tool calls
        messages.append(msg)

        # Execute each tool call
        for tc in msg.tool_calls:
            tool_name = tc.function.name
            try:
                args = json.loads(tc.function.arguments)
            except json.JSONDecodeError:
                args = {}

            if tool_log_callback:
                tool_log_callback(
                    f"[bold yellow]⚙ {tool_name}[/bold yellow] "
                    f"[dim]{json.dumps(args)}[/dim]"
                )

            result = (
                AVAILABLE_TOOLS[tool_name](**args)
                if tool_name in AVAILABLE_TOOLS
                else f"Unknown tool: {tool_name}"
            )

            if tool_log_callback:
                preview = result[:120].replace("\n", " ")
                tool_log_callback(f"[green]✓ Result:[/green] [dim]{preview}...[/dim]")

            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": result,
            })

    return "Max iterations reached without a final answer."


# ─────────────────────────── TUI ──────────────────────────────

SYSTEM_PROMPT = (
    "You are ResearchBot, an intelligent research assistant. "
    "You have access to web search, web fetch, and ArXiv paper search tools. "
    "Always use tools to find real-time or factual information — never guess "
    "about current weather, prices, or recent events. "
    "Be concise and cite sources when possible. "
    "If web_fetch content is truncated, summarize only what is available."
)


def _safe_role(m) -> str:
    """Get role from either a dict or a ChatCompletionMessage object."""
    if isinstance(m, dict):
        return m.get("role", "")
    return getattr(m, "role", "")


def _safe_content(m) -> str:
    """Get content from either a dict or a ChatCompletionMessage object."""
    if isinstance(m, dict):
        content = m.get("content", "")
    else:
        content = getattr(m, "content", "") or ""
    return content if isinstance(content, str) else str(content)


class ResearchBotApp(App):
    CSS = """
    Screen {
        background: #0d1117;
    }
    #title-bar {
        height: 1;
        background: #161b22;
        color: #58a6ff;
        padding: 0 2;
        text-align: center;
    }
    #main {
        height: 1fr;
    }
    #chat-panel {
        width: 65%;
        border-right: solid #30363d;
        padding: 1;
    }
    #tool-panel {
        width: 35%;
        padding: 1;
    }
    #chat-label {
        height: 1;
        color: #58a6ff;
        text-style: bold;
        margin-bottom: 1;
    }
    #tool-label {
        height: 1;
        color: #f0883e;
        text-style: bold;
        margin-bottom: 1;
    }
    #chat-log {
        height: 1fr;
        background: #0d1117;
        border: solid #30363d;
        padding: 0 1;
    }
    #tool-log {
        height: 1fr;
        background: #0d1117;
        border: solid #30363d;
        padding: 0 1;
    }
    #input-bar {
        height: 3;
        background: #161b22;
        padding: 0 1;
        border-top: solid #30363d;
    }
    Input {
        background: #21262d;
        color: #e6edf3;
        border: solid #30363d;
        height: 3;
    }
    Input:focus {
        border: solid #58a6ff;
    }
    Footer {
        background: #161b22;
        color: #8b949e;
    }
    """

    BINDINGS = [
        Binding("ctrl+l", "clear_display", "Clear Display"),
        Binding("ctrl+k", "clear_history", "Reset History"),
        Binding("ctrl+s", "save_chat", "Save Chat"),
        Binding("ctrl+q", "quit", "Quit"),
    ]

    def __init__(self):
        super().__init__()
        self.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        self.is_processing = False

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Static("🔬 ResearchBot — Web · ArXiv · Live Data", id="title-bar")
        with Horizontal(id="main"):
            with Vertical(id="chat-panel"):
                yield Static("💬 Chat", id="chat-label")
                yield RichLog(id="chat-log", highlight=True, markup=True, wrap=True)
            with Vertical(id="tool-panel"):
                yield Static("⚙ Tool Activity", id="tool-label")
                yield RichLog(id="tool-log", highlight=True, markup=True, wrap=True)
        with Horizontal(id="input-bar"):
            yield Input(placeholder="Ask anything... (Ctrl+Q to quit)")
        yield Footer()

    def on_mount(self):
        chat = self.query_one("#chat-log", RichLog)
        chat.write("[dim]ResearchBot ready. Try:[/dim]")
        chat.write("[dim]  • What is the current temperature in Delhi?[/dim]")
        chat.write("[dim]  • Find recent papers on electrodynamics[/dim]")
        chat.write("[dim]  • What happened in AI news this week?[/dim]")
        chat.write("")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        user_text = event.value.strip()
        if not user_text:
            return
        event.input.clear()

        if self.is_processing:
            self.query_one("#chat-log", RichLog).write(
                "[yellow]⏳ Still processing previous request...[/yellow]"
            )
            return

        self.query_one("#chat-log", RichLog).write(
            f"[bold cyan]You[/bold cyan]  {user_text}\n"
        )
        self.query_one("#tool-log", RichLog).write("[dim]── New query ──[/dim]")

        self.is_processing = True
        self._process(user_text)

    @work(thread=True, exclusive=True)
    def _process(self, text: str):
        """Runs in a background thread via @work decorator."""
        tool_log = self.query_one("#tool-log", RichLog)
        chat_log = self.query_one("#chat-log", RichLog)

        def log_tool(msg: str):
            self.call_from_thread(tool_log.write, msg)

        self.messages.append({"role": "user", "content": text})

        try:
            reply = run_agent(self.messages, tool_log_callback=log_tool)
            self.messages.append({"role": "assistant", "content": reply})
            self.call_from_thread(
                chat_log.write,
                f"[bold magenta]Bot[/bold magenta]   {reply}\n"
            )
        except Exception as e:
            self.call_from_thread(chat_log.write, f"[red]Error: {e}[/red]\n")
        finally:
            self.is_processing = False

    def action_clear_display(self):
        self.query_one("#chat-log", RichLog).clear()
        self.query_one("#tool-log", RichLog).clear()

    def action_clear_history(self):
        self.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        self.action_clear_display()
        self.query_one("#chat-log", RichLog).write(
            "[dim]History cleared. Fresh start![/dim]\n"
        )

    def action_save_chat(self):
        """Ctrl+S — save conversation to timestamped file, handles both dict and object messages."""
        filename = f"chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        lines = []
        for m in self.messages:
            role = _safe_role(m)
            if role == "system" or role == "tool":
                continue
            label = "You" if role == "user" else "Bot"
            content = _safe_content(m)
            if content:  # skip empty assistant messages (tool-call-only turns)
                lines.append(f"[{label}]\n{content}\n")

        with open(filename, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        self.query_one("#chat-log", RichLog).write(
            f"[green]✓ Chat saved to {filename}[/green]"
        )


# ──────────────────────── ENTRY POINT ─────────────────────────

if __name__ == "__main__":
    ResearchBotApp().run()