import math
import aiohttp
from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from keyboards.reply import get_main_keyboard
from keyboards.inline import get_surahs_keyboard, get_verses_keyboard, get_audio_keyboard
from database.db_manager import (
    save_user_location, get_user_location, get_all_surahs, 
    get_surah_info, get_verse, get_all_duas, get_dua_by_id, search_verses_by_text,
    set_user_script, get_user_script, get_random_verse
)

router = Router()

def get_nearest_region(lat, lon):
    regions = {
        "Toshkent": (41.3110, 69.2405), "Andijon": (40.7820, 72.3442), "Buxoro": (39.7747, 64.4286),
        "Farg'ona": (40.3863, 71.7161), "Jizzax": (40.1158, 67.8422), "Urganch": (41.5500, 60.6333),
        "Namangan": (41.0010, 71.6675), "Navoiy": (40.0844, 65.3791), "Qarshi": (38.8611, 65.7952),
        "Samarqand": (39.6270, 66.9749), "Guliston": (40.4897, 68.7842), "Termiz": (37.2241, 67.2783),
        "Nukus": (42.4619, 59.6166)
    }
    nearest_region, min_dist = "Toshkent", float('inf')
    for region, (r_lat, r_lon) in regions.items():
        dist = math.sqrt((lat - r_lat)**2 + (lon - r_lon)**2)
        if dist < min_dist:
            min_dist, nearest_region = dist, region
    return nearest_region

# 1. /START VA TIL TANLASH
@router.message(CommandStart())
async def cmd_start(message: Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🇺🇿 Lotincha (Lotin)", callback_data="set_script:latin"),
            InlineKeyboardButton(text="🇺🇿 Кириллча (Kirill)", callback_data="set_script:cyrillic")
        ]
    ])
    text = (
        f"Assalomu alaykum, {message.from_user.full_name}!\n\n"
        "📖 **Qur'oni Karim botiga xush kelibsiz.**\n\n"
        "Iltimos, o'zingizga qulay yozuv turini tanlang / Пожалуйста, выберите удобный шрифт:"
    )
    await message.answer(text, reply_markup=keyboard, parse_mode="Markdown")

@router.callback_query(F.data.startswith("set_script:"))
async def set_script_callback(call: CallbackQuery):
    script = call.data.split(":")[1]
    await set_user_script(call.from_user.id, script)
    
    lang = "Lotin yozuvi" if script == 'latin' else "Кирилл ёзуви"
    await call.message.delete()
    await call.message.answer(
        f"✅ Muvaffaqiyatli tanlandi: **{lang}**\n\nPastdagi menyudan kerakli bo'limni tanlang:",
        reply_markup=get_main_keyboard(),
        parse_mode="Markdown"
    )
    await call.answer()

# 2. LOKATSIYA VA NAMOZ VAQTLARI
@router.message(F.location)
async def handle_location(message: Message):
    await save_user_location(message.from_user.id, message.location.latitude, message.location.longitude)
    await message.answer("✅ Joylashuvingiz muvaffaqiyatli saqlandi!", reply_markup=get_main_keyboard())

@router.message(F.text == "🕌 Namoz vaqtlari")
async def prayer_times_handler(message: Message):
    location = await get_user_location(message.from_user.id)
    if not location or not location['latitude']:
        await message.answer("Siz hali joylashuvingizni yubormagansiz. Iltimos, pastdagi «📍 Joylashuvni jo'natish» tugmasini bosing.")
        return

    lat, lon = location['latitude'], location['longitude']
    region = get_nearest_region(lat, lon)
    islom_url = f"https://islomapi.uz/api/present/day?region={region}"
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(islom_url, timeout=5) as response:
                if response.status == 200:
                    data = await response.json(content_type=None)
                    times = data['times']
                    hijri = data.get('hijri', {})
                    text = (
                        f"🕌 **Namoz vaqtlari ({region})**\n🗓 Milodiy: {data.get('date', '')}\n"
                        f"🌙 Hijriy: {hijri.get('day', '')} {hijri.get('month', '')}, {hijri.get('year', '')}-yil\n\n"
                        f"🌅 Bomdod: {times.get('tong_saharlik', '')}\n🌄 Quyosh: {times.get('quyosh', '')}\n"
                        f"☀️ Peshin: {times.get('peshin', '')}\n🌇 Asr: {times.get('asr', '')}\n"
                        f"🌆 Shom: {times.get('shom_iftor', '')}\n🌃 Xufton: {times.get('hufton', '')}"
                    )
                    await message.answer(text, parse_mode="Markdown")
        except Exception:
            await message.answer("Vaqtlarni olishda xatolik yuz berdi.")

# 3. KUN OYATI
@router.message(F.text == "✨ Kun oyati")
async def daily_verse_handler(message: Message):
    script = await get_user_script(message.from_user.id)
    verse = await get_random_verse(script)
    if verse:
        text = f"✨ **Kun oyati** ✨\n\n📖 **{verse['surah_name_uz']} surasi, {verse['verse_id']}-oyat**\n\n📝 {verse['text_arabic']}\n\n🇺🇿 {verse['text_uzbek']}"
        await message.answer(text, parse_mode="Markdown")

# 4. DUOLAR
@router.message(F.text == "🤲 Duolar")
async def duas_menu_handler(message: Message):
    script = await get_user_script(message.from_user.id)
    duas = await get_all_duas(script)
    builder = InlineKeyboardBuilder()
    for dua in duas:
        builder.row(InlineKeyboardButton(text=dua['title'], callback_data=f"dua:{dua['id']}"))
    await message.answer("🤲 **Kerakli duoni tanlang:**", reply_markup=builder.as_markup(), parse_mode="Markdown")

@router.callback_query(F.data.startswith("dua:"))
async def dua_detail_callback(call: CallbackQuery):
    script = await get_user_script(call.from_user.id)
    dua = await get_dua_by_id(int(call.data.split(":")[1]), script)
    if dua:
        text = f"🤲 **{dua['title']}**\n\n📝 {dua['text_arabic']}\n\n📖 O'qilishi: _{dua['text_translit']}_\n\n🇺🇿 Ma'nosi: {dua['text_uzbek']}"
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_to_duas")]])
        await call.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await call.answer()

@router.callback_query(F.data == "back_to_duas")
async def back_to_duas_callback(call: CallbackQuery):
    script = await get_user_script(call.from_user.id)
    duas = await get_all_duas(script)
    builder = InlineKeyboardBuilder()
    for dua in duas:
        builder.row(InlineKeyboardButton(text=dua['title'], callback_data=f"dua:{dua['id']}"))
    await call.message.edit_text("🤲 **Kerakli duoni tanlang:**", reply_markup=builder.as_markup(), parse_mode="Markdown")
    await call.answer()

# 5. QIDIRUV
@router.message(F.text == "🔍 Qidiruv")
async def search_prompt_handler(message: Message):
    await message.answer("🔍 **Qidiruv**\n\nQidirmoqchi bo'lgan so'zingizni yuboring (masalan: _sabr_):", parse_mode="Markdown")

@router.message(F.text & ~F.text.in_({"📖 Qur'on o'qish va tinglash", "🕌 Namoz vaqtlari", "✨ Kun oyati", "🤲 Duolar", "🔍 Qidiruv", "📿 Elektron tasbeh"}))
async def search_verses_handler(message: Message):
    keyword = message.text.strip()
    if len(keyword) < 2: return
        
    script = await get_user_script(message.from_user.id)
    verses = await search_verses_by_text(keyword, script)
    
    if not verses:
        await message.answer(f"«{keyword}» bo'yicha hech narsa topilmadi.")
        return
        
    text = f"🔍 **Natijalar ({len(verses)} ta):**\n\n"
    for v in verses:
        text += f"📖 **{v['surah_name_uz']}, {v['verse_id']}-oyat**\n{v['text_uzbek']}\n\n---\n"
    await message.answer(text, parse_mode="Markdown")

# 6. QUR'ON O'QISH
@router.message(F.text == "📖 Qur'on o'qish va tinglash")
async def quran_read_handler(message: Message):
    script = await get_user_script(message.from_user.id)
    surahs = await get_all_surahs(script)
    await message.answer("📖 **Kerakli surani tanlang:**", reply_markup=get_surahs_keyboard(surahs, page=1), parse_mode="Markdown")

@router.callback_query(F.data.startswith("page:"))
async def surah_page_callback(call: CallbackQuery):
    script = await get_user_script(call.from_user.id)
    surahs = await get_all_surahs(script)
    await call.message.edit_reply_markup(reply_markup=get_surahs_keyboard(surahs, page=int(call.data.split(":")[1])))
    await call.answer()

@router.callback_query(F.data.startswith("surah:"))
async def surah_clicked_callback(call: CallbackQuery):
    script = await get_user_script(call.from_user.id)
    surah_id = int(call.data.split(":")[1])
    surah_info = await get_surah_info(surah_id, script)
    if surah_info:
        await call.message.edit_text(f"📖 **{surah_info['surah_name_uz']} surasi**\nKerakli oyatni tanlang:", 
                                     reply_markup=get_verses_keyboard(surah_id, surah_info['total_verses'], page=1), parse_mode="Markdown")
    await call.answer()

@router.callback_query(F.data.startswith("vpage:"))
async def verse_page_callback(call: CallbackQuery):
    script = await get_user_script(call.from_user.id)
    _, surah_id, page = call.data.split(":")
    surah_info = await get_surah_info(int(surah_id), script)
    await call.message.edit_reply_markup(reply_markup=get_verses_keyboard(int(surah_id), surah_info['total_verses'], page=int(page)))
    await call.answer()

@router.callback_query(F.data == "back_to_surahs")
async def back_to_surahs_callback(call: CallbackQuery):
    script = await get_user_script(call.from_user.id)
    surahs = await get_all_surahs(script)
    await call.message.edit_text("📖 **Kerakli surani tanlang:**", reply_markup=get_surahs_keyboard(surahs, page=1), parse_mode="Markdown")
    await call.answer()

@router.callback_query(F.data.startswith("verse:"))
async def verse_clicked_callback(call: CallbackQuery):
    script = await get_user_script(call.from_user.id)
    _, surah_id, verse_id = call.data.split(":")
    verse = await get_verse(int(surah_id), int(verse_id), script)
    if verse:
        text = f"📖 **{verse['surah_name_uz']} surasi, {verse['verse_id']}-oyat**\n\n📝 {verse['text_arabic']}\n\n🇺🇿 {verse['text_uzbek']}"
        await call.message.answer(text, reply_markup=get_audio_keyboard(int(surah_id), int(verse_id)), parse_mode="Markdown")
    await call.answer()

@router.callback_query(F.data.startswith("audio:"))
async def audio_callback(call: CallbackQuery):
    script = await get_user_script(call.from_user.id)
    _, qari, surah_id, verse_id = call.data.split(":")
    verse = await get_verse(int(surah_id), int(verse_id), script)
    if verse:
        audio_url = verse['audio_ghamdi'] if qari == 'ghamdi' else verse['audio_hussary']
        await call.message.answer_audio(audio=audio_url, caption=f"🎙 {verse['surah_name_uz']} surasi, {verse['verse_id']}-oyat", parse_mode="Markdown")
    await call.answer()

# 7. TASBEH
DHIKRS = [
    {"text": "Subhanalloh", "limit": 33}, {"text": "Alhamdulillah", "limit": 33}, {"text": "Allohu Akbar", "limit": 34}
]
@router.message(F.text == "📿 Elektron tasbeh")
async def tasbih_start_handler(message: Message):
    dhikr = DHIKRS[0]
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📿 Sanash (0)", callback_data="tasbih:0:0")],
        [InlineKeyboardButton(text="🔄 Boshidan boshlash", callback_data="tasbih:reset:0")]
    ])
    await message.answer(f"📿 **Elektron tasbeh**\n\n👉 **{dhikr['text']}**\nSoni: 0 / {dhikr['limit']}", reply_markup=keyboard, parse_mode="Markdown")

@router.callback_query(F.data.startswith("tasbih:"))
async def tasbih_callback(call: CallbackQuery):
    _, dhikr_index, count = call.data.split(":")
    if dhikr_index == "reset":
        index, current_count = 0, 0
    else:
        index, current_count = int(dhikr_index), int(count) + 1
        
    if current_count >= DHIKRS[index]['limit']:
        index, current_count = index + 1, 0
        if index >= len(DHIKRS): index = 0
            
    active_dhikr = DHIKRS[index]
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"📿 Sanash ({current_count})", callback_data=f"tasbih:{index}:{current_count}")],
        [InlineKeyboardButton(text="🔄 Boshidan boshlash", callback_data="tasbih:reset:0")]
    ])
    try:
        await call.message.edit_text(f"📿 **Elektron tasbeh**\n\n👉 **{active_dhikr['text']}**\nSoni: {current_count} / {active_dhikr['limit']}", reply_markup=keyboard, parse_mode="Markdown")
    except Exception:
        pass
    await call.answer()
