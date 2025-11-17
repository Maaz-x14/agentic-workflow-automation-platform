from typing import Any, Dict
from app.db import models
from app.db.database import AsyncSessionLocal
from app.services import llm_adapter, rag_service
import asyncio
from sqlalchemy import insert
import json


async def run_workflow(workflow_id: int):
    """Run a workflow stored in DB (synchronously for MVP)."""
    async with AsyncSessionLocal() as session:
        wf = await session.get(models.Workflow, workflow_id)
        if not wf:
            raise ValueError("Workflow not found")

        execution = models.Execution(workflow_id=workflow_id, status="running")
        session.add(execution)
        await session.flush()

        # nodes expected in wf.graph_json["nodes"]
        nodes = wf.graph_json.get("nodes", [])
        for node in nodes:
            node_id = node.get("id")
            ntype = node.get("type") or node.get("data", {}).get("nodeType", "llm_node")
            input_obj = node.get("data", {})
            output_obj = {}
            try:
                if ntype == "rag_node":
                    query = input_obj.get("query") or input_obj.get("prompt") or ""
                    results = await rag_service.rag_service.search(query, top_k=5)
                    output_obj = {"results": results}
                elif ntype == "llm_node":
                    messages = input_obj.get("messages") or [{"role": "user", "content": input_obj.get("prompt", "") }]
                    resp = await llm_adapter.generate_response(messages)
                    output_obj = {"response": resp}
                else:
                    # action_node or unknown
                    output_obj = {"result": f"executed {ntype}"}
                # persist step
                step = models.StepResult(
                    execution_id=execution.id,
                    node_id=str(node_id),
                    node_type=str(ntype),
                    input=input_obj,
                    output=output_obj,
                )
                session.add(step)
                await session.flush()
            except Exception as e:
                step = models.StepResult(
                    execution_id=execution.id,
                    node_id=str(node_id),
                    node_type=str(ntype),
                    input=input_obj,
                    output={"error": str(e)},
                )
                session.add(step)
                execution.status = "failed"
                await session.commit()
                return {"execution_id": execution.id, "status": "failed"}

        execution.status = "completed"
        await session.commit()
        return {"execution_id": execution.id, "status": "completed"}

