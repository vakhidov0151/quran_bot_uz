import asyncio
import logging
import datetime
import aiohttp
import aiosqlite
import os
from aiogram import Bot, Dispatcher
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from config import BOT_TOKEN, DB_PATH
from handlers import start

logging.basicConfig(level=logging.INFO)

async def send_prayer_notifications(bot: Bot):
    try:
        # Baza manzilini to'g'ri oladi
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT user_id, latitude, longitude FROM users WHERE latitude IS NOT NULL") as cursor:
                users = await cursor.fetchall()
                
        if not users:
            return

        today_date = datetime.datetime.now().strftime("%d-%m-%Y")

        async with aiohttp.ClientSession() as session:
            for user in users:
                user_id = user['user_id']
                lat = user['latitude']
                lon = user['longitude']
                
                url = f"http://api.aladhan.com/v1/timings?latitude={lat}&longitude={lon}&method=1&school=1&tune=0,0,0,0,0,5,0,-18,0"
                try:
                    async with session.get(url, timeout=5) as response:
                        if response.status == 200:
                            data = await response.json(content_type=None)
                            if data['code'] == 200:
                                timings = data['data']['timings']
                                text = (
                                    f"🌅 **Kunlik namoz vaqtlari eslatmasi**\n"
                                    f"🗓 Sana: {today_date}\n\n"
                                    f"🌅 Bomdod: {timings['Fajr']}\n"
                                    f"🌄 Quyosh: {timings['Sunrise']}\n"
                                    f"☀️ Peshin: {timings['Dhuhr']}\n"
                                    f"🌇 Asr: {timings['Asr']}\n"
                                    f"🌆 Shom: {timings['Maghrib']}\n"
                                    f"🌃 Xufton: {timings['Isha']}\n\n"
                                    f"*(Alloh ibodatlaringizni qabul qilsin!)*"
                                )
                                await bot.send_message(user_id, text, parse_mode="Markdown")
                                await asyncio.sleep(0.3) 
                except Exception:
                    pass
    except Exception as e:
        print(f"Bildirishnoma yuborishda xatolik: {e}")

async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    # Asosiy routerlarni ulash
    dp.include_router(start.router)

    # Baza fayli mavjudligini tekshirish
    if not os.path.exists(DB_PATH):
        print(f"DIQQAT: {DB_PATH} fayli topilmadi! Bot bo'sh baza yaratadi.")

    # Bazani ulash va jadvallarni tekshirish
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            latitude REAL,
            longitude REAL
        )
        """)
        try:
            await db.execute("ALTER TABLE users ADD COLUMN script TEXT DEFAULT 'latin'")
        except Exception:
            pass
        await db.commit()

    scheduler = AsyncIOScheduler(timezone="Asia/Tashkent")
    scheduler.add_job(send_prayer_notifications, "cron", hour=5, minute=0, args=(bot,))
    scheduler.start()

    print("🚀 Bot muvaffaqiyatli ishga tushdi!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
