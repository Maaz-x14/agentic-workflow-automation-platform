from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import uuid

router = APIRouter()


class WorkflowCreate(BaseModel):
    name: str
    nodes: dict = {}


@router.post("/", status_code=201)
async def create_workflow(payload: WorkflowCreate):
    # TODO: persist workflow
    workflow_id = str(uuid.uuid4())
    return {"id": workflow_id, "name": payload.name}


@router.get("/{workflow_id}")
async def get_workflow(workflow_id: str):
    # TODO: retrieve workflow
    if not workflow_id:
        raise HTTPException(status_code=404, detail="Not found")
    return {"id": workflow_id, "name": "Demo Workflow", "nodes": []}


@router.post("/run/{workflow_id}")
async def run_workflow(workflow_id: str):
    # TODO: kick off workflow execution via workflow_engine
    exec_id = str(uuid.uuid4())
    return {"execution_id": exec_id, "status": "started"}


@router.get("/{workflow_id}/executions")
async def list_executions(workflow_id: str):
    # TODO: list executions
    return [{"execution_id": "example-exec-1", "status": "finished"}]


@router.get("/execution/{exec_id}")
async def get_execution(exec_id: str):
    # TODO: fetch execution trace
    return {"execution_id": exec_id, "status": "finished", "steps": []}
