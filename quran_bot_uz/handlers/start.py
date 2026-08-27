import math
import aiohttp
import os
from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from keyboards.reply import get_main_keyboard
from keyboards.inline import get_surahs_keyboard, get_verses_keyboard, get_audio_keyboard
from database.db_manager import (
    save_user_location, get_user_location, get_all_surahs, 
    get_surah_info, get_verse, get_all_duas, get_dua_by_id, search_verses_by_text,
    set_user_script, get_user_script, get_random_verse
)
from config import DB_PATH

router = Router()

@router.message(Command("testdb"))
async def test_db_handler(message: Message):
    import aiosqlite
    from config import DB_PATH
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute("SELECT name FROM sqlite_master WHERE type='table';") as cursor:
                tables = await cursor.fetchall()
                names = [t[0] for t in tables if t[0] != 'sqlite_sequence']
                
                text = f"✅ BAZA ULANDI: {DB_PATH}\n\nJadvallar ({len(names)} ta):\n\n"
                for name in names:
                    async with db.execute(f"PRAGMA table_info('{name}')") as c:
                        cols = await c.fetchall()
                        col_names = [col[1] for col in cols]
                        text += f"📁 **{name}**\nUstunlari: {', '.join(col_names)}\n\n"
                        
                await message.answer(text[:4000])
    except Exception as e:
        await message.answer(f"❌ Xato: {e}")

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
    await set_user_script(call.fromuser.id, script)
    lang = "Lotin yozuvi" if script == 'latin' else "Кирилл ёзуви"
    menu_text = "Pastdagi menyudan kerakli bo'limni tanlang:" if script == 'latin' else "Пастдаги менюдан керакли бўлимни танланг:"
    
    await call.message.delete()
    await call.message.answer(
        f"✅ Muvaffaqiyatli tanlandi: **{lang}**\n\n{menu_text}",
        reply_markup=get_main_keyboard(script),
        parse_mode="Markdown"
    )
    await call.answer()

@router.message(F.location)
async def handle_location(message: Message):
    script = await get_user_script(message.from_user.id)
    await save_user_location(message.from_user.id, message.location.latitude, message.location.longitude)
    msg_text = "✅ Joylashuvingiz muvaffaqiyatli saqlandi!\n\nEndi «🕌 Namoz vaqtlari» tugmasini bosing." if script == 'latin' else "✅ Жойлашувингиз муваффақиятли сақланди!\n\nЭнди «🕌 Намоз вақтлари» тугмасини босинг."
    await message.answer(msg_text, reply_markup=get_main_keyboard(script))

@router.message(F.text.in_({"🕌 Namoz vaqtlari", "🕌 Намоз вақтлари"}))
async def prayer_times_handler(message: Message):
    script = await get_user_script(message.from_user.id)
    location = await get_user_location(message.from_user.id)
    
    if not location or not location['latitude']:
        msg_text = "Siz hali joylashuvingizni yubormagansiz.\n\nIltimos, pastdagi «📍 Joylashuvni jo'natish» tugmasini bosing." if script == 'latin' else "Сиз ҳали жойлашувингизни юбормагансиз.\n\nИлтимос, пастдаги «📍 Жойлашувни жўнатиш» тугмасини босинг."
        await message.answer(msg_text)
        return

    try:
        lat = float(location['latitude'])
        lon = float(location['longitude'])
        
        # === ISLOM.UZ VAQTLARIGA TO'LIQ MOSLANGAN YANGI API HAQOLA ===
        aladhan_url = f"http://api.aladhan.com/v1/timings?latitude={lat}&longitude={lon}&method=99&methodSettings=18,null,15&tune=0,0,0,0,0,0,5,0,0&school=1"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(aladhan_url, timeout=8) as response:
                if response.status == 200:
                    data = await response.json()
                    timings = data['data']['timings']
                    h_date = data['data']['date']['hijri']
                    
                    if script == 'latin':
                        text = (f"🕌 **Namoz vaqtlari** (Joylashuvingiz bo'yicha)\n\n"
                                f"🗓 Milodiy: {data['data']['date']['readable']}\n"
                                f"🌙 Hijriy: {h_date['day']} {h_date['month']['en']}, {h_date['year']}-yil\n\n"
                                f"🌅 Bomdod: {timings['Fajr']}\n🌄 Quyosh: {timings['Sunrise']}\n"
                                f"☀️ Peshin: {timings['Dhuhr']}\n🌇 Asr: {timings['Asr']}\n"
                                f"🌆 Shom: {timings['Maghrib']}\n🌃 Xufton: {timings['Isha']}")
                    else:
                        text = (f"🕌 **Намоз вақтлари** (Жойлашувингиз бўйича)\n\n"
                                f"🗓 Милодий: {data['data']['date']['readable']}\n"
                                f"🌙 Ҳижрий: {h_date['day']} {h_date['month']['en']}, {h_date['year']}-йил\n\n"
                                f"🌅 Бомдод: {timings['Fajr']}\n🌄 Қуёш: {timings['Sunrise']}\n"
                                f"☀️ Пешин: {timings['Dhuhr']}\n🌇 Аср: {timings['Asr']}\n"
                                f"🌆 Шом: {timings['Maghrib']}\n🌃 Хуфтон: {timings['Isha']}")
                    await message.answer(text, parse_mode="Markdown")
                else:
                    await message.answer("API serverida xatolik yuz berdi." if script == 'latin' else "API серверида хатолик юз берди.")
    except Exception as e:
        await message.answer(f"Xatolik: {e}")

@router.message(F.text.in_({"✨ Kun oyati", "✨ Кун ояти"}))
async def daily_verse_handler(message: Message):
    try:
        script = await get_user_script(message.from_user.id)
        verse = await get_random_verse(script)
        if verse:
            title = "✨ **Kun oyati** ✨" if script == 'latin' else "✨ **Кун ояти** ✨"
            sura_text = "surasi" if script == 'latin' else "сураси"
            oyat_text = "oyat" if script == 'latin' else "оят"
            name = verse.get('surah_name_uz', verse.get('name_uz', ''))
            v_id = verse.get('verse_id', verse.get('id', ''))
            ar = verse.get('text_arabic', verse.get('arabic', ''))
            uz = verse.get('text_uzbek', verse.get('uzbek', verse.get('text', '')))
            
            text = f"{title}\n\n📖 **{name} {sura_text}, {v_id}-{oyat_text}**\n\n📝 {ar}\n\n🇺🇿 {uz}"
            await message.answer(text, parse_mode="Markdown")
        else:
            await message.answer("Bazada oyatlar topilmadi.")
    except Exception as e:
         await message.answer(f"Xato (Kun oyati): {e}")

@router.message(F.text.in_({"🤲 Duolar", "🤲 Дуолар"}))
async def duas_menu_handler(message: Message):
    script = await get_user_script(message.from_user.id)
    duas = await get_all_duas(script)
    builder = InlineKeyboardBuilder()
    for dua in duas:
        builder.row(InlineKeyboardButton(text=dua['title'], callback_data=f"dua:{dua['id']}"))
    msg_text = "🤲 **Kerakli duoni tanlang:**" if script == 'latin' else "🤲 **Керакли дуони танланг:**"
    await message.answer(msg_text, reply_markup=builder.as_markup(), parse_mode="Markdown")

@router.callback_query(F.data.startswith("dua:"))
async def dua_detail_callback(call: CallbackQuery):
    script = await get_user_script(call.from_user.id)
    dua = await get_dua_by_id(int(call.data.split(":")[1]), script)
    if dua:
        oqilishi = "O'qilishi" if script == 'latin' else "Ўқилиши"
        manosi = "Ma'nosi" if script == 'latin' else "Маъноси"
        text = f"🤲 **{dua['title']}**\n\n📝 {dua['text_arabic']}\n\n📖 {oqilishi}: _{dua['text_translit']}_\n\n🇺🇿 {manosi}: {dua['text_uzbek']}"
        btn_back = "🔙 Orqaga" if script == 'latin' else "🔙 Орқага"
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=btn_back, callback_data="back_to_duas")]])
        await call.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await call.answer()

@router.callback_query(F.data == "back_to_duas")
async def back_to_duas_callback(call: CallbackQuery):
    script = await get_user_script(call.from_user.id)
    duas = await get_all_duas(script)
    builder = InlineKeyboardBuilder()
    for dua in duas:
        builder.row(InlineKeyboardButton(text=dua['title'], callback_data=f"dua:{dua['id']}"))
    msg_text = "🤲 **Kerakli duoni tanlang:**" if script == 'latin' else "🤲 **Керакли дуони танланг:**"
    await call.message.edit_text(msg_text, reply_markup=builder.as_markup(), parse_mode="Markdown")
    await call.answer()

@router.message(F.text.in_({"🔍 Qidiruv", "🔍 Қидирув"}))
async def search_prompt_handler(message: Message):
    script = await get_user_script(message.from_user.id)
    text = "🔍 **Qidiruv**\n\nQidirmoqchi bo'lgan so'zingizni yuboring (masalan: _sabr_):" if script == 'latin' else "🔍 **Қидирув**\n\nҚидирмоқчи бўлган сўзингизни юборинг (масалан: _сабр_):"
    await message.answer(text, parse_mode="Markdown")

@router.message(F.text.in_({"📖 Qur'on o'qish va tinglash", "📖 Қуръон ўқиш ва тинглаш"}))
async def quran_read_handler(message: Message):
    try:
        script = await get_user_script(message.from_user.id)
        surahs = await get_all_surahs(script)
        if not surahs:
            await message.answer("Bazada suralar topilmadi.")
            return
        msg_text = "📖 **Kerakli surani tanlang:**" if script == 'latin' else "📖 **Керакли сурани танланг:**"
        await message.answer(msg_text, reply_markup=get_surahs_keyboard(surahs, page=1, script=script), parse_mode="Markdown")
    except Exception as e:
        await message.answer(f"Xatolik (Qur'on menyusi): {e}")

@router.callback_query(F.data.startswith("page:"))
async def surah_page_callback(call: CallbackQuery):
    script = await get_user_script(call.from_user.id)
    surahs = await get_all_surahs(script)
    await call.message.edit_reply_markup(reply_markup=get_surahs_keyboard(surahs, page=int(call.data.split(":")[1]), script=script))
    await call.answer()

@router.callback_query(F.data.startswith("surah:"))
async def surah_clicked_callback(call: CallbackQuery):
    try:
        script = await get_user_script(call.from_user.id)
        surah_id = int(call.data.split(":")[1])
        surah_info = await get_surah_info(surah_id, script)
        if surah_info:
            sura_text = "surasi" if script == 'latin' else "сураси"
            tanlang = "Kerakli oyatni tanlang:" if script == 'latin' else "Керакли оятни танланг:"
            name = surah_info.get('surah_name_uz', surah_info.get('name_uz', 'Sura'))
            tot_verses = surah_info.get('total_verses', surah_info.get('verses_count', 0))
            await call.message.edit_text(f"📖 **{name} {sura_text}**\n{tanlang}", 
                                         reply_markup=get_verses_keyboard(surah_id, tot_verses, page=1, script=script), parse_mode="Markdown")
    except Exception as e:
        await call.message.answer(f"Xato: {e}")
    await call.answer()

@router.callback_query(F.data.startswith("vpage:"))
async def verse_page_callback(call: CallbackQuery):
    script = await get_user_script(call.from_user.id)
    _, surah_id, page = call.data.split(":")
    surah_info = await get_surah_info(int(surah_id), script)
    tot_verses = surah_info.get('total_verses', surah_info.get('verses_count', 0))
    await call.message.edit_reply_markup(reply_markup=get_verses_keyboard(int(surah_id), tot_verses, page=int(page), script=script))
    await call.answer()

@router.callback_query(F.data == "back_to_surahs")
async def back_to_surahs_callback(call: CallbackQuery):
    script = await get_user_script(call.from_user.id)
    surahs = await get_all_surahs(script)
    msg_text = "📖 **Kerakli surani tanlang:**" if script == 'latin' else "📖 **Керакли сурани танланг:**"
    await call.message.edit_text(msg_text, reply_markup=get_surahs_keyboard(surahs, page=1, script=script), parse_mode="Markdown")
    await call.answer()

@router.callback_query(F.data.startswith("full:"))
async def full_surah_callback(call: CallbackQuery):
    try:
        script = await get_user_script(call.from_user.id)
        surah_id = int(call.data.split(":")[1])
        surah_info = await get_surah_info(surah_id, script)
        
        if surah_info:
            padded_id = str(surah_id).zfill(3)
            audio_url = f"https://server8.mp3quran.net/afs/{padded_id}.mp3"
            name = surah_info.get('surah_name_uz', surah_info.get('name_uz', f"{surah_id}-sura"))
            
            msg = f"🎧 **{name}** (To'liq)\n🎙 Mishary Rashid Alafasy" if script == 'latin' else f"🎧 **{name}** (Тўлиқ)\n🎙 Мишари Рашид Алафасий"
            
            await call.message.answer(
                f"{msg}\n\n📥 **Audio havola:** [Tinglash / Yuklab olish]({audio_url})", 
                parse_mode="Markdown"
            )
        else:
            await call.message.answer("Sura topilmadi." if script == 'latin' else "Сура топилмади.")
    except Exception as e:
        await call.message.answer(f"Xato (Audio): {e}")
    await call.answer()

@router.callback_query(F.data.startswith("verse:"))
async def verse_clicked_callback(call: CallbackQuery):
    try:
        script = await get_user_script(call.from_user.id)
        _, surah_id, verse_id = call.data.split(":")
        verse = await get_verse(int(surah_id), int(verse_id), script)
        if verse:
            sura_text = "surasi" if script == 'latin' else "сураси"
            oyat_text = "oyat" if script == 'latin' else "оят"
            name = verse.get('surah_name_uz', verse.get('name_uz', ''))
            v_id = verse.get('verse_id', verse.get('id', ''))
            ar = verse.get('text_arabic', verse.get('arabic', ''))
            uz = verse.get('text_uzbek', verse.get('uzbek', verse.get('text', '')))
            
            text = f"📖 **{name} {sura_text}, {v_id}-{oyat_text}**\n\n📝 {ar}\n\n🇺🇿 {uz}"
            await call.message.answer(text, reply_markup=get_audio_keyboard(int(surah_id), int(verse_id), script=script), parse_mode="Markdown")
    except Exception as e:
        await call.message.answer(f"Xato: {e}")
    await call.answer()

@router.callback_query(F.data.startswith("audio:"))
async def audio_callback(call: CallbackQuery):
    script = await get_user_script(call.from_user.id)
    _, qari, surah_id, verse_id = call.data.split(":")
    verse = await get_verse(int(surah_id), int(verse_id), script)
    if verse:
        sura_text = "surasi" if script == 'latin' else "сураси"
        oyat_text = "oyat" if script == 'latin' else "оят"
        name = verse.get('surah_name_uz', verse.get('name_uz', ''))
        v_id = verse.get('verse_id', verse.get('id', ''))
        audio_url = verse.get('audio_ghamdi', '') if qari == 'ghamdi' else verse.get('audio_hussary', '')
        
        if audio_url:
            await call.message.answer_audio(audio=audio_url, caption=f"🎙 {name} {sura_text}, {v_id}-{oyat_text}", parse_mode="Markdown")
        else:
            await call.message.answer("Audio topilmadi" if script == 'latin' else "Аудио топилмади")
    await call.answer()

@router.message(F.text.in_({"📿 Elektron tasbeh", "📿 Электрон тасбеҳ"}))
async def tasbih_start_handler(message: Message):
    script = await get_user_script(message.from_user.id)
    dhikrs = [{"text": "Субҳаналлоҳ" if script == 'cyrillic' else "Subhanalloh", "limit": 33}, 
              {"text": "Алҳамдулиллаҳ" if script == 'cyrillic' else "Alhamdulillah", "limit": 33}, 
              {"text": "Аллоҳу Акбар" if script == 'cyrillic' else "Allohu Akbar", "limit": 34}]
    btn_sanash = "📿 Санаш" if script == 'cyrillic' else "📿 Sanash"
    btn_reset = "🔄 Бошидан бошлаш" if script == 'cyrillic' else "🔄 Boshidan boshlash"
    title_text = "📿 **Электрон тасбеҳ**" if script == 'cyrillic' else "📿 **Elektron tasbeh**"
    soni_text = "Сони" if script == 'cyrillic' else "Soni"
    
    dhikr = dhikrs[0]
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"{btn_sanash} (0)", callback_data="tasbih:0:0")],
        [InlineKeyboardButton(text=btn_reset, callback_data="tasbih:reset:0")]
    ])
    await message.answer(f"{title_text}\n\n👉 **{dhikr['text']}**\n{soni_text}: 0 / {dhikr['limit']}", reply_markup=keyboard, parse_mode="Markdown")

@router.callback_query(F.data.startswith("tasbih:"))
async def tasbih_callback(call: CallbackQuery):
    script = await get_user_script(call.from_user.id)
    dhikrs = [{"text": "Субҳаналлоҳ" if script == 'cyrillic' else "Subhanalloh", "limit": 33}, 
              {"text": "Алҳамдулиллаҳ" if script == 'cyrillic' else "Alhamdulillah", "limit": 33}, 
              {"text": "Аллоҳу Акбар" if script == 'cyrillic' else "Allohu Akbar", "limit": 34}]
    btn_sanash = "📿 Санаш" if script == 'cyrillic' else "📿 Sanash"
    btn_reset = "🔄 Бошидан бошлаш" if script == 'cyrillic' else "🔄 Boshidan boshlash"
    title_text = "📿 **Электрон тасбеҳ**" if script == 'cyrillic' else "📿 **Elektron tasbeh**"
    soni_text = "Сони" if script == 'cyrillic' else "Soni"

    _, dhikr_index, count = call.data.split(":")
    if dhikr_index == "reset":
        index, current_count = 0, 0
    else:
        index, current_count = int(dhikr_index), int(count) + 1
        
    if current_count >= dhikrs[index]['limit']:
        index, current_count = index + 1, 0
        if index >= len(dhikrs): index = 0
            
    active_dhikr = dhikrs[index]
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"{btn_sanash} ({current_count})", callback_data=f"tasbih:{index}:{current_count}")],
        [InlineKeyboardButton(text=btn_reset, callback_data="tasbih:reset:0")]
    ])
    try:
        await call.message.edit_text(f"{title_text}\n\n👉 **{active_dhikr['text']}**\n{soni_text}: {current_count} / {active_dhikr['limit']}", reply_markup=keyboard, parse_mode="Markdown")
    except Exception: pass
    await call.answer()

@router.message(F.text & ~F.text.in_({"📖 Qur'on o'qish va tinglash", "📖 Қуръон ўқиш ва тинглаш", "🕌 Namoz vaqtlari", "🕌 Намоз вақтлари", "✨ Kun oyati", "✨ Кун ояти", "🤲 Duolar", "🤲 Дуолар", "🔍 Qidiruv", "🔍 Қидирув", "📿 Elektron tasbeh", "📿 Электрон тасбеҳ"}))
async def search_verses_handler(message: Message):
    try:
        keyword = message.text.strip()
        if len(keyword) < 2: return
            
        script = await get_user_script(message.from_user.id)
        
        verses = await search_verses_by_text(keyword, script)
        if not verses:
            verses = await search_verses_by_text(keyword.lower(), script)
            if not verses:
                verses = await search_verses_by_text(keyword.capitalize(), script)
        
        if not verses:
            msg = f"«{keyword}» bo'yicha hech narsa topilmadi." if script == 'latin' else f"«{keyword}» бўйича ҳеч нарса топилмади."
            await message.answer(msg)
            return
            
        text = f"🔍 **Natijalar ({len(verses)} ta):**\n\n" if script == 'latin' else f"🔍 **Натижалар ({len(verses)} та):**\n\n"
        oyat_text = "oyat" if script == 'latin' else "оят"
        
        for v in verses:
            name = v.get('surah_name_uz', v.get('name_uz', 'Sura'))
            v_id = v.get('verse_id', v.get('id', 0))
            uz_text = v.get('text_uzbek', v.get('uzbek', v.get('text', '')))
            text += f"📖 **{name}, {v_id}-{oyat_text}**\n{uz_text}\n\n---\n"
            
        if len(text) > 4000:
            text = text[:4000] + "...\n(Ko'p natija topildi / Кўп натижа топилди)"
            
        await message.answer(text, parse_mode="Markdown")
    except Exception as e:
        await message.answer(f"Xatolik (Qidiruv): {e}")
