# Week 5 Capstone: Making Code Scout Extensible

## The Big Picture: What's New?
Last week, my agent was capable but rigid. If I wanted to teach it a new workflow, I had to hardcode it into the system prompt or write a new Python tool. This week, I completely decoupled the agent's capabilities from its core code. 

Now, Code Scout can learn new procedures just by dropping a markdown file into a folder (Skills), and it can interact with the outside world by reading a simple JSON config file (MCP). It feels less like a hardcoded script and more like a modular system where every component plugs in cleanly.

## Feature 1: Progressive Disclosure (The Skills System)
**What I built:** I created a `skills/` directory and implemented a `commit` skill. 
**Why I chose it:** I wanted a way to safely stage and commit my work without bloating the main system prompt. 
**How it works:** On startup, `agent.py` scans the `skills/` directory, parses the YAML frontmatter of `SKILL.md`, and injects *only* the name and description into the system prompt. When I ask the agent to "save my work", it triggers the `load_skill` tool, reads the full markdown body, and executes the step-by-step Git procedure. 

## Feature 2: Configuration as Code (MCP Servers)
**What I built:** I integrated the official Python MCP SDK, allowing the agent to connect to remote servers (specifically GitHub) via a `config.json` file.
**Why I chose it:** Hardcoding API endpoints inside the Python logic is a bad practice. By moving this to `config.json`, I can add new external tools without touching a single line of Python.
**How it works:** The `MCPManager` reads `config.json` at startup, dynamically substitutes `${GITHUB_PAT}` with my secure token from `.env`, and establishes an async connection. It automatically pulled in 44 GitHub tools.

## Testing, Surprises, and Failures
1. **The Fake Token Crash:** To test the MCP trust boundary, I purposely supplied a dummy `GITHUB_PAT`. The connection actively refused the handshake and threw a 401 Unauthorized error. This proved the agent was successfully routing to the real GitHub API before I gave it a real key.
2. **Smart Boundaries:** When testing my `commit` skill, the agent noticed that some modified files were outside my immediate project directory. Instead of blindly running `git add -A`, it stopped and asked me for clarification. 

## The "Cool Feature" Recipe: End-to-End Live Repo Scraping
Here is a task you can hand the agent in one sentence and walk away from. It uses the GitHub MCP to fetch live repository data.

**The Task:** "facebook and react"
**What the agent does:** It dynamically understands the intent, uses the `search_repositories` MCP tool, connects to the live repo, and fetches real-time stats, formatting them perfectly.

**Live Terminal Output Proof:**
```text
> facebook and react
  [🔧 Tool Running: search_repositories]

Agent: Here are two popular GitHub repositories related to Facebook and React, sorted by stars:

1.  **fbsamples/f8app**
    * **Description**: "Source code of the official F8 app of 2017, powered by React Native and other Facebook open source projects."
    * **Stars**: 13,902
    * **Language**: JavaScript
    * **URL**: [https://github.com/fbsamples/f8app](https://github.com/fbsamples/f8app)

2.  **cookpete/react-player**
    * **Description**: "A React component for playing a variety of URLs..."
    * **Stars**: 10,270
    * **Language**: TypeScript
    * **URL**: [https://github.com/cookpete/react-player](https://github.com/cookpete/react-player)
```

**Replication Recipe:**
1. Clone this repository and ensure you are inside the `week_5/project` directory.
2. Create a `.env` file and add your actual GitHub Personal Access Token: `GITHUB_PAT=github_pat_...`
3. Ensure `config.json` exists with the `api.githubcopilot.com/mcp/` endpoint.
4. Run the agent: `python agent.py`
5. You should see `✅ Connected to MCP Server 'github': 44 tools loaded.`
6. Give the prompt: *"facebook and react"*