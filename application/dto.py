"""数据传输对象定义"""

from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime


@dataclass
class CrawlUrlCommand:
    """爬取 URL 命令"""
    url: str
    options: Optional[Dict[str, Any]] = None


@dataclass
class CrawlResult:
    """爬取结果"""
    task_id: str
    status: str
    url: str
    created_at: datetime
    updated_at: datetime
    content: Optional[str] = None
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    @classmethod
    def from_task(cls, task) -> "CrawlResult":
        """从任务实体创建结果"""
        return cls(
            task_id=str(task.id),
            status=task.status.value,
            url=str(task.url),
            content=task.content,
            error_message=task.error_message,
            created_at=task.created_at,
            updated_at=task.updated_at,
            metadata=task.metadata,
        )


@dataclass
class TaskQuery:
    """任务查询"""
    task_id: Optional[str] = None
    status: Optional[str] = None
    limit: int = 100
    offset: int = 0


@dataclass
class XiaohongshuBrowseCommand:
    """小红书浏览命令"""
    keywords: Optional[list[str]] = None
    config_file: Optional[str] = None
    max_items_per_view: int = 3  # 每个视窗中查看1~5个，默认3个
    max_scrolls: int = 5  # 搜索结果最大滚动次数
    max_comment_scrolls: int = 10  # 评论最大滚动次数
