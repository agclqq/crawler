"""命令行接口主程序"""

import asyncio
import click
from typing import Optional
from loguru import logger

from infrastructure.database.session import AsyncSessionLocal
from infrastructure.repositories import SQLAlchemyCrawlerTaskRepository
from infrastructure.adapters.playwright_service import PlaywrightBrowserService
from infrastructure.adapters.xiaohongshu_service import XiaohongshuBrowserService
from application.use_cases import CrawlUrlUseCase, GetTaskUseCase, ListTasksUseCase
from application.xiaohongshu_use_cases import XiaohongshuBrowseUseCase
from application.xiaohongshu_download_use_cases import XiaohongshuDownloadImagesUseCase
from application.dto import (
    CrawlUrlCommand,
    TaskQuery,
    XiaohongshuBrowseCommand,
    XiaohongshuDownloadImagesCommand,
)


@click.group()
def cli():
    """通用爬虫框架 CLI"""
    pass


@cli.command()
@click.argument("url")
@click.option("--output", "-o", help="输出文件路径")
@click.option("--headless/--no-headless", default=True, help="是否使用无头模式")
def crawl(url: str, output: Optional[str], headless: bool):
    """爬取指定 URL"""

    async def _crawl():
        async with AsyncSessionLocal() as session:
            task_repo = SQLAlchemyCrawlerTaskRepository(session)
            browser_service = PlaywrightBrowserService(headless=headless)

            try:
                use_case = CrawlUrlUseCase(task_repo, browser_service)
                command = CrawlUrlCommand(url=url)
                result = await use_case.execute(command)

                click.echo(f"Task ID: {result.task_id}")
                click.echo(f"Status: {result.status}")
                click.echo(f"URL: {result.url}")

                if result.content:
                    if output:
                        with open(output, "w", encoding="utf-8") as f:
                            f.write(result.content)
                        click.echo(f"Content saved to {output}")
                    else:
                        click.echo(f"Content length: {len(result.content)} bytes")

                if result.error_message:
                    click.echo(f"Error: {result.error_message}", err=True)
            finally:
                await browser_service.close()

    asyncio.run(_crawl())


@cli.command()
@click.argument("task_id")
def get_task(task_id: str):
    """获取任务详情"""

    async def _get_task():
        async with AsyncSessionLocal() as session:
            task_repo = SQLAlchemyCrawlerTaskRepository(session)
            use_case = GetTaskUseCase(task_repo)

            try:
                result = await use_case.execute(task_id)
                click.echo(f"Task ID: {result.task_id}")
                click.echo(f"Status: {result.status}")
                click.echo(f"URL: {result.url}")
                click.echo(f"Created: {result.created_at}")
                click.echo(f"Updated: {result.updated_at}")
                if result.error_message:
                    click.echo(f"Error: {result.error_message}")
            except Exception as e:
                click.echo(f"Error: {str(e)}", err=True)

    asyncio.run(_get_task())


@cli.command()
@click.option("--status", help="按状态筛选")
@click.option("--limit", default=10, help="限制数量")
def list_tasks(status: Optional[str], limit: int):
    """列出任务"""

    async def _list_tasks():
        async with AsyncSessionLocal() as session:
            task_repo = SQLAlchemyCrawlerTaskRepository(session)
            use_case = ListTasksUseCase(task_repo)

            query = TaskQuery(status=status, limit=limit)
            results = await use_case.execute(query)

            if not results:
                click.echo("No tasks found")
                return

            for result in results:
                click.echo(f"\nTask ID: {result.task_id}")
                click.echo(f"  Status: {result.status}")
                click.echo(f"  URL: {result.url}")
                click.echo(f"  Created: {result.created_at}")

    asyncio.run(_list_tasks())


@cli.command()
@click.option(
    "--config", "-c", help="搜索关键词配置文件路径", default="config/search_keywords.json"
)
@click.option("--keywords", "-k", multiple=True, help="直接指定搜索关键词（可多个）")
@click.option("--max-items", default=3, help="每个视窗中查看的内容数量（1-5）", type=int)
@click.option("--max-scrolls", default=5, help="搜索结果最大滚动次数", type=int)
@click.option("--max-comment-scrolls", default=10, help="评论最大滚动次数", type=int)
@click.option("--headless/--no-headless", default=False, help="是否使用无头模式")
def xiaohongshu_browse(
    config: str,
    keywords: tuple,
    max_items: int,
    max_scrolls: int,
    max_comment_scrolls: int,
    headless: bool,
):
    """浏览小红书内容"""

    async def _browse():
        browser_service = XiaohongshuBrowserService(headless=headless)

        try:
            # 构建命令
            keyword_list = list(keywords) if keywords else None
            command = XiaohongshuBrowseCommand(
                keywords=keyword_list,
                config_file=config if not keyword_list else None,
                max_items_per_view=min(max(1, max_items), 5),  # 限制在1-5之间
                max_scrolls=max_scrolls,
                max_comment_scrolls=max_comment_scrolls,
            )

            # 执行用例
            use_case = XiaohongshuBrowseUseCase(browser_service)
            await use_case.execute(command)

            click.echo("Browse completed successfully!")
        except Exception as e:
            click.echo(f"Error: {str(e)}", err=True)
            logger.exception("Browse failed")
        finally:
            await browser_service.close()

    asyncio.run(_browse())


@cli.command(name="xiaohongshu-download-images")
@click.option(
    "--urls",
    "-u",
    multiple=True,
    help="直接指定 URL（可多个）。支持两种方式：1) 多次使用 -u 选项；2) 在一个 -u 值中用空格分隔多个 URL",
)
@click.option("--url-config-file", "-c", help="URL 配置文件路径（每行一个 URL）")
@click.option("--output-dir", "-o", default="output", help="输出目录")
@click.option("--headless/--no-headless", default=False, help="是否使用无头模式")
def xiaohongshu_download_images(
    urls: tuple, url_config_file: Optional[str], output_dir: str, headless: bool
):
    """有序拉取小红书内容图片并保存到 Word 文件"""

    async def _download():
        browser_service = XiaohongshuBrowserService(headless=headless)

        try:
            # 构建命令
            # 处理 URLs：支持空格分隔的多个 URL
            url_list = []
            if urls:
                for url_item in urls:
                    # 如果 URL 中包含空格，可能是多个 URL，需要分割
                    if " " in url_item.strip():
                        # 分割并过滤空字符串
                        split_urls = [u.strip() for u in url_item.split() if u.strip()]
                        url_list.extend(split_urls)
                    else:
                        url_list.append(url_item.strip())
                # 去重但保持顺序
                url_list = list(dict.fromkeys(url_list))

            command = XiaohongshuDownloadImagesCommand(
                urls=url_list if url_list else None,
                url_config_file=url_config_file,
                output_dir=output_dir,
            )

            # 执行用例
            use_case = XiaohongshuDownloadImagesUseCase(browser_service)
            output_path = await use_case.execute(command)

            click.echo(f"Images downloaded and saved to: {output_path}")
        except Exception as e:
            click.echo(f"Error: {str(e)}", err=True)
            logger.exception("Download failed")
        finally:
            await browser_service.close()

    asyncio.run(_download())


if __name__ == "__main__":
    cli()
