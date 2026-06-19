"""
Research Desk — Week 3 Project
===============================
Class hierarchy:
  Agent       — brain: chat(), _run_loop(), dispatch(), sessions
  REPLAgent   — terminal REPL + one-shot CLI
  TUIAgent    — Textual UI (in tui.py)

Usage:
  python agent.py                              # REPLAgent.run()
  python agent.py "What is quantum computing?" # REPLAgent.run_once()
  python agent.py --tui                        # TUIAgent.run()
  python agent.py --session abc123 "continue"
"""
import os
import sys
import json
import uuid
from datetime import datetime, timezone
from openai import OpenAI
from dotenv import load_dotenv
from textual import work

# Apne tools ko import kar rahe hain
from tools.files import read_file, write_file, list_files, edit_file
from tools.web import web_search, web_fetch
from tools.papers import paper_search, read_paper

load_dotenv()

SESSIONS_DIR = ".agent/sessions"
AGENTS_PATHS = ("AGENTS.md", ".agent/AGENTS.md")
MAX_ITERATIONS = 10

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ.get("OPENROUTER_API_KEY"),
)
MODEL = "google/gemini-2.5-flash"

# --- TOOL REGISTRY ---
# AI ko batana ki uske paas kya-kya powers hain
TOOLS = [
    {"type": "function", "function": {"name": "read_file", "description": "Read file lines", "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "start_line": {"type": "integer"}, "read_lines": {"type": "integer"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "write_file", "description": "Write entire file", "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}}, "required": ["path", "content"]}}},
    {"type": "function", "function": {"name": "list_files", "description": "List files", "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "pattern": {"type": "string"}}, "required": []}}},
    {"type": "function", "function": {"name": "edit_file", "description": "Edit lines", "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "operation": {"type": "string", "enum": ["replace", "insert", "delete"]}, "start_line": {"type": "integer"}, "end_line": {"type": "integer"}, "content": {"type": "string"}}, "required": ["path", "operation", "start_line"]}}},
    {"type": "function", "function": {"name": "web_search", "description": "Search the web", "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}}},
    {"type": "function", "function": {"name": "web_fetch", "description": "Fetch webpage content", "parameters": {"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"]}}},
    {"type": "function", "function": {"name": "paper_search", "description": "Search ArXiv papers", "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}}},
    {"type": "function", "function": {"name": "read_paper", "description": "Read ArXiv paper by ID", "parameters": {"type": "object", "properties": {"paper_id": {"type": "string"}}, "required": ["paper_id"]}}}
]

AVAILABLE_TOOLS = {
    "read_file": read_file, "write_file": write_file, "list_files": list_files, "edit_file": edit_file,
    "web_search": web_search, "web_fetch": web_fetch,
    "paper_search": paper_search, "read_paper": read_paper
}

# --- AGENT CORE ---
def build_system_prompt() -> str:
    prompt = "You are Research Desk, a helpful research assistant. You can search the web, read academic papers, and manage files."
    for path in AGENTS_PATHS:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                prompt += f"\n\n{f.read()}"
            break
    return prompt

class Agent:
    """Core agent: loop, tools, sessions. No Textual imports here."""
    def __init__(self, workspace: str = ".", session_id: str | None = None):
        self.workspace = os.path.abspath(workspace)
        os.makedirs(SESSIONS_DIR, exist_ok=True)
        
        if session_id:
            self.session_id = session_id
            filepath = os.path.join(SESSIONS_DIR, f"{session_id}.json")
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    self.messages = json.load(f).get("messages", [])
            except FileNotFoundError:
                self.messages = [{"role": "system", "content": build_system_prompt()}]
        else:
            self.session_id = uuid.uuid4().hex[:8]
            self.messages = [{"role": "system", "content": build_system_prompt()}]

    def _save_session(self):
        filepath = os.path.join(SESSIONS_DIR, f"{self.session_id}.json")
        session_data = {"id": self.session_id, "updated_at": datetime.now(timezone.utc).isoformat(), "messages": self.messages}
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(session_data, f, indent=2)

    def chat(self, user_message: str) -> str:
        self.messages.append({"role": "user", "content": user_message})
        final_answer = self._run_loop()
        self._save_session()
        return final_answer

    def run_once(self, prompt: str) -> str:
        return self.chat(prompt)

    def _run_loop(self) -> str:
        for _ in range(MAX_ITERATIONS):
            response = client.chat.completions.create(model=MODEL, messages=self.messages, tools=TOOLS,max_tokens = 2000)
            msg = response.choices[0].message
            self.messages.append(msg.model_dump(exclude_none=True))

            if not msg.tool_calls:
                return msg.content

            for tc in msg.tool_calls:
                result = self.dispatch(tc)
                self.messages.append({"role": "tool", "tool_call_id": tc.id, "content": result})
        
        return "Agent stopped after reaching maximum iterations."

    def dispatch(self, tool_call) -> str:
        name = tool_call.function.name
        args = json.loads(tool_call.function.arguments)
        self._emit("tool_call", name=name, args=args)
        
        if name in AVAILABLE_TOOLS:
            result = AVAILABLE_TOOLS[name](**args)
            return json.dumps(result)
        return json.dumps({"error": f"Tool {name} not found."})

    def _emit(self, event: str, **data) -> None:
        pass


class REPLAgent(Agent):
    """Terminal REPL interface."""
    def run(self) -> None:
        print(f"Research Desk [{self.session_id}] — /quit to exit")
        while True:
            try:
                user_input = input("\n> ").strip()
            except (EOFError, KeyboardInterrupt):
                print(); break
            if not user_input or user_input in ("/quit", "/exit"):
                break
            print(f"\nAgent: {self.chat(user_input)}")

    def _emit(self, event: str, **data) -> None:
        if event == "tool_call":
            print(f"  [🔧 Tool Running: {data.get('name')}]", file=sys.stderr)


# --- MAIN ENTRY POINT ---
def main():
    # Handle Textual TUI
    if "--tui" in sys.argv:
        try:
            from tui import TUIAgentApp
            TUIAgentApp().run()
            return
        except ImportError:
            print("Error: Could not import tui.py. Ensure it exists.")
            return

    # Handle One-Shot CLI vs REPL
    agent = REPLAgent()
    args = [arg for arg in sys.argv[1:] if arg != "--tui"]
    
    if len(args) > 0:
        print(agent.run_once(" ".join(args)))
    else:
        agent.run()

if __name__ == "__main__":
    main()