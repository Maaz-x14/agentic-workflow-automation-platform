from fastapi import APIRouter
from app.services.rag_service import rag_service

router = APIRouter()


@router.get("/")
async def search(q: str = "", limit: int = 5):
    results = await rag_service.search(q, top_k=limit)
    return {"query": q, "results": results}
