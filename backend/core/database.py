"""
数据库核心层：配置 SQLAlchemy 2.0 异步引擎与依赖注入函数。
"""
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from core.config import settings

# 异步引擎（echo=True 可在开发时打印 SQL）
async_engine = create_async_engine(settings.DATABASE_URL, echo=False)

# 异步会话工厂
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncSession:
    """FastAPI 依赖注入：为每个请求提供一个异步数据库会话。"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
