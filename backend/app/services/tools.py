"""Tool implementations: a web search tool (Tavily) and a file writer.

These are exposed both as raw functions and as LangChain @tool-wrapped
objects when LangChain is available. The implementations prefer local
CLI tools when present (tavily, ollama) and fall back to HTTP-based
fetching.
"""
from typing import Optional
import shutil
import os
import httpx

_HAS_TAVILY = shutil.which("tavily") is not None


def web_search_raw(query: str) -> str:
    """Search the web for `query` using Tavily if available, otherwise a simple fetch.

    Returns a string summarizing results (plain text).
    """
    query = query or ""
    # Prefer Tavily CLI if installed
    if _HAS_TAVILY:
        try:
            # tavily search <query> --json  (assumed CLI)
            import subprocess, json
            proc = subprocess.run(["tavily", "search", query, "--json"], capture_output=True, text=True)
            if proc.returncode == 0 and proc.stdout:
                try:
                    payload = json.loads(proc.stdout)
                    # naive: join titles/snippets
                    items = []
                    for r in payload.get("results", [])[:10]:
                        title = r.get("title") or r.get("headline") or ""
                        snippet = r.get("snippet") or r.get("summary") or ""
                        items.append(f"{title}: {snippet}")
                    return "\n---\n".join(items)
                except Exception:
                    return proc.stdout.strip()
        except Exception:
            pass

    # Fallback: simple DuckDuckGo HTML scrape (via allorigins proxy to avoid CORS)
    try:
        url = f"https://html.duckduckgo.com/html?q={httpx.utils.quote(query)}"
        r = httpx.get(url, timeout=15.0)
        if r.status_code == 200:
            text = r.text
            # keep first N chars to avoid huge payloads
            return text[:8000]
    except Exception:
        pass

    return ""


# Try to provide a LangChain-compatible tool wrapper if langchain is installed.
try:
    from langchain.tools import tool

    @tool
    def web_search_tool(query: str) -> str:  # type: ignore
        return web_search_raw(query)
except Exception:
    web_search_tool = web_search_raw


def file_writer_raw(filename: str, content: str) -> str:
    """Write `content` to a filename under `backend/data/` and return the path."""
    os.makedirs("backend/data", exist_ok=True)
    safe_name = os.path.basename(filename)
    path = os.path.join("backend", "data", safe_name)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(content or "")
    return path


try:
    from langchain.tools import tool

    @tool
    def file_writer(path: str, content: str) -> str:  # type: ignore
        return file_writer_raw(path, content)
except Exception:
    file_writer = file_writer_raw
