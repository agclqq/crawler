# 小红书浏览功能使用指南

## 功能概述

实现了小红书浏览、搜索、查看内容和评论的完整功能，包括：

1. **登录状态检查**: 自动检测是否需要登录
2. **搜索功能**: 支持从配置文件或命令行指定搜索关键词
3. **浏览搜索结果**: 自动滚动浏览搜索结果
4. **查看内容**: 随机点击搜索结果，查看详情
5. **浏览评论**: 在内容页面中滚动浏览评论
6. **关闭内容**: 自动关闭内容浮层

## 配置文件

搜索关键词配置文件：`config/search_keywords.json`

```json
{
  "keywords": [
    "美食",
    "旅行",
    "穿搭",
    "护肤",
    "健身",
    "摄影",
    "读书",
    "电影"
  ]
}
```

## 使用方法

### 1. 使用 CLI 命令

```bash
# 使用配置文件中的关键词
uv run crawler xiaohongshu-browse

# 指定配置文件
uv run crawler xiaohongshu-browse --config config/search_keywords.json

# 直接指定关键词（可多个）
uv run crawler xiaohongshu-browse --keywords 美食 --keywords 旅行

# 自定义参数
uv run crawler xiaohongshu-browse \
  --keywords 美食 \
  --max-items 5 \
  --max-scrolls 10 \
  --max-comment-scrolls 15 \
  --no-headless  # 显示浏览器窗口
```

### 2. 使用 Python 代码

```python
import asyncio
from infrastructure.adapters.xiaohongshu_service import XiaohongshuBrowserService
from application.xiaohongshu_use_cases import XiaohongshuBrowseUseCase
from application.dto import XiaohongshuBrowseCommand

async def main():
    browser_service = XiaohongshuBrowserService(headless=False)
    
    try:
        use_case = XiaohongshuBrowseUseCase(browser_service)
        
        command = XiaohongshuBrowseCommand(
            keywords=["美食", "旅行"],
            max_items_per_view=3,
            max_scrolls=5,
            max_comment_scrolls=10,
        )
        
        await use_case.execute(command)
    finally:
        await browser_service.close()

asyncio.run(main())
```

### 3. 运行示例

```bash
uv run python examples/xiaohongshu_browse.py
```

## 参数说明

### CLI 参数

- `--config, -c`: 搜索关键词配置文件路径（默认: `config/search_keywords.json`）
- `--keywords, -k`: 直接指定搜索关键词（可多个）
- `--max-items`: 每个视窗中查看的内容数量（1-5，默认: 3）
- `--max-scrolls`: 搜索结果最大滚动次数（默认: 5）
- `--max-comment-scrolls`: 评论最大滚动次数（默认: 10）
- `--headless/--no-headless`: 是否使用无头模式（默认: False，显示浏览器）

### 程序参数

- `keywords`: 搜索关键词列表（可选）
- `config_file`: 配置文件路径（可选）
- `max_items_per_view`: 每个视窗中查看的内容数量（1-5）
- `max_scrolls`: 搜索结果最大滚动次数
- `max_comment_scrolls`: 评论最大滚动次数

## 工作流程

1. **访问主页**: 访问 `https://www.xiaohongshu.com/`
2. **检查登录**: 
   - 等待页面加载 2 秒
   - 循环检查 HTML 中是否有 `class="login-container"`
   - 如果需要登录，随机等待 1~2 秒
3. **搜索内容**:
   - 从配置文件或命令行参数加载搜索关键词
   - 对每个关键词执行搜索
4. **浏览搜索结果**:
   - 滚动页面，每次滚动 0.3~1.5 视窗高度
   - 停留时间随机 0.5~3 秒
5. **查看内容**:
   - 随机点击当前视窗中的链接（不点击超出视窗的内容）
   - 等待内容页面加载（检查 `id="noteContainer"`）
   - 浏览评论（在 `class="comments-container"` 中）
   - 随机下拉，翻看评论，每次间隔 0.5~5 秒
   - 点击 `noteContainer` 以外的部分关闭内容
6. **重复流程**: 每个视窗中随机查看 1~5 个内容

## 注意事项

1. **登录状态**: 如果检测到需要登录，程序会继续执行，但可能无法正常浏览内容。建议先手动登录。

2. **反爬虫**: 小红书可能有反爬虫机制，建议：
   - 使用非无头模式观察行为
   - 适当增加等待时间
   - 不要过于频繁地访问

3. **选择器**: 如果页面结构变化，可能需要更新选择器：
   - 搜索框选择器
   - 链接选择器
   - 评论容器选择器

4. **视窗高度**: 默认视窗高度为 1080px，如需调整可在代码中修改。

## 扩展开发

### 添加新的选择器

在 `infrastructure/adapters/xiaohongshu_service.py` 中修改相应的选择器列表：

```python
# 搜索框选择器
search_selectors = [
    'input[placeholder*="搜索"]',
    'input[type="search"]',
    # 添加新的选择器
]

# 链接选择器
link_selectors = [
    'a[href*="/explore/"]',
    'a[href*="/discovery/"]',
    # 添加新的选择器
]
```

### 调整滚动和等待时间

在用例中修改随机时间范围：

```python
# 滚动距离
scroll_distance = random.uniform(0.3, 1.5) * 1080

# 等待时间
wait_time = random.uniform(0.5, 3)
```

## 故障排除

### 问题：找不到搜索框

**解决方案**: 检查页面是否已加载，可能需要增加等待时间或更新选择器。

### 问题：点击链接后没有打开内容

**解决方案**: 
1. 检查链接选择器是否正确
2. 确认链接是否在视窗内
3. 增加点击后的等待时间

### 问题：评论容器找不到

**解决方案**: 
1. 确认内容页面已加载（检查 `#noteContainer`）
2. 更新评论容器选择器
3. 增加等待时间

## 日志

程序使用 `loguru` 记录日志，可以通过环境变量 `LOG_LEVEL` 设置日志级别：

```bash
export LOG_LEVEL=DEBUG
uv run crawler xiaohongshu-browse
```

