import json

_todos = []
_next_id = 1

def add_todos(todos: list[dict]) -> dict:
    global _next_id
    added = []
    for t in todos:
        new_todo = {
            "id": _next_id,
            "title": t.get("title", "Untitled task"),
            "description": t.get("description", ""),
            "verification_method": t.get("verification_method", "Run tests"),
            "status": "pending",
            "evidence": None
        }
        _todos.append(new_todo)
        added.append(new_todo)
        _next_id += 1
    return {"status": "success", "added": added}

def get_todos() -> dict:
    return {"todos": _todos, "total_todos": len(_todos)}

def mark_todo(todo_id: int, status: str, evidence: str = None) -> dict:
    for t in _todos:
        if t["id"] == todo_id:
            if status == "completed" and not evidence:
                return {"error": "Cannot mark as completed without evidence. Please provide test output or exit code."}
            t["status"] = status
            if evidence:
                t["evidence"] = evidence
            return {"status": "success", "updated_todo": t}
    return {"error": f"Todo with ID {todo_id} not found."}

def all_todos_completed() -> bool:
    """Helper function to check if plan is fully executed."""
    if not _todos:
        return False
    return all(t["status"] == "completed" for t in _todos)

PLAN_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "add_todos",
            "description": "Add new steps to your planning list. Always create a plan before making changes.",
            "parameters": {
                "type": "object",
                "properties": {
                    "todos": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "title": {"type": "string"},
                                "description": {"type": "string"},
                                "verification_method": {"type": "string"}
                            },
                            "required": ["title", "description", "verification_method"]
                        }
                    }
                },
                "required": ["todos"]
            }
        }
    },
    {
        "type": "function",
        "function": {"name": "get_todos", "description": "Get current todos and status.", "parameters": {"type": "object", "properties": {}}}
    },
    {
        "type": "function",
        "function": {
            "name": "mark_todo",
            "description": "Update todo status. MUST provide evidence to mark 'completed'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "todo_id": {"type": "integer"},
                    "status": {"type": "string", "enum": ["pending", "in_progress", "completed"]},
                    "evidence": {"type": "string"}
                },
                "required": ["todo_id", "status"]
            }
        }
    }
]