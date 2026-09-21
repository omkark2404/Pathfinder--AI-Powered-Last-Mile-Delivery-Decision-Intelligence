import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import init_db, AsyncSessionLocal
from app.ingestion.pipeline import IngestionPipeline
from app.models.models import Dataset
from app.schemas.schemas import IngestRequestSchema

from app.api import (
    health, datasets, routes, deliveries,
    optimization, recommendations, drivers, models, audit
)

# Configure logging
logging.basicConfig(
    level=logging.INFO if settings.ENVIRONMENT == "production" else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def _sample_dataset_exists(session: AsyncSession, dataset_name: str) -> bool:
    """Return True if at least one Dataset row with this name already exists."""
    result = await session.execute(
        select(func.count()).select_from(Dataset).where(Dataset.name == dataset_name)
    )
    return result.scalar_one() > 0


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB tables
    await init_db()

    is_prod = settings.ENVIRONMENT.lower() == "production"

    # Security check: SECRET_KEY
    if settings.is_default_secret_key():
        msg = "Running with the default SECRET_KEY. Set a strong SECRET_KEY environment variable."
        if is_prod:
            logger.error(msg)
            raise RuntimeError(f"SECURITY ERROR: {msg} (Refusing to start in production)")
        else:
            logger.warning(msg)

    # Security check: CORS
    if "*" in settings.get_allowed_origins():
        msg = "CORS ALLOWED_ORIGINS contains '*'. Set explicit origins for production."
        if is_prod:
            logger.error(msg)
            raise RuntimeError(f"SECURITY ERROR: {msg} (Refusing to start in production)")
        else:
            logger.warning(msg)

    # Load sample datasets on first startup only
    async with AsyncSessionLocal() as session:
        pipeline = IngestionPipeline(session)
        for dataset_name in ("AMAZON_LAST_MILE", "MENDELEY_PLANNED_VS_ACTUAL"):
            try:
                if await _sample_dataset_exists(session, dataset_name):
                    logger.info(f"Startup: '{dataset_name}' already loaded — skipping ingestion.")
                    continue
                logger.info(f"Startup: '{dataset_name}' not found — ingesting sample data.")
                await pipeline.run_ingestion(IngestRequestSchema(dataset_name=dataset_name))
            except Exception as e:
                logger.error(f"Initial ingestion notice ({dataset_name}): {e}")

    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    lifespan=lifespan,
)

# CORS: restrict origins in production via the ALLOWED_ORIGINS environment variable.
# Default "*" is development-only; set ALLOWED_ORIGINS=https://your-domain.com in prod.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_allowed_origins(),
    allow_credentials=False,  # credentials=True + origins=* is a security misconfiguration
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

# Mount Routers
app.include_router(health.router)
app.include_router(datasets.router, prefix=settings.API_V1_STR)
app.include_router(routes.router, prefix=settings.API_V1_STR)
app.include_router(deliveries.router, prefix=settings.API_V1_STR)
app.include_router(optimization.router, prefix=settings.API_V1_STR)
app.include_router(recommendations.router, prefix=settings.API_V1_STR)
app.include_router(drivers.router, prefix=settings.API_V1_STR)
app.include_router(models.router, prefix=settings.API_V1_STR)
app.include_router(audit.router, prefix=settings.API_V1_STR)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
