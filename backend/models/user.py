from sqlalchemy import BigInteger, String, Enum, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models import Base

import enum


class UserRole(str, enum.Enum):
    doctor = "doctor"
    patient = "patient"


class User(Base):
    """用户表：存储医生和患者的登录凭证与基本信息。"""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(256), nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), nullable=False)
    full_name: Mapped[str] = mapped_column(String(64), nullable=False)
    employee_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    department: Mapped[str | None] = mapped_column(String(64), nullable=True)
    security_question: Mapped[str | None] = mapped_column(String(256), nullable=True)
    security_answer_hashed: Mapped[str | None] = mapped_column(String(256), nullable=True)
    title: Mapped[str | None] = mapped_column(String(32), nullable=True)
    specialty: Mapped[str | None] = mapped_column(String(128), nullable=True)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    email: Mapped[str | None] = mapped_column(String(128), nullable=True)
    gender: Mapped[str | None] = mapped_column(String(8), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(Text, nullable=True)

    appointments_as_patient: Mapped[list["Appointment"]] = relationship(
        back_populates="patient", lazy="selectin", foreign_keys="Appointment.patient_id"
    )
    appointments_as_doctor: Mapped[list["Appointment"]] = relationship(
        back_populates="doctor", lazy="selectin", foreign_keys="Appointment.doctor_id"
    )
    schedules: Mapped[list["DoctorSchedule"]] = relationship(
        back_populates="doctor", lazy="selectin", foreign_keys="DoctorSchedule.doctor_id",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username='{self.username}', role='{self.role}')>"
