from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.config import settings
from app.db import models
import os

# This gets the directory of the current file (database.py) -> .../backend/app/db
CURRENT_FILE_DIR = os.path.dirname(os.path.abspath(__file__))

# Go up two levels to get to the 'backend' root folder
BACKEND_ROOT = os.path.dirname(os.path.dirname(CURRENT_FILE_DIR))

# ensure data dir exists
data_dir = os.path.join(BACKEND_ROOT, "data")
os.makedirs(data_dir, exist_ok=True)

# Use SQLite for local-first dev; database file stored under backend/data/app.db
database_url = settings.DATABASE_URL

engine = create_async_engine(database_url, echo=False, future=True)

AsyncSessionLocal = sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session


async def init_db():
    # Create tables if they don't exist
    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)

