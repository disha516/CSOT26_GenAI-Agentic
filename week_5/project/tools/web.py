"""
Web search and fetch tools — carry forward from Week 2.

Implement or copy from your week_2/project/:
  - web_search(query) — Serper
  - web_fetch(url) — requests + trafilatura/markdownify
"""

# TODO: copy from Week 2 project
import os
import json
import requests
import trafilatura

def web_search(query: str) -> dict:
    url = "https://google.serper.dev/search"
    headers = {'X-API-KEY': os.environ.get("SERPER_API_KEY", ""), 'Content-Type': 'application/json'}
    try:
        response = requests.post(url, headers=headers, json={"q": query})
        results = response.json().get("organic", [])[:3]
        return {"results": results}
    except Exception as e:
        return {"error": str(e)}

def web_fetch(url: str) -> dict:
    try:
        downloaded = trafilatura.fetch_url(url)
        content = trafilatura.extract(downloaded) if downloaded else ""
        return {"content": content[:3000] if content else "Could not extract content."}
    except Exception as e:
        return {"error": str(e)}