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

# TOSHKEN VAQTINI QAT'IY BELGILASH
TASHKENT_TZ = ZoneInfo("Asia/Tashkent")

# API'ni har daqiqada qiynamaslik uchun xotira
prayer_time_cache = {}

async def check_and_send_prayer_notifications(bot: Bot):
    now = datetime.datetime.now(TASHKENT_TZ)
    current_time = now.strftime("%H:%M")
    current_date = now.strftime("%d-%m-%Y")

    try:
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT user_id, latitude, longitude, script FROM users WHERE latitude IS NOT NULL") as cursor:
                users = await cursor.fetchall()

        if not users:
            return

        async with aiohttp.ClientSession() as session:
            for user in users:
                user_id = user['user_id']
                lat = user['latitude']
                lon = user['longitude']
                script = user['script']

                user_cache = prayer_time_cache.get(user_id)
                if not user_cache or user_cache.get('date') != current_date:
                    url = f"http://api.aladhan.com/v1/timings?latitude={lat}&longitude={lon}&method=99&methodSettings=18,null,15&school=1"
                    try:
                        async with session.get(url, timeout=5) as response:
                            if response.status == 200:
                                data = await response.json()
                                raw_timings = data['data']['timings']
                                # "(UZT)" yozuvlarini olib tashlab, toza soatni qoldiramiz
                                timings = {k: v.split(" ")[0][:5] for k, v in raw_timings.items()}
                                
                                # ⚙️ ISLOM.UZ UCHUN MAXSUS: Shom (Maghrib) ga aniq +5 daqiqa qo'shamiz
                                m_time = datetime.datetime.strptime(timings['Maghrib'], "%H:%M")
                                m_time += datetime.timedelta(minutes=5)
                                timings['Maghrib'] = m_time.strftime("%H:%M")

                                prayer_time_cache[user_id] = {
                                    "date": current_date,
                                    "timings": timings,
                                    "sent": [] 
                                }
                                user_cache = prayer_time_cache[user_id]
                    except Exception:
                        continue 

                if user_cache and user_cache.get('date') == current_date:
                    timings = user_cache['timings']
                    sent_list = user_cache['sent']

                    prayer_names = {
                        "Fajr": ("Bomdod", "Бомдод"),
                        "Dhuhr": ("Peshin", "Пешин"),
                        "Asr": ("Asr", "Аср"),
                        "Maghrib": ("Shom", "Шом"),
                        "Isha": ("Xufton", "Хуфтон")
                    }

                    for p_key, p_names in prayer_names.items():
                        p_time = timings.get(p_key)
                        
                        if p_time == current_time and p_key not in sent_list:
                            p_name = p_names[0] if script == 'latin' else p_names[1]
                            msg = f"🕌 **{p_name} vaqti kirdi!**\n\n_(Alloh ibodatlaringizni qabul qilsin!)_" if script == 'latin' else f"🕌 **{p_name} вақти кирди!**\n\n_(Аллоҳ ибодатларингизни қабул қилсин!)_"
                            
                            try:
                                await bot.send_message(user_id, msg, parse_mode="Markdown")
                                prayer_time_cache[user_id]["sent"].append(p_key)
                                await asyncio.sleep(0.3) 
                            except Exception:
                                pass

    except Exception as e:
        print(f"Xatolik (Checker): {e}")

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

    scheduler = AsyncIOScheduler(timezone=TASHKENT_TZ)
    scheduler.add_job(check_and_send_prayer_notifications, "cron", minute="*", args=(bot,))
    scheduler.start()

    print("🚀 Bot muvaffaqiyatli ishga tushdi!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
