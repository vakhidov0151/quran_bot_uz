import asyncio
import logging
import datetime
from zoneinfo import ZoneInfo
import aiohttp
import aiosqlite
import os
from aiogram import Bot, Dispatcher
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from config import BOT_TOKEN, DB_PATH, USER_DB_PATH
from handlers import start

logging.basicConfig(level=logging.INFO)

# TOSHKEN VAQTINI QAT'IY BELGILASH
TASHKENT_TZ = ZoneInfo("Asia/Tashkent")

# API'ni har daqiqada qiynamaslik uchun xotira
prayer_time_cache = {}

location_cache = {}
user_sent_cache = {}

async def check_and_send_prayer_notifications(bot: Bot):
    # Bu funksiya har daqiqada ishga tushadi, biz endi soatni har bir foydalanuvchining o'z mintaqasiga qarab hisoblaymiz.
    try:
        async with aiosqlite.connect(USER_DB_PATH) as db:
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

                loc_key = f"{round(lat, 2)}_{round(lon, 2)}"

                # Asosiy joriy sanani UTC da olamiz, keshni shu bilan yangilaymiz
                utc_now = datetime.datetime.now(datetime.timezone.utc)
                cache_date_str = utc_now.strftime("%d-%m-%Y")

                if loc_key not in location_cache or location_cache[loc_key].get('date') != cache_date_str:
                    url = f"http://api.aladhan.com/v1/timings?latitude={lat}&longitude={lon}&method=99&methodSettings=15.5,null,15&school=1"
                    try:
                        async with session.get(url, timeout=5) as response:
                            if response.status == 200:
                                data = await response.json()
                                raw_timings = data['data']['timings']
                                loc_tz = data['data']['meta']['timezone'] # 🔥 Asosiy xatolik shu yerda edi (Toshkent vaqti bilan cheklangan)
                                timings = {k: v.split(" ")[0][:5] for k, v in raw_timings.items()}
                                
                                m_time = datetime.datetime.strptime(timings['Maghrib'], "%H:%M")
                                m_time += datetime.timedelta(minutes=5)
                                timings['Maghrib'] = m_time.strftime("%H:%M")

                                location_cache[loc_key] = {
                                    "date": cache_date_str,
                                    "timings": timings,
                                    "timezone": loc_tz
                                }
                    except Exception:
                        continue 

                if user_id not in user_sent_cache or user_sent_cache[user_id].get('date') != cache_date_str:
                    user_sent_cache[user_id] = {"date": cache_date_str, "sent": []}

                loc_data = location_cache.get(loc_key)
                if loc_data and loc_data.get('date') == cache_date_str:
                    timings = loc_data['timings']
                    loc_tz_name = loc_data['timezone']
                    sent_list = user_sent_cache[user_id]['sent']

                    # 🔥 Foydalanuvchining joriy lokal vaqtini aniqlaymiz
                    try:
                        user_now = datetime.datetime.now(ZoneInfo(loc_tz_name))
                        user_current_time = user_now.strftime("%H:%M")
                    except Exception:
                        continue

                    prayer_names = {
                        "Fajr": ("Bomdod", "Бомдод"),
                        "Dhuhr": ("Peshin", "Пешин"),
                        "Asr": ("Asr", "Аср"),
                        "Maghrib": ("Shom", "Шом"),
                        "Isha": ("Xufton", "Хуфтон")
                    }

                    for p_key, p_names in prayer_names.items():
                        p_time = timings.get(p_key)
                        
                        if p_time == user_current_time and p_key not in sent_list:
                            p_name = p_names[0] if script == 'latin' else p_names[1]
                            msg = f"🕌 **{p_name} vaqti kirdi!**\n\n_(Alloh ibodatlaringizni qabul qilsin!)_\n\n👉 @al\\_qurani\\_karim\\_bot" if script == 'latin' else f"🕌 **{p_name} вақти кирди!**\n\n_(Аллоҳ ибодатларингизни қабул қилсин!)_\n\n👉 @al\\_qurani\\_karim\\_bot"
                            
                            try:
                                await bot.send_message(user_id, msg, parse_mode="Markdown")
                                user_sent_cache[user_id]["sent"].append(p_key)
                                await asyncio.sleep(0.1) 
                            except Exception:
                                pass

    except Exception as e:
        print(f"Xatolik (Checker): {e}")

async def check_and_send_juma_notifications(bot: Bot):
    try:
        from database.db_manager import get_random_verse
        
        async with aiosqlite.connect(USER_DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT user_id, script FROM users") as cursor:
                users = await cursor.fetchall()

        if not users:
            return

        for user in users:
            user_id = user['user_id']
            script = user['script']
            
            verse = await get_random_verse(script)
            if verse:
                title = "✨ **Juma ayyomi muborak! Kun oyati** ✨" if script == 'latin' else "✨ **Жума айёми муборак! Кун ояти** ✨"
                sura_text, oyat_text = ("surasi", "oyat") if script == 'latin' else ("сураси", "оят")
                name = verse.get('surah_name_uz', verse.get('name_uz', ''))
                v_id = verse.get('verse_id', verse.get('id', ''))
                ar = verse.get('text_arabic', verse.get('arabic', ''))
                uz = verse.get('text_uzbek', verse.get('uzbek', verse.get('text', '')))
                
                text = f"{title}\n\n📖 **{name} {sura_text}, {v_id}-{oyat_text}**\n\n📝 {ar}\n\n🇺🇿 {uz}\n\n👉 @al\\_qurani\\_karim\\_bot"
                
                try:
                    await bot.send_message(user_id, text, parse_mode="Markdown")
                    await asyncio.sleep(0.1)
                except Exception:
                    pass

    except Exception as e:
        print(f"Xatolik (Juma Checker): {e}")

async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    dp.include_router(start.router)

    if not os.path.exists(DB_PATH):
        print(f"DIQQAT: {DB_PATH} fayli topilmadi!")

    os.makedirs(os.path.dirname(USER_DB_PATH), exist_ok=True)
    async with aiosqlite.connect(USER_DB_PATH) as db:
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
    # Juma xabarnomasi: Har juma kuni soat 08:00 da (Toshkent vaqti bilan)
    scheduler.add_job(check_and_send_juma_notifications, "cron", day_of_week="fri", hour=8, minute=0, args=(bot,))
    scheduler.start()

    print("🚀 Bot muvaffaqiyatli ishga tushdi!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
