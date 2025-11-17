from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List

router = APIRouter()


@router.post("/upload")
async def upload_documents(files: List[UploadFile] = File(...)):
    saved = []
    for f in files:
        # For the MVP we save uploads to ./data/uploads
        contents = await f.read()
        out_path = f"./data/uploads/{f.filename}"
        with open(out_path, "wb") as fh:
            fh.write(contents)
        saved.append({"filename": f.filename, "path": out_path})
    return {"saved": saved}


@router.get("/list")
async def list_documents():
    # TODO: list ingested documents
    return {"documents": []}
