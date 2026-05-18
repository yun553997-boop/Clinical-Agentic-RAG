import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from core.database import async_engine, AsyncSessionLocal


async def add_columns():
    async with AsyncSessionLocal() as session:
        await session.execute(text("ALTER TABLE appointments ADD COLUMN IF NOT EXISTS ai_report TEXT"))
        await session.execute(text("ALTER TABLE appointments ADD COLUMN IF NOT EXISTS doctor_advice TEXT"))
        await session.commit()
        print("Columns added successfully")


asyncio.run(add_columns())
