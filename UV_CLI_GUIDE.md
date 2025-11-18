# UV CLI 入门指南

`uv` 是一个极快的 Python 包安装器和解析器，由 Astral 开发（Ruff 的开发者）。它可以用作 `pip`、`pip-tools`、`virtualenv`、`pipx` 等的替代品。

## 安装 UV

### macOS / Linux

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Windows

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 使用 pip 安装

```bash
pip install uv
```

## 基本概念

### 1. 项目依赖管理

UV 使用 `pyproject.toml` 文件来管理项目依赖，类似于 `poetry` 或 `pipenv`。

### 2. 虚拟环境

UV 会自动管理虚拟环境，默认在项目根目录的 `.venv` 文件夹中。

## 常用命令

### 初始化项目

```bash
# 创建新项目
uv init my-project
cd my-project

# 或者在当前目录初始化
uv init
```

### 添加依赖

```bash
# 添加单个包
uv add requests

# 添加多个包
uv add requests pandas numpy

# 添加开发依赖
uv add --dev pytest black

# 添加特定版本
uv add "requests>=2.28.0"
uv add "django==4.2.0"
```

### 移除依赖

```bash
# 移除包
uv remove requests

# 移除开发依赖
uv remove --dev pytest
```

### 同步依赖

```bash
# 同步依赖（安装 pyproject.toml 中的所有依赖）
uv sync

# 同步并更新锁文件
uv sync --upgrade
```

### 安装依赖

```bash
# 安装项目依赖（等同于 uv sync）
uv install

# 安装特定包（不添加到 pyproject.toml）
uv pip install requests
```

### 运行命令

```bash
# 在虚拟环境中运行 Python 脚本
uv run python script.py

# 运行已安装的命令
uv run pytest
uv run black .

# 运行 Python 模块
uv run python -m infrastructure.database.init_db
```

### 查看依赖

```bash
# 列出所有依赖
uv tree

# 查看特定包的信息
uv pip show requests
```

### 更新依赖

```bash
# 更新所有依赖到最新版本
uv sync --upgrade

# 更新特定包
uv add --upgrade requests
```

### 锁定依赖

```bash
# 生成或更新 uv.lock 文件
uv lock

# 更新锁文件
uv lock --upgrade
```

## 实际使用示例

### 场景 1: 创建新项目

```bash
# 1. 创建项目
uv init my-crawler
cd my-crawler

# 2. 添加依赖
uv add playwright loguru pydantic

# 3. 查看项目结构
ls -la
# 会看到：
# - pyproject.toml  (项目配置和依赖)
# - uv.lock         (锁定的依赖版本)
# - .venv/          (虚拟环境，自动创建)

# 4. 运行代码
uv run python main.py
```

### 场景 2: 在现有项目中使用

```bash
# 1. 进入项目目录
cd /path/to/project

# 2. 同步依赖（安装所有依赖）
uv sync

# 3. 运行项目
uv run python main.py

# 4. 添加新依赖
uv add requests

# 5. 再次同步（确保新依赖被安装）
uv sync
```

### 场景 3: 运行 CLI 工具

```bash
# 1. 安装 CLI 工具（全局或项目级）
uv tool install black
uv tool install pytest

# 2. 运行工具
uv run black .
uv run pytest

# 或者直接使用（如果全局安装）
black .
pytest
```

### 场景 4: 管理多个 Python 版本

```bash
# 1. 安装特定 Python 版本
uv python install 3.11
uv python install 3.12

# 2. 使用特定版本创建项目
uv init --python 3.11 my-project

# 3. 在项目中使用特定版本
uv python pin 3.11
```

## 与本项目的使用

### 当前项目结构

本项目已经配置了 `uv`，你可以看到：

```
crawler/
├── pyproject.toml    # 项目配置和依赖定义
├── uv.lock          # 锁定的依赖版本
└── .venv/           # 虚拟环境（自动创建）
```

### 常用操作

```bash
# 1. 安装/同步所有依赖
uv sync

# 2. 运行爬虫 CLI
uv run crawler xiaohongshu-browse --keywords 美食

# 3. 运行示例脚本
uv run python examples/xiaohongshu_browse.py

# 4. 运行数据库初始化
uv run python -m infrastructure.database.init_db

# 5. 安装 Playwright 浏览器
uv run playwright install

# 6. 添加新依赖
uv add some-package

# 7. 查看依赖树
uv tree
```

## UV vs 其他工具

| 功能 | UV | pip | poetry | pipenv |
|------|----|-----|--------|--------|
| 速度 | ⚡ 极快 | 🐌 慢 | 🚀 快 | 🐌 慢 |
| 依赖解析 | ✅ 优秀 | ⚠️ 基础 | ✅ 优秀 | ✅ 优秀 |
| 虚拟环境管理 | ✅ 自动 | ❌ 手动 | ✅ 自动 | ✅ 自动 |
| 锁文件 | ✅ uv.lock | ❌ 无 | ✅ poetry.lock | ✅ Pipfile.lock |
| 项目模板 | ✅ 支持 | ❌ 无 | ✅ 支持 | ❌ 无 |

## 优势

1. **极快的速度**: 比 pip 快 10-100 倍
2. **自动虚拟环境**: 无需手动创建和管理
3. **依赖解析**: 快速且准确的依赖解析
4. **兼容性**: 兼容 pip 和 PyPI
5. **跨平台**: 支持 Windows、macOS、Linux

## 常见问题

### Q: uv sync 和 uv install 有什么区别？

A: 
- `uv sync`: 同步 `pyproject.toml` 中的依赖，确保虚拟环境与配置一致
- `uv install`: 安装依赖，但不一定与 `pyproject.toml` 完全同步

### Q: 如何迁移现有项目到 uv？

A:
```bash
# 1. 如果有 requirements.txt
uv pip compile requirements.txt -o pyproject.toml

# 2. 或者手动创建 pyproject.toml，然后
uv sync
```

### Q: uv.lock 文件需要提交到 Git 吗？

A: **是的**，应该提交。它确保所有开发者使用相同的依赖版本。

### Q: 如何更新所有依赖？

A:
```bash
uv sync --upgrade
# 或
uv lock --upgrade
uv sync
```

## 更多资源

- 官方文档: https://docs.astral.sh/uv/
- GitHub: https://github.com/astral-sh/uv
- 快速开始: https://docs.astral.sh/uv/getting-started/

