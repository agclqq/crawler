"""小红书浏览器服务适配器"""

import asyncio
import random
import time
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

            # 反爬虫策略：去除自动化特征
            launch_args = [
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

            self._browser = await browser_class.launch(
                headless=self._headless,
                args=launch_args,
                # 设置真实的浏览器选项
                channel=None,  # 使用系统安装的 Chrome（如果可用）
            )
            logger.info(f"Browser {self._browser_type} launched with anti-detection features")

        return self._browser

    async def _get_page(self) -> Page:
        """获取页面实例"""
        if self._page is None:
            browser = await self._ensure_browser()
            self._page = await browser.new_page()

            # 设置视口
            await self._page.set_viewport_size({"width": 1920, "height": 1080})

            # 反爬虫策略：伪装为自然人使用的浏览器
            # 1. 设置真实的 User-Agent
            await self._page.set_extra_http_headers(
                {
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                    "Accept-Encoding": "gzip, deflate, br",
                    "Connection": "keep-alive",
                    "Upgrade-Insecure-Requests": "1",
                    "Sec-Fetch-Dest": "document",
                    "Sec-Fetch-Mode": "navigate",
                    "Sec-Fetch-Site": "none",
                    "Sec-Fetch-User": "?1",
                    "Cache-Control": "max-age=0",
                }
            )

            # 2. 注入脚本去除 webdriver 特征
            await self._page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                
                // 覆盖 plugins
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5]
                });
                
                // 覆盖 languages
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['zh-CN', 'zh', 'en']
                });
                
                // 覆盖 permissions
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                        Promise.resolve({ state: Notification.permission }) :
                        originalQuery(parameters)
                );
                
                // 覆盖 chrome 对象
                window.chrome = {
                    runtime: {}
                };
                
                // 覆盖 Notification
                Object.defineProperty(window, 'Notification', {
                    get: () => undefined
                });
            """)

            # 3. 设置额外的上下文选项
            context = self._page.context
            await context.set_extra_http_headers({"Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8"})

        return self._page

    async def check_login_status(self, url: URL) -> bool:
        """检查是否需要登录

        Returns:
            True: 已登录, False: 需要登录
        """
        page = await self._get_page()

        logger.info(f"Checking login status at {url.value}")

        # 使用 load 而不是 networkidle，因为 networkidle 可能永远达不到（持续的网络请求）
        try:
            await page.goto(url.value, wait_until="load", timeout=60000)
        except Exception as e:
            logger.warning(f"Page load timeout or error: {e}, trying to continue...")
            # 即使超时也继续，可能页面已经部分加载

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
        """搜索关键词
        搜索框的CSS选择器为: #search-input
        """
        page = await self._get_page()

        logger.info(f"Searching for: {keyword.value}")

        # 优先使用精确的选择器: #search-input
        primary_selector = "#search-input"
        search_input = None

        try:
            search_input = await page.wait_for_selector(primary_selector, timeout=5000)
            logger.debug(f"Found search input with primary selector: {primary_selector}")
        except Exception as e:
            logger.warning(
                f"Could not find search input with primary selector {primary_selector}: {e}"
            )
            # 如果主要选择器失败，使用备用选择器
            search_selectors = [
                'input[placeholder*="搜索"]',
                'input[type="search"]',
                ".search-input input",
                "input.search-input",
                "#search-input",  # 再次尝试
            ]

            for selector in search_selectors:
                try:
                    search_input = await page.wait_for_selector(selector, timeout=3000)
                    if search_input:
                        logger.info(f"Found search input with fallback selector: {selector}")
                        break
                except Exception:
                    continue

        if not search_input:
            raise Exception("Could not find search input with any selector")

        # 清空并输入搜索词
        await search_input.click()
        await search_input.fill(keyword.value)
        await asyncio.sleep(0.5)

        # 按回车或点击搜索按钮
        await search_input.press("Enter")
        await asyncio.sleep(2)

        logger.info(f"Search completed for: {keyword.value}")

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
        内容链接的CSS选择器为: .feeds-container .note-item a

        Returns:
            List of (link, link_id) tuples
        """
        page = await self._get_page()

        # 使用精确的选择器: .feeds-container .note-item .cover
        primary_selector = ".feeds-container .note-item .cover"
        visible_links = []

        try:
            # 使用主要选择器查找链接
            links = await page.query_selector_all(primary_selector)
            logger.debug(f"Found {len(links)} links with primary selector: {primary_selector}")
            if not links:
                logger.warning("No links found with primary selector, trying fallback selectors")
                return await self._get_visible_links_fallback()

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
            logger.warning(f"Error finding links with primary selector {primary_selector}: {e}")
            logger.info("No links found with primary selector, trying fallback selectors")
            # 使用备用方法
            return await self._get_visible_links_fallback()

        logger.info(f"Found {len(visible_links)} visible links")
        return visible_links

    async def _get_visible_links_fallback(self) -> List[tuple[Locator, str]]:
        """备用方法：如果主要选择器失败，使用全局搜索"""
        page = await self._get_page()

        link_selectors = [
            ".feeds-container .note-item a",
            ".note-item a",
            'a[href*="/explore/"]',
            'a[href*="/discovery/"]',
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

        logger.info(f"Found {len(visible_links)} visible links with fallback selectors")
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

    async def wait_for_content_page(self, timeout: int = 10000) -> bool:
        """等待内容页面加载（检查是否有 .note-container）

        Returns:
            True: 内容页面已加载, False: 超时
        """
        page = await self._get_page()

        try:
            await page.wait_for_selector(".note-container", timeout=timeout)
            logger.info("Content page loaded")
            return True
        except Exception:
            logger.warning("Content page not found")
            return False

    async def check_content_type(self) -> str:
        """检查内容类型：图片或视频

        Returns:
            "image": 图片内容
            "video": 视频内容
            "unknown": 未知类型
        """
        page = await self._get_page()

        try:
            # 检查是否为图片内容
            image_container = await page.query_selector(
                ".note-container .media-container .slider-container"
            )
            if image_container:
                logger.info("Content type: image")
                return "image"

            # 检查是否为视频内容
            video_container = await page.query_selector(
                ".note-container .media-container .player-container"
            )
            if video_container:
                logger.info("Content type: video")
                return "video"

            logger.warning("Content type: unknown")
            return "unknown"
        except Exception as e:
            logger.error(f"Error checking content type: {e}")
            return "unknown"

    async def browse_image_content(self) -> None:
        """浏览图片内容"""
        page = await self._get_page()

        logger.info("Browsing image content")

        # 获取图片数量
        try:
            slide_count = await page.evaluate("""
                () => {
                    const slides = document.querySelectorAll('.slider-container .swiper-slide');
                    return slides.length;
                }
            """)

            if slide_count == 0:
                logger.warning("No slides found in image content")
                return

            logger.info(f"Found {slide_count} images")

            # 点击右箭头翻页，1~slide_count次
            click_count = random.randint(1, slide_count)
            logger.info(f"Will click right arrow {click_count} times")

            for i in range(click_count):
                try:
                    right_arrow = await page.query_selector(".arrow-controller.right")
                    if right_arrow:
                        await right_arrow.click()
                        wait_time = random.uniform(0.5, 1)
                        logger.info(
                            f"Clicked right arrow {i + 1}/{click_count}, waiting {wait_time:.2f}s"
                        )
                        await asyncio.sleep(wait_time)
                    else:
                        logger.warning("Right arrow not found, stopping image browsing")
                        break
                except Exception as e:
                    logger.error(f"Error clicking right arrow: {e}")
                    break
        except Exception as e:
            logger.error(f"Error browsing image content: {e}")

    async def browse_video_content(self) -> None:
        """浏览视频内容"""
        page = await self._get_page()

        logger.info("Browsing video content")
        time.sleep(100)
        try:
            # 尝试获取视频时长
            video_duration = await page.evaluate("document.querySelector('.player-container video').duration")

            if video_duration:
                logger.info(f"Video duration: {video_duration:.2f} seconds")

                if video_duration > 10:
                    # 视频超过10秒，看完
                    logger.info(
                        f"Video is longer than 10s, watching full video ({video_duration:.2f}s)"
                    )
                    await asyncio.sleep(video_duration)
                else:
                    # 视频不超过10秒，看随机5~15秒
                    watch_time = random.uniform(2, 5)
                    actual_watch_time = min(watch_time, video_duration)
                    logger.info(
                        f"Video is {video_duration:.2f}s, watching for {actual_watch_time:.2f}s"
                    )
                    await asyncio.sleep(actual_watch_time)
            else:
                # 无法获取视频时长，随机看5~15秒
                watch_time = random.uniform(2, 5)
                logger.info(f"Could not get video duration, watching for {watch_time:.2f}s")
                await asyncio.sleep(watch_time)
        except Exception as e:
            logger.error(f"Error browsing video content: {e}")
            # 出错时默认等待一段时间
            await asyncio.sleep(random.uniform(5, 10))

    async def browse_comments_smart(self, content_type: str) -> None:
        """智能浏览文章正文与评论

        Args:
            content_type: 内容类型 ("image" 或 "video")
        """
        page = await self._get_page()

        logger.info(f"Browsing article content and comments for {content_type} content")

        css_note_scroller = ".note-scroller"
        css_comments_container = ".comments-container"
        try:
            # 检查评论容器
            comments_container = await page.query_selector(css_comments_container)
            if not comments_container:
                logger.warning("Comments container not found")
                return

            # 获取父评论数量
            logger.debug(
                f"Getting parent comment count for: {css_comments_container} .parent-comment"
            )
            comments = await page.query_selector_all(f"{css_comments_container} .parent-comment")
            parent_comment_count = len(comments)

            if parent_comment_count == 0:
                logger.info("No parent comments found")
                return

            logger.info(f"Found {parent_comment_count} parent comments")

            max_scrolls = random.randint(1, parent_comment_count)

            logger.info(f"Will scroll comments {max_scrolls} times")

            for i in range(max_scrolls):
                # 检查是否还可以向上滚动
                can_scroll = await page.evaluate(f"""
                    () => {{
                        const container = document.querySelector('{css_note_scroller}');
                        if (!container) return false;
                        return container.scrollTop > 0 || container.scrollHeight > container.clientHeight;
                    }}
                """)

                if not can_scroll:
                    logger.info("Comments container cannot scroll further, stopping")
                    break

                # 向上滚动100~300px
                scroll_distance = random.uniform(100, 300)
                await page.evaluate(f"""
                    () => {{
                        const container = document.querySelector('{css_note_scroller}');
                        if (container) {{
                            container.scrollTop += {scroll_distance};
                        }}
                    }}
                """)

                logger.info(
                    f"Scrolled comments up by {scroll_distance:.0f}px ({i + 1}/{max_scrolls})"
                )
                await asyncio.sleep(random.uniform(0.5, 1.5))

        except Exception as e:
            logger.error(f"Error browsing comments: {e}")

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
