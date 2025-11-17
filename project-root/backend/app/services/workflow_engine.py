from typing import Any, Dict
import asyncio


async def execute_workflow(workflow: Dict[str, Any], inputs: Dict[str, Any] = None):
    """Simple sequential executor for workflow nodes.

    This is a placeholder for the real engine. It iterates over nodes
    in the given workflow (assumed list) and simulates execution.
    """
    trace = []
    inputs = inputs or {}
    for node in workflow.get("nodes", []):
        # simulate asynchronous node execution
        await asyncio.sleep(0.01)
        step = {"node_id": node.get("id"), "output": {"text": "ok"}}
        trace.append(step)
    return {"status": "finished", "trace": trace}
