from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """SQLAlchemy 声明式基类，所有模型共享。"""
    pass


from models.patient import Patient, MedicalRecord
from models.user import User
from models.appointment import Appointment

__all__ = ["Base", "Patient", "MedicalRecord", "User", "Appointment"]
