import re
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from database.db_manager import get_verse, get_all_surahs, get_surah_info
from keyboards.inline import get_surahs_keyboard, get_verses_keyboard

router = Router()

@router.message(F.text == "📖 Suralar ro'yxati")
async def show_surahs_menu(message: Message):
    surahs = await get_all_surahs()
    await message.answer("Suralardan birini tanlang:", reply_markup=get_surahs_keyboard(surahs, page=1))

@router.callback_query(F.data.startswith("page:"))
async def change_surah_page(callback: CallbackQuery):
    page = int(callback.data.split(":")[1])
    surahs = await get_all_surahs()
    await callback.message.edit_reply_markup(reply_markup=get_surahs_keyboard(surahs, page=page))
    await callback.answer()

@router.callback_query(F.data.startswith("surah:"))
async def show_verses_menu(callback: CallbackQuery):
    surah_id = int(callback.data.split(":")[1])
    surah_info = await get_surah_info(surah_id)
    text = (f"📖 **{surah_info['surah_name_uz']} surasi** ({surah_info['surah_name_ar']})\n"
            f"Jami oyatlar soni: {surah_info['total_verses']} ta\n\n"
            f"Oyat raqamini tanlang yoki surani to'liq tinglang 👇")
    await callback.message.edit_text(text, reply_markup=get_verses_keyboard(surah_id, surah_info['total_verses'], page=1), parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data.startswith("vpage:"))
async def change_verses_page(callback: CallbackQuery):
    _, surah_id, page = callback.data.split(":")
    surah_id, page = int(surah_id), int(page)
    surah_info = await get_surah_info(surah_id)
    await callback.message.edit_reply_markup(reply_markup=get_verses_keyboard(surah_id, surah_info['total_verses'], page=page))
    await callback.answer()

@router.callback_query(F.data == "back_to_surahs")
async def back_to_surahs(callback: CallbackQuery):
    surahs = await get_all_surahs()
    await callback.message.edit_text("Suralardan birini tanlang:", reply_markup=get_surahs_keyboard(surahs, page=1))
    await callback.answer()

# OYAT TANLANGANDA QORILAR TUGMASI (4 TA QORI)
@router.callback_query(F.data.startswith("verse:"))
async def send_specific_verse(callback: CallbackQuery):
    _, surah_id, verse_id = callback.data.split(":")
    verse = await get_verse(int(surah_id), int(verse_id))
    text = (f"📖 **{verse['surah_name_uz']} surasi, {verse['verse_id']}-oyat**\n({verse['surah_name_ar']})\n\n"
            f"**Arabcha:**\n{verse['text_arabic']}\n\n**Ma'nosi:**\n{verse['text_uzbek']}")
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎙 Abdulbosit Abdussomad", callback_data=f"vq:abdulbasit:{surah_id}:{verse_id}")],
        [InlineKeyboardButton(text="🎙 M. Siddiq al-Minshaviy", callback_data=f"vq:minshawi:{surah_id}:{verse_id}")],
        [InlineKeyboardButton(text="🎙 Xalil Xusoriy", callback_data=f"vq:husary:{surah_id}:{verse_id}")],
        [InlineKeyboardButton(text="🎙 Mishari Rashid", callback_data=f"vq:mishary:{surah_id}:{verse_id}")]
    ])
    await callback.message.answer(text, reply_markup=kb, parse_mode="Markdown")
    await callback.answer()

# OYAT AUDIOSI MANBALARI (4 TA QORI)
@router.callback_query(F.data.startswith("vq:"))
async def send_verse_audio(callback: CallbackQuery):
    _, qari, surah_id, verse_id = callback.data.split(":")
    surah_id, verse_id = int(surah_id), int(verse_id)
    
    qari_paths = {
        "abdulbasit": "Abdul_Basit_Murattal_192kbps",
        "minshawi": "Minshawy_Murattal_128kbps",
        "husary": "Husary_128kbps",
        "mishary": "Alafasy_128kbps"
    }
    
    file_name = f"{surah_id:03d}{verse_id:03d}.mp3"
    audio_url = f"https://everyayah.com/data/{qari_paths[qari]}/{file_name}"
    
    await callback.answer("⏳ Oyat audiosi yuklanmoqda...")
    try:
        await callback.message.answer_audio(audio=audio_url)
    except Exception:
        await callback.message.answer(f"🎧 [Audioni eshitish]({audio_url})", parse_mode="Markdown")

# TO'LIQ SURA UCHUN QORI TANLASH MENYUSI (4 TA QORI)
@router.callback_query(F.data.startswith("full:"))
async def select_full_qari(callback: CallbackQuery):
    surah_id = int(callback.data.split(":")[1])
    surah_info = await get_surah_info(surah_id)
    
    text = f"📖 **{surah_info['surah_name_uz']} surasi**ni to'liq tinglash uchun qorini tanlang 👇"
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎙 Abdulbosit Abdussomad", callback_data=f"fq:abdulbasit:{surah_id}")],
        [InlineKeyboardButton(text="🎙 M. Siddiq al-Minshaviy", callback_data=f"fq:minshawi:{surah_id}")],
        [InlineKeyboardButton(text="🎙 Xalil Xusoriy", callback_data=f"fq:husary:{surah_id}")],
        [InlineKeyboardButton(text="🎙 Mishari Rashid", callback_data=f"fq:mishary:{surah_id}")],
        [InlineKeyboardButton(text="⬅️ Orqaga", callback_data=f"surah:{surah_id}")]
    ])
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
    await callback.answer()

# TO'LIQ SURA HAVOLALARI (4 TA QORI)
@router.callback_query(F.data.startswith("fq:"))
async def send_full_audio_link(callback: CallbackQuery):
    _, qari, surah_id = callback.data.split(":")
    surah_id = int(surah_id)
    surah_info = await get_surah_info(surah_id)
    
    qari_names = {
        "abdulbasit": "Abdulbosit Abdussomad",
        "minshawi": "Muhammad Siddiq al-Minshaviy",
        "husary": "Mahmud Xalil al-Xusoriy",
        "mishary": "Mishari Rashid al-Afasiy"
    }
    
    urls = {
        "abdulbasit": f"https://server7.mp3quran.net/basit/{surah_id:03d}.mp3",
        "minshawi": f"https://server10.mp3quran.net/minsh/{surah_id:03d}.mp3",
        "husary": f"https://server13.mp3quran.net/husr/{surah_id:03d}.mp3",
        "mishary": f"https://server8.mp3quran.net/afs/{surah_id:03d}.mp3"
    }
    
    text = (
        f"📖 **{surah_info['surah_name_uz']} surasi** (To'liq)\n"
        f"🎙 Qori: {qari_names[qari]}\n\n"
        f"🎧 To'g'ridan-to'g'ri tinglash yoki yuklab olish:"
    )
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌐 Onlayn tinglash / Yuklab olish", url=urls[qari])],
        [InlineKeyboardButton(text="⬅️ Qorilarga qaytish", callback_data=f"full:{surah_id}")]
    ])
    
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
    await callback.answer()

@router.message(F.text.regexp(r"^([1-9]|[1-9][0-9]|10[0-9]|11[0-4])$"))
async def search_surah_by_number(message: Message):
    surah_id = int(message.text.strip())
    surah_info = await get_surah_info(surah_id)
    text = (f"📖 **{surah_info['surah_name_uz']} surasi** ({surah_info['surah_name_ar']})\n"
            f"Jami oyatlar soni: {surah_info['total_verses']} ta\n\n"
            f"Oyat raqamini tanlang yoki surani to'liq tinglang 👇")
    await message.answer(text, reply_markup=get_verses_keyboard(surah_id, surah_info['total_verses'], page=1), parse_mode="Markdown")
