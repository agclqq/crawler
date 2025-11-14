"""仓储接口定义"""

from abc import ABC, abstractmethod
from typing import Optional, List
from domain.entities import CrawlerTask
from domain.value_objects import TaskId


class ICrawlerTaskRepository(ABC):
    """爬虫任务仓储接口"""

    @abstractmethod
    async def save(self, task: CrawlerTask) -> None:
        """保存任务"""
        pass

    @abstractmethod
    async def find_by_id(self, task_id: TaskId) -> Optional[CrawlerTask]:
        """根据 ID 查找任务"""
        pass

    @abstractmethod
    async def find_all(self, limit: int = 100, offset: int = 0) -> List[CrawlerTask]:
        """查找所有任务"""
        pass

    @abstractmethod
    async def find_by_status(self, status: str, limit: int = 100) -> List[CrawlerTask]:
        """根据状态查找任务"""
        pass
