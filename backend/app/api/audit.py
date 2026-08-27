from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.core.database import get_db
from app.models.models import AuditLog
from app.schemas.schemas import AuditLogSchema

router = APIRouter(prefix="/audit", tags=["Auditability"])

@router.get("", response_model=List[AuditLogSchema])
async def list_audit_logs(db: AsyncSession = Depends(get_db)):
    stmt = select(AuditLog).order_by(AuditLog.timestamp.desc()).limit(100)
    res = await db.execute(stmt)
    return res.scalars().all()
