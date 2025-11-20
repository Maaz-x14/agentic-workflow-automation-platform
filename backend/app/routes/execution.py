from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from app.db.database import AsyncSessionLocal
from app.db import models
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
import json
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
    """Run a provided workflow graph (nodes + edges) and stream NDJSON events for UI feedback."""

    async def event_generator():
        try:
            try:
                print(f"Received Graph: {len(payload.nodes)} nodes, {len(payload.edges)} edges")
            except Exception:
                print("Received Graph: could not read payload sizes")

            # Build adjacency and indegree maps
            node_ids = [n.id for n in payload.nodes]
            adj: Dict[str, List[str]] = {nid: [] for nid in node_ids}
            indeg: Dict[str, int] = {nid: 0 for nid in node_ids}

            for e in payload.edges:
                # ensure edge endpoints exist
                if e.source not in adj or e.target not in adj:
                    print(f"Warning: edge references unknown node: {e}")
                    continue
                adj[e.source].append(e.target)
                indeg[e.target] = indeg.get(e.target, 0) + 1

            # Kahn's algorithm for topological ordering
            queue = [nid for nid, d in indeg.items() if d == 0]
            topo: List[str] = []
            while queue:
                cur = queue.pop(0)
                topo.append(cur)
                for nb in adj.get(cur, []):
                    indeg[nb] -= 1
                    if indeg[nb] == 0:
                        queue.append(nb)

            if len(topo) != len(node_ids):
                # cycle detected
                print("⚠️ Cycle detected in workflow graph; aborting run")
                # Yield an error and end
                yield (json.dumps({"type": "error", "node_id": None, "error": "Cycle detected in workflow graph"}) + "\n")
                return

            # Map node id -> node object for quick lookup
            node_map: Dict[str, Node] = {n.id: n for n in payload.nodes}

            # Execute nodes sequentially in topo order
            context: Dict[str, Any] = {}

            for nid in topo:
                node = node_map.get(nid)
                if not node:
                    continue

                # Notify start of node
                yield (json.dumps({"type": "start", "node_id": nid}) + "\n")

                print(f"Executing node {nid} (type={node.type})")
                ntype = node.type or (node.data or {}).get("nodeType")
                if ntype != 'agent':
                    print(f"Skipping non-agent node {nid}")
                    # send skipped as result
                    yield (json.dumps({"type": "result", "node_id": nid, "result": json.dumps({"status": "skipped", "reason": "not agent"})}) + "\n")
                    continue

                goal = (node.data or {}).get("goal") or (node.data or {}).get("prompt") or ""
                if not goal:
                    print(f"⚠️ Node {nid} missing goal; skipping")
                    yield (json.dumps({"type": "result", "node_id": nid, "result": json.dumps({"status": "skipped", "reason": "missing goal"})}) + "\n")
                    continue

                # Build context string from parent nodes' results
                parent_ids = [e.source for e in payload.edges if e.target == nid]
                parent_texts: List[str] = []
                for pid in parent_ids:
                    p_res = context.get(pid)
                    # If the parent produced a structured result, prefer passing along its raw search_context
                    if isinstance(p_res, dict):
                        if p_res.get('search_context'):
                            parent_texts.append("Previous Step Raw Findings:\n" + str(p_res.get('search_context')))
                        if p_res.get('result'):
                            parent_texts.append(str(p_res.get('result')))
                        else:
                            parent_texts.append(str(p_res))
                    else:
                        parent_texts.append(str(p_res))

                context_string = "\n---\n".join(parent_texts) if parent_texts else ""

                try:
                    res = await run_single_agent(goal, context=context_string)
                    print(f"Node {nid} result: {res}")
                    context[nid] = res

                    # send result event
                    yield (json.dumps({"type": "result", "node_id": nid, "result": res}) + "\n")

                except HTTPException:
                    # re-raise HTTPExceptions
                    raise
                except Exception as e:
                    print(f"Error executing node {nid}: {e}")
                    context[nid] = {"status": "error", "detail": str(e)}
                    yield (json.dumps({"type": "error", "node_id": nid, "error": str(e)}) + "\n")

            # final end event
            yield (json.dumps({"type": "end"}) + "\n")

        except Exception as e:
            # If some unexpected error occurs at generator level, emit an error event
            try:
                yield (json.dumps({"type": "error", "node_id": None, "error": str(e)}) + "\n")
            except Exception:
                pass

    return StreamingResponse(event_generator(), media_type="application/x-ndjson")
