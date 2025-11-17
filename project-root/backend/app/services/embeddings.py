from typing import List


class Embeddings:
    def __init__(self):
        pass

    async def embed_texts(self, texts: List[str]):
        # Placeholder: return list of zero vectors
        return [[0.0] * 768 for _ in texts]


embeddings = Embeddings()
