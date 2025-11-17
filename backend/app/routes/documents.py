from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List
import os
from app.services.rag_service import rag_service

router = APIRouter()


@router.post("/upload")
async def upload_documents(files: List[UploadFile] = File(...)):
    saved = []
    os.makedirs("backend/data/uploads", exist_ok=True)
    for f in files:
        contents = await f.read()
        out_path = os.path.join("backend", "data", "uploads", f.filename)
        with open(out_path, "wb") as fh:
            fh.write(contents)
        # process document: chunk, embed, store
        await rag_service.process_document(out_path, filename=f.filename)
        saved.append({"filename": f.filename, "path": out_path})
    return {"saved": saved}


@router.get("/list")
async def list_documents():
    # TODO: list ingested documents
    return {"documents": []}
