from datetime import datetime
from sqlalchemy import BigInteger, ForeignKey, String, Text, DateTime, Enum, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models import Base

import enum


class AppointmentStatus(str, enum.Enum):
    pending = "待就诊"
    completed = "已完成"


class Appointment(Base):
    """预约挂号表：存储患者预约信息。"""

    __tablename__ = "appointments"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    patient_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=False, index=True
    )
    doctor_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=False, index=True
    )
    department: Mapped[str] = mapped_column(String(64), nullable=False)
    appointment_time: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    status: Mapped[AppointmentStatus] = mapped_column(
        Enum(AppointmentStatus), default=AppointmentStatus.pending, nullable=False
    )
    symptoms_desc: Mapped[str] = mapped_column(Text, nullable=True)
    ai_report: Mapped[str | None] = mapped_column(Text, nullable=True)
    doctor_advice: Mapped[str | None] = mapped_column(Text, nullable=True)

    patient: Mapped["User"] = relationship(
        back_populates="appointments_as_patient", foreign_keys=[patient_id]
    )
    doctor: Mapped["User"] = relationship(
        back_populates="appointments_as_doctor", foreign_keys=[doctor_id]
    )

    def __repr__(self) -> str:
        return f"<Appointment(id={self.id}, patient_id={self.patient_id}, doctor_id={self.doctor_id}, status='{self.status}')>"
