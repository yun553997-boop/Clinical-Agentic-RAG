"""
业务端点：预约挂号。
"""
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import get_current_user
from core.database import get_db
from models.appointment import Appointment, AppointmentStatus
from models.user import User, UserRole

router = APIRouter()


class AppointmentCreate(BaseModel):
    """预约挂号请求体。"""
    doctor_id: int = Field(..., description="目标医生 ID")
    department: str = Field(..., min_length=1, max_length=64, description="预约科室")
    appointment_time: datetime | None = Field(None, description="预约时间（默认当前时间）")
    symptoms_desc: str | None = Field(None, description="初步症状描述")


class AppointmentResponse(BaseModel):
    """挂号单响应。"""
    id: int
    patient_id: int
    doctor_id: int
    patient_name: str
    department: str
    appointment_time: str
    status: str
    symptoms_desc: str | None

    model_config = {"from_attributes": True}


@router.post("/", response_model=AppointmentResponse, status_code=status.HTTP_201_CREATED)
async def create_appointment(
    req: AppointmentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """患者提交预约挂号。"""
    if current_user.role != UserRole.patient:
        raise HTTPException(status_code=403, detail="仅患者可提交挂号申请")

    # 校验目标医生是否存在且角色为 doctor
    result = await db.execute(select(User).where(User.id == req.doctor_id))
    doctor = result.scalar_one_or_none()
    if doctor is None or doctor.role != UserRole.doctor:
        raise HTTPException(status_code=400, detail="目标医生不存在")

    appointment = Appointment(
        patient_id=current_user.id,
        doctor_id=req.doctor_id,
        department=req.department,
        appointment_time=req.appointment_time or datetime.now(timezone.utc),
        status=AppointmentStatus.pending,
        symptoms_desc=req.symptoms_desc,
    )
    db.add(appointment)
    await db.commit()
    await db.refresh(appointment)

    return AppointmentResponse(
        id=appointment.id,
        patient_id=appointment.patient_id,
        doctor_id=appointment.doctor_id,
        patient_name=current_user.full_name,
        department=appointment.department,
        appointment_time=appointment.appointment_time.isoformat(),
        status=appointment.status.value,
        symptoms_desc=appointment.symptoms_desc,
    )


@router.get("/today", response_model=list[AppointmentResponse])
async def get_today_appointments(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """医生获取指派给自己且状态为"待就诊"的今日挂号列表。"""
    if current_user.role != UserRole.doctor:
        raise HTTPException(status_code=403, detail="仅医生可查看今日挂号")

    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    result = await db.execute(
        select(Appointment)
        .where(
            and_(
                Appointment.doctor_id == current_user.id,
                Appointment.status == AppointmentStatus.pending,
                Appointment.appointment_time >= today_start,
            )
        )
        .order_by(Appointment.appointment_time.asc())
    )
    appointments = result.scalars().all()

    return [
        AppointmentResponse(
            id=a.id,
            patient_id=a.patient_id,
            doctor_id=a.doctor_id,
            patient_name=a.patient.full_name,
            department=a.department,
            appointment_time=a.appointment_time.isoformat(),
            status=a.status.value,
            symptoms_desc=a.symptoms_desc,
        )
        for a in appointments
    ]
