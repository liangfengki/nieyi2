import os
import asyncio
from sqlalchemy import select, delete
from app.db.database import AsyncSessionLocal
from app.models.models import GenerationTask
from app.core.config import GENERATED_IMAGES_DIR

async def cleanup_old_generation_tasks(max_images: int = 100):
    """
    清理历史生成记录，保留最近生成的图片不超过 max_images 张。
    删除数据库记录，并删除对应的本地图片文件。
    """
    try:
        async with AsyncSessionLocal() as db:
            # 按创建时间降序查询所有任务
            result = await db.execute(
                select(GenerationTask).order_by(GenerationTask.created_at.desc())
            )
            tasks = result.scalars().all()

            total_images = 0
            tasks_to_delete = []

            for task in tasks:
                num_images = len(task.images) if task.images else 0
                
                # 如果已经达到了最大图片数量限制，后续的旧任务全部标记为删除
                if total_images >= max_images:
                    tasks_to_delete.append(task)
                else:
                    # 如果加上当前任务的图片数量超出了限制，也可以选择保留这个任务（略微超限），
                    # 或是严格限制。为了完整保留一次任务的生成结果，我们选择保留整个任务。
                    total_images += num_images

            if not tasks_to_delete:
                return

            print(f"[Cleanup] Found {len(tasks_to_delete)} old tasks to delete. Keeping {total_images} recent images.")

            for task in tasks_to_delete:
                # 1. 删除本地图片文件
                if task.images:
                    for img_url in task.images:
                        if img_url.startswith("/static/generated/"):
                            filename = img_url.split("/")[-1]
                            filepath = os.path.join(GENERATED_IMAGES_DIR, filename)
                            if os.path.exists(filepath):
                                try:
                                    os.remove(filepath)
                                    print(f"[Cleanup] Deleted file: {filepath}")
                                except Exception as e:
                                    print(f"[Cleanup] Failed to delete file {filepath}: {e}")

                # 2. 从数据库删除任务记录
                await db.execute(delete(GenerationTask).where(GenerationTask.id == task.id))

            await db.commit()
            print(f"[Cleanup] Successfully deleted {len(tasks_to_delete)} old tasks.")

    except Exception as e:
        print(f"[Cleanup] Error during cleanup: {e}")
        import traceback
        traceback.print_exc()

def trigger_cleanup_background():
    """
    在后台触发清理任务的便捷函数
    """
    asyncio.create_task(cleanup_old_generation_tasks(100))
