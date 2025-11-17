from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def search(q: str = "", limit: int = 5):
    # Dummy results for now; real implementation will query PGVector
    results = [
        {"id": f"chunk_{i}", "text": f"Result for {q} - chunk {i}", "score": 1.0 / (i + 1)}
        for i in range(limit)
    ]
    return {"query": q, "results": results}
