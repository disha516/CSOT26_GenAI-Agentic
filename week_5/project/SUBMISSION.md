# Week 5 Capstone: Making Code Scout Extensible

## The Big Picture: What's New?
Last week, my agent was capable but rigid. If I wanted to teach it a new workflow, I had to hardcode it into the system prompt or write a new Python tool. This week, I completely decoupled the agent's capabilities from its core code. 

Now, Code Scout can learn new procedures just by dropping a markdown file into a folder (Skills), and it can interact with the outside world by reading a simple JSON config file (MCP). It feels less like a hardcoded script and more like a modular system where every component plugs in cleanly.

## Feature 1: Progressive Disclosure (The Skills System)
**What I built:** I created a `skills/` directory and implemented a `commit` skill. 
**Why I chose it:** I wanted a way to safely stage and commit my work without bloating the main system prompt. Paying token costs on every turn for a Git workflow I only use at the end of a session didn't make sense.
**How it works:** On startup, `agent.py` scans the `skills/` directory, parses the YAML frontmatter of `SKILL.md`, and injects *only* the name and description into the system prompt. When I ask the agent to "save my work", it triggers the `load_skill` tool, reads the full markdown body, and executes the step-by-step Git procedure. 

## Feature 2: Configuration as Code (MCP Servers)
**What I built:** I integrated the official Python MCP SDK, allowing the agent to connect to remote servers (specifically GitHub) via a `config.json` file.
**Why I chose it:** Hardcoding API endpoints and auth headers inside the Python logic is a bad practice. By moving this to `config.json`, I can add new external tools (like a database or another API) without touching a single line of Python.
**How it works:** The `MCPManager` reads `config.json` at startup, dynamically substitutes `${GITHUB_PAT}` with my secure token from the `.env` file, and establishes an async connection using `streamablehttp_client`. It automatically pulled in 44 GitHub tools and merged them into the agent's dispatch loop.

## Testing, Surprises, and Failures
I didn't just assume things worked; I broke them on purpose:
1. **The Path Failure:** I initially ran the agent from the root directory instead of `project/`. The agent gracefully failed to find the skills folder, proving that my relative pathing and missing-directory fallbacks were working.
2. **The Fake Token Crash:** To test the MCP trust boundary, I purposely supplied a dummy `GITHUB_PAT`. The connection actively refused the handshake and threw a 401 Unauthorized error. This was a great validation that the agent was successfully routing to the real GitHub API before I even gave it a real key.
3. **Smart Boundaries:** When testing my `commit` skill, the agent noticed that some modified files were outside my immediate project directory. Instead of blindly running `git add -A`, it stopped and asked me for clarification. This safety guardrails surprised me in a good way!

## The "Cool Feature" Recipe: End-to-End Live Repo Scraping
Here is a task you can hand the agent in one sentence and walk away from. 

**The Task:** "List the latest issues from the freeCodeCamp/freeCodeCamp repository."
**What the agent does:** It understands the intent, matches it with the GitHub MCP tools, connects to the live repo, and fetches real-time, timestamped issues, formatting them nicely in the terminal.

**Replication Recipe:**
1. Clone this repository and ensure you are inside the `week_5/project` directory.
2. Create a `.env` file and add your actual GitHub Personal Access Token: `GITHUB_PAT=github_pat_...`
3. Ensure `config.json` exists with the `api.githubcopilot.com/mcp/` endpoint.
4. Run the agent: `python agent.py`
5. You should see `✅ Connected to MCP Server 'github': 44 tools loaded.`
6. Give the prompt: *"List the latest issues from the freeCodeCamp/freeCodeCamp repository."*
7. "Done" looks like the agent outputting a numbered list of live issues directly from GitHub, complete with labels and creation dates, without you ever opening a browser.