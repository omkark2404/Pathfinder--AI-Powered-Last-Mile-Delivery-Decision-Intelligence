"""
Regression test: startup sample-data initialization must be idempotent.

Verifies that:
  1. First initialization creates exactly one Dataset row for each sample name.
  2. Calling the same initialization logic a second time does NOT create a second row.

Uses an in-memory SQLite database so no files are left behind.
"""

import pytest
import pytest_asyncio
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

from app.core.database import Base
from app.ingestion.pipeline import IngestionPipeline
from app.models.models import Dataset
from app.schemas.schemas import IngestRequestSchema
from app.main import _sample_dataset_exists


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def mem_session():
    """Provides an isolated in-memory SQLite async session per test."""
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


# ---------------------------------------------------------------------------
# Helper that mirrors the logic now used in lifespan()
# ---------------------------------------------------------------------------

async def _run_sample_initialization(session: AsyncSession) -> None:
    """Mirrors the idempotent startup logic from main.lifespan()."""
    pipeline = IngestionPipeline(session)
    for dataset_name in ("AMAZON_LAST_MILE", "MENDELEY_PLANNED_VS_ACTUAL"):
        if await _sample_dataset_exists(session, dataset_name):
            continue
        await pipeline.run_ingestion(IngestRequestSchema(dataset_name=dataset_name))


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_first_startup_creates_sample_datasets(mem_session):
    """Initial startup must persist one Dataset row for each sample dataset."""
    await _run_sample_initialization(mem_session)

    for name in ("AMAZON_LAST_MILE", "MENDELEY_PLANNED_VS_ACTUAL"):
        count_result = await mem_session.execute(
            select(func.count()).select_from(Dataset).where(Dataset.name == name)
        )
        count = count_result.scalar_one()
        assert count == 1, (
            f"Expected exactly 1 Dataset row for '{name}' after first startup, got {count}"
        )


@pytest.mark.asyncio
async def test_second_startup_does_not_duplicate_datasets(mem_session):
    """Running initialization twice must not create duplicate Dataset rows."""
    # First startup
    await _run_sample_initialization(mem_session)
    # Second startup (simulates server restart)
    await _run_sample_initialization(mem_session)

    for name in ("AMAZON_LAST_MILE", "MENDELEY_PLANNED_VS_ACTUAL"):
        count_result = await mem_session.execute(
            select(func.count()).select_from(Dataset).where(Dataset.name == name)
        )
        count = count_result.scalar_one()
        assert count == 1, (
            f"Expected exactly 1 Dataset row for '{name}' after second startup, got {count} "
            f"(duplicates detected — idempotency broken)"
        )
