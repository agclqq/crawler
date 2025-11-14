# 快速开始指南

## 前置要求

- Python 3.10+
- uv (推荐) 或 conda

## 安装步骤

### 1. 安装 uv（如果未安装）

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. 初始化项目

```bash
# 运行初始化脚本
./setup.sh

# 或手动执行
uv sync
uv run playwright install
uv run python -m infrastructure.database.init_db
```

### 3. 配置环境变量（可选）

```bash
cp .env.example .env
# 编辑 .env 文件设置数据库 URL 等配置
```

## 使用示例

### 基础爬虫示例

```bash
uv run python examples/basic_crawler.py
```

### 数据库操作示例

```bash
uv run python examples/database_demo.py
```

### 使用 CLI

```bash
# 爬取 URL
uv run crawler crawl https://example.com --output output.html

# 查看任务列表
uv run crawler list-tasks

# 查看任务详情
uv run crawler get-task <task_id>
```

## 项目结构说明

```
crawler/
├── domain/              # 领域层 - 核心业务逻辑
│   ├── entities.py      # 实体定义
│   ├── value_objects.py # 值对象
│   ├── repositories.py  # 仓储接口
│   └── services.py      # 领域服务接口
├── application/         # 应用层 - 用例实现
│   ├── use_cases.py     # 用例
│   └── dto.py           # 数据传输对象
├── infrastructure/      # 基础设施层 - 技术实现
│   ├── adapters/        # 外部服务适配器
│   ├── database/        # 数据库配置
│   └── repositories.py  # 仓储实现
├── interface/           # 接口层 - API/CLI
│   └── cli/             # 命令行接口
└── examples/            # 示例代码
```

## 扩展开发

### 添加新的爬虫功能

1. 在 `infrastructure/adapters/playwright_service.py` 中扩展 `PlaywrightBrowserService`
2. 或创建新的浏览器服务实现 `IBrowserService` 接口

### 添加新的用例

1. 在 `application/use_cases.py` 中创建新的用例类
2. 在 `interface/cli/main.py` 中添加对应的 CLI 命令

### 添加新的数据模型

1. 在 `domain/entities.py` 中定义实体
2. 在 `infrastructure/database/models.py` 中定义数据库模型
3. 在 `infrastructure/database/mappers.py` 中添加映射函数
4. 在 `infrastructure/repositories.py` 中实现仓储

## 数据库支持

默认使用 SQLite，可以通过环境变量切换到 PostgreSQL：

```bash
# .env
DATABASE_URL=postgresql+asyncpg://user:password@localhost/dbname
```

## 开发工具

```bash
# 代码格式化
uv run black .

# 代码检查
uv run ruff check .

# 类型检查
uv run mypy .

# 运行测试
uv run pytest
```

## 常见问题

### Q: 如何切换浏览器？

A: 设置环境变量 `PLAYWRIGHT_BROWSER=firefox` 或 `webkit`

### Q: 如何禁用无头模式？

A: 设置环境变量 `PLAYWRIGHT_HEADLESS=false` 或使用 CLI 参数 `--no-headless`

### Q: 如何查看日志？

A: 日志使用 loguru，默认输出到控制台。可以通过环境变量 `LOG_LEVEL` 设置日志级别。

