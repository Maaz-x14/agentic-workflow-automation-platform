from fastapi import APIRouter, HTTPException, Depends
from app.db.database import AsyncSessionLocal
from app.db import models
from sqlalchemy.ext.asyncio import AsyncSession

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
