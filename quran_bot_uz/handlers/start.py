import aiohttp
import aiosqlite
from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message
from keyboards.reply import get_main_keyboard
from database.db_manager import save_user_location, get_user_location
from config import DB_PATH

router = Router()

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
        
        # YANGILANISH: method=1 va school=1 qo'shildi (Hanafiya mazhabi uchun)
        url = f"http://api.aladhan.com/v1/timings?latitude={lat}&longitude={lon}&method=1&school=1"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                data = await response.json()
                
        if data['code'] == 200:
            timings = data['data']['timings']
            date = data['data']['date']['readable']
            
            text = (
                f"🕌 **Namoz vaqtlari**\n"
                f"🗓 Sana: {date}\n\n"
                f"🌅 Bomdod: {timings['Fajr']}\n"
                f"🌄 Quyosh: {timings['Sunrise']}\n"
                f"☀️ Peshin: {timings['Dhuhr']}\n"
                f"🌇 Asr: {timings['Asr']}\n"
                f"🌆 Shom: {timings['Maghrib']}\n"
                f"🌃 Xufton: {timings['Isha']}\n"
            )
            await message.answer(text, parse_mode="Markdown")
        else:
            await message.answer("Vaqtlarni olishda xatolik yuz berdi.")
    except Exception as e:
        await message.answer(f"Tizimda xatolik yuz berdi: {e}")

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
