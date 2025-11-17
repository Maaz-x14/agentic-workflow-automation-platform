import os
from typing import List, Dict
from app.services.embeddings import generate_embedding
from app.db import models
from app.db.database import AsyncSessionLocal
import asyncio
import math
import json
from PyPDF2 import PdfReader


class RAGService:
    def __init__(self):
        # ensure uploads dir
        os.makedirs("backend/data/uploads", exist_ok=True)

    async def process_document(self, file_path: str, filename: str = None):
        """Process a file on disk: extract text, chunk, embed and store in DB."""
        filename = filename or os.path.basename(file_path)
        text = ""
        if filename.lower().endswith(".pdf"):
            try:
                reader = PdfReader(file_path)
                for p in reader.pages:
                    text += p.extract_text() or ""
            except Exception:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as fh:
                    text = fh.read()
        else:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as fh:
                text = fh.read()

        # chunk text into ~500 char chunks with overlap
        chunks = []
        chunk_size = 800
        overlap = 200
        i = 0
        while i < len(text):
            chunk = text[i:i+chunk_size]
            if chunk.strip():
                chunks.append(chunk.strip())
            i += chunk_size - overlap

        async with AsyncSessionLocal() as session:
            doc = models.Document(filename=filename)
            session.add(doc)
            await session.flush()
            for c in chunks:
                emb = await generate_embedding(c)
                chunk_model = models.DocumentChunk(document_id=doc.id, content=c, embedding=emb)
                session.add(chunk_model)
            await session.commit()
        return {"document": filename, "chunks": len(chunks)}

    async def search(self, query: str, top_k: int = 5) -> List[Dict]:
        q_emb = await generate_embedding(query)
        # load all chunks
        async with AsyncSessionLocal() as session:
            res = await session.execute(models.DocumentChunk.__table__.select())
            rows = res.fetchall()
            scored = []
            import numpy as np
            qv = np.array(q_emb, dtype=float)
            for r in rows:
                emb = r.embedding
                if not emb:
                    continue
                ev = np.array(emb, dtype=float)
                # cosine similarity
                denom = (np.linalg.norm(qv) * np.linalg.norm(ev))
                score = float(np.dot(qv, ev) / denom) if denom > 0 else 0.0
                scored.append({"id": r.id, "content": r.content, "score": score})
            scored.sort(key=lambda x: x["score"], reverse=True)
            return scored[:top_k]




rag_service = RAGService()
