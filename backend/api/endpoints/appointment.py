"""
业务端点：预约挂号。
"""
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from api.dependencies import get_current_user
from core.database import get_db
from models.appointment import Appointment, AppointmentStatus
from models.schedule import DoctorSchedule
from models.user import User, UserRole

router = APIRouter()


class AppointmentCreate(BaseModel):
    """预约挂号请求体。"""
    doctor_id: int = Field(..., description="目标医生 ID")
    department: str = Field(..., min_length=1, max_length=64, description="预约科室")
    slot_id: int = Field(..., description="选择的排班时段 ID")
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
    paid: bool = False
    payment_method: str | None = None

    model_config = {"from_attributes": True}


@router.post("/", response_model=AppointmentResponse, status_code=status.HTTP_201_CREATED)
async def create_appointment(
    req: AppointmentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """患者提交预约挂号（基于医生排班时段）。"""
    if current_user.role != UserRole.patient:
        raise HTTPException(status_code=403, detail="仅患者可提交挂号申请")

    # 校验目标医生是否存在且角色为 doctor
    result = await db.execute(select(User).where(User.id == req.doctor_id))
    doctor = result.scalar_one_or_none()
    if doctor is None or doctor.role != UserRole.doctor:
        raise HTTPException(status_code=400, detail="目标医生不存在")

    # 校验排班时段
    slot = await db.get(DoctorSchedule, req.slot_id)
    if slot is None:
        raise HTTPException(status_code=400, detail="该时段不存在")
    if slot.doctor_id != req.doctor_id:
        raise HTTPException(status_code=400, detail="时段与医生不匹配")
    if slot.is_booked:
        raise HTTPException(status_code=400, detail="该时段已被预约")

    # 组合日期和时间
    appt_time = datetime.combine(slot.slot_date, slot.slot_time)

    # 标记时段为已预约
    slot.is_booked = True

    appointment = Appointment(
        patient_id=current_user.id,
        doctor_id=req.doctor_id,
        department=req.department,
        appointment_time=appt_time,
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
        paid=appointment.paid,
        payment_method=appointment.payment_method,
    )


@router.get("/today", response_model=list[AppointmentResponse])
async def get_today_appointments(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """医生获取指派给自己且状态为"待就诊"的今日挂号列表。"""
    if current_user.role != UserRole.doctor:
        raise HTTPException(status_code=403, detail="仅医生可查看今日挂号")

    today_start = datetime.now(timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0, tzinfo=None
    )
    result = await db.execute(
        select(Appointment)
        .options(selectinload(Appointment.patient))
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
            paid=a.paid,
            payment_method=a.payment_method,
        )
        for a in appointments
    ]


class MyAppointmentResponse(BaseModel):
    """我的预约记录响应。"""
    id: int
    department: str
    doctor_name: str
    appointment_time: str
    status: str
    symptoms_desc: str | None
    ai_report: str | None = None
    doctor_advice: str | None = None
    paid: bool = False
    payment_method: str | None = None

    model_config = {"from_attributes": True}


class SubmitAppointmentRequest(BaseModel):
    """提交会诊请求体（处方+报告）。"""
    ai_report: str = Field(..., description="AI 生成的诊疗报告（Markdown）")
    doctor_advice: str | None = Field(None, description="医生补充医嘱")


@router.get("/my", response_model=list[MyAppointmentResponse])
async def get_my_appointments(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """患者查看自己的预约记录，按时间倒序。"""
    if current_user.role != UserRole.patient:
        raise HTTPException(status_code=403, detail="仅患者可查看自己的预约记录")

    result = await db.execute(
        select(Appointment)
        .options(selectinload(Appointment.doctor))
        .where(Appointment.patient_id == current_user.id)
        .order_by(Appointment.appointment_time.desc())
    )
    appointments = result.scalars().all()

    return [
        MyAppointmentResponse(
            id=a.id,
            department=a.department,
            doctor_name=a.doctor.full_name,
            appointment_time=a.appointment_time.isoformat(),
            status=a.status.value,
            symptoms_desc=a.symptoms_desc,
            ai_report=a.ai_report,
            doctor_advice=a.doctor_advice,
            paid=a.paid,
            payment_method=a.payment_method,
        )
        for a in appointments
    ]


@router.delete("/{appointment_id}")
async def cancel_appointment(
    appointment_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """患者取消自己的预约挂号（物理删除）。"""
    if current_user.role != UserRole.patient:
        raise HTTPException(status_code=403, detail="仅患者可取消预约")

    result = await db.execute(
        select(Appointment).where(Appointment.id == appointment_id)
    )
    appointment = result.scalar_one_or_none()
    if appointment is None:
        raise HTTPException(status_code=404, detail="预约记录不存在")
    if appointment.patient_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权取消他人的预约")

    await db.delete(appointment)
    await db.commit()
    return {"message": "取消预约成功"}


@router.put("/{appointment_id}/submit")
async def submit_appointment(
    appointment_id: int,
    req: SubmitAppointmentRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """医生完成会诊：保存 AI 报告和医嘱，标记预约为已完成。"""
    if current_user.role != UserRole.doctor:
        raise HTTPException(status_code=403, detail="仅医生可完成会诊")

    result = await db.execute(
        select(Appointment).where(Appointment.id == appointment_id)
    )
    appointment = result.scalar_one_or_none()
    if appointment is None:
        raise HTTPException(status_code=404, detail="预约记录不存在")
    if appointment.doctor_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权操作他人的预约")

    appointment.ai_report = req.ai_report
    appointment.doctor_advice = req.doctor_advice
    appointment.status = AppointmentStatus.completed

    await db.commit()
    await db.refresh(appointment)

    return {"message": "处方已提交，报告已发送给患者"}
