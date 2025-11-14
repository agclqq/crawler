"""仓储实现"""

from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from domain.entities import CrawlerTask
from domain.repositories import ICrawlerTaskRepository
from domain.value_objects import TaskId
from infrastructure.database.models import CrawlerTaskModel
from infrastructure.database.mappers import task_to_model, model_to_task


class SQLAlchemyCrawlerTaskRepository(ICrawlerTaskRepository):
    """SQLAlchemy 实现的爬虫任务仓储"""
    
    def __init__(self, session: AsyncSession):
        self._session = session
    
    async def save(self, task: CrawlerTask) -> None:
        """保存任务"""
        model = task_to_model(task)
        
        # 检查是否存在
        existing = await self._session.get(CrawlerTaskModel, str(task.id))
        
        if existing:
            # 更新现有记录
            for key, value in model.__dict__.items():
                if key != '_sa_instance_state':
                    setattr(existing, key, value)
        else:
            # 创建新记录
            self._session.add(model)
        
        await self._session.commit()
    
    async def find_by_id(self, task_id: TaskId) -> Optional[CrawlerTask]:
        """根据 ID 查找任务"""
        model = await self._session.get(CrawlerTaskModel, str(task_id))
        if not model:
            return None
        return model_to_task(model)
    
    async def find_all(self, limit: int = 100, offset: int = 0) -> List[CrawlerTask]:
        """查找所有任务"""
        stmt = select(CrawlerTaskModel).order_by(CrawlerTaskModel.created_at.desc()).limit(limit).offset(offset)
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [model_to_task(model) for model in models]
    
    async def find_by_status(self, status: str, limit: int = 100) -> List[CrawlerTask]:
        """根据状态查找任务"""
        stmt = (
            select(CrawlerTaskModel)
            .where(CrawlerTaskModel.status == status)
            .order_by(CrawlerTaskModel.created_at.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [model_to_task(model) for model in models]

