"""Playwright 浏览器服务适配器"""

from typing import Dict, Any, Optional
from playwright.async_api import Page
from loguru import logger

from domain.value_objects import URL
from infrastructure.adapters.base_browser_service import BaseBrowserService


class PlaywrightBrowserService(BaseBrowserService):
    """Playwright 浏览器服务实现（通用爬虫）"""

    def __init__(
        self,
        browser_type: Optional[str] = None,
        headless: Optional[bool] = None,
        timeout: Optional[int] = None,
        cookies_dir: Optional[str] = None,
        enable_anti_detection: bool = False,  # 默认不启用反检测（通用爬虫）
        enable_cookies_persistence: bool = False,  # 默认不启用 cookies 持久化
    ):
        """初始化 Playwright 浏览器服务

        Args:
            browser_type: 浏览器类型
            headless: 是否无头模式
            timeout: 超时时间
            cookies_dir: Cookies 存储目录
            enable_anti_detection: 是否启用反检测（默认 False）
            enable_cookies_persistence: 是否启用 Cookies 持久化（默认 False）
        """
        super().__init__(
            browser_type=browser_type,
            headless=headless,
            timeout=timeout,
            cookies_dir=cookies_dir,
            enable_anti_detection=enable_anti_detection,
            enable_cookies_persistence=enable_cookies_persistence,
        )

    async def _get_page(self) -> Page:
        """获取页面实例（每次创建新页面）"""
        browser = await self._ensure_browser()
        page = await browser.new_page()

        # 设置超时
        page.set_default_timeout(self._timeout)

        # 如果启用反检测，设置反爬虫策略
        if self._enable_anti_detection:
            await self._setup_anti_detection(page)

        return page

    async def crawl(
        self,
        url: URL,
        options: Optional[Dict[str, Any]] = None,
    ) -> str:
        """爬取指定 URL 的内容"""
        options = options or {}
        page = await self._get_page()

        try:
            # 设置视口大小（可选）
            if "viewport" in options:
                await page.set_viewport_size(options["viewport"])
            else:
                await page.set_viewport_size({"width": 1920, "height": 1080})

            # 设置 User-Agent（可选，如果未启用反检测）
            if not self._enable_anti_detection and "user_agent" in options:
                await page.set_extra_http_headers({"User-Agent": options["user_agent"]})

            # 加载 cookies（如果启用）
            if self._enable_cookies_persistence:
                domain = self._get_domain_from_url(url.value)
                await self._load_cookies(page, domain)

            # 导航到 URL
            logger.info(f"Navigating to {url.value}")
            await page.goto(url.value, wait_until=options.get("wait_until", "load"))

            # 等待特定元素（可选）
            if "wait_for_selector" in options:
                await page.wait_for_selector(options["wait_for_selector"])

            # 执行自定义脚本（可选）
            if "execute_script" in options:
                await page.evaluate(options["execute_script"])

            # 保存 cookies（如果启用）
            if self._enable_cookies_persistence:
                domain = self._get_domain_from_url(url.value)
                await self._save_cookies(page, domain)

            # 获取页面内容
            content = await page.content()
            logger.info(f"Successfully crawled {url.value}")

            return content

        finally:
            await page.close()

