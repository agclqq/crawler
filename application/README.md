# Application Layer (应用层)

## 概述

应用层负责编排领域对象来完成特定的用例（Use Cases）。它协调领域层和基础设施层，但不包含业务规则本身。

## 职责

1. **用例服务（Use Cases）**: 实现具体的业务用例
2. **DTO（Data Transfer Objects）**: 数据传输对象
3. **应用服务（Application Services）**: 编排多个用例或领域服务

## 最佳实践

### 1. 用例设计原则

每个用例应该：
- 专注于一个业务目标
- 协调领域对象完成业务逻辑
- 处理事务边界
- 处理异常和错误

```python
# ✅ 好的用例设计
class CrawlUrlUseCase:
    """爬取 URL 的用例"""
    
    def __init__(
        self,
        task_repo: ICrawlerTaskRepository,
        browser_service: IBrowserService,
    ):
        self._task_repo = task_repo
        self._browser_service = browser_service
    
    async def execute(self, command: CrawlUrlCommand) -> CrawlResult:
        """执行爬取用例"""
        # 1. 创建领域对象
        task = CrawlerTask.create(command.url)
        
        # 2. 保存任务
        await self._task_repo.save(task)
        
        # 3. 执行爬取
        try:
            result = await self._browser_service.crawl(task.url)
            task.complete(result)
        except Exception as e:
            task.fail(str(e))
        finally:
            await self._task_repo.save(task)
        
        return CrawlResult.from_task(task)
```

### 2. DTO 设计

使用 DTO 在层之间传输数据：

```python
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
    content: Optional[str] = None
    error: Optional[str] = None
```

### 3. 依赖注入

通过构造函数注入依赖，便于测试：

```python
class CrawlUrlUseCase:
    def __init__(
        self,
        task_repo: ICrawlerTaskRepository,
        browser_service: IBrowserService,
    ):
        # 依赖注入
        pass
```

### 4. 事务管理

在应用层管理事务边界：

```python
class CrawlUrlUseCase:
    async def execute(self, command: CrawlUrlCommand) -> CrawlResult:
        async with self._unit_of_work:
            # 所有操作在同一事务中
            task = CrawlerTask.create(command.url)
            await self._task_repo.save(task)
            # ...
```

## 目录结构

```
application/
├── use_cases/         # 用例实现
├── dto/               # 数据传输对象
├── services/          # 应用服务
└── mappers/           # DTO 和领域对象映射
```

## 注意事项

- 应用层不包含业务规则，只负责编排
- 使用依赖注入提高可测试性
- 保持用例的单一职责
- 处理异常并转换为适当的错误响应

