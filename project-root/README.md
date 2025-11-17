# Agentic Workflow Automation Platform (Local-first MVP)

This repository contains a scaffold for a local-first, zero-cost agentic workflow automation platform.

Structure
- `backend/` - FastAPI backend with services and dummy routes
- `frontend/` - Vite + React frontend with a minimal React Flow editor

Quick start (one-time)

1. Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

2. Frontend

```bash
cd frontend
# install node deps (npm, yarn, or pnpm)
npm install
npm run dev
```

APIs
- `GET /health` - health check
- `POST /workflow/` - create a workflow (dummy)
- `POST /workflow/run/{id}` - start a workflow (dummy)
- `POST /documents/upload` - upload files
- `GET /search?q=...` - dummy search

Next steps
- Implement persistence, PGVector integration, embeddings, and local LLM adapter.
- Improve frontend editor and wire endpoints.
