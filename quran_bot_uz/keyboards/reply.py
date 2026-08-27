from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_main_keyboard(script='latin'):
    if script == 'latin':
        kb = [
            [KeyboardButton(text="📖 Qur'on o'qish va tinglash")],
            [KeyboardButton(text="🕌 Namoz vaqtlari"), KeyboardButton(text="✨ Kun oyati")],
            [KeyboardButton(text="🤲 Duolar"), KeyboardButton(text="📿 Elektron tasbeh")],
            [KeyboardButton(text="🧭 Qibla"), KeyboardButton(text="🔍 Qidiruv")],
            [KeyboardButton(text="⚙️ Sozlamalar")]
        ]
    else:
        kb = [
            [KeyboardButton(text="📖 Қуръон ўқиш ва тинглаш")],
            [KeyboardButton(text="🕌 Намоз вақтлари"), KeyboardButton(text="✨ Кун ояти")],
            [KeyboardButton(text="🤲 Дуолар"), KeyboardButton(text="📿 Электрон тасбеҳ")],
            [KeyboardButton(text="🧭 Қибла"), KeyboardButton(text="🔍 Қидирув")],
            [KeyboardButton(text="⚙️ Созламалар")]
        ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
