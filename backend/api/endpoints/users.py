"""
用户查询端点：获取医生列表等。
"""
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from models.user import User, UserRole

router = APIRouter()


class DoctorResponse(BaseModel):
    """医生列表项。"""
    id: int
    full_name: str
    department: str | None

    model_config = {"from_attributes": True}


@router.get("/doctors", response_model=list[DoctorResponse])
async def get_doctors(
    department: str | None = Query(None, description="按科室筛选"),
    db: AsyncSession = Depends(get_db),
):
    """获取医生列表，可按科室筛选。"""
    stmt = select(User).where(User.role == UserRole.doctor)
    if department:
        stmt = stmt.where(User.department == department)
    result = await db.execute(stmt)
    doctors = result.scalars().all()
    return [
        DoctorResponse(
            id=d.id,
            full_name=d.full_name,
            department=d.department,
        )
        for d in doctors
    ]
