import os
import json
import requests
import xml.etree.ElementTree as ET
from openai import OpenAI
from dotenv import load_dotenv
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Header, Footer, Input, RichLog

load_dotenv()
client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=os.environ.get("OPENROUTER_API_KEY"))
MODEL = "google/gemini-2.5-flash"

# --- TOOLS ---
def web_search(query: str) -> str:
    url = "https://google.serper.dev/search"
    headers = {'X-API-KEY': os.environ.get("SERPER_API_KEY"), 'Content-Type': 'application/json'}
    response = requests.post(url, headers=headers, json={"q": query})
    return json.dumps(response.json().get("organic", [])[:3])

def search_arxiv(query: str) -> str:
    url = f"http://export.arxiv.org/api/query?search_query=all:{query}&start=0&max_results=3"
    response = requests.get(url)
    root = ET.fromstring(response.content)
    results = [f"{e.find('{http://www.w3.org/2005/Atom}title').text} ({e.find('{http://www.w3.org/2005/Atom}id').text})" for e in root.findall('{http://www.w3.org/2005/Atom}entry')]
    return "\n".join(results) if results else "No papers found."

TOOLS = [
    {"type": "function", "function": {"name": "web_search", "description": "Search the web", "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}}},
    {"type": "function", "function": {"name": "search_arxiv", "description": "Search research papers", "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}}}
]
AVAILABLE_TOOLS = {"web_search": web_search, "search_arxiv": search_arxiv}

# --- AGENT LOOP ---
def run_agent(messages: list) -> str:
    response = client.chat.completions.create(model=MODEL, messages=messages, tools=TOOLS,max_tokens =1000)
    msg = response.choices[0].message
    if msg.tool_calls:
        messages.append(msg)
        for tc in msg.tool_calls:
            tool_name = tc.function.name
            args = json.loads(tc.function.arguments)
            result = AVAILABLE_TOOLS[tool_name](**args)
            messages.append({"role": "tool", "tool_call_id": tc.id, "content": result})
        return run_agent(messages) # Loop back to get final answer
    return msg.content

# --- TUI ---
class ChatApp(App):
    BINDINGS = [Binding("ctrl+l", "clear_display", "Clear"), Binding("ctrl+k", "clear_history", "Reset"), Binding("ctrl+q", "quit", "Quit")]
    def __init__(self):
        super().__init__()
        self.messages = [{"role": "system", "content": "You are a research agent. Use tools to find info and papers."}]
    def compose(self) -> ComposeResult:
        yield Header(); yield RichLog(id="log", highlight=True); yield Input(placeholder="Ask anything..."); yield Footer()
    def on_input_submitted(self, event: Input.Submitted) -> None:
        user_text = event.value.strip(); event.input.clear()
        self.query_one("#log", RichLog).write(f"[bold cyan][You][/bold cyan] {user_text}")
        self.run_worker(self.process(user_text), thread=True)
    def process(self, text):
        reply = run_agent(self.messages + [{"role": "user", "content": text}])
        self.call_from_thread(self.query_one("#log", RichLog).write, f"[bold magenta][Agent][/bold magenta] {reply}")
    def action_clear_display(self): self.query_one("#log", RichLog).clear()
    def action_clear_history(self): self.messages = []; self.action_clear_display()

if __name__ == "__main__":
    ChatApp().run()