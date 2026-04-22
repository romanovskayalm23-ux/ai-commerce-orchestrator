import asyncio
import logging
import os
from aiohttp import web

from aiogram import Bot, Dispatcher

from config import settings
from database import Database
from handlers import create_router
from services.ab_testing import ABTestingService
from services.analytics import AnalyticsService
from services.generation import MultiPlatformGenerator
from services.marketplace import MarketplaceService
from services.queue import QueueService


async def health_check(request):
    return web.Response(text="Bot is running")


async def run() -> None:
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    bot = Bot(token=settings.bot_token)
    db = Database(settings.db_path)

    await db.connect()
    await db.init()

    generator = MultiPlatformGenerator(db)
    queue_service = QueueService(db=db, generator=generator, bot=bot)
    ab_testing = ABTestingService(db)
    analytics = AnalyticsService(db)
    marketplace = MarketplaceService()

    await queue_service.start()

    dp = Dispatcher()
    dp.include_router(
        create_router(
            db=db,
            queue_service=queue_service,
            ab_testing=ab_testing,
            analytics=analytics,
            marketplace=marketplace,
        )
    )

    # Start health check server for Render
    app = web.Application()
    app.router.add_get("/", health_check)
    app.router.add_get("/health", health_check)

    runner = web.AppRunner(app)
    await runner.setup()

    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

    logging.info(f"Health check server started on port {port}")

    try:
        await dp.start_polling(bot)
    finally:
        await queue_service.stop()
        await db.close()
        await bot.session.close()
        await runner.cleanup()


if __name__ == "__main__":
    asyncio.run(run())
