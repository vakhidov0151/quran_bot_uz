import asyncio
import logging
import aiosqlite
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN
from handlers import start, search

logging.basicConfig(level=logging.INFO)

async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    dp.include_router(start.router)
    dp.include_router(search.router)

    # YANGI: Bot yonganda bazaga kirib, "users" jadvalini majburiy tekshiradi va yaratadi
    async with aiosqlite.connect("data/quran.db") as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            latitude REAL,
            longitude REAL
        )
        """)
        await db.commit()

    print("🚀 Bot muvaffaqiyatli ishga tushdi va baza to'liq tekshirildi!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
