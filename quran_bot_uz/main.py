import asyncio
import logging
import datetime
import aiohttp
import aiosqlite
from aiogram import Bot, Dispatcher
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from config import BOT_TOKEN
from handlers import start, search

logging.basicConfig(level=logging.INFO)

# Har kuni erta tongda barcha foydalanuvchilarga o'sha kunlik namoz vaqtlarini hisoblab yuboruvchi funksiya
async def send_prayer_notifications(bot: Bot):
    try:
        # Bazadagi barcha foydalanuvchilarning ID raqami va kordinatalarini olamiz
        async with aiosqlite.connect("data/quran.db") as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT user_id, latitude, longitude FROM users WHERE latitude IS NOT NULL") as cursor:
                users = await cursor.fetchall()
                
        if not users:
            return

        # Bugungi sana
        today_date = datetime.datetime.now().strftime("%d-%m-%Y")

        async with aiohttp.ClientSession() as session:
            for user in users:
                user_id = user['user_id']
                lat = user['latitude']
                lon = user['longitude']
                
                # Aladhan API orqali o'sha foydalanuvchi kordinatasiga mos vaqtlarni olamiz (Hanafiya: school=1, method=1)
                url = f"http://api.aladhan.com/v1/timings?latitude={lat}&longitude={lon}&method=1&school=1&tune=0,0,0,0,0,5,0,-18,0"
                
                try:
                    async with session.get(url, timeout=5) as response:
                        if response.status == 200:
                            data = await response.json(content_type=None)
                            if data['code'] == 200:
                                timings = data['data']['timings']
                                
                                # Bu yerda hozircha foydalanuvchiga erta tongda o'sha kunning to'liq namoz vaqtlarini eslatma sifatida yuboramiz
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
                                await asyncio.sleep(0.3) # Serverni qiynamaslik uchun kichik tanaffus
                except Exception:
                    pass
    except Exception as e:
        print(f"Bildirishnoma yuborishda xatolik: {e}")

async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    dp.include_router(start.router)
    dp.include_router(search.router)

    # Bazani tekshirish va yaratish
    async with aiosqlite.connect("data/quran.db") as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            latitude REAL,
            longitude REAL
        )
        """)
        await db.commit()

    # Scheduler (Avtomat vaqt bo'yicha ishlovchi tizim)
    scheduler = AsyncIOScheduler(timezone="Asia/Tashkent")
    
    # Har kuni tong soat 05:00 da o'sha kunlik namoz vaqtlarini yuborishga sozlaymiz
    scheduler.add_job(send_prayer_notifications, "cron", hour=5, minute=0, args=(bot,))
    scheduler.start()

    print("🚀 Bot muvaffaqiyatli ishga tushdi, baza va namoz vaqtlari bildirishnomasi sozlandi!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
