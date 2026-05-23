"""
业务端点：传统处方筏管理。
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from api.dependencies import get_current_user
from core.database import get_db
from models.appointment import Appointment
from models.prescription import Prescription
from models.user import User, UserRole

router = APIRouter()


class MedicationItem(BaseModel):
    drug_name: str = Field(..., description="药品名称")
    specification: str = Field(..., description="规格")
    dosage: str = Field(..., description="单次用量")
    usage_method: str = Field(..., description="用法")
    frequency: str = Field(..., description="频次")
    days: int = Field(..., ge=1, description="天数")


class PrescriptionCreate(BaseModel):
    diagnosis: str = Field("", description="诊断结论")
    medications: list[MedicationItem] = Field(..., min_length=1, description="药品列表")
    notes: str | None = Field(None, description="医嘱备注")


class PrescriptionResponse(BaseModel):
    id: int
    appointment_id: int
    diagnosis: str | None
    medications: list[dict]
    notes: str | None
    created_at: str

    model_config = {"from_attributes": True}


@router.post("/{appointment_id}", response_model=PrescriptionResponse)
async def save_prescription(
    appointment_id: int,
    req: PrescriptionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """医生为指定预约创建或更新处方（upsert）。"""
    if current_user.role != UserRole.doctor:
        raise HTTPException(status_code=403, detail="仅医生可创建处方")

    result = await db.execute(
        select(Appointment).where(Appointment.id == appointment_id)
    )
    appointment = result.scalar_one_or_none()
    if appointment is None:
        raise HTTPException(status_code=404, detail="预约记录不存在")
    if appointment.doctor_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权为此预约创建处方")

    # Upsert: 删除已有处方再创建
    existing = await db.execute(
        select(Prescription).where(Prescription.appointment_id == appointment_id)
    )
    old = existing.scalar_one_or_none()
    if old is not None:
        await db.delete(old)

    prescription = Prescription(
        appointment_id=appointment_id,
        doctor_id=current_user.id,
        patient_id=appointment.patient_id,
        diagnosis=req.diagnosis,
        medications=[m.model_dump() for m in req.medications],
        notes=req.notes,
    )
    db.add(prescription)
    await db.commit()
    await db.refresh(prescription)

    return PrescriptionResponse(
        id=prescription.id,
        appointment_id=prescription.appointment_id,
        diagnosis=prescription.diagnosis,
        medications=prescription.medications,
        notes=prescription.notes,
        created_at=prescription.created_at.isoformat(),
    )


@router.get("/by-appointment/{appointment_id}", response_model=PrescriptionResponse | None)
async def get_prescription_by_appointment(
    appointment_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取指定预约关联的处方（医生或对应的患者可查看）。"""
    result = await db.execute(
        select(Appointment)
        .options(selectinload(Appointment.prescription))
        .where(Appointment.id == appointment_id)
    )
    appointment = result.scalar_one_or_none()
    if appointment is None:
        raise HTTPException(status_code=404, detail="预约记录不存在")

    # 权限校验：仅关联的医生或患者可查看
    if current_user.id not in (appointment.doctor_id, appointment.patient_id):
        raise HTTPException(status_code=403, detail="无权查看此处方")

    rx = appointment.prescription
    if rx is None:
        return None

    return PrescriptionResponse(
        id=rx.id,
        appointment_id=rx.appointment_id,
        diagnosis=rx.diagnosis,
        medications=rx.medications,
        notes=rx.notes,
        created_at=rx.created_at.isoformat(),
    )


@router.get("/my", response_model=list[PrescriptionResponse])
async def get_my_prescriptions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """患者查看自己的处方列表（按时间倒序）。"""
    if current_user.role != UserRole.patient:
        raise HTTPException(status_code=403, detail="仅患者可查看自己的处方")

    result = await db.execute(
        select(Prescription)
        .where(Prescription.patient_id == current_user.id)
        .order_by(Prescription.created_at.desc())
    )
    prescriptions = result.scalars().all()

    return [
        PrescriptionResponse(
            id=rx.id,
            appointment_id=rx.appointment_id,
            diagnosis=rx.diagnosis,
            medications=rx.medications,
            notes=rx.notes,
            created_at=rx.created_at.isoformat(),
        )
        for rx in prescriptions
    ]
