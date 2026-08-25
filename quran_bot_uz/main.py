import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession
from config import BOT_TOKEN
from handlers import start, search

logging.basicConfig(level=logging.INFO)

async def main():
    # PythonAnywhere bepul serveri uchun maxsus darvoza (proxy)
    session = AiohttpSession(proxy="http://proxy.server:3128")
    
    bot = Bot(token=BOT_TOKEN, session=session)
    dp = Dispatcher()

    # Yozgan komandalarimizni botga ulaymiz
    dp.include_router(start.router)
    dp.include_router(search.router)

    print("🚀 Bot muvaffaqiyatli ishga tushdi!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())