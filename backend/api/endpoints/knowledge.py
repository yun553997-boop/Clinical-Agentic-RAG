"""
知识库管理 API：上传医学指南 PDF、自动向量化注入 ChromaDB、文档列表与删除。
"""
import os
import shutil
import logging
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from api.dependencies import get_current_user
from core.database import get_db
from models.user import User, UserRole
from models.knowledge import KnowledgeDoc
from tools.rag_tool import _get_collection

logger = logging.getLogger(__name__)

router = APIRouter()

# 上传文件保存目录
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_UPLOAD_DIR = os.path.join(_BASE_DIR, "data", "uploads")

# 文本切分器
_text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50,
    separators=["\n\n", "\n", "。", "！", "？", "；", "，", " ", ""],
)

# ── 响应模型 ──

class KnowledgeDocResponse(BaseModel):
    """文档列表项响应。"""
    id: int
    filename: str
    upload_time: str
    uploader_name: str
    status: str

    model_config = {"from_attributes": True}


class UploadResponse(BaseModel):
    """上传成功响应。"""
    id: int
    filename: str
    message: str


# ── 接口 ──

@router.get("/", response_model=list[KnowledgeDocResponse])
async def list_docs(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取所有已上传的知识库文档列表（按时间倒序）。"""
    if current_user.role != UserRole.doctor:
        raise HTTPException(status_code=403, detail="仅医生可访问知识库")

    result = await db.execute(
        select(KnowledgeDoc).order_by(KnowledgeDoc.upload_time.desc())
    )
    docs = result.scalars().all()

    return [
        KnowledgeDocResponse(
            id=d.id,
            filename=d.filename,
            upload_time=d.upload_time.isoformat(),
            uploader_name=d.uploader.full_name if d.uploader else "未知",
            status=d.status,
        )
        for d in docs
    ]


@router.post("/upload", response_model=UploadResponse)
async def upload_doc(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """上传医学指南 PDF，自动完成文本提取、切分与向量化注入。"""
    if current_user.role != UserRole.doctor:
        raise HTTPException(status_code=403, detail="仅医生可上传知识文档")

    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="仅支持 PDF 格式文件")

    # ── 1. 保存文件到本地 ──
    os.makedirs(_UPLOAD_DIR, exist_ok=True)
    safe_filename = file.filename.replace("\\", "/").split("/")[-1]
    file_path = os.path.join(_UPLOAD_DIR, safe_filename)

    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    # ── 2. 创建数据库记录 ──
    doc_record = KnowledgeDoc(
        filename=safe_filename,
        uploader_id=current_user.id,
        status="向量化中",
    )
    db.add(doc_record)
    await db.commit()
    await db.refresh(doc_record)

    try:
        # ── 3. 使用 PyPDFLoader 加载 PDF ──
        loader = PyPDFLoader(file_path)
        pages = loader.load()

        if not pages:
            raise ValueError("PDF 文件无有效文本内容")

        # ── 4. 文本切分 ──
        chunks = _text_splitter.split_documents(pages)

        if not chunks:
            raise ValueError("文本切分后无有效片段")

        # ── 5. 注入 ChromaDB（与 rag_tool 使用同一集合） ──
        collection = _get_collection()
        ids = [f"doc_{doc_record.id}_chunk_{i}" for i in range(len(chunks))]
        collection.add(
            documents=[c.page_content for c in chunks],
            metadatas=[
                {"doc_id": str(doc_record.id), "source": safe_filename}
                for _ in chunks
            ],
            ids=ids,
        )

        # ── 6. 更新状态为"已向量化" ──
        doc_record.status = "已向量化"
        await db.commit()
        await db.refresh(doc_record)

        logger.info(
            "知识文档 '%s' 上传成功，共 %d 个文本片段已注入向量库",
            safe_filename,
            len(chunks),
        )

        return UploadResponse(
            id=doc_record.id,
            filename=safe_filename,
            message=f"上传成功，已将 {len(chunks)} 个文本片段注入知识库",
        )

    except Exception as e:
        # 向量化失败：更新状态并清理文件
        doc_record.status = "向量化失败"
        await db.commit()
        logger.error("向量化文档 '%s' 失败：%s", safe_filename, str(e))
        raise HTTPException(
            status_code=500,
            detail=f"文档向量化失败：{str(e)}",
        )


@router.delete("/{doc_id}")
async def delete_doc(
    doc_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """删除知识库文档，同时从 ChromaDB 中移除对应向量数据。"""
    if current_user.role != UserRole.doctor:
        raise HTTPException(status_code=403, detail="仅医生可删除知识文档")

    result = await db.execute(
        select(KnowledgeDoc).where(KnowledgeDoc.id == doc_id)
    )
    doc = result.scalar_one_or_none()
    if doc is None:
        raise HTTPException(status_code=404, detail="文档不存在")

    # 从 ChromaDB 中删除对应向量
    try:
        collection = _get_collection()
        collection.delete(where={"doc_id": str(doc_id)})
    except Exception as e:
        logger.warning("删除 ChromaDB 向量数据失败（doc_id=%d）：%s", doc_id, str(e))

    # 删除本地文件
    file_path = os.path.join(_UPLOAD_DIR, doc.filename)
    if os.path.exists(file_path):
        os.remove(file_path)

    # 删除数据库记录
    await db.delete(doc)
    await db.commit()

    return {"message": f"已成功删除文档 '{doc.filename}'"}
