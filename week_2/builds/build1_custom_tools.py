import os
import json
import requests
import trafilatura
from openai import OpenAI
from dotenv import load_dotenv
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Header, Footer, Input, RichLog

# Load keys
load_dotenv()
client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=os.environ.get("OPENROUTER_API_KEY"))
MODEL = "google/gemini-2.5-flash"

# --- 1. TOOLS (Build 1 & 2 logic) ---
def web_search(query: str) -> str:
    headers = {'X-API-KEY': os.environ.get("SERPER_API_KEY"), 'Content-Type': 'application/json'}
    res = requests.post("https://google.serper.dev/search", headers=headers, json={"q": query})
    return json.dumps(res.json().get("organic", [])[:3])

def web_fetch(url: str) -> str:
    downloaded = trafilatura.fetch_url(url)
    return trafilatura.extract(downloaded)[:2000] if downloaded else "Error fetching page."

TOOLS = [
    {"type": "function", "function": {"name": "web_search", "description": "Search web", "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}}},
    {"type": "function", "function": {"name": "web_fetch", "description": "Fetch URL", "parameters": {"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"]}}}
]
AVAILABLE_TOOLS = {"web_search": web_search, "web_fetch": web_fetch}

# --- 2. AGENT LOOP (Handles multi-step reasoning) ---
def run_agent(messages: list) -> str:
    while True:
        response = client.chat.completions.create(model=MODEL, messages=messages, tools=TOOLS)
        msg = response.choices[0].message
        messages.append(msg)
        
        if not msg.tool_calls: return msg.content
        
        for tc in msg.tool_calls:
            name = tc.function.name
            args = json.loads(tc.function.arguments)
            result = AVAILABLE_TOOLS[name](**args)
            messages.append({"role": "tool", "tool_call_id": tc.id, "content": result})

# --- 3. TEXTUAL TUI (Build 3) ---
class ResearchBot(App):
    BINDINGS = [
        Binding("ctrl+l", "clear_display", "Clear Display"),
        Binding("ctrl+k", "clear_history", "Reset History"),
        Binding("ctrl+q", "quit", "Quit"),
        Binding("ctrl+s", "save_chat", "Save Log")
    ]

    def __init__(self):
        super().__init__()
        self.messages = [{"role": "system", "content": "You are a helpful research agent."}]

    def compose(self) -> ComposeResult:
        yield Header(); yield RichLog(id="log", highlight=True); yield Input(placeholder="Ask anything..."); yield Footer()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        user_text = event.value.strip()
        if not user_text: return
        event.input.clear()
        self.query_one("#log", RichLog).write(f"[bold cyan][You][/bold cyan] {user_text}")
        self.run_worker(self.process_request(user_text), thread=True)

    def process_request(self, text):
        reply = run_agent(self.messages + [{"role": "user", "content": text}])
        self.messages.append({"role": "assistant", "content": reply})
        self.call_from_thread(self.query_one("#log", RichLog).write, f"[bold magenta][Agent][/bold magenta] {reply}")

    def action_clear_display(self): self.query_one("#log", RichLog).clear()
    def action_clear_history(self): 
        self.messages = [{"role": "system", "content": "You are a helpful research agent."}]
        self.action_clear_display()
    def action_save_chat(self):
        with open("chat_log.txt", "w") as f: f.write(str(self.messages))
        self.query_one("#log", RichLog).write("[yellow]Chat saved to chat_log.txt[/yellow]")

if __name__ == "__main__":
    ResearchBot().run()