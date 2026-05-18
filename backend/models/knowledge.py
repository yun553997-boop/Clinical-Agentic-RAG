"""
ORM 模型：知识库文档表 (knowledge_docs)。
"""
from datetime import datetime
from sqlalchemy import BigInteger, ForeignKey, String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models import Base


class KnowledgeDoc(Base):
    """知识库文档表：记录上传的医疗指南 PDF 文件及其向量化状态。"""

    __tablename__ = "knowledge_docs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    filename: Mapped[str] = mapped_column(String(256), nullable=False)
    upload_time: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    uploader_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(32), default="已向量化", nullable=False)

    uploader: Mapped["User"] = relationship(
        lazy="selectin", foreign_keys=[uploader_id]
    )
