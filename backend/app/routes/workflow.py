from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Any
from app.db import models, schemas
from app.db.database import AsyncSessionLocal, init_db
from app.services.workflow_engine import run_workflow
from sqlalchemy.ext.asyncio import AsyncSession
import json

router = APIRouter()


class WorkflowCreate(BaseModel):
    name: str
    graph_json: Any


async def get_session() -> AsyncSession:
    async with AsyncSessionLocal() as s:
        yield s


@router.on_event("startup")
async def startup():
    await init_db()


@router.post("/", status_code=201)
async def create_workflow(payload: WorkflowCreate, session: AsyncSession = Depends(get_session)):
    wf = models.Workflow(name=payload.name, graph_json=payload.graph_json)
    session.add(wf)
    await session.flush()
    await session.commit()
    return {"id": wf.id, "name": wf.name}


@router.get("/{workflow_id}")
async def get_workflow(workflow_id: int, session: AsyncSession = Depends(get_session)):
    wf = await session.get(models.Workflow, workflow_id)
    if not wf:
        raise HTTPException(status_code=404, detail="Not found")
    return {"id": wf.id, "name": wf.name, "graph_json": wf.graph_json}


@router.post("/run/{workflow_id}")
async def run_workflow_endpoint(workflow_id: int):
    # synchronous run for MVP
    res = await run_workflow(workflow_id)
    return res


@router.get("/{workflow_id}/executions")
async def list_executions(workflow_id: int, session: AsyncSession = Depends(get_session)):
    q = await session.execute(models.Execution.__table__.select().where(models.Execution.workflow_id == workflow_id))
    rows = q.fetchall()
    items = [{"execution_id": r.id, "status": r.status} for r in rows]
    return items


@router.get("/execution/{exec_id}")
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
