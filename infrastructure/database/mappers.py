"""领域对象和数据库模型映射"""

from domain.entities import CrawlerTask
from domain.value_objects import TaskId, URL, TaskStatus
from infrastructure.database.models import CrawlerTaskModel


def task_to_model(task: CrawlerTask) -> CrawlerTaskModel:
    """将领域实体转换为数据库模型"""
    return CrawlerTaskModel(
        id=str(task.id),
        url=str(task.url),
        status=task.status.value,
        content=task.content,
        error_message=task.error_message,
        task_metadata=task.metadata,  # 使用 task_metadata 属性
        created_at=task.created_at,
        updated_at=task.updated_at,
    )


def model_to_task(model: CrawlerTaskModel) -> CrawlerTask:
    """将数据库模型转换为领域实体"""
    return CrawlerTask(
        id=TaskId(model.id),
        url=URL(model.url),
        status=TaskStatus(model.status),
        content=model.content,
        error_message=model.error_message,
        metadata=model.task_metadata or {},  # 从 task_metadata 读取
        created_at=model.created_at,
        updated_at=model.updated_at,
    )

