import asyncio
import logging
import datetime
from zoneinfo import ZoneInfo
import aiohttp
import aiosqlite
import os
from aiogram import Bot, Dispatcher
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from config import BOT_TOKEN, DB_PATH
from handlers import start

logging.basicConfig(level=logging.INFO)

# 1. TOSHKEN VAQTINI QAT'IY BELGILASH
TASHKENT_TZ = ZoneInfo("Asia/Tashkent")

async def send_prayer_notifications(bot: Bot):
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT user_id, latitude, longitude, script FROM users WHERE latitude IS NOT NULL") as cursor:
                users = await cursor.fetchall()
                
        if not users:
            return

        # Vaqtni ham Toshkent bo'yicha olamiz
        today_date = datetime.datetime.now(TASHKENT_TZ).strftime("%d-%m-%Y")

        async with aiohttp.ClientSession() as session:
            for user in users:
                user_id = user['user_id']
                lat = user['latitude']
                lon = user['longitude']
                script = user['script']
                
                url = f"http://api.aladhan.com/v1/timings?latitude={lat}&longitude={lon}&method=1&school=1"
                try:
                    async with session.get(url, timeout=10) as response:
                        if response.status == 200:
                            data = await response.json()
                            timings = data['data']['timings']
                            
                            if script == 'latin':
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
                            else:
                                text = (
                                    f"🌅 **Кунлик намоз вақтлари эслатмаси**\n"
                                    f"🗓 Сана: {today_date}\n\n"
                                    f"🌅 Бомдод: {timings['Fajr']}\n"
                                    f"🌄 Қуёш: {timings['Sunrise']}\n"
                                    f"☀️ Пешин: {timings['Dhuhr']}\n"
                                    f"🌇 Аср: {timings['Asr']}\n"
                                    f"🌆 Шом: {timings['Maghrib']}\n"
                                    f"🌃 Хуфтон: {timings['Isha']}\n\n"
                                    f"*(Аллоҳ ибодатларингизни қабул қилсин!)*"
                                )
                            await bot.send_message(user_id, text, parse_mode="Markdown")
                            await asyncio.sleep(0.5) # Telegram bloklamasligi uchun pauza
                except Exception as e:
                    print(f"Xato (Foydalanuvchi {user_id}): {e}")
    except Exception as e:
        print(f"Bildirishnoma yuborishda xatolik: {e}")

async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    dp.include_router(start.router)

    if not os.path.exists(DB_PATH):
        print(f"DIQQAT: {DB_PATH} fayli topilmadi!")

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            latitude REAL,
            longitude REAL,
            script TEXT DEFAULT 'latin'
        )
        """)
        await db.commit()

    # 2. SCHEDULER'NI TOSHKENT VAQTIGA QULFLASH
    scheduler = AsyncIOScheduler(timezone=TASHKENT_TZ)
    
    # Har kuni ertalab soat 05:00 da hammaga kunlik ro'yxatni yuboradi
    scheduler.add_job(send_prayer_notifications, "cron", hour=5, minute=0, args=(bot,))
    scheduler.start()

    print("🚀 Bot muvaffaqiyatli ishga tushdi!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
