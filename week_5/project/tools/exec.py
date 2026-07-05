import os
import shlex
import subprocess

WORKSPACE_ROOT = os.path.abspath(os.environ.get("WORKSPACE_ROOT", "."))
TIMEOUT_DEFAULT = 10
MAX_OUTPUT_CHARS = 8000
READ_ONLY_PREFIXES = ("dir ", "grep", "find", "ls", "cat", "head", "tail", "wc", "git log", "git diff", "git status", "git blame", "git show", "pytest", "python -m pytest", "ruff", "flake8", "mypy")
DESTRUCTIVE_PATTERNS = ("rm ", "mv ", ">", ">>", "git commit", "git push", "git checkout --", "pip install", "npm install", "curl ", "sudo ", "chmod ")

def paths_within_sandbox(command: str, workspace_root: str) -> bool:
    try:
        tokens = shlex.split(command)
    except ValueError:
        return False
    abs_workspace = os.path.abspath(workspace_root)
    for token in tokens:
        if token.startswith('/') or '..' in token:
            abs_token = os.path.abspath(os.path.join(abs_workspace, token))
            if not abs_token.startswith(abs_workspace):
                return False
    return True

def classify_command(command: str) -> str:
    for pattern in DESTRUCTIVE_PATTERNS:
        if pattern in command:
            return "ask"
    for prefix in READ_ONLY_PREFIXES:
        if command.startswith(prefix):
            return "read_only"
    return "ask"

def run_command(command: str, cwd: str = WORKSPACE_ROOT, timeout: int = TIMEOUT_DEFAULT) -> dict:
    if not paths_within_sandbox(command, cwd):
        return {"error": "Command blocked: attempted to access files outside sandbox."}
        
    if classify_command(command) == "ask":
        print(f"\n⚠️ WARNING: The agent wants to run a potentially destructive or unclassified command:")
        print(f"👉 {command}")
        choice = input("Allow this command? (y/n): ").strip().lower()
        if choice != 'y':
            return {"error": "Command blocked by human operator."}
            
    try:
        result = subprocess.run(command, shell=True, cwd=cwd, timeout=timeout, capture_output=True, text=True)
        stdout = result.stdout[:MAX_OUTPUT_CHARS] + ("\n...[TRUNCATED]" if len(result.stdout) > MAX_OUTPUT_CHARS else "")
        stderr = result.stderr[:MAX_OUTPUT_CHARS] + ("\n...[TRUNCATED]" if len(result.stderr) > MAX_OUTPUT_CHARS else "")
        return {"exit_code": result.returncode, "stdout": stdout, "stderr": stderr}
    except subprocess.TimeoutExpired:
        return {"error": f"Command timed out after {timeout} seconds."}
    except Exception as e:
        return {"error": f"Execution failed: {str(e)}"}

EXEC_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "run_command",
            "description": "Run a shell command in the workspace and return its output. Use this to run tests, search, or make changes.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "The shell command to run."},
                    "timeout": {"type": "integer"}
                },
                "required": ["command"]
            }
        }
    }
]