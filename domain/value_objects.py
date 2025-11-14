"""值对象定义"""

from dataclasses import dataclass
from urllib.parse import urlparse
from domain.exceptions import InvalidURLError


@dataclass(frozen=True)
class URL:
    """URL 值对象"""
    value: str
    
    def __post_init__(self):
        """验证 URL 格式"""
        if not self._is_valid(self.value):
            raise InvalidURLError(f"Invalid URL: {self.value}")
    
    @staticmethod
    def _is_valid(url: str) -> bool:
        """检查 URL 是否有效"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False
    
    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class TaskId:
    """任务 ID 值对象"""
    value: str
    
    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class TaskStatus:
    """任务状态值对象"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    
    value: str
    
    def __post_init__(self):
        """验证状态值"""
        valid_statuses = [
            self.PENDING,
            self.RUNNING,
            self.COMPLETED,
            self.FAILED,
            self.CANCELLED,
        ]
        if self.value not in valid_statuses:
            raise ValueError(f"Invalid status: {self.value}")
    
    def __str__(self) -> str:
        return self.value
    
    @classmethod
    def pending(cls) -> "TaskStatus":
        return cls(cls.PENDING)
    
    @classmethod
    def running(cls) -> "TaskStatus":
        return cls(cls.RUNNING)
    
    @classmethod
    def completed(cls) -> "TaskStatus":
        return cls(cls.COMPLETED)
    
    @classmethod
    def failed(cls) -> "TaskStatus":
        return cls(cls.FAILED)
    
    @classmethod
    def cancelled(cls) -> "TaskStatus":
        return cls(cls.CANCELLED)


@dataclass(frozen=True)
class SearchKeyword:
    """搜索关键词值对象"""
    value: str
    
    def __post_init__(self):
        """验证搜索词"""
        if not self.value or not self.value.strip():
            raise ValueError("Search keyword cannot be empty")
    
    def __str__(self) -> str:
        return self.value.strip()
