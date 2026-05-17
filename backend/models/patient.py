"""
ORM 模型层：患者表 (patients) 与就诊记录表 (medical_records)。
使用 SQLAlchemy 2.0 Mapped 语法定义。
"""
from datetime import datetime
from sqlalchemy import BigInteger, ForeignKey, String, Text, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models import Base


class Patient(Base):
    """患者表：存储患者基本信息。"""

    __tablename__ = "patients"

    # 主键自增 ID
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    # 患者姓名
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    # 患者年龄
    age: Mapped[int] = mapped_column(nullable=False)
    # 基础病史（如"高血压、糖尿病"）
    medical_history: Mapped[str] = mapped_column(Text, nullable=True)

    # 一对多关联：一个患者对应多条就诊记录
    medical_records: Mapped[list["MedicalRecord"]] = relationship(
        back_populates="patient", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Patient(id={self.id}, name='{self.name}', age={self.age})>"


class MedicalRecord(Base):
    """就诊记录表：存储患者每次就诊的详细信息。"""

    __tablename__ = "medical_records"

    # 主键自增 ID
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    # 外键关联到患者表
    patient_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("patients.id"), nullable=False
    )
    # 就诊时间（默认当前时间）
    visit_time: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    # 症状描述
    symptoms: Mapped[str] = mapped_column(Text, nullable=False)
    # 诊断结果
    diagnosis: Mapped[str] = mapped_column(Text, nullable=False)
    # 开具药物（多个药物用逗号分隔）
    prescribed_drugs: Mapped[str] = mapped_column(Text, nullable=True)

    # 反向关联回患者表
    patient: Mapped["Patient"] = relationship(back_populates="medical_records")

    def __repr__(self) -> str:
        return f"<MedicalRecord(id={self.id}, patient_id={self.patient_id}, diagnosis='{self.diagnosis[:20]}...')>"
