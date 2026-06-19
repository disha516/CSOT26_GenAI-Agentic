"""
Paper search and read tools — Hugging Face Papers API (arXiv index).

Implement:
  - paper_search(query, limit) -> {papers: [{arxiv_id, title, abstract, url}, ...]}
  - read_paper(arxiv_id) -> {title, abstract, content, url, ...}

API docs: week_3/3_paper_tools.md
"""
import requests

def paper_search(query: str) -> dict:
    """Searches for academic papers using Hugging Face Papers API."""
    url = "https://huggingface.co/api/papers/search"
    try:
        response = requests.get(url, params={"q": query})
        if response.status_code == 200:
            # Return top 3 paper metadata
            return {"papers": response.json()[:3]}
        return {"error": f"API returned status {response.status_code}"}
    except Exception as e:
        return {"error": str(e)}

def read_paper(paper_id: str) -> dict:
    """Reads paper metadata and abstract using the paper ID."""
    url = f"https://huggingface.co/api/papers/{paper_id}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            return {
                "title": data.get("title"),
                "authors": [a.get("name") for a in data.get("authors", [])],
                "abstract": data.get("summary", "No abstract available.")
            }
        return {"error": "Paper not found or API error."}
    except Exception as e:
        return {"error": str(e)}