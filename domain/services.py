"""领域服务定义"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from domain.value_objects import URL


class IBrowserService(ABC):
    """浏览器服务接口"""

    @abstractmethod
    async def crawl(self, url: URL, options: Optional[Dict[str, Any]] = None) -> str:
        """爬取指定 URL 的内容"""
        pass

    @abstractmethod
    async def close(self) -> None:
        """关闭浏览器"""
        pass


class URLNormalizer:
    """URL 标准化服务"""

    @staticmethod
    def normalize(url: str) -> str:
        """标准化 URL"""
        url = url.strip()
        # 移除末尾的斜杠（可选）
        if url.endswith("/") and len(url) > 1:
            url = url[:-1]
        return url

    @staticmethod
    def is_same_domain(url1: str, url2: str) -> bool:
        """检查两个 URL 是否属于同一域名"""
        from urllib.parse import urlparse

        domain1 = urlparse(url1).netloc
        domain2 = urlparse(url2).netloc
        return domain1 == domain2
