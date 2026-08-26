from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def get_audio_keyboard(surah_id: int, verse_id: int, script='latin'):
    ghamdi = "🎙 Саъд ал-Ғомидий" if script == 'cyrillic' else "🎙 Sa'd al-G'omidiy"
    hussary = "🎙 Халил ал-Ҳусорий" if script == 'cyrillic' else "🎙 Xalil al-Husoriy"
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=ghamdi, callback_data=f"audio:ghamdi:{surah_id}:{verse_id}"),
            InlineKeyboardButton(text=hussary, callback_data=f"audio:hussary:{surah_id}:{verse_id}")
        ]
    ])

def get_surahs_keyboard(surahs, page: int = 1, limit: int = 10, script='latin'):
    builder = InlineKeyboardBuilder()
    start_idx = (page - 1) * limit
    end_idx = start_idx + limit
    
    for surah in surahs[start_idx:end_idx]:
        # Xatoni oldini olish: arabcha nomi bazada bo'lmasa xato bermaydi
        ar_name = surah.get('surah_name_ar', '')
        surah_text = f"{surah['surah_id']}. {surah.get('surah_name_uz', '')}"
        if ar_name:
            surah_text += f" ({ar_name})"
            
        builder.row(InlineKeyboardButton(text=surah_text, callback_data=f"surah:{surah['surah_id']}"))
    
    nav_buttons = []
    btn_prev = "⬅️ Олдинги" if script == 'cyrillic' else "⬅️ Oldingi"
    btn_next = "Кейинги ➡️" if script == 'cyrillic' else "Keyingi ➡️"
    
    if page > 1:
        nav_buttons.append(InlineKeyboardButton(text=btn_prev, callback_data=f"page:{page-1}"))
    if end_idx < len(surahs):
        nav_buttons.append(InlineKeyboardButton(text=btn_next, callback_data=f"page:{page+1}"))
    
    if nav_buttons:
        builder.row(*nav_buttons)
        
    return builder.as_markup()

def get_verses_keyboard(surah_id: int, total_verses: int, page: int = 1, limit: int = 30, script='latin'):
    builder = InlineKeyboardBuilder()
    
    btn_full = "▶️ Тўлиқ сурани тинглаш" if script == 'cyrillic' else "▶️ To'liq surani tinglash"
    builder.row(InlineKeyboardButton(text=btn_full, callback_data=f"full:{surah_id}"))
    
    start_idx = (page - 1) * limit + 1
    end_idx = min(start_idx + limit - 1, total_verses)
    
    row = []
    for v in range(start_idx, end_idx + 1):
        row.append(InlineKeyboardButton(text=str(v), callback_data=f"verse:{surah_id}:{v}"))
        if len(row) == 5:
            builder.row(*row)
            row = []
    if row:
        builder.row(*row)
            
    nav_buttons = []
    btn_prev = "⬅️ Олдинги" if script == 'cyrillic' else "⬅️ Oldingi"
    btn_next = "Кейинги ➡️" if script == 'cyrillic' else "Keyingi ➡️"
    btn_back = "🔙 Сураларга қайтиш" if script == 'cyrillic' else "🔙 Suralarga qaytish"

    if page > 1:
        nav_buttons.append(InlineKeyboardButton(text=btn_prev, callback_data=f"vpage:{surah_id}:{page-1}"))
    if end_idx < total_verses:
        nav_buttons.append(InlineKeyboardButton(text=btn_next, callback_data=f"vpage:{surah_id}:{page+1}"))
    
    if nav_buttons:
        builder.row(*nav_buttons)
        
    builder.row(InlineKeyboardButton(text=btn_back, callback_data="back_to_surahs"))
    
    return builder.as_markup()
