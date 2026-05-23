"""
数据库核心层：配置 SQLAlchemy 2.0 异步引擎与依赖注入函数。
"""
from sqlalchemy import text
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


def run_migrations(connection):
    """幂等迁移：处理已有表结构变更。"""
    # appointments 表新增字段
    connection.execute(text(
        "ALTER TABLE appointments ADD COLUMN IF NOT EXISTS paid BOOLEAN DEFAULT FALSE"
    ))
    connection.execute(text(
        "ALTER TABLE appointments ADD COLUMN IF NOT EXISTS payment_method VARCHAR(16)"
    ))
    # users 表新增字段
    connection.execute(text(
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS security_question VARCHAR(256)"
    ))
    connection.execute(text(
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS security_answer_hashed VARCHAR(256)"
    ))
    # prescriptions 表：若缺少新字段则删表重建（旧表无 doctor_id/patient_id 列）
    _rebuild_prescriptions_if_stale(connection)


def _rebuild_prescriptions_if_stale(connection):
    """检查 prescriptions 表是否缺少 doctor_id 列，若是则删表重建。

    不在此处执行 COMMIT——run_migrations 与 create_all 在同一个外层事务中运行，
    PostgreSQL DDL 是事务性的，DROP TABLE 在同一事务内对后续 CREATE TABLE 可见，
    外层事务提交时一并生效。
    """
    import logging
    logger = logging.getLogger("migrate")
    result = connection.execute(text(
        "SELECT column_name FROM information_schema.columns"
        " WHERE table_name = 'prescriptions' AND column_name = 'doctor_id'"
    ))
    if result.fetchone() is None:
        logger.info("prescriptions 表结构过旧，正在重建…")
        connection.execute(text("DROP TABLE IF EXISTS prescriptions CASCADE"))


async def get_db() -> AsyncSession:
    """FastAPI 依赖注入：为每个请求提供一个异步数据库会话。"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
