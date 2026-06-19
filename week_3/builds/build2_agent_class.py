import os
import sys
import json
import uuid
import glob as glob_module
from datetime import datetime, timezone
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

WORKSPACE_ROOT = os.path.abspath(os.environ.get("WORKSPACE_ROOT", "."))
MAX_ITERATIONS = 10
MAX_READ_CHARS = 12_000
SESSIONS_DIR = ".agent/sessions"
AGENTS_PATHS = ("AGENTS.md", ".agent/AGENTS.md")

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
)
# Note: Ensure you have access to this model on OpenRouter, or change to "google/gemini-2.5-flash" if it fails.
MODEL = "google/gemini-2.5-flash" 

# --- File tools ---

def resolve_path(path: str) -> str:
    """Security check: Ensures the agent doesn't read/write files outside the workspace."""
    target = os.path.abspath(os.path.join(WORKSPACE_ROOT, path))
    if not target.startswith(WORKSPACE_ROOT):
        raise ValueError(f"Path {path} is outside the workspace.")
    return target

def read_file(path: str, start_line: int = 1, read_lines: int = 200) -> dict:
    """Read a specific number of lines from a file, returning line numbers."""
    try:
        target = resolve_path(path)
        with open(target, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        end_line = min(start_line + read_lines - 1, len(lines))
        # Adding line numbers so the AI knows exactly which lines to edit later
        content_with_lines = "".join([f"{i+1}| {lines[i]}" for i in range(start_line - 1, end_line)])
        
        return {
            "content": content_with_lines,
            "has_more": end_line < len(lines),
            "end_line": end_line
        }
    except Exception as e:
        return {"error": str(e)}

def write_file(path: str, content: str) -> dict:
    """Overwrites or creates a new file with the given content."""
    try:
        target = resolve_path(path)
        os.makedirs(os.path.dirname(target) or ".", exist_ok=True)
        with open(target, "w", encoding="utf-8") as f:
            f.write(content)
        return {"success": True, "path": path}
    except Exception as e:
        return {"error": str(e)}

def edit_file(path: str, operation: str, start_line: int, end_line: int | None = None, content: str | None = None) -> dict:
    """Edits a file (replace, insert, delete) based on line numbers."""
    try:
        target = resolve_path(path)
        with open(target, "r", encoding="utf-8") as f:
            lines = f.readlines()
            
        start_idx = start_line - 1
        end_idx = end_line if end_line else start_line
        
        new_lines = content.split('\n') if content else []
        new_lines = [l + '\n' for l in new_lines if l] # Re-add newlines
        
        if operation == "replace":
            lines[start_idx:end_idx] = new_lines
        elif operation == "delete":
            del lines[start_idx:end_idx]
        elif operation in ["insert", "append"]:
            lines[start_idx:start_idx] = new_lines
            
        with open(target, "w", encoding="utf-8") as f:
            f.writelines(lines)
        return {"success": True, "operation": operation}
    except Exception as e:
        return {"error": str(e)}

def list_files(path: str = ".", pattern: str = "*") -> dict:
    """Lists files in the workspace matching a pattern."""
    try:
        target_dir = resolve_path(path)
        search_path = os.path.join(target_dir, "**", pattern)
        files = glob_module.glob(search_path, recursive=True)
        rel_files = [os.path.relpath(f, WORKSPACE_ROOT) for f in files if os.path.isfile(f)]
        return {"files": rel_files}
    except Exception as e:
        return {"error": str(e)}

TOOLS = [
    {"type": "function", "function": {"name": "read_file", "description": "Read file lines", "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "start_line": {"type": "integer"}, "read_lines": {"type": "integer"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "write_file", "description": "Write entire file", "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}}, "required": ["path", "content"]}}},
    {"type": "function", "function": {"name": "list_files", "description": "List files in directory", "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "pattern": {"type": "string"}}, "required": []}}},
    {"type": "function", "function": {"name": "edit_file", "description": "Edit lines in a file", "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "operation": {"type": "string", "enum": ["replace", "insert", "delete"]}, "start_line": {"type": "integer"}, "end_line": {"type": "integer"}, "content": {"type": "string"}}, "required": ["path", "operation", "start_line"]}}}
]
AVAILABLE_TOOLS = {"read_file": read_file, "write_file": write_file, "list_files": list_files, "edit_file": edit_file}

# --- Agent System ---

def build_system_prompt() -> str:
    prompt = "You are Research Desk, a helpful research assistant. You can read, write, and edit files in the workspace."
    for path in AGENTS_PATHS:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                prompt += f"\n\n{f.read()}"
            break
    return prompt

class Agent:
    """Core agent: loop, tools, sessions. No UI."""

    def __init__(self, workspace: str = ".", session_id: str | None = None):
        self.workspace = os.path.abspath(workspace)
        os.makedirs(SESSIONS_DIR, exist_ok=True)
        
        # Load existing session or create new memory
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
            response = client.chat.completions.create(model=MODEL, messages=self.messages, tools=TOOLS)
            msg = response.choices[0].message
            self.messages.append(msg)

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
        """Override in REPLAgent/TUIAgent for tool logging."""
        pass


class REPLAgent(Agent):
    """Terminal REPL + one-shot CLI."""

    def run(self) -> None:
        print(f"Research Desk [{self.session_id}] — /quit to exit")
        while True:
            try:
                user_input = input("\n> ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                break
            if not user_input or user_input in ("/quit", "/exit"):
                break
            print(f"\nAgent: {self.chat(user_input)}")

    def _emit(self, event: str, **data) -> None:
        if event == "tool_call":
            print(f"  [🔧 Tool Running: {data.get('name')}]", file=sys.stderr)


def main():
    agent = REPLAgent()
    if len(sys.argv) > 1:
        print(agent.run_once(" ".join(sys.argv[1:])))
        return
    agent.run()

if __name__ == "__main__":
    main()