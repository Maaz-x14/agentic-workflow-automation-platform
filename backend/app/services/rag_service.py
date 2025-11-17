from typing import List, Dict


class RAGService:
    def __init__(self):
        pass

    async def retrieve(self, query: str, top_k: int = 5) -> List[Dict]:
        # Placeholder: return dummy chunks
        return [{"id": f"chunk_{i}", "text": f"Context for {query} - {i}"} for i in range(top_k)]


rag_service = RAGService()
