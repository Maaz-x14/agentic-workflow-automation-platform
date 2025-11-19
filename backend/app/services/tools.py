import os
from dotenv import load_dotenv
load_dotenv()
import shutil
import subprocess
import traceback
from typing import Optional
from langchain_core.tools import tool

# 1. Try importing Tavily (python package)
try:
    from tavily import TavilyClient
    has_tavily_pkg = True
except Exception:
    TavilyClient = None
    has_tavily_pkg = False

# 2. Detect tavily CLI presence
has_tavily_cli = shutil.which("tavily") is not None

# 3. Try importing DuckDuckGo
try:
    from duckduckgo_search import DDGS
    has_ddg = True
except Exception:
    DDGS = None
    has_ddg = False

# 4. Try importing Wikipedia
try:
    import wikipedia
    has_wiki = True
except Exception:
    wikipedia = None
    has_wiki = False

def web_search_raw(query: str) -> str:
    """
    Robust searcher: Tavily -> DuckDuckGo -> Wikipedia -> Error
    """
    print(f"🔎 Searching for: '{query}'")
    print(f"DEBUG: Tavily Key Loaded? {bool(os.getenv('TAVILY_API_KEY'))}")
    print(f"DEBUG: Tavily python package present? {has_tavily_pkg}, Tavily CLI present? {has_tavily_cli}")
    results = []

    # STRATEGY A: TAVILY (Best for Agents) - try hard first
    tavily_key = os.getenv("TAVILY_API_KEY")
    if tavily_key:
        # Try Python package client first
        if has_tavily_pkg:
            try:
                print("   -> Trying Tavily (python client)...")
                client = TavilyClient(api_key=tavily_key)
                # prefer a search() method if present
                if hasattr(client, "search"):
                    response = client.search(query=query, max_results=3)
                elif hasattr(client, "text"):
                    response = client.text(query, max_results=3)
                else:
                    response = None

                # Parse possible response shapes
                if isinstance(response, dict) and response.get("results"):
                    for r in response.get("results", [])[:10]:
                        title = r.get("title") or r.get("headline") or ""
                        content = r.get("content") or r.get("snippet") or ""
                        results.append(f"Title: {title}\nContent: {content}\n")
                    # Save raw response for debugging
                    try:
                        with open('/tmp/web_search_debug.log', 'a', encoding='utf-8') as dbg:
                            dbg.write('TAVILY_CLIENT_RESPONSE:\n')
                            dbg.write(str(response) + '\n---\n')
                    except Exception:
                        pass
                    return "\n".join(results)
                if hasattr(response, "__iter__") and not isinstance(response, (str, bytes)):
                    for r in response:
                        if isinstance(r, dict):
                            title = r.get("title") or r.get("heading") or "No Title"
                            body = r.get("body") or r.get("content") or ""
                        else:
                            title = getattr(r, "title", "No Title")
                            body = getattr(r, "body", "")
                        results.append(f"Title: {title}\nSnippet: {body}\n")
                    if results:
                        try:
                            with open('/tmp/web_search_debug.log', 'a', encoding='utf-8') as dbg:
                                dbg.write('TAVILY_CLIENT_ITERABLE_RESPONSE:\n')
                                dbg.write(str(list(response)) + '\n---\n')
                        except Exception:
                            pass
                        return "\n".join(results)
            except Exception:
                print("   ❌ Tavily (python client) failed — full traceback:")
                traceback.print_exc()

        # Try Tavily CLI if python package unavailable or failed
        if has_tavily_cli:
            try:
                print("   -> Trying Tavily (CLI)...")
                env = os.environ.copy()
                env["TAVILY_API_KEY"] = tavily_key
                proc = subprocess.run(["tavily", "search", query, "--json"], capture_output=True, text=True, env=env, timeout=30)
                if proc.returncode == 0 and proc.stdout:
                    try:
                        import json as _json
                        payload = _json.loads(proc.stdout)
                        for r in payload.get("results", [])[:10]:
                            title = r.get("title") or r.get("headline") or ""
                            snippet = r.get("snippet") or r.get("summary") or ""
                            results.append(f"Title: {title}\nSnippet: {snippet}\n")
                        if results:
                            # Save CLI raw stdout for debugging
                            try:
                                with open('/tmp/web_search_debug.log', 'a', encoding='utf-8') as dbg:
                                    dbg.write('TAVILY_CLI_STDOUT:\n')
                                    dbg.write(proc.stdout + '\n---\n')
                            except Exception:
                                pass
                            return "\n".join(results)
                    except Exception:
                        # If output isn't JSON, return raw stdout truncated
                        out = proc.stdout.strip()
                        if out:
                            try:
                                with open('/tmp/web_search_debug.log', 'a', encoding='utf-8') as dbg:
                                    dbg.write('TAVILY_CLI_RAW_OUT:\n')
                                    dbg.write(out + '\n---\n')
                            except Exception:
                                pass
                            return out[:8000]
            except Exception:
                print("   ❌ Tavily (CLI) failed — full traceback:")
                traceback.print_exc()

    # STRATEGY B: DUCKDUCKGO (Free backup)
    if has_ddg:
        try:
            print("   -> Trying DuckDuckGo...")
            # Use the text method directly
            ddg_results = DDGS().text(query, max_results=3)
            if ddg_results:
                try:
                    with open('/tmp/web_search_debug.log', 'a', encoding='utf-8') as dbg:
                        dbg.write('DDG_RAW_RESULTS:\n')
                        dbg.write(str(ddg_results) + '\n---\n')
                except Exception:
                    pass
                for r in ddg_results:
                    # DDG keys vary, handle safely
                    title = r.get('title', 'No Title')
                    body = r.get('body', r.get('content', ''))
                    results.append(f"Title: {title}\nSnippet: {body}\n")
                return "\n".join(results)
        except Exception as e:
            print(f"   ❌ DuckDuckGo failed: {e}")

    # STRATEGY C: WIKIPEDIA (Last Resort)
    if has_wiki:
        try:
            print("   -> Trying Wikipedia...")
            wiki_res = wikipedia.summary(query, sentences=3)
            return f"Wikipedia Summary: {wiki_res}"
        except Exception as e:
             print(f"   ❌ Wikipedia failed: {e}")

    return "System Error: Search failed on all providers. Please check your internet or API keys."


def file_writer_raw(filename: str, content: str) -> str:
    """Writes content to backend/data/filename."""
    try:
        # Ensure we write to the 'data' directory relative to this file
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        data_dir = os.path.join(base_dir, "data")
        os.makedirs(data_dir, exist_ok=True)
        
        filepath = os.path.join(data_dir, filename)
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
            
        return f"Successfully wrote to {filepath}"
    except Exception as e:
        return f"Error writing file: {str(e)}"

# Create LangChain Tool Wrappers
@tool("web_search_tool")
def web_search_tool(query: str) -> str:
    """Search the web for information."""
    return web_search_raw(query)

@tool("file_writer")
def file_writer(filename: str, content: str) -> str:
    """Write a file to disk."""
    return file_writer_raw(filename, content)