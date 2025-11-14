"""基础爬虫示例"""

import asyncio
from infrastructure.database.session import AsyncSessionLocal
from infrastructure.database.init_db import init_database
from infrastructure.repositories import SQLAlchemyCrawlerTaskRepository
from infrastructure.adapters.playwright_service import PlaywrightBrowserService
from application.use_cases import CrawlUrlUseCase
from application.dto import CrawlUrlCommand


async def main():
    """主函数"""
    # 初始化数据库
    await init_database()
    
    # 创建依赖
    async with AsyncSessionLocal() as session:
        task_repo = SQLAlchemyCrawlerTaskRepository(session)
        browser_service = PlaywrightBrowserService(headless=True)
        
        try:
            # 创建用例
            use_case = CrawlUrlUseCase(task_repo, browser_service)
            
            # 执行爬取
            command = CrawlUrlCommand(
                url="https://example.com",
                options={
                    "wait_until": "load",
                }
            )
            
            result = await use_case.execute(command)
            
            print(f"Task ID: {result.task_id}")
            print(f"Status: {result.status}")
            print(f"URL: {result.url}")
            
            if result.content:
                print(f"Content length: {len(result.content)} bytes")
                # 保存内容到文件
                with open("example_output.html", "w", encoding="utf-8") as f:
                    f.write(result.content)
                print("Content saved to example_output.html")
            
            if result.error_message:
                print(f"Error: {result.error_message}")
        
        finally:
            await browser_service.close()


if __name__ == "__main__":
    asyncio.run(main())

