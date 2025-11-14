# 通用爬虫框架

基于 Playwright 的通用爬虫框架，采用领域驱动设计（DDD）架构。

## 特性

- 🏗️ **DDD 分层架构**: 清晰的领域驱动设计，易于维护和扩展
- 🎭 **Playwright 支持**: 强大的浏览器自动化能力
- 💾 **数据库集成**: 支持 SQLite 和 PostgreSQL，易于扩展
- 🖥️ **CLI 工具**: 便捷的命令行接口
- 📝 **类型提示**: 完整的 Python 类型提示支持
- 🔧 **易于扩展**: 清晰的接口设计，方便添加新功能

## 项目结构

```
crawler/
├── domain/              # 领域层 - 核心业务逻辑和实体
├── application/         # 应用层 - 用例和业务流程
├── infrastructure/      # 基础设施层 - 技术实现
├── interface/           # 接口层 - API 和 CLI
├── tests/               # 测试文件
└── examples/            # 示例代码
```

详细结构说明请参考 [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)

## 快速开始

### 前置要求

- Python 3.10+
- uv (推荐) 或 conda

### 安装步骤

```bash
# 1. 运行初始化脚本（推荐）
./setup.sh

# 或手动安装
uv sync
uv run playwright install
uv run python -m infrastructure.database.init_db
```

### 运行示例

```bash
# 基础爬虫示例
uv run python examples/basic_crawler.py

# 数据库操作示例
uv run python examples/database_demo.py

# 使用 CLI
uv run crawler crawl https://example.com --output output.html
```

更多使用说明请参考 [QUICKSTART.md](QUICKSTART.md)

## 架构说明

本项目采用 DDD（领域驱动设计）分层架构：

- **Domain Layer**: 定义核心业务实体、值对象和领域服务
- **Application Layer**: 实现具体的用例和业务流程编排
- **Infrastructure Layer**: 提供技术实现（Playwright、数据库等）
- **Interface Layer**: 提供外部接口（API、CLI 等）

详细说明请参考各层的 README.md 文件：
- [领域层 README](domain/README.md)
- [应用层 README](application/README.md)
- [基础设施层 README](infrastructure/README.md)
- [接口层 README](interface/README.md)

## 开发规范

请参考 [.cursorrules](.cursorrules) 文件了解项目的开发规范和最佳实践。

## 依赖管理

本项目使用 `uv` 管理 Python 依赖。如果某些包无法通过 uv 管理，可以使用 conda。

主要依赖：
- `playwright`: 浏览器自动化
- `sqlalchemy`: ORM 框架
- `pydantic`: 数据验证
- `loguru`: 日志记录
- `click`: CLI 框架

## 数据库支持

- **SQLite** (默认): 适合开发和测试
- **PostgreSQL**: 适合生产环境

通过环境变量 `DATABASE_URL` 配置数据库连接。

## 许可证

MIT License

