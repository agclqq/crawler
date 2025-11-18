# 代码重构说明文档

## 重构概述

本次重构将公共功能抽取到基类 `BaseBrowserService`，提升了代码复用率和可维护性。

## 重构内容

### 1. 创建基础服务类

**文件**: `infrastructure/adapters/base_browser_service.py`

创建了 `BaseBrowserService` 基类，包含以下公共功能：

#### 浏览器管理
- `_ensure_browser()` - 浏览器启动逻辑
- `_get_launch_args()` - 浏览器启动参数（支持反检测）
- `close()` - 关闭浏览器

#### 反爬虫策略
- `_setup_anti_detection()` - 设置反爬虫策略（统一入口）
- `_set_anti_detection_headers()` - 设置 HTTP Headers
- `_inject_anti_detection_scripts()` - 注入 JavaScript 脚本
- `_get_anti_detection_script()` - 获取反检测脚本内容

#### Cookies 持久化
- `_get_domain_from_url()` - 从 URL 提取域名
- `_get_cookies_file_path()` - 获取 cookies 文件路径
- `_load_cookies()` - 加载 cookies
- `_save_cookies()` - 保存 cookies

#### 人类行为模拟
- `_simulate_human_mouse_movement()` - 鼠标轨迹模拟（贝塞尔曲线）
- `_simulate_human_typing()` - 键盘输入模拟

### 2. 重构 PlaywrightBrowserService

**文件**: `infrastructure/adapters/playwright_service.py`

- 继承 `BaseBrowserService`
- 实现 `_get_page()` 方法（每次创建新页面）
- 支持可选的反检测和 cookies 持久化功能
- 默认不启用反检测（通用爬虫场景）

### 3. 重构 XiaohongshuBrowserService

**文件**: `infrastructure/adapters/xiaohongshu_service.py`

- 继承 `BaseBrowserService`
- 删除重复代码（约 400+ 行）
- 实现 `_get_page()` 方法（单例模式，复用页面）
- 默认启用反检测和 cookies 持久化
- 保留小红书特定的业务逻辑

## 代码复用率提升

### 重构前
- `XiaohongshuBrowserService`: ~960 行
- `PlaywrightBrowserService`: ~95 行
- **总计**: ~1055 行
- **重复代码**: ~400 行

### 重构后
- `BaseBrowserService`: ~450 行（公共功能）
- `XiaohongshuBrowserService`: ~560 行（业务逻辑）
- `PlaywrightBrowserService`: ~106 行（通用爬虫）
- **总计**: ~1116 行
- **重复代码**: 0 行

### 复用率提升
- **代码复用**: 公共功能集中管理，易于维护
- **功能扩展**: 新增浏览器服务只需继承基类
- **配置灵活**: 支持按需启用/禁用功能

## 架构优势

### 1. 单一职责原则
- **BaseBrowserService**: 负责浏览器基础功能和公共策略
- **PlaywrightBrowserService**: 负责通用爬虫场景
- **XiaohongshuBrowserService**: 负责小红书特定业务逻辑

### 2. 开闭原则
- 对扩展开放：可以轻松创建新的浏览器服务（如 `WeiboBrowserService`）
- 对修改封闭：公共功能修改只需在基类中进行

### 3. 依赖倒置原则
- 具体服务类依赖抽象基类
- 基类定义公共接口和默认实现

## 使用示例

### 通用爬虫（不启用反检测）

```python
from infrastructure.adapters.playwright_service import PlaywrightBrowserService

service = PlaywrightBrowserService(
    headless=False,
    enable_anti_detection=False,  # 不启用反检测
    enable_cookies_persistence=False  # 不启用 cookies 持久化
)
```

### 通用爬虫（启用反检测）

```python
service = PlaywrightBrowserService(
    headless=False,
    enable_anti_detection=True,  # 启用反检测
    enable_cookies_persistence=True  # 启用 cookies 持久化
)
```

### 小红书爬虫（默认启用所有功能）

```python
from infrastructure.adapters.xiaohongshu_service import XiaohongshuBrowserService

service = XiaohongshuBrowserService(
    headless=False,
    # enable_anti_detection=True,  # 默认启用
    # enable_cookies_persistence=True  # 默认启用
)
```

### 创建新的浏览器服务

```python
from infrastructure.adapters.base_browser_service import BaseBrowserService
from playwright.async_api import Page

class WeiboBrowserService(BaseBrowserService):
    """微博浏览器服务"""
    
    async def _get_page(self) -> Page:
        """获取页面实例"""
        if self._page is None:
            browser = await self._ensure_browser()
            self._page = await browser.new_page()
            await self._page.set_viewport_size({"width": 1920, "height": 1080})
            
            # 使用基类的反检测功能
            if self._enable_anti_detection:
                await self._setup_anti_detection(self._page)
        
        return self._page
    
    # 实现微博特定的业务逻辑
    async def login(self):
        # ...
        pass
```

## 功能配置

### BaseBrowserService 初始化参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `browser_type` | `Optional[str]` | `settings.playwright_browser` | 浏览器类型 |
| `headless` | `Optional[bool]` | `settings.playwright_headless` | 是否无头模式 |
| `timeout` | `Optional[int]` | `settings.playwright_timeout` | 超时时间（毫秒） |
| `cookies_dir` | `Optional[str]` | `"cookies"` | Cookies 存储目录 |
| `enable_anti_detection` | `bool` | `True` | 是否启用反检测 |
| `enable_cookies_persistence` | `bool` | `True` | 是否启用 Cookies 持久化 |

### 各服务默认配置

| 服务 | `enable_anti_detection` | `enable_cookies_persistence` |
|------|------------------------|------------------------------|
| `BaseBrowserService` | `True` | `True` |
| `PlaywrightBrowserService` | `False` | `False` |
| `XiaohongshuBrowserService` | `True` | `True` |

## 迁移指南

### 现有代码兼容性

所有现有代码无需修改，因为：
1. 接口保持不变（`IBrowserService`）
2. 方法签名保持一致
3. 默认行为保持一致

### 新功能使用

如果需要使用新的配置选项：

```python
# 旧代码（仍然有效）
service = XiaohongshuBrowserService(headless=False)

# 新代码（可以使用新配置）
service = XiaohongshuBrowserService(
    headless=False,
    enable_anti_detection=True,
    enable_cookies_persistence=True
)
```

## 测试建议

1. **功能测试**: 确保所有现有功能正常工作
2. **兼容性测试**: 验证现有代码无需修改
3. **扩展测试**: 测试新创建的浏览器服务

## 后续优化方向

1. **配置管理**: 将反检测策略配置化
2. **插件系统**: 支持自定义反检测插件
3. **性能优化**: 优化 cookies 加载和保存性能
4. **错误处理**: 增强错误处理和重试机制

