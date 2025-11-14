"""小红书浏览器服务适配器"""

import asyncio
import random
from typing import Dict, Any, Optional, List
from playwright.async_api import Page, Browser, Locator, Playwright
from loguru import logger

from domain.services import IBrowserService
from domain.value_objects import URL, SearchKeyword
from infrastructure.config import settings


class XiaohongshuBrowserService(IBrowserService):
    """小红书浏览器服务实现"""

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
        self._page: Optional[Page] = None

    async def _ensure_browser(self) -> Browser:
        """确保浏览器已启动"""
        if self._browser is None:
            from playwright.async_api import async_playwright

            if self._playwright is None:
                self._playwright = await async_playwright().start()

            browser_class = getattr(self._playwright, self._browser_type)
            self._browser = await browser_class.launch(
                headless=self._headless, args=["--disable-blink-features=AutomationControlled"]
            )
            logger.info(f"Browser {self._browser_type} launched")

        return self._browser

    async def _get_page(self) -> Page:
        """获取页面实例"""
        if self._page is None:
            browser = await self._ensure_browser()
            self._page = await browser.new_page()
            # 设置视口
            await self._page.set_viewport_size({"width": 1920, "height": 1080})
            # 设置 User-Agent
            await self._page.set_extra_http_headers(
                {
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                }
            )

        return self._page

    async def check_login_status(self, url: URL) -> bool:
        """检查是否需要登录

        Returns:
            True: 已登录, False: 需要登录
        """
        page = await self._get_page()

        logger.info(f"Checking login status at {url.value}")
        await page.goto(url.value, wait_until="networkidle")

        # 等待页面完整加载
        await asyncio.sleep(2)

        # 检查登录状态
        html = await page.content()

        if 'class="login-container"' in html or "login-container" in html:
            logger.info("Login required")
            return False
        else:
            logger.info("Already logged in")
            return True

    async def wait_for_login(self, timeout: int = 300) -> None:
        """等待用户登录（最多等待timeout秒）"""
        page = await self._get_page()

        logger.info("Waiting for manual login...")
        start_time = asyncio.get_event_loop().time()

        while True:
            html = await page.content()

            # 检查是否已登录（登录容器消失）
            if 'class="login-container"' not in html and "login-container" not in html:
                logger.info("Login detected!")
                return

            # 检查超时
            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed > timeout:
                logger.warning(f"Login timeout after {timeout}s")
                return

            # 等待一段时间后再次检查
            await asyncio.sleep(2)

    async def search(self, keyword: SearchKeyword) -> None:
        """搜索关键词"""
        page = await self._get_page()

        logger.info(f"Searching for: {keyword.value}")

        # 查找搜索框并输入
        search_selectors = [
            'input[placeholder*="搜索"]',
            'input[type="search"]',
            ".search-input input",
            "input.search-input",
        ]

        search_input = None
        for selector in search_selectors:
            try:
                search_input = await page.wait_for_selector(selector, timeout=5000)
                if search_input:
                    break
            except Exception:
                continue

        if not search_input:
            raise Exception("Could not find search input")

        # 清空并输入搜索词
        await search_input.click()
        await search_input.fill(keyword.value)
        await asyncio.sleep(0.5)

        # 按回车或点击搜索按钮
        await search_input.press("Enter")
        await asyncio.sleep(2)

        logger.info(f"Search completed for: {keyword.value}")

    async def browse_search_results(self, max_scrolls: int = 5) -> None:
        """浏览搜索结果并滚动（兼容旧接口）"""
        logger.info("Browsing search results")

        for i in range(max_scrolls):
            await self.scroll_search_results()
            wait_time = random.uniform(0.5, 3)
            await asyncio.sleep(wait_time)

    async def scroll_search_results(self) -> None:
        """搜索结果页下拉0.5~1.5倍视窗高度
        注意：翻页后会重写 #exploreFeeds 中的结果
        """
        page = await self._get_page()

        # 随机滚动距离（0.5~1.5倍视窗高度）
        scroll_distance = random.uniform(0.5, 1.5) * 1080  # 视窗高度

        # 记录滚动前的位置
        scroll_before = await page.evaluate("window.scrollY")

        await page.evaluate(f"window.scrollBy(0, {scroll_distance})")

        # 等待页面加载新内容（翻页可能需要时间）
        await asyncio.sleep(1)

        # 检查是否翻页（#exploreFeeds 内容可能被重写）
        scroll_after = await page.evaluate("window.scrollY")

        logger.info(
            f"Scrolled search results by {scroll_distance:.0f}px (from {scroll_before:.0f} to {scroll_after:.0f})"
        )

        # 如果滚动距离很大，可能是翻页，等待更长时间让内容加载
        if scroll_distance > 800:
            await asyncio.sleep(1)

    async def get_visible_links(self) -> List[tuple[Locator, str]]:
        """获取当前视窗中可见的链接及其唯一标识
        搜索结果在 id="exploreFeeds" 中

        Returns:
            List of (link, link_id) tuples
        """
        page = await self._get_page()

        # 首先检查是否存在 #exploreFeeds 容器
        explore_feeds = await page.query_selector("#exploreFeeds")
        if not explore_feeds:
            logger.warning("#exploreFeeds container not found, trying alternative selectors")
            # 如果找不到，使用备用选择器
            return await self._get_visible_links_fallback()

        # 在 #exploreFeeds 容器中查找链接
        link_selectors = [
            'a[href*="/explore/"]',
            'a[href*="/discovery/"]',
            ".note-item a",
            ".feed-item a",
            "a.note-item",
            'a[href*="/note/"]',  # 添加笔记链接选择器
        ]

        visible_links = []
        for selector in link_selectors:
            try:
                # 在 #exploreFeeds 容器内查找
                links = await explore_feeds.query_selector_all(selector)
                for link in links:
                    # 检查是否在视窗中
                    box = await link.bounding_box()
                    if box and box["y"] >= 0 and box["y"] <= 1080:
                        # 获取链接的唯一标识（href）
                        try:
                            href = await link.get_attribute("href")
                            link_id = href or str(id(link))
                        except Exception:
                            link_id = str(id(link))
                        visible_links.append((link, link_id))
            except Exception as e:
                logger.debug(f"Error finding links with selector {selector}: {e}")
                continue

        logger.info(f"Found {len(visible_links)} visible links in #exploreFeeds")
        return visible_links

    async def _get_visible_links_fallback(self) -> List[tuple[Locator, str]]:
        """备用方法：如果找不到 #exploreFeeds，使用全局搜索"""
        page = await self._get_page()

        link_selectors = [
            'a[href*="/explore/"]',
            'a[href*="/discovery/"]',
            ".note-item a",
            ".feed-item a",
            "a.note-item",
            'a[href*="/note/"]',
        ]

        visible_links = []
        for selector in link_selectors:
            try:
                links = await page.query_selector_all(selector)
                for link in links:
                    # 检查是否在视窗中
                    box = await link.bounding_box()
                    if box and box["y"] >= 0 and box["y"] <= 1080:
                        # 获取链接的唯一标识（href）
                        try:
                            href = await link.get_attribute("href")
                            link_id = href or str(id(link))
                        except Exception:
                            link_id = str(id(link))
                        visible_links.append((link, link_id))
            except Exception:
                continue

        return visible_links

    async def click_random_visible_link_not_opened(
        self, opened_links: set
    ) -> tuple[bool, Optional[str]]:
        """随机点击当前视窗中未打开过的链接

        Args:
            opened_links: 已打开的链接ID集合

        Returns:
            (是否成功点击, 链接ID)
        """
        visible_links_with_ids = await self.get_visible_links()

        if not visible_links_with_ids:
            logger.warning("No visible links found")
            return False, None

        # 过滤掉已打开的链接
        available_links = [
            (link, link_id)
            for link, link_id in visible_links_with_ids
            if link_id not in opened_links
        ]

        if not available_links:
            logger.info("All visible links have been opened")
            return False, None

        # 随机选择一个未打开的链接
        link, link_id = random.choice(available_links)

        try:
            await link.click(timeout=5000)
            logger.info(f"Clicked on a new link: {link_id[:50]}")
            await asyncio.sleep(1)  # 等待页面加载
            return True, link_id
        except Exception as e:
            logger.error(f"Failed to click link: {e}")
            return False, None

    async def click_random_visible_link(self) -> bool:
        """随机点击当前视窗中的一个链接（兼容旧接口）

        Returns:
            True: 成功点击, False: 没有找到链接
        """
        clicked, _ = await self.click_random_visible_link_not_opened(set())
        return clicked

    async def wait_for_content_page(self, timeout: int = 10000) -> bool:
        """等待内容页面加载（检查是否有 id="noteContainer"）

        Returns:
            True: 内容页面已加载, False: 超时
        """
        page = await self._get_page()

        try:
            await page.wait_for_selector("#noteContainer", timeout=timeout)
            logger.info("Content page loaded")
            return True
        except Exception:
            logger.warning("Content page not found")
            return False

    async def browse_comments(self, max_scrolls: int = 10) -> None:
        """浏览评论并滚动（兼容旧接口）"""
        logger.info("Browsing comments")

        for i in range(max_scrolls):
            await self.scroll_comments()
            wait_time = random.uniform(0.5, 5)
            await asyncio.sleep(wait_time)

    async def scroll_comments(self) -> None:
        """下拉评论"""
        page = await self._get_page()

        # 在评论容器内滚动
        scroll_distance = random.uniform(200, 500)
        await page.evaluate(f"""
            const container = document.querySelector('.comments-container, [class*="comment"], .comment-list');
            if (container) {{
                container.scrollTop += {scroll_distance};
            }}
        """)
        logger.info(f"Scrolled comments by {scroll_distance:.0f}px")

    async def check_comments_overflow(self) -> bool:
        """检查评论是否超出当前评论框高度

        Returns:
            True: 评论超出高度，可以继续滚动, False: 评论未超出或找不到评论容器
        """
        page = await self._get_page()

        # 查找评论容器
        comment_selectors = [
            ".comments-container",
            '[class*="comment"]',
            ".comment-list",
        ]

        comment_container = None
        for selector in comment_selectors:
            try:
                comment_container = await page.query_selector(selector)
                if comment_container:
                    break
            except Exception:
                continue

        if not comment_container:
            logger.debug("Comment container not found")
            return False

        # 检查评论容器是否可以滚动
        try:
            scroll_info = await page.evaluate("""
                () => {
                    const container = document.querySelector('.comments-container, [class*="comment"], .comment-list');
                    if (!container) return {scrollable: false};
                    return {
                        scrollable: container.scrollHeight > container.clientHeight,
                        scrollTop: container.scrollTop,
                        scrollHeight: container.scrollHeight,
                        clientHeight: container.clientHeight
                    };
                }
            """)

            is_overflow = scroll_info.get("scrollable", False)
            if is_overflow:
                logger.info(
                    f"Comments overflow detected: scrollHeight={scroll_info.get('scrollHeight')}, clientHeight={scroll_info.get('clientHeight')}"
                )
            return is_overflow
        except Exception as e:
            logger.warning(f"Failed to check comments overflow: {e}")
            return False

    async def close_content_page(self) -> None:
        """关闭当前内容页面（点击 noteContainer 以外的部分）"""
        page = await self._get_page()

        logger.info("Closing content page")

        # 点击页面左上角（noteContainer 以外）
        await page.click("body", position={"x": 50, "y": 50})
        await asyncio.sleep(1)

    async def crawl(self, url: URL, options: Optional[Dict[str, Any]] = None) -> str:
        """爬取指定 URL 的内容（实现接口要求）"""
        page = await self._get_page()
        await page.goto(url.value, wait_until="networkidle")
        await asyncio.sleep(2)
        return await page.content()

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
