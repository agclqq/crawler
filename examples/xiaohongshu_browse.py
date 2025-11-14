"""小红书浏览示例"""

import asyncio
from infrastructure.adapters.xiaohongshu_service import XiaohongshuBrowserService
from application.xiaohongshu_use_cases import XiaohongshuBrowseUseCase
from application.dto import XiaohongshuBrowseCommand


async def main():
    """主函数"""
    # 创建浏览器服务（非无头模式，方便观察）
    browser_service = XiaohongshuBrowserService(headless=False)
    
    try:
        # 创建用例
        use_case = XiaohongshuBrowseUseCase(browser_service)
        
        # 构建命令
        command = XiaohongshuBrowseCommand(
            keywords=["云鲸 j6", "云鲸 逍遥002","云鲸 逍遥002max"],  # 可以直接指定关键词
            # config_file="config/search_keywords.json",  # 或使用配置文件
            max_items_per_view=3,
            max_scrolls=5,
            max_comment_scrolls=10,
        )
        
        # 执行浏览
        await use_case.execute(command)
        
        print("浏览完成！")
    
    finally:
        await browser_service.close()


if __name__ == "__main__":
    asyncio.run(main())

