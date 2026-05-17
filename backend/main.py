"""
FastAPI 主入口：临床智能诊疗辅助工作流 (Agentic RAG Medical Assistant)。
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.endpoints.chat import router as chat_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期：启动时检查数据库连接等资源。"""
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("main")
    logger.info("Agentic RAG Medical Assistant 启动中...")
    yield
    logger.info("Agentic RAG Medical Assistant 关闭。")


app = FastAPI(
    title="Clinical Agentic RAG",
    description="智能临床诊疗辅助工作流 —— 基于 LangChain Agent + 通义千问 + ChromaDB",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS 中间件：允许前端开发服务器 (Vite) 跨域访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(chat_router, prefix="/api/chat", tags=["AI 临床诊疗对话"])


@app.get("/", tags=["健康检查"])
async def root():
    """健康检查端点。"""
    return {
        "status": "ok",
        "service": "Clinical Agentic RAG",
        "version": "0.1.0",
    }
