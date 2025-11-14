# 项目结构说明

## 目录树

```
crawler/
├── domain/                      # 领域层
│   ├── __init__.py
│   ├── README.md                # 领域层说明文档
│   ├── entities.py              # 实体定义（CrawlerTask）
│   ├── value_objects.py         # 值对象（URL, TaskId, TaskStatus）
│   ├── repositories.py          # 仓储接口（ICrawlerTaskRepository）
│   ├── services.py              # 领域服务接口（IBrowserService）
│   └── exceptions.py            # 领域异常
│
├── application/                 # 应用层
│   ├── __init__.py
│   ├── README.md                # 应用层说明文档
│   ├── use_cases.py             # 用例实现
│   │   ├── CrawlUrlUseCase      # 爬取 URL 用例
│   │   ├── GetTaskUseCase       # 获取任务用例
│   │   └── ListTasksUseCase     # 列出任务用例
│   └── dto.py                   # 数据传输对象
│       ├── CrawlUrlCommand
│       ├── CrawlResult
│       └── TaskQuery
│
├── infrastructure/              # 基础设施层
│   ├── __init__.py
│   ├── README.md                # 基础设施层说明文档
│   ├── config.py                # 配置管理
│   ├── repositories.py          # 仓储实现（SQLAlchemyCrawlerTaskRepository）
│   └── adapters/                # 外部服务适配器
│       ├── __init__.py
│       └── playwright_service.py # Playwright 浏览器服务
│   └── database/                # 数据库模块
│       ├── __init__.py
│       ├── models.py             # SQLAlchemy 模型
│       ├── session.py            # 数据库会话管理
│       ├── mappers.py            # 领域对象和数据库模型映射
│       └── init_db.py            # 数据库初始化脚本
│
├── interface/                   # 接口层
│   ├── __init__.py
│   ├── README.md                # 接口层说明文档
│   └── cli/                     # 命令行接口
│       ├── __init__.py
│       └── main.py              # CLI 主程序
│
├── examples/                    # 示例代码
│   ├── __init__.py
│   ├── basic_crawler.py         # 基础爬虫示例
│   └── database_demo.py         # 数据库操作示例
│
├── tests/                       # 测试文件
│   └── __init__.py
│
├── pyproject.toml               # 项目配置和依赖
├── uv.lock                      # uv 依赖锁定文件
├── .gitignore                   # Git 忽略文件
├── .cursorrules                 # Cursor 开发规范
├── .env.example                 # 环境变量示例
├── setup.sh                     # 项目初始化脚本
├── README.md                    # 项目主文档
├── QUICKSTART.md                # 快速开始指南
└── PROJECT_STRUCTURE.md         # 本文件
```

## 各层职责

### Domain Layer (领域层)
- **位置**: `domain/`
- **职责**: 核心业务逻辑，不依赖任何技术框架
- **包含**:
  - 实体（Entities）
  - 值对象（Value Objects）
  - 领域服务接口（Domain Service Interfaces）
  - 仓储接口（Repository Interfaces）
  - 领域异常（Domain Exceptions）

### Application Layer (应用层)
- **位置**: `application/`
- **职责**: 用例实现和业务流程编排
- **包含**:
  - 用例服务（Use Cases）
  - 数据传输对象（DTOs）
  - 用例编排逻辑

### Infrastructure Layer (基础设施层)
- **位置**: `infrastructure/`
- **职责**: 技术实现和外部服务集成
- **包含**:
  - 仓储实现（Repository Implementations）
  - 外部服务适配器（Adapters）
  - 数据库配置和模型
  - 配置管理

### Interface Layer (接口层)
- **位置**: `interface/`
- **职责**: 外部接口（API、CLI）
- **包含**:
  - CLI 命令
  - 输入验证
  - 响应序列化

## 数据流

```
CLI/API (Interface Layer)
    ↓
Use Cases (Application Layer)
    ↓
Entities & Services (Domain Layer)
    ↓
Repositories & Adapters (Infrastructure Layer)
    ↓
Database / Playwright
```

## 依赖关系

- **Domain** ← 无依赖（最纯净）
- **Application** ← 依赖 Domain
- **Infrastructure** ← 依赖 Domain（实现接口）
- **Interface** ← 依赖 Application, Infrastructure

## 扩展点

### 添加新的浏览器引擎
1. 在 `domain/services.py` 中定义接口（如果不存在）
2. 在 `infrastructure/adapters/` 中实现新的适配器
3. 在配置中支持选择不同的浏览器服务

### 添加新的数据存储
1. 在 `infrastructure/database/models.py` 中添加新模型
2. 在 `infrastructure/repositories.py` 中实现新的仓储
3. 在 `infrastructure/database/mappers.py` 中添加映射

### 添加新的用例
1. 在 `application/use_cases.py` 中实现新用例
2. 在 `application/dto.py` 中定义相关 DTO
3. 在 `interface/cli/main.py` 中添加 CLI 命令

## 最佳实践

1. **保持领域层纯净**: 不要引入技术框架依赖
2. **依赖注入**: 通过构造函数注入依赖
3. **接口隔离**: 定义清晰的接口契约
4. **单一职责**: 每个类只做一件事
5. **类型提示**: 使用类型提示提高代码可读性

