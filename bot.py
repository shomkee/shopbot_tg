import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN
from database import init_db
from handlers import admin, common, payments, profile, shop
from middlewares import BlockMiddleware


async def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    if not BOT_TOKEN:
        raise SystemExit("✕ BOT_TOKEN не задан. Заполните файл .env (см. .env.example)")

    await init_db()

    bot = Bot(BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())

    dp.message.middleware(BlockMiddleware())
    dp.callback_query.middleware(BlockMiddleware())

    # admin первым, чтобы FSM-состояния админки имели приоритет
    dp.include_router(admin.router)
    dp.include_router(common.router)
    dp.include_router(shop.router)
    dp.include_router(profile.router)
    dp.include_router(payments.router)

    await bot.delete_webhook(drop_pending_updates=True)
    logging.info("Бот запущен")
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass