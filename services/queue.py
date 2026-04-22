from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field

from aiogram import Bot

from database import Database
from services.generation import MultiPlatformGenerator


@dataclass(order=True, slots=True)
class QueueItem:
    priority: int
    created_at: float
    task_id: int = field(compare=False)
    user_id: int = field(compare=False)
    campaign_id: int = field(compare=False)
    product_name: str = field(compare=False)
    platforms: list[str] = field(compare=False)


class QueueService:
    def __init__(self, db: Database, generator: MultiPlatformGenerator, bot: Bot) -> None:
        self.db = db
        self.generator = generator
        self.bot = bot
        self._queue: asyncio.PriorityQueue[QueueItem] = asyncio.PriorityQueue()
        self._worker_task: asyncio.Task[None] | None = None
        self.logger = logging.getLogger("queue")

    async def start(self) -> None:
        if self._worker_task is None:
            self._worker_task = asyncio.create_task(self._worker(), name="generation-worker")

    async def stop(self) -> None:
        if self._worker_task is not None:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
            self._worker_task = None

    async def enqueue(
        self,
        user_id: int,
        campaign_id: int,
        product_name: str,
        platforms: list[str],
        priority: int,
    ) -> int:
        task_id = await self.db.create_queue_task(
            user_id=user_id,
            campaign_id=campaign_id,
            prompt=f"Generate campaign for {product_name}",
            priority=priority,
        )

        item = QueueItem(
            priority=priority,
            created_at=time.time(),
            task_id=task_id,
            user_id=user_id,
            campaign_id=campaign_id,
            product_name=product_name,
            platforms=platforms,
        )

        await self._queue.put(item)
        return task_id

    async def _worker(self) -> None:
        while True:
            item = await self._queue.get()
            try:
                await self.db.set_queue_task_status(item.task_id, "processing")
                await self.db.update_campaign_status(item.campaign_id, "generating")

                variant_ids = await self.generator.generate_campaign(
                    campaign_id=item.campaign_id,
                    product_name=item.product_name,
                    platforms=item.platforms,
                )

                await self.db.set_queue_task_status(item.task_id, "done")
                await self.db.update_campaign_status(item.campaign_id, "ready")

                variants = await self.db.get_campaign_variants(item.campaign_id)

                message = f"✅ Кампания #{item.campaign_id} готова!\n\n"
                message += f"Товар: {item.product_name}\n"
                message += f"Создано вариантов: {len(variants)}\n\n"

                for v in variants:
                    message += f"📱 {v['platform'].title()}\n"
                    message += f"   {v['copy_text'][:60]}...\n"
                    message += f"   {v['hashtags'][:40]}...\n\n"

                message += f"Используй /campaigns чтобы посмотреть детали и запустить A/B тест."

                await self.bot.send_message(item.user_id, text=message)

            except Exception:
                self.logger.exception("Queue worker failed for task %s", item.task_id)
                await self.db.set_queue_task_status(item.task_id, "failed")
                await self.db.update_campaign_status(item.campaign_id, "failed")
                await self.bot.send_message(
                    item.user_id,
                    text=f"❌ Ошибка при генерации кампании #{item.campaign_id}. Попробуй снова с /create_campaign.",
                )
            finally:
                self._queue.task_done()
