"""
Research Desk — Week 5 Project (Code Scout with Skills & MCP)
===========================================
Class hierarchy:
  Agent       — brain: chat(), _run_loop(), dispatch(), sessions
  REPLAgent   — terminal REPL + one-shot CLI
  TUIAgent    — Textual UI (in tui.py)
"""
import os
import sys
import json
import uuid
import asyncio
from datetime import datetime, timezone
from openai import OpenAI
from dotenv import load_dotenv

from tools.files import read_file, write_file, list_files, edit_file
from tools.web import web_search, web_fetch
from tools.papers import paper_search, read_paper
from tools.exec import run_command, EXEC_TOOLS
from tools.search import grep, list_definitions, SEARCH_TOOLS
from tools.plan import add_todos, get_todos, mark_todo, all_todos_completed, PLAN_TOOLS
from tools.skills import load_skill, get_all_skills_metadata, SKILL_TOOLS

# WEEK 5: Naya MCP Loader import
from tools.mcp_manager import MCPManager, load_mcp_config

load_dotenv()

MAX_ITERATIONS = 15 

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ.get("OPENROUTER_API_KEY"),
)
MODEL = "google/gemini-2.5-flash"

# --- TOOL REGISTRY ---
BASE_TOOLS = [
    {"type": "function", "function": {"name": "read_file", "description": "Read file lines", "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "start_line": {"type": "integer"}, "read_lines": {"type": "integer"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "write_file", "description": "Write entire file", "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}}, "required": ["path", "content"]}}},
    {"type": "function", "function": {"name": "list_files", "description": "List files", "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "pattern": {"type": "string"}}, "required": []}}},
    {"type": "function", "function": {"name": "edit_file", "description": "Edit lines", "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "operation": {"type": "string", "enum": ["replace", "insert", "delete"]}, "start_line": {"type": "integer"}, "end_line": {"type": "integer"}, "content": {"type": "string"}}, "required": ["path", "operation", "start_line"]}}},
    {"type": "function", "function": {"name": "web_search", "description": "Search the web", "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}}},
    {"type": "function", "function": {"name": "web_fetch", "description": "Fetch webpage content", "parameters": {"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"]}}},
    {"type": "function", "function": {"name": "paper_search", "description": "Search ArXiv papers", "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}}},
    {"type": "function", "function": {"name": "read_paper", "description": "Read ArXiv paper by ID", "parameters": {"type": "object", "properties": {"paper_id": {"type": "string"}}, "required": ["paper_id"]}}}
]

# Naya static tools list (mcp_tools dynamically class ke andar add honge)
STATIC_TOOLS = BASE_TOOLS + EXEC_TOOLS + SEARCH_TOOLS + PLAN_TOOLS + SKILL_TOOLS

AVAILABLE_TOOLS = {
    "read_file": read_file, "write_file": write_file, "list_files": list_files, "edit_file": edit_file,
    "web_search": web_search, "web_fetch": web_fetch,
    "paper_search": paper_search, "read_paper": read_paper,
    "run_command": run_command,
    "grep": grep,
    "list_definitions": list_definitions,
    "add_todos": add_todos,
    "get_todos": get_todos,
    "mark_todo": mark_todo,
    "load_skill": load_skill
}

def build_system_prompt(workspace: str) -> str:
    prompt = "You are Code Scout, an autonomous coding agent. You investigate codebases, make plans using the todo tools, execute shell commands, and verify your fixes before claiming you are done."
    
    # WEEK 5: Inject Skill Metadata
    prompt += "\n" + get_all_skills_metadata()
    
    paths_to_check = ["AGENTS.md", os.path.join(".agent", "AGENTS.md")]
    for path in paths_to_check:
        full_path = os.path.join(workspace, path)
        if os.path.exists(full_path):
            with open(full_path, "r", encoding="utf-8") as f:
                prompt += f"\n\n{f.read()}"
            break
    return prompt

class Agent:
    """Core agent: loop, tools, sessions."""
    def __init__(self, mcp_manager: MCPManager, workspace: str = ".", session_id: str | None = None):
        self.workspace = os.path.abspath(workspace)
        self.sessions_dir = os.path.join(self.workspace, ".agent", "sessions")
        os.makedirs(self.sessions_dir, exist_ok=True)
        
        # WEEK 5: Store mcp_manager and combine all tools
        self.mcp_manager = mcp_manager
        self.all_tools = STATIC_TOOLS + self.mcp_manager.mcp_tools
        
        if session_id:
            self.session_id = session_id
            filepath = os.path.join(self.sessions_dir, f"{session_id}.json")
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    self.messages = json.load(f).get("messages", [])
            except FileNotFoundError:
                self.messages = [{"role": "system", "content": build_system_prompt(self.workspace)}]
        else:
            self.session_id = uuid.uuid4().hex[:8]
            self.messages = [{"role": "system", "content": build_system_prompt(self.workspace)}]
        
        self._save_session()

    def _save_session(self):
        filepath = os.path.join(self.sessions_dir, f"{self.session_id}.json")
        session_data = {"id": self.session_id, "updated_at": datetime.now(timezone.utc).isoformat(), "messages": self.messages}
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(session_data, f, indent=2)

    # WEEK 5: Async chat and loops for network calls
    async def chat(self, user_message: str) -> str:
        self.messages.append({"role": "user", "content": user_message})
        final_answer = await self._run_loop()
        self._save_session()
        return final_answer

    async def run_once(self, prompt: str) -> str:
        return await self.chat(prompt)

    async def _run_loop(self) -> str:
        for _ in range(MAX_ITERATIONS):
            response = client.chat.completions.create(model=MODEL, messages=self.messages, tools=self.all_tools, max_tokens=2000)
            msg = response.choices[0].message
            self.messages.append(msg.model_dump(exclude_none=True))

            if not msg.tool_calls:
                # SAFETY GATE
                todos_state = get_todos()
                if todos_state["total_todos"] > 0 and not all_todos_completed():
                    force_msg = "Warning: Your task is NOT done. You have incomplete todos in your plan. You must complete them and use `mark_todo` with test evidence before stopping."
                    self.messages.append({"role": "user", "content": force_msg})
                    continue 
                return msg.content

            for tc in msg.tool_calls:
                result = await self.dispatch(tc)
                self.messages.append({"role": "tool", "tool_call_id": tc.id, "content": result})
        
        return "Agent stopped after reaching maximum iterations."

    async def dispatch(self, tool_call) -> str:
        name = tool_call.function.name
        args = json.loads(tool_call.function.arguments)
        self._emit("tool_call", name=name, args=args)
        
        # 1. Check Local Python Tools first
        if name in AVAILABLE_TOOLS:
            result = AVAILABLE_TOOLS[name](**args)
            return json.dumps(result)[:10000]
            
        # 2. Check MCP Tools (GitHub, etc.)
        if name in self.mcp_manager.tool_to_session:
            result = await self.mcp_manager.call_tool(name, args)
            return json.dumps(result)[:10000]
            
        return json.dumps({"error": f"Tool {name} not found."})

    def _emit(self, event: str, **data) -> None:
        pass


class REPLAgent(Agent):
    """Terminal REPL interface."""
    async def run(self) -> None:
        print(f"Code Scout (Week 5) [{self.session_id}] — /quit to exit, /sessions to list, /resume <id> to switch")
        while True:
            try:
                user_input = input("\n> ").strip()
            except (EOFError, KeyboardInterrupt):
                print(); break
            if not user_input or user_input in ("/quit", "/exit"):
                break
            
            if user_input == "/sessions":
                print("\nSaved Sessions:")
                for f in os.listdir(self.sessions_dir):
                    if f.endswith(".json"):
                        print(f" - {f.replace('.json', '')}")
                continue
            
            if user_input.startswith("/resume "):
                new_id = user_input.split(" ")[1].strip()
                filepath = os.path.join(self.sessions_dir, f"{new_id}.json")
                if os.path.exists(filepath):
                    self.session_id = new_id
                    with open(filepath, "r", encoding="utf-8") as f:
                        self.messages = json.load(f).get("messages", [])
                    print(f"\nResumed session: {new_id}")
                else:
                    print(f"\nSession {new_id} not found.")
                continue

            print(f"\nAgent: {await self.chat(user_input)}")

    def _emit(self, event: str, **data) -> None:
        if event == "tool_call":
            print(f"  [🔧 Tool Running: {data.get('name')}]", file=sys.stderr)


# WEEK 5: Main entry point ab async hai
async def main_async():
    # 1. MCP Servers connect karna
    mcp_manager = MCPManager()
    servers_config = load_mcp_config()
    await mcp_manager.connect_all(servers_config)

    # 2. Argument parsing
    session_id = None
    args = []
    
    i = 1
    while i < len(sys.argv):
        if sys.argv[i] == "--session" and i + 1 < len(sys.argv):
            session_id = sys.argv[i+1]
            i += 2
        else:
            args.append(sys.argv[i])
            i += 1

    # 3. Initialize Agent
    agent = REPLAgent(mcp_manager=mcp_manager, session_id=session_id)
    
    if len(args) > 0:
        print(await agent.run_once(" ".join(args)))
    else:
        await agent.run()
        
    # 4. Clean exit
    await mcp_manager.aclose()


def main():
    if "--tui" in sys.argv:
        try:
            from tui import TUIAgentApp
            TUIAgentApp().run()
            return
        except ImportError:
            print("Error: Could not import tui.py. Ensure it exists.")
            return
            
    asyncio.run(main_async())


if __name__ == "__main__":
    main()