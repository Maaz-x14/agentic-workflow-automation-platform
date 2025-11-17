from pydantic import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "Agentic Workflow Automation Platform"
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/app.db"
    # Ollama or other LLM endpoint, kept local-only
    LLM_ENDPOINT: str = "http://localhost:11434"

    class Config:
        env_file = ".env"


settings = Settings()
