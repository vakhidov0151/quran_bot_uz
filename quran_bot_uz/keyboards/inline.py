from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def get_audio_keyboard(surah_id: int, verse_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🎙 Sa'd al-G'omidiy", callback_data=f"audio:ghamdi:{surah_id}:{verse_id}"),
            InlineKeyboardButton(text="🎙 Xalil al-Husoriy", callback_data=f"audio:hussary:{surah_id}:{verse_id}")
        ]
    ])

def get_surahs_keyboard(surahs, page: int = 1, limit: int = 10):
    builder = InlineKeyboardBuilder()
    start_idx = (page - 1) * limit
    end_idx = start_idx + limit
    
    for surah in surahs[start_idx:end_idx]:
        builder.row(InlineKeyboardButton(
            text=f"{surah['surah_id']}. {surah['surah_name_uz']} ({surah['surah_name_ar']})",
            callback_data=f"surah:{surah['surah_id']}"
        ))
    
    nav_buttons = []
    if page > 1:
        nav_buttons.append(InlineKeyboardButton(text="⬅️ Oldingi", callback_data=f"page:{page-1}"))
    if end_idx < len(surahs):
        nav_buttons.append(InlineKeyboardButton(text="Keyingi ➡️", callback_data=f"page:{page+1}"))
    
    if nav_buttons:
        builder.row(*nav_buttons)
        
    return builder.as_markup()

def get_verses_keyboard(surah_id: int, total_verses: int, page: int = 1, limit: int = 30):
    builder = InlineKeyboardBuilder()
    
    builder.row(InlineKeyboardButton(text="▶️ To'liq surani tinglash", callback_data=f"full:{surah_id}"))
    
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
    if page > 1:
        nav_buttons.append(InlineKeyboardButton(text="⬅️ Oldingi", callback_data=f"vpage:{surah_id}:{page-1}"))
    if end_idx < total_verses:
        nav_buttons.append(InlineKeyboardButton(text="Keyingi ➡️", callback_data=f"vpage:{surah_id}:{page+1}"))
    
    # MANA SHU QATOR TUSHIB QOLGAN EDI:
    if nav_buttons:
        builder.row(*nav_buttons)
        
    builder.row(InlineKeyboardButton(text="🔙 Suralarga qaytish", callback_data="back_to_surahs"))
    
    return builder.as_markup()
