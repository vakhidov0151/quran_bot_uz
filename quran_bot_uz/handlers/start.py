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
    msg_text = "✅ Joylashuvingiz muvaffaqiyatli saqlandi!" if script == 'latin' else "✅ Жойлашувингиз муваффақиятли сақланди!"
    await message.answer(msg_text, reply_markup=get_main_keyboard(script))

@router.message(F.text.in_({"🕌 Namoz vaqtlari", "🕌 Намоз вақтлари"}))
async def prayer_times_handler(message: Message):
    script = await get_user_script(message.from_user.id)
    location = await get_user_location(message.from_user.id)
    if not location or not location['latitude']:
        msg_text = "Siz hali joylashuvingizni yubormagansiz." if script == 'latin' else "Сиз ҳали жойлашувингизни юбормагансиз."
        await message.answer(msg_text)
        return

    lat, lon = location['latitude'], location['longitude']
    region = get_nearest_region(lat, lon)
    islom_url = f"https://islomapi.uz/api/present/day?region={region}"
    aladhan_url = f"http://api.aladhan.com/v1/timings?latitude={lat}&longitude={lon}&method=1&school=1&tune=0,0,0,0,0,5,0,-18,0"
    
    async with aiohttp.ClientSession() as session:
        # ZAXIRA 1: islomapi
        try:
            async with session.get(islom_url, timeout=3) as response:
                if response.status == 200:
                    data = await response.json(content_type=None)
                    times = data['times']
                    hijri = data.get('hijri', {})
                    if script == 'latin':
                        text = (f"🕌 **Namoz vaqtlari ({region})**\n🗓 Milodiy: {data.get('date', '')}\n"
                                f"🌙 Hijriy: {hijri.get('day', '')} {hijri.get('month', '')}, {hijri.get('year', '')}-yil\n\n"
                                f"🌅 Bomdod: {times.get('tong_saharlik', '')}\n🌄 Quyosh: {times.get('quyosh', '')}\n"
                                f"☀️ Peshin: {times.get('peshin', '')}\n🌇 Asr: {times.get('asr', '')}\n"
                                f"🌆 Shom: {times.get('shom_iftor', '')}\n🌃 Xufton: {times.get('hufton', '')}")
                    else:
                        text = (f"🕌 **Намоз вақтлари ({region})**\n🗓 Милодий: {data.get('date', '')}\n"
                                f"🌙 Ҳижрий: {hijri.get('day', '')} {hijri.get('month', '')}, {hijri.get('year', '')}-йил\n\n"
                                f"🌅 Бомдод: {times.get('tong_saharlik', '')}\n🌄 Қуёш: {times.get('quyosh', '')}\n"
                                f"☀️ Пешин: {times.get('peshin', '')}\n🌇 Аср: {times.get('asr', '')}\n"
                                f"🌆 Шом: {times.get('shom_iftor', '')}\n🌃 Хуфтон: {times.get('hufton', '')}")
                    await message.answer(text, parse_mode="Markdown")
                    return
        except: pass

        # ZAXIRA 2: Aladhan API (Islomapi ishlamay qolganda)
        try:
            async with session.get(aladhan_url, timeout=4) as response:
                if response.status == 200:
                    data = await response.json()
                    timings = data['data']['timings']
                    h_date = data['data']['date']['hijri']
                    
                    if script == 'latin':
                        text = (f"🕌 **Namoz vaqtlari (Zaxira - {region})**\n🗓 Milodiy: {data['data']['date']['readable']}\n"
                                f"🌙 Hijriy: {h_date['day']} {h_date['month']['en']}, {h_date['year']}-yil\n\n"
                                f"🌅 Bomdod: {timings['Fajr']}\n🌄 Quyosh: {timings['Sunrise']}\n"
                                f"☀️ Peshin: {timings['Dhuhr']}\n🌇 Asr: {timings['Asr']}\n"
                                f"🌆 Shom: {timings['Maghrib']}\n🌃 Xufton: {timings['Isha']}")
                    else:
                        text = (f"🕌 **Намоз вақтлари (Захира - {region})**\n🗓 Милодий: {data['data']['date']['readable']}\n"
                                f"🌙 Ҳижрий: {h_date['day']} {h_date['month']['en']}, {h_date['year']}-йил\n\n"
                                f"🌅 Бомдод: {timings['Fajr']}\n🌄 Қуёш: {timings['Sunrise']}\n"
                                f"☀️ Пешин: {timings['Dhuhr']}\n🌇 Аср: {timings['Asr']}\n"
                                f"🌆 Шом: {timings['Maghrib']}\n🌃 Хуфтон: {timings['Isha']}")
                    await message.answer(text, parse_mode="Markdown")
                    return
        except:
            await message.answer("Xatolik: Tarmoq uzildi" if script == 'latin' else "Хатолик: Тармоқ узилди")

@router.message(F.text.in_({"✨ Kun oyati", "✨ Кун ояти"}))
async def daily_verse_handler(message: Message):
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
        msg_text = "📖 **Kerakli surani tanlang:**" if script == 'latin' else "📖 **Керакли сурани танланг:**"
        await message.answer(msg_text, reply_markup=get_surahs_keyboard(surahs, page=1, script=script), parse_mode="Markdown")
    except Exception as e:
        await message.answer(f"Xatolik: {e}")

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
    except: pass
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

@router.callback_query(F.data.startswith("verse:"))
async def verse_clicked_callback(call: CallbackQuery):
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
    keyword = message.text.strip()
    if len(keyword) < 2: return
        
    script = await get_user_script(message.from_user.id)
    
    # Katta yoki kichik harfda yozilganini inobatga olib izlash
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
