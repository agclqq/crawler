"""数据库初始化脚本"""

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from infrastructure.config import settings
from infrastructure.database.models import Base


async def init_database():
    """初始化数据库表"""
    engine = create_async_engine(settings.database_url, echo=True)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    await engine.dispose()
    print("Database initialized successfully!")


if __name__ == "__main__":
    asyncio.run(init_database())

