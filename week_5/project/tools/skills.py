import os

WORKSPACE_ROOT = os.path.abspath(os.environ.get("WORKSPACE_ROOT", "."))
SKILLS_DIR = os.path.join(WORKSPACE_ROOT, "skills")

def _parse_skill_file(skill_name: str) -> dict | None:
    """Helper to parse YAML frontmatter and body from SKILL.md"""
    skill_path = os.path.join(SKILLS_DIR, skill_name, "SKILL.md")
    if not os.path.isfile(skill_path):
        return None
    
    with open(skill_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Split by '---' to separate YAML metadata from Markdown body
    parts = content.split("---")
    if len(parts) >= 3:
        metadata_text = parts[1].strip()
        body_text = "---".join(parts[2:]).strip()
        
        metadata = {}
        for line in metadata_text.split('\n'):
            if ':' in line:
                k, v = line.split(':', 1)
                metadata[k.strip()] = v.strip()
        
        return {"metadata": metadata, "body": body_text}
    return None

def get_all_skills_metadata() -> str:
    """Scans the skills directory and returns a formatted string of available skills."""
    if not os.path.isdir(SKILLS_DIR):
        return ""
        
    skills_info = []
    for item in os.listdir(SKILLS_DIR):
        if os.path.isdir(os.path.join(SKILLS_DIR, item)):
            parsed = _parse_skill_file(item)
            if parsed and "metadata" in parsed:
                name = parsed["metadata"].get("name", item)
                desc = parsed["metadata"].get("description", "No description")
                skills_info.append(f"- Skill '{name}': {desc}")
                
    if skills_info:
        return "\nAVAILABLE SKILLS:\n" + "\n".join(skills_info)
    return ""

def load_skill(name: str) -> dict:
    """Load the full instructions for a specific skill."""
    parsed = _parse_skill_file(name)
    if not parsed:
        return {"error": f"Skill '{name}' not found. Check if skills/{name}/SKILL.md exists."}
    
    return {
        "status": "success",
        "name": parsed["metadata"].get("name", name),
        "instructions": parsed["body"]
    }

SKILL_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "load_skill",
            "description": "Load the full procedure for a specific skill. Call this when a user asks for a task that matches an available skill's description.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "The exact name of the skill to load (e.g., 'commit')"}
                },
                "required": ["name"]
            }
        }
    }
]