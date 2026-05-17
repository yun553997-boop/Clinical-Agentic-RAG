"""
核心配置层：使用 pydantic-settings 读取 .env 环境变量。
"""
import os
from pydantic_settings import BaseSettings

# 计算 .env 文件的绝对路径（位于 backend 目录下）
_ENV_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")


class Settings(BaseSettings):
    """应用全局配置，自动从 .env 文件加载。"""

    # 大模型 API Key（通义千问 / DeepSeek 兼容 OpenAI 格式）
    LLM_API_KEY: str

    # LLM 服务地址（默认为通义千问 DashScope，也可替换为 DeepSeek 等兼容端点）
    LLM_BASE_URL: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"

    # 默认模型名称
    LLM_MODEL_NAME: str = "qwen-plus"

    # PostgreSQL 异步连接 URL（格式：postgresql+asyncpg://用户:密码@主机:端口/库名）
    DATABASE_URL: str

    # JWT 密钥（生产环境应使用强随机字符串）
    SECRET_KEY: str = "clinical-agentic-rag-secret-key-change-in-production"
    # JWT 签名算法
    ALGORITHM: str = "HS256"
    # Token 过期时间（分钟）
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24

    # 应用运行端口
    APP_PORT: int = 8000

    model_config = {"env_file": _ENV_FILE, "extra": "allow"}


# 全局单例配置对象
settings = Settings()
