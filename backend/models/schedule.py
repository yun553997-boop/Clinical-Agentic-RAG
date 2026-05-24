from datetime import date, datetime, time

from sqlalchemy import BigInteger, Boolean, Date, DateTime, ForeignKey, Time, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models import Base


class DoctorSchedule(Base):
    """医生出诊排班表：存储医生设置的可用预约时间段。"""

    __tablename__ = "doctor_schedules"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    doctor_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=False, index=True
    )
    slot_date: Mapped[date] = mapped_column(Date, nullable=False)
    slot_time: Mapped[time] = mapped_column(Time, nullable=False)
    is_booked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    doctor: Mapped["User"] = relationship(back_populates="schedules", foreign_keys=[doctor_id])

    def __repr__(self) -> str:
        return f"<DoctorSchedule(id={self.id}, doctor_id={self.doctor_id}, {self.slot_date} {self.slot_time})>"
