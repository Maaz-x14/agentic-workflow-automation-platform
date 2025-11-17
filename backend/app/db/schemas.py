from pydantic import BaseModel
from typing import Any, List, Optional
from datetime import datetime


class WorkflowCreate(BaseModel):
    name: str
    graph_json: Any


class WorkflowOut(BaseModel):
    id: int
    name: str
    graph_json: Any
    created_at: datetime

    class Config:
        from_attributes = True  # <-- FIXED


class ExecutionOut(BaseModel):
    id: int
    workflow_id: int
    status: str
    started_at: datetime
    finished_at: Optional[datetime]

    class Config:
        from_attributes = True  # <-- FIXED


class StepResultOut(BaseEmodel):
    id: int
    execution_id: int
    node_id: str
    node_type: str
    input: Any
    output: Any
    timestamp: datetime

    class Config:
        from_attributes = True  # <-- FIXED