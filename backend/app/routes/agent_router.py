from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Any
import asyncio
from dotenv import load_dotenv
load_dotenv()

router = APIRouter()


class AgentRunRequest(BaseModel):
    goal: str | None = None


@router.post("/test_agent")
async def test_agent(payload: AgentRunRequest):
    """Run a small agent that searches the web and writes results to a file.

    This endpoint attempts to use LangChain's AgentExecutor and a local
    Ollama LLM. If LangChain or Ollama is not available, it falls back to a
    procedural execution using the tools directly.
    """
    goal = payload.goal or "Search for info on LangGraph and save it to a file."

    # Import tools (these may be LangChain tool wrappers or plain functions)
    from app.services.tools import web_search_tool, file_writer

    # Try to use LangChain's agent stack if available
    try:
        # Lazy imports so endpoint can still exist without langchain installed
        from langchain.agents import create_tool_calling_agent, AgentExecutor
        from langchain.schema import HumanMessage
        # Create a very small Ollama-backed LLM wrapper for LangChain if possible
        try:
            # Attempt to use the LangChain Ollama wrapper (if present in the environment)
            from langchain_ollama import Ollama
            llm = Ollama()
        except Exception:
            # Fallback: define a tiny LangChain-compatible LLM wrapper that calls the
            # local `ollama` CLI. This implements a minimal `__call__` style API used
            # by some LangChain helpers. Note: this is intentionally minimal and may
            # need package-specific adjustments in your environment.
            import subprocess
            from langchain.llms.base import LLM

            class OllamaCLI(LLM):
                """Minimal LangChain LLM wrapper that calls `ollama chat llama3` via CLI."""

                def _call(self, prompt: str, stop: list | None = None) -> str:  # type: ignore
                    proc = subprocess.run(["ollama", "chat", "llama3", "--stdin"], input=prompt, capture_output=True, text=True)
                    return proc.stdout if proc.returncode == 0 else proc.stderr

                def _identifying_params(self):
                    return {"backend": "ollama-cli"}

            llm = OllamaCLI()

        tools = [web_search_tool, file_writer]

        # create_tool_calling_agent returns an Agent instance; wrap with AgentExecutor
        agent = create_tool_calling_agent(llm, tools)
        agent_executor = AgentExecutor.from_agent_and_tools(agent, tools, verbose=True)

        # Run the agent on the user's goal
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, lambda: agent_executor.run(goal))

        return {"status": "ok", "result": str(result)}
    except Exception as e:
        # Fallback behavior: call tools directly (safe offline path)
        try:
            # web_search_tool may be a LangChain Tool object or a plain function.
            if hasattr(web_search_tool, "run"):
                search_res = web_search_tool.run("LangGraph")
            else:
                search_res = web_search_tool("LangGraph")

            # Save to file
            filename = "langgraph_search.txt"
            if hasattr(file_writer, "run"):
                path = file_writer.run(filename, search_res)
            else:
                path = file_writer(filename, search_res)

            return {"status": "fallback", "saved_path": path, "summary_snippet": (search_res or "")[:1000], "error": str(e)}
        except Exception as inner:
            raise HTTPException(status_code=500, detail={"error": str(e), "fallback_error": str(inner)})
