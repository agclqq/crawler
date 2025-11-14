"""数据库操作示例"""

import asyncio
from infrastructure.database.session import AsyncSessionLocal
from infrastructure.database.init_db import init_database
from infrastructure.database.models import CrawlerTaskModel
from infrastructure.repositories import SQLAlchemyCrawlerTaskRepository
from domain.entities import CrawlerTask
from domain.value_objects import TaskStatus


async def demo_create_task():
    """演示创建任务"""
    print("=== 创建任务示例 ===")
    
    async with AsyncSessionLocal() as session:
        repo = SQLAlchemyCrawlerTaskRepository(session)
        
        # 创建任务
        task = CrawlerTask.create("https://example.com", metadata={"demo": True})
        await repo.save(task)
        
        print(f"Created task: {task.id}")
        print(f"Status: {task.status}")
        print(f"URL: {task.url}")


async def demo_query_tasks():
    """演示查询任务"""
    print("\n=== 查询任务示例 ===")
    
    async with AsyncSessionLocal() as session:
        repo = SQLAlchemyCrawlerTaskRepository(session)
        
        # 查询所有任务
        tasks = await repo.find_all(limit=10)
        print(f"Found {len(tasks)} tasks")
        
        for task in tasks:
            print(f"  - {task.id}: {task.status.value} - {task.url}")


async def demo_update_task():
    """演示更新任务"""
    print("\n=== 更新任务示例 ===")
    
    async with AsyncSessionLocal() as session:
        repo = SQLAlchemyCrawlerTaskRepository(session)
        
        # 获取第一个任务
        tasks = await repo.find_all(limit=1)
        if not tasks:
            print("No tasks found")
            return
        
        task = tasks[0]
        print(f"Original status: {task.status.value}")
        
        # 更新任务状态
        task.start()
        await repo.save(task)
        
        # 重新查询验证
        updated_task = await repo.find_by_id(task.id)
        print(f"Updated status: {updated_task.status.value}")


async def demo_query_by_status():
    """演示按状态查询"""
    print("\n=== 按状态查询示例 ===")
    
    async with AsyncSessionLocal() as session:
        repo = SQLAlchemyCrawlerTaskRepository(session)
        
        # 查询待处理的任务
        pending_tasks = await repo.find_by_status(TaskStatus.PENDING, limit=10)
        print(f"Found {len(pending_tasks)} pending tasks")
        
        # 查询已完成的任务
        completed_tasks = await repo.find_by_status(TaskStatus.COMPLETED, limit=10)
        print(f"Found {len(completed_tasks)} completed tasks")


async def main():
    """主函数"""
    # 初始化数据库
    await init_database()
    
    # 运行示例
    await demo_create_task()
    await demo_query_tasks()
    await demo_update_task()
    await demo_query_by_status()


if __name__ == "__main__":
    asyncio.run(main())

