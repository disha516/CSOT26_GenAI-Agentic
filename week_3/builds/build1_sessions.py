import json
import os
import uuid
from datetime import datetime, timezone

SESSIONS_DIR = ".agent/sessions"
AGENTS_PATHS = ("AGENTS.md", ".agent/AGENTS.md")

BASE_PROMPT = "You are Research Desk, a helpful research assistant."


def create_session() -> str:
    """Return a new 8-char hex session ID."""
    os.makedirs(SESSIONS_DIR, exist_ok=True)

    return uuid.uuid4().hex[:8]


def save_session(session_id: str, messages: list, title: str = "Untitled") -> None:
    """Write session JSON to .agent/sessions/{id}.json"""
    os.makedirs(SESSIONS_DIR, exist_ok=True)
    filepath = os.path.join(SESSIONS_DIR, f"{session_id}.json")
    
   
    session_data = {
        "id": session_id,
        "title": title,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "messages": messages
    }
    
    
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(session_data, f, indent=2)


def load_session(session_id: str) -> dict:
    """Load and return session dict including messages list."""
    filepath = os.path.join(SESSIONS_DIR, f"{session_id}.json")
    try:
       
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"id": session_id, "title": "New Session", "messages": []}


def list_sessions() -> list[dict]:
    """Return sessions sorted by updated_at descending."""
    if not os.path.exists(SESSIONS_DIR):
        return []
    
    sessions = []
   
    for filename in os.listdir(SESSIONS_DIR):
        if filename.endswith(".json"):
            filepath = os.path.join(SESSIONS_DIR, filename)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # Sirf metadata store kar rahe hain list ke liye (messages hata diye taaki memory bache)
                    sessions.append({
                        "id": data.get("id"), 
                        "title": data.get("title", "Untitled"), 
                        "updated_at": data.get("updated_at", "")
                    })
            except Exception:
                continue
                
    
    sessions.sort(key=lambda x: x["updated_at"], reverse=True)
    return sessions


def build_system_prompt() -> str:
    """Base prompt + AGENTS.md if it exists."""
    prompt = BASE_PROMPT
    
    
    for path in AGENTS_PATHS:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                prompt += f"\n\n{f.read()}"
            break  
            
    return prompt


if __name__ == "__main__":
    sid = create_session()
    messages = [
        {"role": "system", "content": build_system_prompt()},
        {"role": "user", "content": "What is a surface code?"},
        {"role": "assistant", "content": "A surface code is a type of quantum error correcting code."},
    ]
    save_session(sid, messages, title="Quantum error correction")
    print(f"Saved session: {sid}")
    print(f"All sessions: {list_sessions()}")
    print(f"Loaded: {load_session(sid)['title']}")