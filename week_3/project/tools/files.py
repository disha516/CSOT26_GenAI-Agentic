"""
Sandboxed file tools — see week_3/2_agent_class.md

Implement:
  - resolve_path
  - read_file(path, start_line=1, read_lines=200)  — numbered lines, has_more
  - write_file(path, content)
  - edit_file(path, operation, start_line, end_line?, content?)  — replace | delete | append
  - list_files(path, pattern)
"""

# TODO: implement — see Build 2
import os
import glob as glob_module

WORKSPACE_ROOT = os.path.abspath(os.environ.get("WORKSPACE_ROOT", "."))

def resolve_path(path: str) -> str:
    target = os.path.abspath(os.path.join(WORKSPACE_ROOT, path))
    if not target.startswith(WORKSPACE_ROOT):
        raise ValueError(f"Path {path} is outside the workspace.")
    return target

def read_file(path: str, start_line: int = 1, read_lines: int = 200) -> dict:
    try:
        target = resolve_path(path)
        with open(target, "r", encoding="utf-8") as f:
            lines = f.readlines()
        end_line = min(start_line + read_lines - 1, len(lines))
        content = "".join([f"{i+1}| {lines[i]}" for i in range(start_line - 1, end_line)])
        return {"content": content, "has_more": end_line < len(lines), "end_line": end_line}
    except Exception as e:
        return {"error": str(e)}

def write_file(path: str, content: str) -> dict:
    try:
        target = resolve_path(path)
        os.makedirs(os.path.dirname(target) or ".", exist_ok=True)
        with open(target, "w", encoding="utf-8") as f:
            f.write(content)
        return {"success": True, "path": path}
    except Exception as e:
        return {"error": str(e)}

def edit_file(path: str, operation: str, start_line: int, end_line: int | None = None, content: str | None = None) -> dict:
    try:
        target = resolve_path(path)
        with open(target, "r", encoding="utf-8") as f:
            lines = f.readlines()
        start_idx = start_line - 1
        end_idx = end_line if end_line else start_line
        new_lines = [l + '\n' for l in (content.split('\n') if content else []) if l]
        
        if operation == "replace": lines[start_idx:end_idx] = new_lines
        elif operation == "delete": del lines[start_idx:end_idx]
        elif operation in ["insert", "append"]: lines[start_idx:start_idx] = new_lines
            
        with open(target, "w", encoding="utf-8") as f:
            f.writelines(lines)
        return {"success": True, "operation": operation}
    except Exception as e:
        return {"error": str(e)}

def list_files(path: str = ".", pattern: str = "*") -> dict:
    try:
        target_dir = resolve_path(path)
        search_path = os.path.join(target_dir, "**", pattern)
        files = glob_module.glob(search_path, recursive=True)
        return {"files": [os.path.relpath(f, WORKSPACE_ROOT) for f in files if os.path.isfile(f)]}
    except Exception as e:
        return {"error": str(e)}
