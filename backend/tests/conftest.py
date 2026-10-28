import os
import sys

# Ensure backend root is on sys.path when running bare `pytest`
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# Ensure tests default to SQLite fallback rather than connecting to external Postgres
os.environ.setdefault("DATABASE_URL", "")

import pytest_asyncio  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine  # noqa: E402

from app.core.database import Base  # noqa: E402


@pytest_asyncio.fixture
async def mem_session():
    """Isolated in-memory SQLite session per test."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        future=True,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False, autoflush=False
    )
    async with session_factory() as session:
        yield session
    await engine.dispose()
