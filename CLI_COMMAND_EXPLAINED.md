# CLI 命令参数详解

## 命令结构

```bash
uv run crawler xiaohongshu-browse [选项]
```

## 各部分含义

### 1. `uv`
**含义**: UV 包管理器命令

**作用**: 用于运行 Python 项目中的命令，类似于 `npm run` 或 `cargo run`

**说明**: 
- UV 会自动激活项目的虚拟环境（`.venv`）
- 无需手动 `source .venv/bin/activate`
- 确保在正确的 Python 环境中运行

---

### 2. `run`
**含义**: UV 的运行命令

**作用**: 在项目的虚拟环境中执行命令

**说明**:
- `uv run` 会在项目的虚拟环境中执行后续命令
- 等同于：激活虚拟环境 → 运行命令 → 退出虚拟环境
- 比手动管理虚拟环境更方便

**等价命令**:
```bash
# 传统方式
source .venv/bin/activate
crawler xiaohongshu-browse
deactivate

# UV 方式（一行搞定）
uv run crawler xiaohongshu-browse
```

---

### 3. `crawler`
**含义**: 项目的 CLI 入口命令

**定义位置**: `pyproject.toml` 第 32 行
```toml
[project.scripts]
crawler = "interface.cli.main:cli"
```

**作用**: 
- 这是项目定义的 CLI 命令名称
- 指向 `interface.cli.main` 模块的 `cli` 函数
- 使用 Click 框架构建的命令组（command group）

**说明**:
- 安装项目后，`crawler` 命令会被注册到系统 PATH
- 可以通过 `crawler --help` 查看所有可用命令
- 是项目的"主命令"，下面有多个子命令

**查看帮助**:
```bash
uv run crawler --help
# 输出：
# Usage: crawler [OPTIONS] COMMAND [ARGS]...
# 
#   通用爬虫框架 CLI
# 
# Commands:
#   crawl              爬取指定 URL
#   get-task           获取任务详情
#   list-tasks         列出任务
#   xiaohongshu-browse 浏览小红书内容
```

---

### 4. `xiaohongshu-browse`
**含义**: 小红书浏览功能的子命令

**定义位置**: `interface/cli/main.py` 第 109-143 行

**作用**: 执行小红书自动浏览功能

**功能**: 
- 自动登录检测
- 搜索关键词
- 浏览搜索结果
- 查看内容和评论
- 模拟人类行为

**说明**:
- 这是 `crawler` 命令组下的一个子命令
- 使用下划线命名，但在 CLI 中可以用连字符调用
- 即 `xiaohongshu-browse` 和 `xiaohongshu_browse` 都可以

---

## 完整命令示例

### 基本用法

```bash
# 使用配置文件中的关键词
uv run crawler xiaohongshu-browse

# 直接指定关键词
uv run crawler xiaohongshu-browse --keywords 美食

# 多个关键词
uv run crawler xiaohongshu-browse --keywords 美食 --keywords 旅行
```

### 完整参数示例

```bash
uv run crawler xiaohongshu-browse \
  --keywords 美食 \
  --keywords 旅行 \
  --max-items 5 \
  --max-scrolls 10 \
  --max-comment-scrolls 15 \
  --no-headless
```

## 可用选项

### `--config` / `-c`
- **类型**: 字符串
- **默认值**: `config/search_keywords.json`
- **说明**: 搜索关键词配置文件路径
- **示例**: `--config my_keywords.json`

### `--keywords` / `-k`
- **类型**: 可重复选项（可多次使用）
- **默认值**: 无（使用配置文件）
- **说明**: 直接指定搜索关键词
- **示例**: `--keywords 美食 --keywords 旅行`

### `--max-items`
- **类型**: 整数
- **默认值**: `3`
- **说明**: 每个视窗中查看的内容数量（1-5）
- **示例**: `--max-items 5`

### `--max-scrolls`
- **类型**: 整数
- **默认值**: `5`
- **说明**: 搜索结果最大滚动次数
- **示例**: `--max-scrolls 10`

### `--max-comment-scrolls`
- **类型**: 整数
- **默认值**: `10`
- **说明**: 评论最大滚动次数
- **示例**: `--max-comment-scrolls 15`

### `--headless` / `--no-headless`
- **类型**: 布尔标志
- **默认值**: `False`（显示浏览器）
- **说明**: 是否使用无头模式
- **示例**: `--headless`（无头模式）或 `--no-headless`（显示浏览器）

## 命令执行流程

```
uv run crawler xiaohongshu-browse --keywords 美食
    │
    ├─ 1. UV 激活虚拟环境 (.venv)
    │
    ├─ 2. 查找并执行 crawler 命令
    │     └─ 定位到 interface.cli.main:cli
    │
    ├─ 3. Click 解析命令参数
    │     └─ 识别子命令: xiaohongshu-browse
    │
    ├─ 4. 执行 xiaohongshu_browse 函数
    │     ├─ 创建 XiaohongshuBrowserService
    │     ├─ 构建 XiaohongshuBrowseCommand
    │     ├─ 执行 XiaohongshuBrowseUseCase
    │     └─ 关闭浏览器服务
    │
    └─ 5. UV 退出虚拟环境
```

## 等价命令对比

### 使用 UV（推荐）
```bash
uv run crawler xiaohongshu-browse --keywords 美食
```

### 传统方式
```bash
# 1. 激活虚拟环境
source .venv/bin/activate

# 2. 运行命令
crawler xiaohongshu-browse --keywords 美食

# 3. 退出虚拟环境
deactivate
```

### 直接使用 Python 模块
```bash
python -m interface.cli.main xiaohongshu-browse --keywords 美食
```

## 查看帮助信息

```bash
# 查看主命令帮助
uv run crawler --help

# 查看子命令帮助
uv run crawler xiaohongshu-browse --help
```

## 常见问题

### Q: 为什么用 `uv run` 而不是直接运行 `crawler`？

A: 
- `uv run` 确保在正确的虚拟环境中运行
- 自动管理依赖和 Python 版本
- 无需手动激活虚拟环境

### Q: `crawler` 命令是怎么来的？

A: 
- 定义在 `pyproject.toml` 的 `[project.scripts]` 中
- 安装项目后自动注册到系统
- 指向 `interface.cli.main:cli` 函数

### Q: 可以不用 `uv run` 吗？

A: 
- 可以，但需要先激活虚拟环境
- 或者直接使用 `python -m interface.cli.main`
- `uv run` 更方便，推荐使用

### Q: 命令名称可以改吗？

A: 
- 可以，修改 `pyproject.toml` 中的 `crawler = "interface.cli.main:cli"`
- 例如改为 `my-crawler = "interface.cli.main:cli"`
- 然后重新安装项目：`uv sync`


