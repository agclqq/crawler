"""配置管理"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """应用配置"""
    
    # 数据库配置
    database_url: str = "sqlite+aiosqlite:///./crawler.db"
    
    # 日志配置
    log_level: str = "INFO"
    
    # Playwright 配置
    playwright_browser: str = "chromium"  # chromium, firefox, webkit
    playwright_headless: bool = True
    playwright_timeout: int = 30000  # 毫秒
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# 全局配置实例
settings = Settings()

