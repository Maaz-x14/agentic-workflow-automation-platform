from fastapi import FastAPI
# Load .env automatically so TAVILY_API_KEY and other vars are available
from dotenv import load_dotenv
load_dotenv()
from fastapi.middleware.cors import CORSMiddleware

from app.routes import workflow, documents, search, execution, agent_router

app = FastAPI(title="Agentic Workflow Automation Platform - Backend")

# CORS - allow frontend dev server
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

# include routers
app.include_router(workflow.router, prefix="/workflow", tags=["workflow"])
app.include_router(documents.router, prefix="/documents", tags=["documents"])
app.include_router(search.router, prefix="/search", tags=["search"])
app.include_router(execution.router, prefix="/execution", tags=["execution"])
# Also expose execution endpoints under /workflow (so frontend can POST /workflow/run)
app.include_router(execution.router, prefix="/workflow", tags=["workflow-exec"])
app.include_router(agent_router.router, prefix="/agent", tags=["agent"])