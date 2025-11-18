"""基础浏览器服务类，包含公共功能"""

import asyncio
import json
import random
from pathlib import Path
from typing import Dict, Any, Optional
from urllib.parse import urlparse
from abc import ABC, abstractmethod
from playwright.async_api import Page, Browser, Locator, Playwright
from loguru import logger

from domain.services import IBrowserService
from infrastructure.config import settings


class BaseBrowserService(IBrowserService, ABC):
    """基础浏览器服务，提供公共功能"""

    def __init__(
        self,
        browser_type: Optional[str] = None,
        headless: Optional[bool] = None,
        timeout: Optional[int] = None,
        cookies_dir: Optional[str] = None,
        enable_anti_detection: bool = True,
        enable_cookies_persistence: bool = True,
    ):
        """初始化基础浏览器服务

        Args:
            browser_type: 浏览器类型（chromium, firefox, webkit）
            headless: 是否无头模式
            timeout: 超时时间（毫秒）
            cookies_dir: Cookies 存储目录
            enable_anti_detection: 是否启用反检测功能
            enable_cookies_persistence: 是否启用 Cookies 持久化
        """
        self._browser_type = browser_type or settings.playwright_browser
        self._headless = headless if headless is not None else settings.playwright_headless
        self._timeout = timeout or settings.playwright_timeout
        self._enable_anti_detection = enable_anti_detection
        self._enable_cookies_persistence = enable_cookies_persistence

        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
        self._page: Optional[Page] = None

        # Cookies 持久化配置
        if self._enable_cookies_persistence:
            self._cookies_dir = Path(cookies_dir or "cookies")
            self._cookies_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Cookies directory: {self._cookies_dir.absolute()}")
        else:
            self._cookies_dir = None

    # ========== 浏览器管理 ==========

    async def _ensure_browser(self) -> Browser:
        """确保浏览器已启动"""
        if self._browser is None:
            from playwright.async_api import async_playwright

            if self._playwright is None:
                self._playwright = await async_playwright().start()

            browser_class = getattr(self._playwright, self._browser_type)

            # 浏览器启动参数
            launch_args = self._get_launch_args()

            self._browser = await browser_class.launch(
                headless=self._headless,
                args=launch_args,
                channel=None,  # 使用系统安装的 Chrome（如果可用）
            )
            logger.info(f"Browser {self._browser_type} launched")

        return self._browser

    def _get_launch_args(self) -> list[str]:
        """获取浏览器启动参数

        Returns:
            启动参数列表
        """
        if self._enable_anti_detection:
            return [
                "--disable-blink-features=AutomationControlled",
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
        return []

    @abstractmethod
    async def _get_page(self) -> Page:
        """获取页面实例（子类实现）"""
        pass

    async def close(self) -> None:
        """关闭浏览器"""
        if self._page:
            await self._page.close()
            self._page = None

        if self._browser:
            await self._browser.close()
            self._browser = None
            logger.info("Browser closed")

        if self._playwright:
            await self._playwright.stop()
            self._playwright = None
            logger.info("Playwright stopped")

    # ========== 反爬虫策略 ==========

    async def _setup_anti_detection(self, page: Page) -> None:
        """设置反爬虫策略

        Args:
            page: Playwright 页面对象
        """
        if not self._enable_anti_detection:
            return

        # 1. 设置 HTTP Headers
        await self._set_anti_detection_headers(page)

        # 2. 注入 JavaScript 脚本
        await self._inject_anti_detection_scripts(page)

        # 3. 设置额外的上下文选项
        context = page.context
        await context.set_extra_http_headers({"Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8"})

    async def _set_anti_detection_headers(self, page: Page) -> None:
        """设置反检测 HTTP Headers

        Args:
            page: Playwright 页面对象
        """
        common_ua = (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"
        )

        await page.set_extra_http_headers(
            {
                "User-Agent": common_ua,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                "Accept-Encoding": "gzip, deflate, br, zstd",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-User": "?1",
                "Cache-Control": "max-age=0",
            }
        )

    async def _inject_anti_detection_scripts(self, page: Page) -> None:
        """注入反检测 JavaScript 脚本

        Args:
            page: Playwright 页面对象
        """
        await page.add_init_script(self._get_anti_detection_script())

    def _get_anti_detection_script(self) -> str:
        """获取反检测 JavaScript 脚本

        Returns:
            JavaScript 代码字符串
        """
        return """
            // ========== 反爬虫策略：去除自动化特征 ==========
            
            // 1. 隐藏 webdriver 属性
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            
            // 2. 伪装 plugins（模拟真实浏览器插件）
            Object.defineProperty(navigator, 'plugins', {
                get: () => {
                    const plugins = [
                        { name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer', description: 'Portable Document Format' },
                        { name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai', description: '' },
                        { name: 'Native Client', filename: 'internal-nacl-plugin', description: '' }
                    ];
                    return plugins;
                }
            });
            
            // 3. 伪装 languages
            Object.defineProperty(navigator, 'languages', {
                get: () => ['zh-CN', 'zh', 'en-US', 'en']
            });
            
            // 4. 伪装 platform
            Object.defineProperty(navigator, 'platform', {
                get: () => 'Win32'
            });
            
            // 5. 伪装 hardwareConcurrency（CPU核心数）
            Object.defineProperty(navigator, 'hardwareConcurrency', {
                get: () => 8
            });
            
            // 6. 伪装 deviceMemory（内存大小，单位GB）
            Object.defineProperty(navigator, 'deviceMemory', {
                get: () => 8
            });
            
            // 7. 覆盖 permissions
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
            
            // 8. 伪装 chrome 对象
            window.chrome = {
                runtime: {},
                loadTimes: function() {},
                csi: function() {},
                app: {}
            };
            
            // 9. 覆盖 Notification
            Object.defineProperty(window, 'Notification', {
                get: () => undefined
            });
            
            // 10. 伪装 vendor
            Object.defineProperty(navigator, 'vendor', {
                get: () => 'Google Inc.'
            });
            
            // ========== 指纹伪装：Canvas 指纹 ==========
            const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
            HTMLCanvasElement.prototype.toDataURL = function(type) {
                if (type === 'image/png' || type === undefined) {
                    // 添加微小的随机噪声，使 Canvas 指纹更真实
                    const context = this.getContext('2d');
                    if (context) {
                        const imageData = context.getImageData(0, 0, this.width, this.height);
                        for (let i = 0; i < imageData.data.length; i += 4) {
                            // 添加极小的随机噪声（0-1像素值）
                            imageData.data[i] += Math.random() * 0.01;
                        }
                        context.putImageData(imageData, 0, 0);
                    }
                }
                return originalToDataURL.apply(this, arguments);
            };
            
            // ========== 指纹伪装：WebGL 指纹 ==========
            const getParameter = WebGLRenderingContext.prototype.getParameter;
            WebGLRenderingContext.prototype.getParameter = function(parameter) {
                if (parameter === 37445) { // UNMASKED_VENDOR_WEBGL
                    return 'Intel Inc.';
                }
                if (parameter === 37446) { // UNMASKED_RENDERER_WEBGL
                    return 'Intel Iris OpenGL Engine';
                }
                return getParameter.apply(this, arguments);
            };
            
            // ========== 指纹伪装：AudioContext 指纹 ==========
            const AudioContext = window.AudioContext || window.webkitAudioContext;
            if (AudioContext) {
                const originalCreateOscillator = AudioContext.prototype.createOscillator;
                AudioContext.prototype.createOscillator = function() {
                    const oscillator = originalCreateOscillator.apply(this, arguments);
                    const originalStart = oscillator.start;
                    oscillator.start = function() {
                        // 添加微小的随机延迟，使音频指纹更真实
                        return originalStart.apply(this, arguments);
                    };
                    return oscillator;
                };
            }
            
            // ========== 指纹伪装：屏幕属性 ==========
            Object.defineProperty(screen, 'availWidth', {
                get: () => 1920
            });
            Object.defineProperty(screen, 'availHeight', {
                get: () => 1080
            });
            Object.defineProperty(screen, 'width', {
                get: () => 1920
            });
            Object.defineProperty(screen, 'height', {
                get: () => 1080
            });
            Object.defineProperty(screen, 'colorDepth', {
                get: () => 24
            });
            Object.defineProperty(screen, 'pixelDepth', {
                get: () => 24
            });
            
            // ========== 指纹伪装：时区 ==========
            Date.prototype.getTimezoneOffset = function() {
                return -480; // UTC+8 (中国时区)
            };
            
            // ========== 防止检测自动化工具 ==========
            // 覆盖 toString 方法，防止检测
            const originalToString = Function.prototype.toString;
            Function.prototype.toString = function() {
                if (this === navigator.webdriver) {
                    return 'function webdriver() { [native code] }';
                }
                return originalToString.apply(this, arguments);
            };
        """

    # ========== Cookies 持久化 ==========

    def _get_domain_from_url(self, url: str) -> str:
        """从 URL 中提取域名

        Args:
            url: 完整的 URL

        Returns:
            域名（如：xiaohongshu.com）
        """
        parsed = urlparse(url)
        domain = parsed.netloc or parsed.path
        # 移除端口号
        if ":" in domain:
            domain = domain.split(":")[0]
        return domain

    def _get_cookies_file_path(self, domain: str) -> Path:
        """获取指定域名的 cookies 文件路径

        Args:
            domain: 域名

        Returns:
            cookies 文件路径
        """
        if not self._cookies_dir:
            raise ValueError("Cookies persistence is not enabled")
        # 将域名中的点替换为下划线，作为文件名
        safe_domain = domain.replace(".", "_")
        return self._cookies_dir / f"{safe_domain}.json"

    async def _load_cookies(self, page: Page, domain: str) -> None:
        """加载指定域名的 cookies

        Args:
            page: Playwright 页面对象
            domain: 域名
        """
        if not self._enable_cookies_persistence:
            return

        cookies_file = self._get_cookies_file_path(domain)

        if not cookies_file.exists():
            logger.debug(f"Cookies file not found for domain {domain}: {cookies_file}")
            return

        try:
            with open(cookies_file, "r", encoding="utf-8") as f:
                cookies = json.load(f)

            if cookies:
                # 确保 cookies 包含必要的字段
                for cookie in cookies:
                    if "domain" not in cookie:
                        cookie["domain"] = domain

                await page.context.add_cookies(cookies)
                logger.info(f"Loaded {len(cookies)} cookies for domain {domain}")
            else:
                logger.debug(f"No cookies to load for domain {domain}")
        except json.JSONDecodeError as e:
            logger.warning(f"Invalid JSON in cookies file {cookies_file}: {e}")
        except Exception as e:
            logger.error(f"Failed to load cookies for domain {domain}: {e}")

    async def _save_cookies(self, page: Page, domain: str) -> None:
        """保存指定域名的 cookies

        Args:
            page: Playwright 页面对象
            domain: 域名
        """
        if not self._enable_cookies_persistence:
            return

        try:
            # 获取当前页面的所有 cookies
            cookies = await page.context.cookies()

            # 过滤出属于当前域名的 cookies
            domain_cookies = [cookie for cookie in cookies if domain in cookie.get("domain", "")]

            if domain_cookies:
                cookies_file = self._get_cookies_file_path(domain)
                with open(cookies_file, "w", encoding="utf-8") as f:
                    json.dump(domain_cookies, f, indent=2, ensure_ascii=False)
                logger.debug(f"Saved {len(domain_cookies)} cookies for domain {domain}")
            else:
                logger.debug(f"No cookies to save for domain {domain}")
        except Exception as e:
            logger.error(f"Failed to save cookies for domain {domain}: {e}")

    # ========== 人类行为模拟 ==========

    async def _simulate_human_mouse_movement(
        self, page: Page, start_x: float, start_y: float, end_x: float, end_y: float
    ) -> None:
        """模拟人类鼠标移动轨迹（贝塞尔曲线）

        Args:
            page: Playwright 页面对象
            start_x: 起始 X 坐标
            start_y: 起始 Y 坐标
            end_x: 结束 X 坐标
            end_y: 结束 Y 坐标
        """
        # 使用贝塞尔曲线生成自然的鼠标轨迹
        steps = random.randint(20, 40)  # 移动步数
        control_point_1_x = start_x + (end_x - start_x) * random.uniform(0.2, 0.4)
        control_point_1_y = start_y + (end_y - start_y) * random.uniform(0.2, 0.4)
        control_point_2_x = start_x + (end_x - start_x) * random.uniform(0.6, 0.8)
        control_point_2_y = start_y + (end_y - start_y) * random.uniform(0.6, 0.8)

        for i in range(steps):
            t = i / steps
            # 三次贝塞尔曲线公式
            x = (
                (1 - t) ** 3 * start_x
                + 3 * (1 - t) ** 2 * t * control_point_1_x
                + 3 * (1 - t) * t**2 * control_point_2_x
                + t**3 * end_x
            )
            y = (
                (1 - t) ** 3 * start_y
                + 3 * (1 - t) ** 2 * t * control_point_1_y
                + 3 * (1 - t) * t**2 * control_point_2_y
                + t**3 * end_y
            )

            # 添加随机抖动，使轨迹更自然
            x += random.uniform(-2, 2)
            y += random.uniform(-2, 2)

            await page.mouse.move(x, y)
            await asyncio.sleep(random.uniform(0.001, 0.003))  # 每步之间的延迟

    async def _simulate_human_typing(
        self, element: Locator, text: str, typing_speed: float = 0.1
    ) -> None:
        """模拟人类打字（随机延迟）

        Args:
            element: 输入元素
            text: 要输入的文本
            typing_speed: 每个字符的打字速度（秒）
        """
        await element.click()
        await asyncio.sleep(random.uniform(0.1, 0.3))

        for char in text:
            await element.type(char, delay=random.uniform(typing_speed * 0.5, typing_speed * 1.5))
            # 偶尔停顿（模拟思考）
            if random.random() < 0.1:  # 10% 概率
                await asyncio.sleep(random.uniform(0.2, 0.5))

