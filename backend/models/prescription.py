from datetime import datetime
from sqlalchemy import BigInteger, ForeignKey, String, Text, DateTime, func, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models import Base


class Prescription(Base):
    """处方表：医生开具的传统处方筏，一个预约对应一张处方。"""

    __tablename__ = "prescriptions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    appointment_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("appointments.id"), nullable=False, unique=True, index=True
    )
    doctor_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=False
    )
    patient_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=False
    )
    diagnosis: Mapped[str] = mapped_column(Text, nullable=True)
    medications: Mapped[list] = mapped_column(JSON, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    appointment: Mapped["Appointment"] = relationship(back_populates="prescription")
    doctor: Mapped["User"] = relationship(foreign_keys=[doctor_id])
    patient: Mapped["User"] = relationship(foreign_keys=[patient_id])

    def __repr__(self) -> str:
        return f"<Prescription(id={self.id}, appointment_id={self.appointment_id})>"
