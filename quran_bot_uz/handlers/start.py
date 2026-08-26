from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Tasbeh zikrlarini va ularning limitlarini belgilab qo'yamiz
DHIKRS = [
    {"text": "Subhanalloh (سُبْحَانَ ٱللَّٰهِ)", "limit": 33},
    {"text": "Alhamdulillah (ٱلْحَمْدُ لِلَّٰهِ)", "limit": 33},
    {"text": "Allohu Akbar (ٱللَّٰهُ أَكْبَرُ)", "limit": 34}
]

# 1. Asosiy menyudan "📿 Elektron tasbeh" bosilganda ishlaydi
@router.message(F.text == "📿 Elektron tasbeh")
async def tasbih_start_handler(message: Message):
    # Birinchi zikr bilan boshlaymiz (indeks: 0, soni: 0)
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

# 2. Tasbeh tugmasi bosilganda raqamlarni oshirish va zikrni almashtirish
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
    
    # Agar joriy zikr o'z limitiga yetsa (masalan, 33 taga), keyingi zikrga o'tamiz
    if current_count >= dhikr['limit']:
        index += 1
        current_count = 0
        # Agar hamma zikrlar tugasa, boshidan boshlaymiz
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
        pass # Bir xil matn bo'lib qolganda xato bermasligi uchun
    await call.answer()
