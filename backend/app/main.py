from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import workflow, documents, search, execution, agent_router

app = FastAPI(title="Agentic Workflow Automation Platform - Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok"}


app.include_router(workflow.router, prefix="/workflow", tags=["workflow"])
app.include_router(documents.router, prefix="/documents", tags=["documents"])
app.include_router(search.router, prefix="/search", tags=["search"])
app.include_router(execution.router, prefix="/execution", tags=["execution"])
app.include_router(agent_router.router, prefix="/agent", tags=["agent"])
