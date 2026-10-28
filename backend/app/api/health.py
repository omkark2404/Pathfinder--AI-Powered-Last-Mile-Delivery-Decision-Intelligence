import os
from fastapi import APIRouter
from app.core.config import settings
from app.ingestion.pipeline import resolve_dataset_file

router = APIRouter()


def describe_data_sources() -> dict:
    """Which file (if any) backs each dataset, and whether it is real or synthetic."""
    sources = {}
    for name in ("AMAZON_LAST_MILE", "MENDELEY_PLANNED_VS_ACTUAL"):
        path, is_synthetic = resolve_dataset_file(name)
        if path is None:
            sources[name] = "missing"
        elif is_synthetic:
            sources[name] = "synthetic_fixture"
        else:
            sources[name] = "sample" if "sample" in os.path.basename(path) else "full"
    return sources


@router.get("/health")
async def health_check():
    # Derive environment from whether a real DATABASE_URL has been configured.
    env = "production" if (settings.DATABASE_URL and "localhost" not in settings.DATABASE_URL) else "development"
    sources = describe_data_sources()
    if all(v == "missing" for v in sources.values()):
        data_mode = "synthetic_demo"
    elif all(v == "full" for v in sources.values()):
        data_mode = "public_datasets"
    else:
        data_mode = "bundled_samples"
    labels = {
        "missing": "not found (in-code synthetic fixture used)",
        "synthetic_fixture": "synthetic fixture, not real delivery data",
        "sample": "real sample subset",
        "full": "full public dataset",
    }
    note = f"Amazon Last Mile: {labels[sources['AMAZON_LAST_MILE']]}. Mendeley planned-vs-actual: {labels[sources['MENDELEY_PLANNED_VS_ACTUAL']]}."
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": "1.0.0",
        "environment": env,
        "data_mode": data_mode,
        "data_sources": sources,
        "data_mode_note": note,
    }
