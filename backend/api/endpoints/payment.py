"""
支付端点：模拟微信/支付宝支付。
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import get_current_user
from core.database import get_db
from models.appointment import Appointment
from models.user import User, UserRole

router = APIRouter()


@router.post("/{appointment_id}/pay")
async def pay_appointment(
    appointment_id: int,
    method: str = Query("wechat", pattern="^(wechat|alipay)$", description="支付方式"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """模拟支付：将挂号单标记为已支付。"""
    if current_user.role != UserRole.patient:
        raise HTTPException(status_code=403, detail="仅患者可进行支付")

    result = await db.execute(
        select(Appointment).where(Appointment.id == appointment_id)
    )
    appointment = result.scalar_one_or_none()
    if appointment is None:
        raise HTTPException(status_code=404, detail="预约记录不存在")
    if appointment.patient_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权操作他人的预约")
    if appointment.paid:
        raise HTTPException(status_code=400, detail="该挂号单已支付")

    appointment.paid = True
    appointment.payment_method = method
    await db.commit()

    return {"message": "支付成功（模拟）", "appointment_id": appointment_id, "method": method}
