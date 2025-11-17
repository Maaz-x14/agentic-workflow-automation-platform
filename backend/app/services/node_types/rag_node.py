from app.services.rag_service import rag_service

async def execute(node_data: dict):
    query = node_data.get("query") or node_data.get("prompt") or ""
    results = await rag_service.search(query, top_k=node_data.get("top_k", 5))
    return {"results": results}
