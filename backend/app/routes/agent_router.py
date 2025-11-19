from fastapi import APIRouter
from pydantic import BaseModel
from typing import Any
from app.services.agent_service import run_single_agent

router = APIRouter()


class AgentRunRequest(BaseModel):
    goal: str | None = None


@router.post("/test_agent")
async def test_agent(payload: AgentRunRequest):
    goal = payload.goal or "Search for info on LangGraph and save it to a file."
    res = await run_single_agent(goal)
    return res