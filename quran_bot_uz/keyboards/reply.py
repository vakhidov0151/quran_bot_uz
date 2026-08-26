from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_main_keyboard(script='latin'):
    if script == 'cyrillic':
        return ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="📖 Қуръон ўқиш ва тинглаш")],
                [KeyboardButton(text="🕌 Намоз вақтлари"), KeyboardButton(text="✨ Кун ояти")],
                [KeyboardButton(text="🤲 Дуолар"), KeyboardButton(text="🔍 Қидирув")],
                [KeyboardButton(text="📿 Электрон тасбеҳ")],
                [KeyboardButton(text="📍 Жойлашувни жўнатиш", request_location=True)]
            ],
            resize_keyboard=True,
            input_field_placeholder="Керакли бўлимни танланг 👇"
        )
    else:
        return ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="📖 Qur'on o'qish va tinglash")],
                [KeyboardButton(text="🕌 Namoz vaqtlari"), KeyboardButton(text="✨ Kun oyati")],
                [KeyboardButton(text="🤲 Duolar"), KeyboardButton(text="🔍 Qidiruv")],
                [KeyboardButton(text="📿 Elektron tasbeh")],
                [KeyboardButton(text="📍 Joylashuvni jo'natish", request_location=True)]
            ],
            resize_keyboard=True,
            input_field_placeholder="Kerakli bo'limni tanlang 👇"
        )
