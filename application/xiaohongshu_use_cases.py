"""小红书浏览用例实现"""

import asyncio
import json
import random
from pathlib import Path
from typing import List, Optional
from loguru import logger

from domain.value_objects import URL, SearchKeyword
from domain.exceptions import DomainError
from infrastructure.adapters.xiaohongshu_service import XiaohongshuBrowserService
from application.dto import XiaohongshuBrowseCommand


class XiaohongshuBrowseUseCase:
    """小红书浏览用例"""
    
    XIAOHONGSHU_HOME_URL = "https://www.xiaohongshu.com/"
    DEFAULT_CONFIG_FILE = "config/search_keywords.json"
    
    def __init__(self, browser_service: XiaohongshuBrowserService):
        self._browser_service = browser_service
    
    def _load_keywords(self, config_file: Optional[str] = None) -> List[str]:
        """从配置文件加载搜索关键词"""
        config_path = Path(config_file or self.DEFAULT_CONFIG_FILE)
        
        if not config_path.exists():
            raise DomainError(f"Config file not found: {config_path}")
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                keywords = data.get('keywords', [])
                if not keywords:
                    raise DomainError("No keywords found in config file")
                return keywords
        except json.JSONDecodeError as e:
            raise DomainError(f"Invalid JSON in config file: {e}")
        except Exception as e:
            raise DomainError(f"Failed to load config file: {e}")
    
    async def execute(self, command: XiaohongshuBrowseCommand) -> None:
        """执行小红书浏览用例"""
        logger.info("Starting Xiaohongshu browse use case")
        
        try:
            # 1. 加载搜索关键词
            if command.keywords:
                keywords = command.keywords
            else:
                keywords = self._load_keywords(command.config_file)
            
            logger.info(f"Loaded {len(keywords)} keywords")
            
            # 2. 访问主页并检查登录状态
            home_url = URL(self.XIAOHONGSHU_HOME_URL)
            is_logged_in = await self._browser_service.check_login_status(home_url)
            
            # 3. 如果未登录，等待登录
            if not is_logged_in:
                logger.info("Not logged in, waiting for manual login...")
                await self._browser_service.wait_for_login()
                # 登录成功后等待0.2~1秒
                wait_time = random.uniform(0.2, 1)
                logger.info(f"Login detected, waiting {wait_time:.2f}s before searching")
                await asyncio.sleep(wait_time)
            
            # 4. 循环搜索词的数量次
            for keyword_str in keywords:
                try:
                    keyword = SearchKeyword(keyword_str)
                    await self._browse_keyword(keyword, command)
                except Exception as e:
                    logger.error(f"Error browsing keyword {keyword_str}: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Browse use case failed: {e}")
            raise
    
    async def _browse_keyword(
        self,
        keyword: SearchKeyword,
        command: XiaohongshuBrowseCommand,
    ) -> None:
        """浏览单个关键词的搜索结果"""
        logger.info(f"Browsing keyword: {keyword.value}")
        
        # 1. 搜索关键词
        await self._browser_service.search(keyword)
        
        # 2. 搜索结果加载完成后，等待1~3秒
        wait_time = random.uniform(1, 3)
        logger.info(f"Search results loaded, waiting {wait_time:.2f}s")
        await asyncio.sleep(wait_time)
        
        # 3. 循环随机1~5次
        max_iterations = random.randint(1, 5)
        logger.info(f"Will browse {max_iterations} items")
        
        opened_links = set()  # 记录已打开的链接，确保不重复

        for iteration in range(max_iterations):
            logger.info(f"Iteration {iteration + 1}/{max_iterations}")

            # 3.1 随机不重复打开当前页面中搜索结果的内容
            # 注意：翻页后 #exploreFeeds 会被重写，所以需要重新获取链接
            clicked, link_id = await self._browser_service.click_random_visible_link_not_opened(opened_links)

            if not clicked:
                logger.warning("No new visible links to click, scrolling...")
                # 如果找不到新链接，滚动页面
                await self._browser_service.scroll_search_results()
                # 翻页后 #exploreFeeds 会被重写，清空已打开链接记录（新页面内容）
                # 但保留部分记录以避免在同一页面重复打开
                if len(opened_links) > 10:  # 如果记录太多，可能是翻页了
                    logger.info("Possible page turn detected, clearing some link records")
                    opened_links.clear()
                await asyncio.sleep(random.uniform(1, 3))
                continue

            # 记录已打开的链接
            if link_id:
                opened_links.add(link_id)
            
            # 等待内容页面加载
            content_loaded = await self._browser_service.wait_for_content_page()
            
            if content_loaded:
                # 记录内容浏览开始时间
                browse_start_time = asyncio.get_event_loop().time()
                
                # 3.2 检查评论是否超出当前评论框高度
                has_more_comments = await self._browser_service.check_comments_overflow()
                
                if has_more_comments:
                    # 如果评论超出当前评论框高度，循环1~3次下拉评论
                    comment_scrolls = random.randint(1, 3)
                    logger.info(f"Comments overflow detected, will scroll {comment_scrolls} times")
                    
                    for _ in range(comment_scrolls):
                        await self._browser_service.scroll_comments()
                        wait_time = random.uniform(1, 3)
                        await asyncio.sleep(wait_time)
                
                # 确保内容浏览时长至少5~20秒
                elapsed_time = asyncio.get_event_loop().time() - browse_start_time
                min_browse_time = random.uniform(5, 20)
                
                if elapsed_time < min_browse_time:
                    remaining_time = min_browse_time - elapsed_time
                    logger.info(f"Content browsed for {elapsed_time:.2f}s, waiting additional {remaining_time:.2f}s to reach minimum {min_browse_time:.2f}s")
                    await asyncio.sleep(remaining_time)
                else:
                    logger.info(f"Content browsed for {elapsed_time:.2f}s (exceeds minimum {min_browse_time:.2f}s)")
                
                # 关闭内容页面
                await self._browser_service.close_content_page()
                await asyncio.sleep(random.uniform(0.5, 1.5))
            else:
                logger.warning("Content page not loaded, trying to go back")
                # 尝试返回
                page = await self._browser_service._get_page()
                await page.go_back()
                await asyncio.sleep(1)
            
            # 3.3 搜索结果页下拉0.5~1.5倍视窗高度，等待1~3秒
            await self._browser_service.scroll_search_results()
            wait_time = random.uniform(1, 3)
            logger.info(f"Scrolled search results, waiting {wait_time:.2f}s")
            await asyncio.sleep(wait_time)
        
        logger.info(f"Finished browsing keyword: {keyword.value}")

