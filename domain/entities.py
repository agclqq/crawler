"""实体定义"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import uuid

from domain.value_objects import URL, TaskId, TaskStatus
from domain.exceptions import TaskStateError


@dataclass
class CrawlerTask:
    """爬虫任务实体"""

    id: TaskId
    url: URL
    status: TaskStatus
    created_at: datetime
    updated_at: datetime
    content: Optional[str] = None
    error_message: Optional[str] = None
    metadata: dict = field(default_factory=dict)

    @classmethod
    def create(cls, url: str, metadata: Optional[dict] = None) -> "CrawlerTask":
        """创建新的爬虫任务"""
        task_id = TaskId(str(uuid.uuid4()))
        now = datetime.utcnow()
        return cls(
            id=task_id,
            url=URL(url),
            status=TaskStatus.pending(),
            created_at=now,
            updated_at=now,
            metadata=metadata or {},
        )

    def start(self) -> None:
        """启动任务"""
        if self.status.value != TaskStatus.PENDING:
            raise TaskStateError(f"Cannot start task in {self.status.value} state")
        self.status = TaskStatus.running()
        self.updated_at = datetime.utcnow()

    def complete(self, content: str) -> None:
        """完成任务"""
        if self.status.value != TaskStatus.RUNNING:
            raise TaskStateError(f"Cannot complete task in {self.status.value} state")
        self.status = TaskStatus.completed()
        self.content = content
        self.updated_at = datetime.utcnow()

    def fail(self, error_message: str) -> None:
        """标记任务失败"""
        if self.status.value not in [TaskStatus.PENDING, TaskStatus.RUNNING]:
            raise TaskStateError(f"Cannot fail task in {self.status.value} state")
        self.status = TaskStatus.failed()
        self.error_message = error_message
        self.updated_at = datetime.utcnow()

    def cancel(self) -> None:
        """取消任务"""
        if self.status.value not in [TaskStatus.PENDING, TaskStatus.RUNNING]:
            raise TaskStateError(f"Cannot cancel task in {self.status.value} state")
        self.status = TaskStatus.cancelled()
        self.updated_at = datetime.utcnow()

    def is_finished(self) -> bool:
        """检查任务是否已完成（成功或失败）"""
        return self.status.value in [
            TaskStatus.COMPLETED,
            TaskStatus.FAILED,
            TaskStatus.CANCELLED,
        ]
