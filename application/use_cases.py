"""用例实现"""

from typing import List
from loguru import logger

from domain.entities import CrawlerTask
from domain.repositories import ICrawlerTaskRepository
from domain.services import IBrowserService
from domain.exceptions import TaskNotFoundError
from application.dto import CrawlUrlCommand, CrawlResult, TaskQuery


class CrawlUrlUseCase:
    """爬取 URL 用例"""

    def __init__(
        self,
        task_repository: ICrawlerTaskRepository,
        browser_service: IBrowserService,
    ):
        self._task_repository = task_repository
        self._browser_service = browser_service

    async def execute(self, command: CrawlUrlCommand) -> CrawlResult:
        """执行爬取用例"""
        logger.info(f"Starting crawl for URL: {command.url}")

        # 1. 创建任务实体
        task = CrawlerTask.create(command.url, metadata=command.options or {})
        await self._task_repository.save(task)

        # 2. 启动任务
        try:
            task.start()
            await self._task_repository.save(task)

            # 3. 执行爬取
            content = await self._browser_service.crawl(task.url, command.options)

            # 4. 完成任务
            task.complete(content)
            await self._task_repository.save(task)

            logger.info(f"Task {task.id} completed successfully")

        except Exception as e:
            logger.error(f"Task {task.id} failed: {str(e)}")
            task.fail(str(e))
            await self._task_repository.save(task)

        return CrawlResult.from_task(task)


class GetTaskUseCase:
    """获取任务用例"""

    def __init__(self, task_repository: ICrawlerTaskRepository):
        self._task_repository = task_repository

    async def execute(self, task_id: str) -> CrawlResult:
        """获取任务详情"""
        from domain.value_objects import TaskId

        task = await self._task_repository.find_by_id(TaskId(task_id))
        if not task:
            raise TaskNotFoundError(f"Task {task_id} not found")

        return CrawlResult.from_task(task)


class ListTasksUseCase:
    """列出任务用例"""

    def __init__(self, task_repository: ICrawlerTaskRepository):
        self._task_repository = task_repository

    async def execute(self, query: TaskQuery) -> List[CrawlResult]:
        """列出任务"""
        if query.task_id:
            from domain.value_objects import TaskId

            task = await self._task_repository.find_by_id(TaskId(query.task_id))
            return [CrawlResult.from_task(task)] if task else []

        if query.status:
            tasks = await self._task_repository.find_by_status(
                query.status,
                limit=query.limit,
            )
        else:
            tasks = await self._task_repository.find_all(
                limit=query.limit,
                offset=query.offset,
            )

        return [CrawlResult.from_task(task) for task in tasks]
