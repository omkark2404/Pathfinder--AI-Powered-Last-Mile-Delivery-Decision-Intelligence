from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.core.database import get_db
from app.models.models import Dataset, IngestionRun
from app.schemas.schemas import DatasetSchema, IngestRequestSchema, DataQualityReportSchema
from app.ingestion.pipeline import IngestionPipeline

router = APIRouter(prefix="/datasets", tags=["Datasets"])

@router.get("", response_model=List[DatasetSchema])
async def list_datasets(db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Dataset))
    return res.scalars().all()

@router.post("/ingest")
async def ingest_dataset(request: IngestRequestSchema, db: AsyncSession = Depends(get_db)):
    pipeline = IngestionPipeline(db)
    dataset, run, report = await pipeline.run_ingestion(request)
    return {
        "dataset_id": dataset.id,
        "name": dataset.name,
        "status": run.status,
        "quality_report": report
    }

@router.get("/quality", response_model=List[dict])
async def get_data_quality_reports(db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(IngestionRun))
    runs = res.scalars().all()
    return [r.quality_report for r in runs if r.quality_report]
