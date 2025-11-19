from fastapi import APIRouter, HTTPException, Depends
from app.db.database import AsyncSessionLocal
from app.db import models
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Any, List, Dict
from app.services.agent_service import run_single_agent

router = APIRouter()


class Node(BaseModel):
    id: str
    type: str | None = None
    data: Dict[str, Any] | None = None


class Edge(BaseModel):
    id: str | None = None
    source: str
    target: str


class WorkflowRequest(BaseModel):
    nodes: List[Node]
    edges: List[Edge]

router = APIRouter()


async def get_session() -> AsyncSession:
    async with AsyncSessionLocal() as s:
        yield s


@router.get("/{exec_id}")
async def get_execution(exec_id: int, session: AsyncSession = Depends(get_session)):
    ex = await session.get(models.Execution, exec_id)
    if not ex:
        raise HTTPException(status_code=404, detail="Execution not found")
    steps_q = await session.execute(models.StepResult.__table__.select().where(models.StepResult.execution_id == ex.id))
    steps = steps_q.fetchall()
    steps_out = []
    for s in steps:
        steps_out.append({
            "id": s.id,
            "node_id": s.node_id,
            "node_type": s.node_type,
            "input": s.input,
            "output": s.output,
            "timestamp": str(s.timestamp),
        })
    return {"execution_id": ex.id, "status": ex.status, "steps": steps_out}


@router.post("/run")
async def run_workflow_graph(payload: WorkflowRequest):
    """Run a provided workflow graph (nodes + edges). For now iterate nodes and execute agent nodes."""
    results: Dict[str, Any] = {}
    try:
        print(f"Received Graph: {len(payload.nodes)} nodes, {len(payload.edges)} edges")
    except Exception:
        print("Received Graph: could not read payload sizes")

    for node in payload.nodes:
        print(f"Checking Node ID: {node.id}, Type: {node.type}")
        ntype = node.type or (node.data or {}).get("nodeType")
        # Ensure we look for exactly 'agent' type
        if ntype == "agent":
            goal = (node.data or {}).get("goal") or (node.data or {}).get("prompt") or ""
            if not goal:
                print(f"⚠️ Node {node.id} is missing 'goal' in data")
                results[node.id] = {"status": "skipped", "reason": "missing goal"}
                continue

            print(f"Found Agent Node! Goal: {goal}")
            try:
                res = await run_single_agent(goal)
                print(f"Agent result for node {node.id}: {res}")
                results[node.id] = res
            except Exception as e:
                print(f"Error running agent for node {node.id}: {e}")
                results[node.id] = {"status": "error", "detail": str(e)}
        else:
            print(f"Node {node.id} is not an agent (type={ntype}); skipping")

    return {"status": "completed", "results": results}
