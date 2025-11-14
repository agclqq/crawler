# Domain Layer (领域层)

## 概述

领域层是 DDD 架构的核心，包含业务领域的所有核心概念和规则。这一层不依赖任何技术实现，只关注业务逻辑。

## 职责

1. **实体（Entities）**: 具有唯一标识的业务对象
2. **值对象（Value Objects）**: 不可变的业务概念
3. **领域服务（Domain Services）**: 不属于特定实体的业务逻辑
4. **仓储接口（Repository Interfaces）**: 定义数据访问的抽象接口

## 最佳实践

### 1. 保持领域层纯净

- ❌ 不要引入技术框架依赖（如 SQLAlchemy、Playwright 等）
- ✅ 只使用 Python 标准库和纯业务逻辑库（如 pydantic）
- ✅ 定义接口而非实现

### 2. 实体设计原则

```python
# ✅ 好的实体设计
class CrawlerTask(Entity):
    """爬虫任务实体"""
    id: TaskId
    url: URL
    status: TaskStatus
    created_at: datetime
    
    def start(self) -> None:
        """领域方法：启动任务"""
        if self.status != TaskStatus.PENDING:
            raise DomainError("只能启动待处理的任务")
        self.status = TaskStatus.RUNNING
```

### 3. 值对象设计

```python
# ✅ 好的值对象设计
@dataclass(frozen=True)
class URL:
    """URL 值对象"""
    value: str
    
    def __post_init__(self):
        if not self._is_valid(self.value):
            raise ValueError(f"Invalid URL: {self.value}")
```

### 4. 领域服务

当业务逻辑不属于任何特定实体时，使用领域服务：

```python
class URLNormalizer:
    """URL 标准化服务"""
    
    @staticmethod
    def normalize(url: str) -> str:
        # 业务逻辑：标准化 URL
        pass
```

### 5. 仓储接口

定义数据访问的抽象接口，实现在基础设施层：

```python
class ICrawlerTaskRepository(ABC):
    """爬虫任务仓储接口"""
    
    @abstractmethod
    async def save(self, task: CrawlerTask) -> None:
        pass
    
    @abstractmethod
    async def find_by_id(self, task_id: TaskId) -> Optional[CrawlerTask]:
        pass
```

## 目录结构

```
domain/
├── entities/          # 实体定义
├── value_objects/     # 值对象定义
├── services/          # 领域服务
├── repositories/      # 仓储接口
└── exceptions/        # 领域异常
```

## 注意事项

- 领域层应该是框架无关的，可以独立测试
- 使用类型提示增强代码可读性
- 遵循单一职责原则，每个类只做一件事

