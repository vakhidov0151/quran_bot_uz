import math
import aiohttp
import aiosqlite
from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message
from keyboards.reply import get_main_keyboard
from database.db_manager import save_user_location, get_user_location
from config import DB_PATH

router = Router()

def get_nearest_region(lat, lon):
    regions = {
        "Toshkent": (41.3110, 69.2405),
        "Andijon": (40.7820, 72.3442),
        "Buxoro": (39.7747, 64.4286),
        "Farg'ona": (40.3863, 71.7161),
        "Jizzax": (40.1158, 67.8422),
        "Urganch": (41.5500, 60.6333),
        "Namangan": (41.0010, 71.6675),
        "Navoiy": (40.0844, 65.3791),
        "Qarshi": (38.8611, 65.7952),
        "Samarqand": (39.6270, 66.9749),
        "Guliston": (40.4897, 68.7842),
        "Termiz": (37.2241, 67.2783),
        "Nukus": (42.4619, 59.6166)
    }
    
    nearest_region = "Toshkent"
    min_dist = float('inf')
    
    for region, (r_lat, r_lon) in regions.items():
        dist = math.sqrt((lat - r_lat)**2 + (lon - r_lon)**2)
        if dist < min_dist:
            min_dist = dist
            nearest_region = region
            
    return nearest_region

@router.message(CommandStart())
async def cmd_start(message: Message):
    welcome_text = (
        f"Assalomu alaykum, {message.from_user.full_name}!\n\n"
        "📖 **Qur'oni Karim botiga xush kelibsiz.**\n\n"
        "Pastdagi menyudan kerakli bo'limni tanlang:"
    )
    await message.answer(welcome_text, reply_markup=get_main_keyboard(), parse_mode="Markdown")

@router.message(F.location)
async def handle_location(message: Message):
    try:
        lat = message.location.latitude
        lon = message.location.longitude
        user_id = message.from_user.id
        
        await save_user_location(user_id, lat, lon)
        
        text = (
            "✅ Joylashuvingiz muvaffaqiyatli saqlandi!\n\n"
            "Endi «🕌 Namoz vaqtlari» tugmasini bossangiz, aynan siz turgan hudud vaqti ko'rsatiladi."
        )
        await message.answer(text, reply_markup=get_main_keyboard())
    except Exception as e:
        await message.answer(f"Lokatsiyani saqlashda xatolik yuz berdi: {e}")

# ==========================================
# YANGILANISH: Aqlli zaxira (Fallback) tizimi
# ==========================================
@router.message(F.text == "🕌 Namoz vaqtlari")
async def prayer_times_handler(message: Message):
    try:
        user_id = message.from_user.id
        location = await get_user_location(user_id)
        
        if not location:
            await message.answer("Siz hali joylashuvingizni yubormagansiz. Iltimos, pastdagi «📍 Joylashuvni jo'natish» tugmasini bosing.")
            return

        lat = location['latitude']
        lon = location['longitude']
        region = get_nearest_region(lat, lon)
        
        islom_url = f"https://islomapi.uz/api/present/day?region={region}"
        # Zaxira uchun Aladhan manzili (Hanafiya: school=1, Markaziy Osiyo: method=1)
        aladhan_url = f"http://api.aladhan.com/v1/timings?latitude={lat}&longitude={lon}&method=1&school=1"
        
        async with aiohttp.ClientSession() as session:
            # 1-URINISH: Islom.uz saytidan olishga harakat qilamiz
            try:
                async with session.get(islom_url, timeout=5) as response:
                    # Agar server 200 (Yaxshi) degan javob qilsa, islom.uz dan olamiz
                    if response.status == 200:
                        data = await response.json(content_type=None)
                        if 'times' in data:
                            times = data['times']
                            text = (
                                f"🕌 **Namoz vaqtlari ({region})**\n"
                                f"🗓 Sana: {data.get('date', '')}\n\n"
                                f"🌅 Bomdod: {times.get('tong_saharlik', '')}\n"
                                f"🌄 Quyosh: {times.get('quyosh', '')}\n"
                                f"☀️ Peshin: {times.get('peshin', '')}\n"
                                f"🌇 Asr: {times.get('asr', '')}\n"
                                f"🌆 Shom (Iftor): {times.get('shom_iftor', '')}\n"
                                f"🌃 Xufton: {times.get('hufton', '')}\n\n"
                                f"*(Manba: O'zbekiston Musulmonlari Idorasi)*"
                            )
                            await message.answer(text, parse_mode="Markdown")
                            return # Ish bajarildi, shu yerda to'xtatamiz
            except Exception:
                pass # Agar Islom.uz dan xato kelsa, indamay keyingi qadamga o'tamiz

            # 2-URINISH: Agar Islom.uz o'chiq bo'lsa, avtomat Aladhanni ishga tushiramiz
            async with session.get(aladhan_url) as response:
                data = await response.json(content_type=None)
                if data['code'] == 200:
                    timings = data['data']['timings']
                    date = data['data']['date']['readable']
                    text = (
                        f"🕌 **Namoz vaqtlari (Zaxira)**\n"
                        f"🗓 Sana: {date}\n\n"
                        f"🌅 Bomdod: {timings['Fajr']}\n"
                        f"🌄 Quyosh: {timings['Sunrise']}\n"
                        f"☀️ Peshin: {timings['Dhuhr']}\n"
                        f"🌇 Asr: {timings['Asr']}\n"
                        f"🌆 Shom: {timings['Maghrib']}\n"
                        f"🌃 Xufton: {timings['Isha']}\n\n"
                        f"*(Eslatma: islom.uz serverida vaqtinchalik uzilish bo'lgani uchun vaqtlar xalqaro tizimdan olindi)*"
                    )
                    await message.answer(text, parse_mode="Markdown")
                else:
                    await message.answer("Ikkala serverdan ham vaqtlarni olishda xatolik yuz berdi.")
                    
    except Exception as e:
        await message.answer(f"Tizimda kutilmagan xatolik: {e}")

@router.message(F.text == "✨ Kun oyati")
async def daily_verse_handler(message: Message):
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM verses ORDER BY RANDOM() LIMIT 1") as cursor:
                verse = await cursor.fetchone()
        
        if verse:
            text = (
                f"✨ **Kun oyati** ✨\n\n"
                f"📖 **{verse['surah_name_uz']} surasi, {verse['verse_id']}-oyat**\n\n"
                f"📝 {verse['text_arabic']}\n\n"
                f"🇺🇿 {verse['text_uzbek']}"
            )
            await message.answer(text, parse_mode="Markdown")
        else:
            await message.answer("Hozircha bazada oyatlar topilmadi.")
    except Exception as e:
        await message.answer(f"Oyatni yuklashda xatolik yuz berdi: {e}")

@router.message(F.text == "📖 Qur'on o'qish va tinglash")
async def quran_read_handler(message: Message):
    await message.answer(
        "Qur'on o'qish uchun sura va oyat raqamini yuboring.\n"
        "Misol uchun: `2:255` yoki `114:1`", 
        parse_mode="Markdown"
    )
