from pydantic import BaseModel
from typing import Any, List, Optional
from datetime import datetime

# defines what your API JSON looks like (inputs and outputs)
class WorkflowCreate(BaseModel):  # POST request to create a new workflow
    name: str
    graph_json: Any  # User must provide the React Flow graph data


class WorkflowOut(BaseModel):  # When the Backend sends data back to the Frontend
    id: int
    name: str
    graph_json: Any
    created_at: datetime

    class Config:
        from_attributes = True  # Tells pydantic, giving you a SQLAlchemy database object (from models.py)


class ExecutionOut(BaseModel):  # specific "Run" of a workflow
    id: int
    workflow_id: int  # Links it back to the parent design
    status: str
    started_at: datetime
    finished_at: Optional[datetime]

    class Config:
        from_attributes = True  


class StepResultOut(BaseModel):  # logs for a single node execution
    id: int
    execution_id: int
    node_id: str
    node_type: str
    input: Any
    output: Any
    timestamp: datetime

    class Config:
        from_attributes = True  