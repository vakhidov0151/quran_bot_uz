import math
import aiohttp
import aiosqlite
from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from keyboards.reply import get_main_keyboard
from keyboards.inline import get_surahs_keyboard, get_verses_keyboard, get_audio_keyboard
from database.db_manager import save_user_location, get_user_location, get_all_surahs, get_surah_info, get_verse
from config import DB_PATH

router = Router()

# Hududlar kordinatasi (Namoz vaqtlari uchun)
def get_nearest_region(lat, lon):
    regions = {
        "Toshkent": (41.3110, 69.2405), "Andijon": (40.7820, 72.3442), "Buxoro": (39.7747, 64.4286),
        "Farg'ona": (40.3863, 71.7161), "Jizzax": (40.1158, 67.8422), "Urganch": (41.5500, 60.6333),
        "Namangan": (41.0010, 71.6675), "Navoiy": (40.0844, 65.3791), "Qarshi": (38.8611, 65.7952),
        "Samarqand": (39.6270, 66.9749), "Guliston": (40.4897, 68.7842), "Termiz": (37.2241, 67.2783),
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

# 1. /start buyrug'i
@router.message(CommandStart())
async def cmd_start(message: Message):
    welcome_text = (
        f"Assalomu alaykum, {message.from_user.full_name}!\n\n"
        "📖 **Qur'oni Karim botiga xush kelibsiz.**\n\n"
        "Pastdagi menyudan kerakli bo'limni tanlang:"
    )
    await message.answer(welcome_text, reply_markup=get_main_keyboard(), parse_mode="Markdown")

# 2. Lokatsiyani qabul qilish
@router.message(F.location)
async def handle_location(message: Message):
    try:
        lat = message.location.latitude
        lon = message.location.longitude
        user_id = message.from_user.id
        await save_user_location(user_id, lat, lon)
        text = "✅ Joylashuvingiz muvaffaqiyatli saqlandi!\n\nEndi «🕌 Namoz vaqtlari» tugmasini bossangiz, aynan siz turgan hudud vaqti ko'rsatiladi."
        await message.answer(text, reply_markup=get_main_keyboard())
    except Exception as e:
        await message.answer(f"Lokatsiyani saqlashda xatolik: {e}")

# 3. Namoz vaqtlari (Islom.uz + Aladhan zaxirasi va tune sozlamasi bilan)
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
        aladhan_url = f"http://api.aladhan.com/v1/timings?latitude={lat}&longitude={lon}&method=1&school=1&tune=0,0,0,0,0,5,0,-18,0"
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(islom_url, timeout=5) as response:
                    if response.status == 200:
                        data = await response.json(content_type=None)
                        if 'times' in data:
                            times = data['times']
                            text = (
                                f"🕌 **Namoz vaqtlari ({region})**\n🗓 Sana: {data.get('date', '')}\n\n"
                                f"🌅 Bomdod: {times.get('tong_saharlik', '')}\n🌄 Quyosh: {times.get('quyosh', '')}\n"
                                f"☀️ Peshin: {times.get('peshin', '')}\n🌇 Asr: {times.get('asr', '')}\n"
                                f"🌆 Shom (Iftor): {times.get('shom_iftor', '')}\n🌃 Xufton: {times.get('hufton', '')}\n\n"
                                f"*(Manba: O'zbekiston Musulmonlari Idorasi)*"
                            )
                            await message.answer(text, parse_mode="Markdown")
                            return 
            except Exception:
                pass 

            async with session.get(aladhan_url) as response:
                data = await response.json(content_type=None)
                if data['code'] == 200:
                    timings = data['data']['timings']
                    text = (
                        f"🕌 **Namoz vaqtlari (Zaxira - {region} ga moslangan)**\n🗓 Sana: {data['data']['date']['readable']}\n\n"
                        f"🌅 Bomdod: {timings['Fajr']}\n🌄 Quyosh: {timings['Sunrise']}\n"
                        f"☀️ Peshin: {timings['Dhuhr']}\n🌇 Asr: {timings['Asr']}\n"
                        f"🌆 Shom: {timings['Maghrib']}\n🌃 Xufton: {timings['Isha']}\n\n"
                        f"*(Eslatma: Zaxira tizimidan O'zbekistonga moslab olindi)*"
                    )
                    await message.answer(text, parse_mode="Markdown")
                else:
                    await message.answer("Vaqtlarni olishda xatolik yuz berdi.")
    except Exception as e:
        await message.answer(f"Xatolik: {e}")

# 4. Kun oyati
@router.message(F.text == "✨ Kun oyati")
async def daily_verse_handler(message: Message):
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM verses ORDER BY RANDOM() LIMIT 1") as cursor:
                verse = await cursor.fetchone()
        if verse:
            text = (f"✨ **Kun oyati** ✨\n\n📖 **{verse['surah_name_uz']} surasi, {verse['verse_id']}-oyat**\n\n"
                    f"📝 {verse['text_arabic']}\n\n🇺🇿 {verse['text_uzbek']}")
            await message.answer(text, parse_mode="Markdown")
    except Exception as e:
        await message.answer(f"Oyatni yuklashda xatolik: {e}")

# 5. Qur'on o'qish (Suralar ro'yxati)
@router.message(F.text == "📖 Qur'on o'qish va tinglash")
async def quran_read_handler(message: Message):
    try:
        surahs = await get_all_surahs()
        if not surahs:
            await message.answer("Bazada suralar topilmadi.")
            return
        keyboard = get_surahs_keyboard(surahs, page=1)
        await message.answer("📖 **Kerakli surani tanlang:**", reply_markup=keyboard, parse_mode="Markdown")
    except Exception as e:
        await message.answer(f"Xatolik: {e}")


# ==========================================
# 6. ELEKTRON TASBEH MANTIQI
# ==========================================
DHIKRS = [
    {"text": "Subhanalloh (سُبْحَانَ ٱللَّٰهِ)", "limit": 33},
    {"text": "Alhamdulillah (ٱلْحَمْدُ لِلَّٰهِ)", "limit": 33},
    {"text": "Allohu Akbar (ٱللَّٰهُ أَكْبَرُ)", "limit": 34}
]

@router.message(F.text == "📿 Elektron tasbeh")
async def tasbih_start_handler(message: Message):
    dhikr = DHIKRS[0]
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📿 Sanash (0)", callback_data="tasbih:0:0")],
        [InlineKeyboardButton(text="🔄 Boshidan boshlash", callback_data="tasbih:reset:0")]
    ])
    text = (
        f"📿 **Elektron tasbeh**\n\n"
        f"Hozirgi zikr:\n👉 **{dhikr['text']}**\n\n"
        f"Soni: 0 / {dhikr['limit']}"
    )
    await message.answer(text, reply_markup=keyboard, parse_mode="Markdown")

@router.callback_query(F.data.startswith("tasbih:"))
async def tasbih_callback(call: CallbackQuery):
    _, dhikr_index, count = call.data.split(":")
    if dhikr_index == "reset":
        index = 0
        current_count = 0
    else:
        index = int(dhikr_index)
        current_count = int(count) + 1
        
    dhikr = DHIKRS[index]
    if current_count >= dhikr['limit']:
        index += 1
        current_count = 0
        if index >= len(DHIKRS):
            index = 0
            
    active_dhikr = DHIKRS[index]
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"📿 Sanash ({current_count})", callback_data=f"tasbih:{index}:{current_count}")],
        [InlineKeyboardButton(text="🔄 Boshidan boshlash", callback_data="tasbih:reset:0")]
    ])
    text = (
        f"📿 **Elektron tasbeh**\n\n"
        f"Hozirgi zikr:\n👉 **{active_dhikr['text']}**\n\n"
        f"Soni: {current_count} / {active_dhikr['limit']}"
    )
    try:
        await call.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    except Exception:
        pass
    await call.answer()


# ==========================================
# INLINE TUGMALAR (Suralar va Oyatlar)
# ==========================================
@router.callback_query(F.data.startswith("page:"))
async def surah_page_callback(call: CallbackQuery):
    page = int(call.data.split(":")[1])
    surahs = await get_all_surahs()
    keyboard = get_surahs_keyboard(surahs, page=page)
    await call.message.edit_reply_markup(reply_markup=keyboard)
    await call.answer()

@router.callback_query(F.data.startswith("surah:"))
async def surah_clicked_callback(call: CallbackQuery):
    surah_id = int(call.data.split(":")[1])
    surah_info = await get_surah_info(surah_id)
    if surah_info:
        total_verses = surah_info['total_verses']
        keyboard = get_verses_keyboard(surah_id, total_verses, page=1)
        text = f"📖 **{surah_info['surah_name_uz']} surasi**\nJami oyatlar soni: {total_verses} ta\n\nKerakli oyatni tanlang:"
        await call.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await call.answer()

@router.callback_query(F.data.startswith("vpage:"))
async def verse_page_callback(call: CallbackQuery):
    _, surah_id, page = call.data.split(":")
    surah_id = int(surah_id)
    page = int(page)
    surah_info = await get_surah_info(surah_id)
    total_verses = surah_info['total_verses']
    keyboard = get_verses_keyboard(surah_id, total_verses, page=page)
    await call.message.edit_reply_markup(reply_markup=keyboard)
    await call.answer()

@router.callback_query(F.data == "back_to_surahs")
async def back_to_surahs_callback(call: CallbackQuery):
    surahs = await get_all_surahs()
    keyboard = get_surahs_keyboard(surahs, page=1)
    await call.message.edit_text("📖 **Kerakli surani tanlang:**", reply_markup=keyboard, parse_mode="Markdown")
    await call.answer()

@router.callback_query(F.data.startswith("verse:"))
async def verse_clicked_callback(call: CallbackQuery):
    _, surah_id, verse_id = call.data.split(":")
    surah_id = int(surah_id)
    verse_id = int(verse_id)
    verse = await get_verse(surah_id, verse_id)
    if verse:
        text = (
            f"📖 **{verse['surah_name_uz']} surasi, {verse['verse_id']}-oyat**\n\n"
            f"📝 {verse['text_arabic']}\n\n"
            f"🇺🇿 {verse['text_uzbek']}"
        )
        keyboard = get_audio_keyboard(surah_id, verse_id)
        await call.message.answer(text, reply_markup=keyboard, parse_mode="Markdown")
    await call.answer()

@router.callback_query(F.data.startswith("audio:"))
async def audio_callback(call: CallbackQuery):
    _, qari, surah_id, verse_id = call.data.split(":")
    surah_id = int(surah_id)
    verse_id = int(verse_id)
    verse = await get_verse(surah_id, verse_id)
    if verse:
        audio_url = verse['audio_ghamdi'] if qari == 'ghamdi' else verse['audio_hussary']
        await call.message.answer_audio(
            audio=audio_url,
            caption=f"🎙 {verse['surah_name_uz']} surasi, {verse['verse_id']}-oyat",
            parse_mode="Markdown"
        )
    await call.answer()
