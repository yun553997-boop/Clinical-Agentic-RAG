"""
医生排班端点：管理可预约时间段。
"""
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import get_current_user
from core.database import get_db
from models.user import User, UserRole
from models.schedule import DoctorSchedule

router = APIRouter()


class ScheduleCreate(BaseModel):
    slot_date: date = Field(..., description="出诊日期 (YYYY-MM-DD)")
    slot_time: str = Field(..., description="时间段 (HH:MM)", pattern=r"^\d{2}:\d{2}$")


class ScheduleResponse(BaseModel):
    id: int
    doctor_id: int
    slot_date: str
    slot_time: str
    is_booked: bool

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm_obj(cls, obj: DoctorSchedule) -> "ScheduleResponse":
        return cls(
            id=obj.id,
            doctor_id=obj.doctor_id,
            slot_date=obj.slot_date.isoformat(),
            slot_time=obj.slot_time.strftime("%H:%M"),
            is_booked=obj.is_booked,
        )


@router.get("/my", response_model=list[ScheduleResponse])
async def get_my_schedules(
    filter_date: date | None = Query(None, alias="date", description="按日期筛选"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """医生查看自己的排班列表。"""
    if current_user.role != UserRole.doctor:
        raise HTTPException(status_code=403, detail="仅医生可访问")
    stmt = select(DoctorSchedule).where(DoctorSchedule.doctor_id == current_user.id)
    if filter_date:
        stmt = stmt.where(DoctorSchedule.slot_date == filter_date)
    stmt = stmt.order_by(DoctorSchedule.slot_date, DoctorSchedule.slot_time)
    result = await db.execute(stmt)
    return [ScheduleResponse.from_orm_obj(s) for s in result.scalars().all()]


@router.post("/", response_model=ScheduleResponse, status_code=201)
async def create_schedule(
    req: ScheduleCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """医生添加一个可用时间段。"""
    if current_user.role != UserRole.doctor:
        raise HTTPException(status_code=403, detail="仅医生可访问")

    # 解析时间
    parts = req.slot_time.split(":")
    from datetime import time
    slot_time = time(hour=int(parts[0]), minute=int(parts[1]))

    slot = DoctorSchedule(
        doctor_id=current_user.id,
        slot_date=req.slot_date,
        slot_time=slot_time,
    )
    db.add(slot)
    await db.commit()
    await db.refresh(slot)
    return ScheduleResponse.from_orm_obj(slot)


@router.delete("/{slot_id}")
async def delete_schedule(
    slot_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """医生删除一个未预约的时间段。"""
    if current_user.role != UserRole.doctor:
        raise HTTPException(status_code=403, detail="仅医生可访问")
    slot = await db.get(DoctorSchedule, slot_id)
    if slot is None:
        raise HTTPException(status_code=404, detail="时间段不存在")
    if slot.doctor_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权操作他人的排班")
    if slot.is_booked:
        raise HTTPException(status_code=400, detail="该时段已被预约，无法删除")
    await db.delete(slot)
    await db.commit()
    return {"message": "已删除"}


@router.get("/available", response_model=list[ScheduleResponse])
async def get_available_slots(
    doctor_id: int = Query(..., description="医生 ID"),
    db: AsyncSession = Depends(get_db),
):
    """患者查看某医生的可用时段（未预约 + 日期 >= 今天）。"""
    today = date.today()
    stmt = (
        select(DoctorSchedule)
        .where(
            and_(
                DoctorSchedule.doctor_id == doctor_id,
                DoctorSchedule.is_booked == False,
                DoctorSchedule.slot_date >= today,
            )
        )
        .order_by(DoctorSchedule.slot_date, DoctorSchedule.slot_time)
    )
    result = await db.execute(stmt)
    return [ScheduleResponse.from_orm_obj(s) for s in result.scalars().all()]
