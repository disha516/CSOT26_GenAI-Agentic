import os
import re
import ast

WORKSPACE_ROOT = os.path.abspath(os.environ.get("WORKSPACE_ROOT", "."))
MAX_GREP_RESULTS = 50
EXCLUDE_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build"}

def resolve_path(path: str) -> str | None:
    abs_workspace = os.path.abspath(WORKSPACE_ROOT)
    target_path = os.path.abspath(os.path.join(abs_workspace, path))
    if target_path.startswith(abs_workspace):
        return target_path
    return None

def grep(pattern: str, path: str = ".", case_sensitive: bool = False, max_results: int = MAX_GREP_RESULTS) -> dict:
    resolved_dir = resolve_path(path)
    if not resolved_dir or not os.path.isdir(resolved_dir):
        return {"error": f"Invalid or inaccessible directory: {path}"}

    flags = 0 if case_sensitive else re.IGNORECASE
    try:
        regex = re.compile(pattern, flags)
    except re.error as e:
        return {"error": f"Invalid regex pattern: {e}"}

    matches = []
    total_matches = 0

    for root, dirs, files in os.walk(resolved_dir):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        for file in files:
            file_path = os.path.join(root, file)
            rel_path = os.path.relpath(file_path, WORKSPACE_ROOT)
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    for line_num, line in enumerate(f, 1):
                        if regex.search(line):
                            total_matches += 1
                            if len(matches) < max_results:
                                matches.append({"file": rel_path, "line": line_num, "text": line.strip()})
            except (UnicodeDecodeError, PermissionError):
                continue

    return {"matches": matches, "truncated": total_matches > max_results, "total_matches": total_matches}

def list_definitions(path: str) -> dict:
    resolved_path = resolve_path(path)
    if not resolved_path or not os.path.isfile(resolved_path):
        return {"error": f"Invalid or missing file: {path}"}

    try:
        with open(resolved_path, "r", encoding="utf-8") as f:
            source = f.read()
        tree = ast.parse(source)
    except SyntaxError as e:
        return {"error": f"SyntaxError: Not a valid Python file - {e}"}
    except Exception as e:
        return {"error": f"Error reading file: {str(e)}"}

    definitions = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            kind = "async function" if isinstance(node, ast.AsyncFunctionDef) else "function"
            definitions.append({"kind": kind, "name": node.name, "line": node.lineno, "end_line": getattr(node, "end_lineno", node.lineno)})
        elif isinstance(node, ast.ClassDef):
            definitions.append({"kind": "class", "name": node.name, "line": node.lineno, "end_line": getattr(node, "end_lineno", node.lineno)})
            for sub_node in node.body:
                if isinstance(sub_node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    definitions.append({"kind": "method", "name": f"{node.name}.{sub_node.name}", "line": sub_node.lineno, "end_line": getattr(sub_node, "end_lineno", sub_node.lineno)})
    return {"definitions": definitions}

SEARCH_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "grep",
            "description": "Search file contents for a pattern across the workspace.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {"type": "string"},
                    "path": {"type": "string"},
                    "case_sensitive": {"type": "boolean"},
                    "max_results": {"type": "integer"}
                },
                "required": ["pattern"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_definitions",
            "description": "List the functions and classes declared in a Python file with line numbers.",
            "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}
        }
    }
]