# Infrastructure Layer (基础设施层)

## 概述

基础设施层提供技术实现，包括外部服务集成、数据持久化、框架适配等。这一层实现领域层和应用层定义的接口。

## 职责

1. **仓储实现（Repository Implementations）**: 实现数据访问
2. **外部服务适配器（Adapters）**: 集成外部服务（如 Playwright）
3. **数据库配置**: 数据库连接和迁移
4. **配置管理**: 环境配置和设置

## 最佳实践

### 1. 实现领域接口

基础设施层实现领域层定义的接口：

```python
# ✅ 实现领域接口
class SQLAlchemyCrawlerTaskRepository(ICrawlerTaskRepository):
    """SQLAlchemy 实现的爬虫任务仓储"""
    
    def __init__(self, session: AsyncSession):
        self._session = session
    
    async def save(self, task: CrawlerTask) -> None:
        # 实现保存逻辑
        pass
    
    async def find_by_id(self, task_id: TaskId) -> Optional[CrawlerTask]:
        # 实现查询逻辑
        pass
```

### 2. Playwright 适配器

将 Playwright 封装为领域服务接口：

```python
class PlaywrightBrowserService(IBrowserService):
    """Playwright 浏览器服务实现"""
    
    def __init__(self, browser_type: str = "chromium"):
        self._browser_type = browser_type
    
    async def crawl(self, url: URL) -> CrawlResult:
        async with async_playwright() as p:
            browser = await p[self._browser_type].launch()
            page = await browser.new_page()
            await page.goto(url.value)
            content = await page.content()
            await browser.close()
            return CrawlResult(content=content)
```

### 3. 数据库配置

使用 SQLAlchemy 和 Alembic 管理数据库：

```python
# ✅ 数据库配置
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

engine = create_async_engine(DATABASE_URL)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
```

### 4. 配置管理

使用环境变量和配置文件：

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    log_level: str = "INFO"
    playwright_browser: str = "chromium"
    
    class Config:
        env_file = ".env"
```

## 目录结构

```
infrastructure/
├── repositories/      # 仓储实现
├── adapters/          # 外部服务适配器
│   └── playwright/    # Playwright 适配器
├── database/          # 数据库配置和模型
│   ├── models/        # SQLAlchemy 模型
│   └── migrations/    # Alembic 迁移
└── config/            # 配置管理
```

## 注意事项

- 基础设施层可以依赖技术框架（SQLAlchemy、Playwright 等）
- 实现领域层定义的接口，保持接口契约
- 处理技术异常并转换为领域异常
- 使用依赖注入容器管理依赖关系

