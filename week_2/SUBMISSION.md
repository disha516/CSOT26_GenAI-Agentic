# Week 2 — ResearchBot Submission

## What I Built

A terminal-based AI research agent with a Textual TUI that can:
- Search the web for real-time information (weather, news, prices, etc.)
- Fetch and read full content from specific URLs
- Search ArXiv for recent academic research papers
- Hold multi-turn conversations with persistent history

---

## Extra Dependencies

Install all required packages using:

```bash
pip install openai python-dotenv textual requests
```

| Package | Purpose |
|---|---|
| `openai` | OpenAI-compatible SDK for OpenRouter API calls |
| `python-dotenv` | Loads API keys from `.env` file |
| `textual` | Terminal UI framework (tested on v8.2.7) |
| `requests` | HTTP calls for Serper, web fetch, and ArXiv |

---

## API Keys Required

Create a `.env` file in the project root with:
OPENROUTER_API_KEY=your_openrouter_key_here
SERPER_API_KEY=your_serper_key_here
- **OpenRouter API key** → https://openrouter.ai/keys  
- **Serper API key** → https://serper.dev (free tier gives 2500 searches)

---

## How to Run

```bash
# 1. Activate your virtual environment
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# 2. Install dependencies
pip install openai python-dotenv textual requests

# 3. Add your API keys to .env

# 4. Run the agent
python agent.py
```

---

## Keyboard Shortcuts

| Shortcut | Action |
|---|---|
| `Ctrl+L` | Clear display (both panels) |
| `Ctrl+K` | Reset conversation history |
| `Ctrl+S` | Save chat to timestamped `.txt` file |
| `Ctrl+Q` | Quit |

---

## Example Queries to Try

- `What is the current temperature in Delhi?`
- `Find recent research papers on electrodynamics`
- `What happened in AI news this week?`
- `Fetch https://en.wikipedia.org/wiki/Quantum_mechanics and summarize it`
- `What is the price of Bitcoin today?`

---

## Model Used

`google/gemini-2.5-flash` via OpenRouter


---

## What I Learned This Week

This week was a big step up from Week 1. Here is what I actually learned:

**Tool Calling** — I thought the model automatically fetches data from the internet,
but actually we have to manually define tools and the model just tells us
"call this tool with these arguments" — we execute it ourselves and send
the result back. That was a completely new mental model for me.

**Agent Loop** — Making a single API call was easy, but building a loop where
the model keeps requesting tools and we keep feeding results back until
it gives a final answer — this concept clicked for me this week and felt
very powerful.

**Textual TUI** — I had no idea Python could make such a clean terminal UI
with split panels, keyboard shortcuts, and real-time updates without
any web tech. Building the chat panel and tool activity log side by side
was really satisfying.

**Threading Bug (hardest part)** — Most of my debugging time went here.
The `call_from_thread` error kept appearing because `_process` was running
on the main thread instead of a background thread. Finally fixed it using
the `@work(thread=True)` decorator from Textual, which properly dispatches
the function to a worker thread.

**Web Search vs Web Fetch** — These are two different things. Search gives
a list of links and snippets. Fetch reads the full content of one specific
URL. Combining both makes the agent much more capable.

**Model Switch** — The assignment suggested using DeepSeek model
(`deepseek/deepseek-v4-flash:free`) but it was not working on OpenRouter
during development — requests were failing or returning empty responses.
So I switched to `google/gemini-2.5-flash` which worked perfectly and
handled tool calling very reliably throughout testing.