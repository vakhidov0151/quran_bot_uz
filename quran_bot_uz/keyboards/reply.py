from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_main_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📖 Qur'on o'qish va tinglash")],
            [KeyboardButton(text="🕌 Namoz vaqtlari"), KeyboardButton(text="✨ Kun oyati")],
            [KeyboardButton(text="🤲 Duolar", text_color=None), KeyboardButton(text="🔍 Qidiruv")],
            [KeyboardButton(text="📿 Elektron tasbeh")],
            [KeyboardButton(text="📍 Joylashuvni jo'natish", request_location=True)]
        ],
        resize_keyboard=True,
        input_field_placeholder="Kerakli bo'limni tanlang 👇"
    )
