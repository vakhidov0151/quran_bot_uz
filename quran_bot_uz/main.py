import asyncio
import logging
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN
from handlers import start, search

logging.basicConfig(level=logging.INFO)

async def main():
    # Railway kabi zamonaviy serverlar uchun to'g'ridan-to'g'ri ulanish
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    # Yozgan komandalarimizni botga ulaymiz
    dp.include_router(start.router)
    dp.include_router(search.router)

    print("🚀 Bot muvaffaqiyatli ishga tushdi!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
