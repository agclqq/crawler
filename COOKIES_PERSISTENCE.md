# Cookies 持久化功能说明

## 功能概述

实现了多站点 cookies 持久化功能，支持：
- 自动创建 cookies 存储目录
- 按域名分别存储 cookies
- 访问域名时自动加载 cookies
- 浏览页面时自动更新 cookies

## 存储结构

Cookies 存储在 `cookies/` 目录下，按域名分别存储为 JSON 文件：

```
cookies/
├── www_xiaohongshu_com.json    # 小红书域名
├── www_example_com.json        # 其他站点
└── ...
```

文件命名规则：将域名中的点（`.`）替换为下划线（`_`），例如：
- `www.xiaohongshu.com` → `www_xiaohongshu_com.json`
- `example.com` → `example_com.json`

## 实现位置

### 核心方法

**文件**: `infrastructure/adapters/xiaohongshu_service.py`

1. **`_get_domain_from_url()`** (第 100-114 行)
   - 从 URL 中提取域名
   - 移除端口号

2. **`_get_cookies_file_path()`** (第 116-127 行)
   - 获取指定域名的 cookies 文件路径
   - 将域名转换为安全的文件名

3. **`_load_cookies()`** (第 129-159 行)
   - 加载指定域名的 cookies
   - 如果文件不存在，静默跳过
   - 自动补充缺失的 domain 字段

4. **`_save_cookies()`** (第 161-186 行)
   - 保存指定域名的 cookies
   - 过滤出属于当前域名的 cookies（包括子域名）
   - 以 JSON 格式保存

### 自动加载和保存位置

Cookies 在以下场景自动加载和保存：

1. **`check_login_status()`** (第 406-441 行)
   - 访问页面前：加载 cookies
   - 页面加载后：保存 cookies

2. **`wait_for_login()`** (第 443-473 行)
   - 登录成功后：保存 cookies
   - 超时后：也保存 cookies（可能已部分登录）

3. **`search()`** (第 475-547 行)
   - 搜索完成后：保存 cookies

4. **`click_random_visible_link_not_opened()`** (第 633-714 行)
   - 点击链接后：保存 cookies（可能跳转到新页面）

5. **`crawl()`** (第 933-947 行)
   - 访问页面前：加载 cookies
   - 页面加载后：保存 cookies

## 使用方法

### 基本使用

```python
from infrastructure.adapters.xiaohongshu_service import XiaohongshuBrowserService

# 使用默认 cookies 目录（cookies/）
browser_service = XiaohongshuBrowserService(headless=False)

# 或指定自定义 cookies 目录
browser_service = XiaohongshuBrowserService(
    headless=False,
    cookies_dir="my_cookies"
)
```

### 工作流程

1. **首次访问**：
   - 访问 `https://www.xiaohongshu.com/`
   - 系统检查 `cookies/www_xiaohongshu_com.json` 是否存在
   - 如果不存在，跳过加载
   - 页面加载后，自动保存 cookies 到文件

2. **后续访问**：
   - 访问相同域名时，自动加载已保存的 cookies
   - 页面加载后，自动更新 cookies 文件

3. **多站点支持**：
   - 每个域名独立存储 cookies
   - 访问不同域名时，自动加载对应的 cookies 文件

## Cookies 文件格式

Cookies 以 JSON 数组格式存储，每个 cookie 包含以下字段：

```json
[
  {
    "name": "session_id",
    "value": "abc123...",
    "domain": ".xiaohongshu.com",
    "path": "/",
    "expires": 1234567890,
    "httpOnly": true,
    "secure": true,
    "sameSite": "Lax"
  },
  ...
]
```

## 注意事项

1. **安全性**：
   - Cookies 文件包含敏感信息（登录凭证等）
   - 已添加到 `.gitignore`，不会被提交到版本控制
   - 请妥善保管 cookies 文件

2. **域名匹配**：
   - 支持子域名匹配（如 `.xiaohongshu.com` 匹配 `www.xiaohongshu.com`）
   - 保存时会过滤出属于当前域名的 cookies

3. **文件权限**：
   - Cookies 目录会在首次使用时自动创建
   - 确保有写入权限

4. **过期处理**：
   - Playwright 会自动处理过期的 cookies
   - 保存时会包含过期时间信息

## 故障排除

### Cookies 未保存

- 检查 `cookies/` 目录是否存在且有写入权限
- 查看日志中的错误信息
- 确认页面已完全加载（等待时间足够）

### Cookies 未加载

- 检查对应的 cookies 文件是否存在
- 确认域名提取是否正确
- 查看日志中的调试信息

### 多域名问题

- 确保每个域名都有独立的 cookies 文件
- 检查域名提取逻辑是否正确处理了子域名

## 扩展功能

如需手动管理 cookies，可以使用以下方法：

```python
# 手动加载 cookies
domain = browser_service._get_domain_from_url("https://www.xiaohongshu.com/")
page = await browser_service._get_page()
await browser_service._load_cookies(page, domain)

# 手动保存 cookies
await browser_service._save_cookies(page, domain)
```

