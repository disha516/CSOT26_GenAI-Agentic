# Week 3 Submission: Research Desk 🚀

## Overview
This week, I upgraded the basic Perplexity clone from Week 2 into a full-fledged "Research Desk" — an AI agent that actually has a memory, follows specific project rules, and can read academic papers. As an electrical engineering undergrad, I'm used to systems breaking and having to debug them piece by piece, but giving an AI agent persistent memory and file-writing capabilities was a totally different and exciting challenge!

## What I Built & Why

1. **Persistent Sessions (The Agent's Memory):** Instead of the agent developing amnesia every time I closed the terminal, I implemented a system to save conversation history to disk as JSON files in `.agent/sessions/`. Now, the agent remembers episodic context (e.g., "what were we talking about yesterday?").

2. **Procedural Memory with `AGENTS.md`:**
   I connected the system prompt to dynamically load rules from `AGENTS.md` on startup. This gives the agent a clear identity and operational boundaries, mimicking the architecture of systems like OpenCode.

3. **Academic Paper Tools (Replacing MCP):**
   I replaced the Week 2 AlphaXiv MCP with custom Python code (`tools/papers.py`) using the Hugging Face Papers API. The agent can now use `paper_search` and `read_paper` independently to pull actual arXiv data for academic queries, instead of just relying on general web searches.

4. **File Operations:**
   Added `files.py` to allow the agent to sandboxed file operations (`read_file`, `write_file`). It can now compile its research findings and save them directly into the `notes/` directory.

5. **The Triple Interface:**
   I separated the core logic (`Agent` brain) from the UI. The same brain now seamlessly powers:
   * A single-shot CLI (`python agent.py "query"`)
   * An interactive REPL loop
   * A Textual TUI (`python agent.py --tui`)

## The Real Engineering (Challenges & Fixes)
Building this wasn't just about writing new features; it was heavily about debugging real-world backend issues:

* **The 402 Token Limit Error:** While testing the OpenRouter API, I hit an "Insufficient Funds" error because the model tried to reserve ~65k tokens. I fixed this by explicitly setting a `max_tokens=2000` limit in the `chat.completions.create` call.
* **The JSON Serialization Crash:** When trying to save sessions to disk, Python threw a `TypeError` because it couldn't serialize the `ChatCompletionMessage` object. I resolved this by applying `.model_dump(exclude_none=True)` to cleanly convert the object into a standard dictionary before appending it to memory.
* **The Textual UI Freeze:** The biggest hurdle was the TUI crashing with a `call_from_thread` RuntimeError. The UI main thread was getting blocked by the API calls. After trying Textual's `@work` decorator, I ultimately re-architected the UI update logic to use Python's native `threading.Thread`. It cleanly pushed the AI processing to the background, leaving the UI perfectly smooth and responsive!

## Conclusion
This week bridged the gap between a simple script and a robust application architecture. Having separate modules for tools, a decoupled agent brain, and persistent storage makes this feel like a real software product ready for more complex tasks.