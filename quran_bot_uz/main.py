import asyncio
import logging
import datetime
from zoneinfo import ZoneInfo
import aiohttp
import aiosqlite
import os
from aiogram import Bot, Dispatcher
from aiogram.exceptions import TelegramRetryAfter, TelegramForbiddenError, TelegramBadRequest
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from config import BOT_TOKEN, DB_PATH, USER_DB_PATH
from handlers import start
from database.db_manager import init_user_db

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("main")

# TOSHKEN VAQTINI QAT'IY BELGILASH
TASHKENT_TZ = ZoneInfo("Asia/Tashkent")

# Namoz vaqti kirgandan keyin shu daqiqalar ichida xabar yuboriladi (aniq daqiqaga bog'lanmaymiz:
# foydalanuvchilar ko'p bo'lsa yoki tekshiruv kechiksa ham hech kim chetda qolmaydi)
NOTIFY_WINDOW_MINUTES = 20
# Telegram limiti ~30 xabar/soniya — biz 25 tadan yuboramiz
SEND_RATE_PER_SECOND = 25

PRAYER_NAMES = {
    "Fajr": ("Bomdod", "Бомдод"),
    "Dhuhr": ("Peshin", "Пешин"),
    "Asr": ("Asr", "Аср"),
    "Maghrib": ("Shom", "Шом"),
    "Isha": ("Xufton", "Хуфтон")
}

location_cache = {}      # loc_key -> {"date": "DD-MM-YYYY" (mahalliy sana), "timings": {...}, "timezone": "..."}
location_tz = {}         # loc_key -> vaqt mintaqasi
location_retry_at = {}   # loc_key -> API xato bergandan keyin qayta urinish vaqti
sent_by_date = {}        # mahalliy sana -> {(user_id, prayer_key)}

STARTED_AT = datetime.datetime.now(datetime.timezone.utc)
send_queue: asyncio.Queue = None


async def message_sender(bot: Bot):
    """Navbatdagi xabarlarni Telegram limitiga rioya qilib yuboradi."""
    while True:
        chat_id, text = await send_queue.get()
        try:
            for _attempt in range(3):
                try:
                    await bot.send_message(chat_id, text, parse_mode="Markdown")
                    break
                except TelegramRetryAfter as e:
                    await asyncio.sleep(e.retry_after + 1)
                except (TelegramForbiddenError, TelegramBadRequest):
                    break  # botni bloklagan yoki chat yo'q
                except Exception as e:
                    log.warning("Xabar yuborilmadi (%s): %s", chat_id, e)
                    break
        finally:
            send_queue.task_done()
        await asyncio.sleep(1 / SEND_RATE_PER_SECOND)


def _parse_timings(data):
    raw_timings = data['data']['timings']
    timings = {k: v.split(" ")[0][:5] for k, v in raw_timings.items()}
    m_time = datetime.datetime.strptime(timings['Maghrib'], "%H:%M")
    m_time += datetime.timedelta(minutes=5)
    timings['Maghrib'] = m_time.strftime("%H:%M")
    return timings


async def fetch_timings(session, loc_key, lat, lon):
    """Joylashuv uchun BUGUNGI (mahalliy sana bo'yicha) namoz vaqtlari. Keshlanadi."""
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    tz_name = location_tz.get(loc_key)
    local_date = datetime.datetime.now(ZoneInfo(tz_name)).strftime("%d-%m-%Y") if tz_name else None

    cached = location_cache.get(loc_key)
    if cached and local_date and cached['date'] == local_date:
        return cached
    if location_retry_at.get(loc_key, now_utc) > now_utc:
        return None

    params = f"latitude={lat}&longitude={lon}&method=99&methodSettings=15.5,null,15&school=1"
    try:
        for _ in range(2):
            path = f"timings/{local_date}" if local_date else "timings"
            async with session.get(f"https://api.aladhan.com/v1/{path}?{params}",
                                   timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status != 200:
                    raise RuntimeError(f"HTTP {response.status}")
                data = await response.json()
            tz_name = data['data']['meta']['timezone']
            location_tz[loc_key] = tz_name
            entry = {
                "date": data['data']['date']['gregorian']['date'],
                "timings": _parse_timings(data),
                "timezone": tz_name,
            }
            real_local_date = datetime.datetime.now(ZoneInfo(tz_name)).strftime("%d-%m-%Y")
            if entry["date"] == real_local_date:
                location_cache[loc_key] = entry
                return entry
            local_date = real_local_date  # birinchi so'rov boshqa kun uchun qaytdi — aniq sana bilan qayta so'raymiz
    except Exception as e:
        log.warning("Namoz vaqtini olib bo'lmadi (%s): %s", loc_key, e)
        location_retry_at[loc_key] = now_utc + datetime.timedelta(minutes=5)
    return None


def _prayer_message(p_names, script):
    p_name = p_names[0] if script == 'latin' else p_names[1]
    if script == 'latin':
        return f"🕌 **{p_name} vaqti kirdi!**\n\n_(Alloh ibodatlaringizni qabul qilsin!)_\n\n👉 @al\\_qurani\\_karim\\_bot"
    return f"🕌 **{p_name} вақти кирди!**\n\n_(Аллоҳ ибодатларингизни қабул қилсин!)_\n\n👉 @al\\_qurani\\_karim\\_bot"


async def check_and_send_prayer_notifications(bot: Bot):
    # Har daqiqada ishga tushadi. Vaqt har bir joylashuvning o'z mintaqasi bo'yicha hisoblanadi.
    try:
        async with aiosqlite.connect(USER_DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT user_id, latitude, longitude, script FROM users WHERE latitude IS NOT NULL") as cursor:
                users = await cursor.fetchall()

        if not users:
            return

        # Bir xil joydagilarni guruhlaymiz: API'ga har joy uchun bitta so'rov
        by_loc = {}
        for user in users:
            loc_key = f"{round(user['latitude'], 2)}_{round(user['longitude'], 2)}"
            by_loc.setdefault(loc_key, []).append(user)

        sem = asyncio.Semaphore(5)
        async with aiohttp.ClientSession() as session:
            async def _load(key, first_user):
                async with sem:
                    return key, await fetch_timings(session, key, first_user['latitude'], first_user['longitude'])
            results = await asyncio.gather(*(_load(k, v[0]) for k, v in by_loc.items()))

        skip_before = STARTED_AT - datetime.timedelta(minutes=2)  # qayta ishga tushganda takror yubormaslik uchun
        for loc_key, entry in results:
            if not entry:
                continue
            now_local = datetime.datetime.now(ZoneInfo(entry['timezone']))
            if entry['date'] != now_local.strftime("%d-%m-%Y"):
                continue
            sent = sent_by_date.setdefault(entry['date'], set())

            for p_key, p_names in PRAYER_NAMES.items():
                try:
                    hh, mm = map(int, entry['timings'][p_key].split(":"))
                except (KeyError, ValueError):
                    continue
                p_dt = now_local.replace(hour=hh, minute=mm, second=0, microsecond=0)
                if not (p_dt <= now_local < p_dt + datetime.timedelta(minutes=NOTIFY_WINDOW_MINUTES)):
                    continue
                if p_dt < skip_before:
                    continue
                for user in by_loc[loc_key]:
                    mark = (user['user_id'], p_key)
                    if mark in sent:
                        continue
                    sent.add(mark)
                    send_queue.put_nowait((user['user_id'], _prayer_message(p_names, user['script'])))

        # Eski kunlarning yozuvlarini tozalaymiz
        while len(sent_by_date) > 3:
            sent_by_date.pop(next(iter(sent_by_date)))

    except Exception as e:
        log.exception("Xatolik (Checker): %s", e)


async def check_and_send_juma_notifications(bot: Bot):
    try:
        from database.db_manager import get_random_verse

        async with aiosqlite.connect(USER_DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT user_id, script FROM users") as cursor:
                users = await cursor.fetchall()

        if not users:
            return

        # Oyat hamma uchun bir xil — har yozuv turi uchun bir marta tayyorlaymiz
        texts = {}
        for script in ('latin', 'cyrillic'):
            verse = await get_random_verse(script)
            if not verse:
                continue
            title = "✨ **Juma ayyomi muborak! Kun oyati** ✨" if script == 'latin' else "✨ **Жума айёми муборак! Кун ояти** ✨"
            sura_text, oyat_text = ("surasi", "oyat") if script == 'latin' else ("сураси", "оят")
            name = verse.get('surah_name_uz', verse.get('name_uz', ''))
            v_id = verse.get('verse_id', verse.get('id', ''))
            ar = verse.get('text_arabic', verse.get('arabic', ''))
            uz = verse.get('text_uzbek', verse.get('uzbek', verse.get('text', '')))
            texts[script] = f"{title}\n\n📖 **{name} {sura_text}, {v_id}-{oyat_text}**\n\n📝 {ar}\n\n🇺🇿 {uz}\n\n👉 @al\\_qurani\\_karim\\_bot"

        for user in users:
            text = texts.get(user['script'] or 'latin') or texts.get('latin')
            if text:
                send_queue.put_nowait((user['user_id'], text))

    except Exception as e:
        log.exception("Xatolik (Juma Checker): %s", e)


async def main():
    global send_queue
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    dp.include_router(start.router)

    if not os.path.exists(DB_PATH):
        print(f"DIQQAT: {DB_PATH} fayli topilmadi!")

    os.makedirs(os.path.dirname(USER_DB_PATH), exist_ok=True)
    await init_user_db()

    send_queue = asyncio.Queue()
    sender_task = asyncio.create_task(message_sender(bot))

    scheduler = AsyncIOScheduler(timezone=TASHKENT_TZ)
    scheduler.add_job(check_and_send_prayer_notifications, "cron", minute="*", args=(bot,),
                      max_instances=1, coalesce=True, misfire_grace_time=30)
    # Juma xabarnomasi: Har juma kuni soat 08:00 da (Toshkent vaqti bilan)
    scheduler.add_job(check_and_send_juma_notifications, "cron", day_of_week="fri", hour=8, minute=0, args=(bot,),
                      max_instances=1, coalesce=True, misfire_grace_time=600)
    scheduler.start()

    print("🚀 Bot muvaffaqiyatli ishga tushdi!")
    try:
        await dp.start_polling(bot)
    finally:
        sender_task.cancel()


if __name__ == "__main__":
    asyncio.run(main())
