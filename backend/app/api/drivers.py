from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Dict, Any

from app.core.database import get_db
from app.models.models import Driver
from app.analytics.delivery import DeliveryAnalytics

router = APIRouter(prefix="/drivers", tags=["Drivers"])

@router.get("")
async def list_drivers(db: AsyncSession = Depends(get_db)):
    return await DeliveryAnalytics.get_driver_analytics(db)

@router.get("/{driver_id}")
async def get_driver(driver_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(Driver).where(Driver.id == driver_id)
    res = await db.execute(stmt)
    driver = res.scalar_one_or_none()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    return driver
