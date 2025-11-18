# 反爬虫策略说明文档

本文档说明项目中所有反爬虫策略的实现位置和功能。

## 反爬虫策略位置总览

所有反爬虫策略都实现在 `infrastructure/adapters/xiaohongshu_service.py` 文件中。

---

## 1. 浏览器启动参数（去除自动化特征）

**位置**: `infrastructure/adapters/xiaohongshu_service.py`  
**行号**: 第 41-54 行  
**方法**: `_ensure_browser()`

```python
# 反爬虫策略：去除自动化特征
launch_args = [
    "--disable-blink-features=AutomationControlled",  # 禁用自动化控制特征
    "--disable-dev-shm-usage",
    "--no-sandbox",
    "--disable-setuid-sandbox",
    "--disable-web-security",
    "--disable-features=IsolateOrigins,site-per-process",
    "--disable-site-isolation-trials",
    "--disable-infobars",
    "--disable-notifications",
    "--disable-popup-blocking",
    "--start-maximized",
]
```

**功能**: 通过浏览器启动参数去除自动化特征，使浏览器看起来更像真实用户使用的浏览器。

---

## 2. User-Agent 设置（百度蜘蛛）

**位置**: `infrastructure/adapters/xiaohongshu_service.py`  
**行号**: 第 75-92 行  
**方法**: `_get_page()`

```python
# 反爬虫策略：伪装为百度蜘蛛
# 1. 设置百度蜘蛛 User-Agent
baidu_spider_ua = "Mozilla/5.0 (compatible; Baiduspider/2.0; +http://www.baidu.com/search/spider.html)"
await self._page.set_extra_http_headers({
    "User-Agent": baidu_spider_ua,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    # ... 其他 HTTP 头
})
```

**功能**: 将 User-Agent 设置为百度蜘蛛，伪装成搜索引擎爬虫。

---

## 3. JavaScript 注入（去除 webdriver 特征 + 指纹伪装）

**位置**: `infrastructure/adapters/xiaohongshu_service.py`  
**行号**: 第 94-240 行  
**方法**: `_get_page()`

### 3.1 去除自动化特征（第 96-159 行）

- **隐藏 webdriver 属性**: 将 `navigator.webdriver` 设置为 `undefined`
- **伪装 plugins**: 模拟真实浏览器插件列表
- **伪装 languages**: 设置语言为 `['zh-CN', 'zh', 'en-US', 'en']`
- **伪装 platform**: 设置为 `'Win32'`
- **伪装硬件信息**: 
  - `hardwareConcurrency`: CPU 核心数（8）
  - `deviceMemory`: 内存大小（8GB）
- **覆盖 permissions**: 处理权限查询
- **伪装 chrome 对象**: 添加 `window.chrome` 对象
- **覆盖 Notification**: 隐藏通知对象
- **伪装 vendor**: 设置为 `'Google Inc.'`

### 3.2 Canvas 指纹伪装（第 161-177 行）

```javascript
// 添加微小的随机噪声，使 Canvas 指纹更真实
const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
HTMLCanvasElement.prototype.toDataURL = function(type) {
    // 添加极小的随机噪声（0-1像素值）
    // ...
}
```

**功能**: 在 Canvas 渲染时添加微小随机噪声，使 Canvas 指纹更真实，避免被识别为自动化工具。

### 3.3 WebGL 指纹伪装（第 179-189 行）

```javascript
// 伪装 WebGL 渲染器信息
WebGLRenderingContext.prototype.getParameter = function(parameter) {
    if (parameter === 37445) { // UNMASKED_VENDOR_WEBGL
        return 'Intel Inc.';
    }
    if (parameter === 37446) { // UNMASKED_RENDERER_WEBGL
        return 'Intel Iris OpenGL Engine';
    }
    // ...
}
```

**功能**: 伪装 WebGL 渲染器信息，使指纹更真实。

### 3.4 AudioContext 指纹伪装（第 191-204 行）

```javascript
// 在音频上下文创建时添加随机延迟
AudioContext.prototype.createOscillator = function() {
    // 添加微小的随机延迟，使音频指纹更真实
    // ...
}
```

**功能**: 在音频上下文创建时添加随机延迟，使音频指纹更真实。

### 3.5 屏幕属性伪装（第 206-224 行）

```javascript
Object.defineProperty(screen, 'availWidth', { get: () => 1920 });
Object.defineProperty(screen, 'availHeight', { get: () => 1080 });
Object.defineProperty(screen, 'width', { get: () => 1920 });
Object.defineProperty(screen, 'height', { get: () => 1080 });
Object.defineProperty(screen, 'colorDepth', { get: () => 24 });
Object.defineProperty(screen, 'pixelDepth', { get: () => 24 });
```

**功能**: 伪装屏幕属性，使其与视口大小一致。

### 3.6 时区伪装（第 226-229 行）

```javascript
Date.prototype.getTimezoneOffset = function() {
    return -480; // UTC+8 (中国时区)
};
```

**功能**: 设置时区为中国时区（UTC+8）。

### 3.7 防止检测自动化工具（第 231-239 行）

```javascript
// 覆盖 toString 方法，防止检测
Function.prototype.toString = function() {
    if (this === navigator.webdriver) {
        return 'function webdriver() { [native code] }';
    }
    return originalToString.apply(this, arguments);
};
```

**功能**: 覆盖 `toString` 方法，防止通过函数字符串检测自动化工具。

---

## 4. 鼠标轨迹模拟

**位置**: `infrastructure/adapters/xiaohongshu_service.py`  
**行号**: 第 31-71 行  
**方法**: `_simulate_human_mouse_movement()`

```python
async def _simulate_human_mouse_movement(
    self, page: Page, start_x: float, start_y: float, end_x: float, end_y: float
) -> None:
    """模拟人类鼠标移动轨迹（贝塞尔曲线）"""
    # 使用贝塞尔曲线生成自然的鼠标轨迹
    # 添加随机抖动，使轨迹更自然
    # ...
```

**功能**: 
- 使用**三次贝塞尔曲线**生成自然的鼠标移动轨迹
- 添加随机抖动，使轨迹更真实
- 每步之间有随机延迟（0.001-0.003秒）

**使用位置**:
- **搜索输入**（第 407-409 行）: 模拟鼠标移动到搜索框
- **点击链接**（第 575 行）: 模拟鼠标移动到链接位置

---

## 5. 键盘输入模拟

**位置**: `infrastructure/adapters/xiaohongshu_service.py`  
**行号**: 第 73-90 行  
**方法**: `_simulate_human_typing()`

```python
async def _simulate_human_typing(
    self, element: Locator, text: str, typing_speed: float = 0.1
) -> None:
    """模拟人类打字（随机延迟）"""
    # 每个字符之间有随机延迟
    # 偶尔停顿（模拟思考）
    # ...
```

**功能**:
- 每个字符输入时有随机延迟（0.5-1.5倍基础速度）
- 10% 概率随机停顿（0.2-0.5秒），模拟思考

**使用位置**:
- **搜索输入**（第 419 行）: 模拟人类打字输入搜索关键词

---

## 6. 随机延迟和等待

**位置**: 整个文件中的多个位置

**功能**: 在关键操作之间添加随机延迟，模拟人类行为：
- 搜索后等待 1-3 秒（`application/xiaohongshu_use_cases.py` 第 95-97 行）
- 点击链接后等待 0.8-1.5 秒（第 580 行）
- 鼠标移动后等待 0.1-0.3 秒（第 576 行）
- 内容浏览时长至少 5-20 秒（`application/xiaohongshu_use_cases.py` 第 154 行）

---

## 总结

### 反爬虫策略分类

1. **浏览器层面**:
   - 启动参数去除自动化特征
   - User-Agent 伪装（百度蜘蛛）

2. **JavaScript 层面**:
   - 去除 webdriver 特征
   - 指纹伪装（Canvas、WebGL、AudioContext、屏幕、时区）
   - 防止自动化工具检测

3. **行为层面**:
   - 鼠标轨迹模拟（贝塞尔曲线）
   - 键盘输入模拟（随机延迟）
   - 随机等待和延迟

### 关键文件位置

- **主要实现**: `infrastructure/adapters/xiaohongshu_service.py`
  - 浏览器启动: 第 31-64 行
  - 页面初始化: 第 66-245 行
  - 鼠标模拟: 第 31-71 行
  - 键盘模拟: 第 73-90 行
  - 点击链接: 第 532-583 行
  - 搜索输入: 第 403-424 行

- **用例层**: `application/xiaohongshu_use_cases.py`
  - 内容浏览时长控制: 第 152-165 行

---

## 注意事项

1. **User-Agent 设置**: 当前设置为百度蜘蛛，某些网站可能会限制搜索引擎爬虫的访问。如需改为普通浏览器 User-Agent，请修改第 77 行。

2. **指纹伪装**: Canvas、WebGL、AudioContext 等指纹伪装可能会影响某些依赖这些 API 的功能，请根据实际情况调整。

3. **鼠标轨迹**: 贝塞尔曲线模拟会增加操作时间，但能有效降低被检测的风险。

4. **性能影响**: 所有反爬虫策略都会增加操作时间，这是为了模拟真实用户行为而必须的权衡。

