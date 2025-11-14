"""Playwright 浏览器服务适配器"""

from typing import Dict, Any, Optional
from playwright.async_api import async_playwright, Browser, Page, Playwright
from loguru import logger

from domain.services import IBrowserService
from domain.value_objects import URL
from infrastructure.config import settings


class PlaywrightBrowserService(IBrowserService):
    """Playwright 浏览器服务实现"""
    
    def __init__(
        self,
        browser_type: Optional[str] = None,
        headless: Optional[bool] = None,
        timeout: Optional[int] = None,
    ):
        self._browser_type = browser_type or settings.playwright_browser
        self._headless = headless if headless is not None else settings.playwright_headless
        self._timeout = timeout or settings.playwright_timeout
        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
    
    async def _ensure_browser(self) -> Browser:
        """确保浏览器已启动"""
        if self._browser is None:
            if self._playwright is None:
                self._playwright = await async_playwright().start()
            
            browser_class = getattr(self._playwright, self._browser_type)
            self._browser = await browser_class.launch(headless=self._headless)
            logger.info(f"Browser {self._browser_type} launched")
        
        return self._browser
    
    async def crawl(
        self,
        url: URL,
        options: Optional[Dict[str, Any]] = None,
    ) -> str:
        """爬取指定 URL 的内容"""
        options = options or {}
        browser = await self._ensure_browser()
        
        page = await browser.new_page()
        
        try:
            # 设置超时
            page.set_default_timeout(self._timeout)
            
            # 设置视口大小（可选）
            if "viewport" in options:
                await page.set_viewport_size(options["viewport"])
            
            # 设置 User-Agent（可选）
            if "user_agent" in options:
                await page.set_extra_http_headers({"User-Agent": options["user_agent"]})
            
            # 导航到 URL
            logger.info(f"Navigating to {url.value}")
            await page.goto(url.value, wait_until=options.get("wait_until", "load"))
            
            # 等待特定元素（可选）
            if "wait_for_selector" in options:
                await page.wait_for_selector(options["wait_for_selector"])
            
            # 执行自定义脚本（可选）
            if "execute_script" in options:
                await page.evaluate(options["execute_script"])
            
            # 获取页面内容
            content = await page.content()
            logger.info(f"Successfully crawled {url.value}")
            
            return content
            
        finally:
            await page.close()
    
    async def close(self) -> None:
        """关闭浏览器"""
        if self._browser:
            await self._browser.close()
            self._browser = None
            logger.info("Browser closed")
        
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None
            logger.info("Playwright stopped")

