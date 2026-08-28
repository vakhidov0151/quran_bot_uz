from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_main_keyboard(script='latin'):
    if script == 'latin':
        kb = [
            [KeyboardButton(text="📖 Qur'on o'qish va tinglash")],
            [KeyboardButton(text="🕌 Namoz vaqtlari"), KeyboardButton(text="🌙 Saharlik / Iftorlik")],
            [KeyboardButton(text="🤲 Duolar"), KeyboardButton(text="✨ Kun oyati")],
            [KeyboardButton(text="🧭 Qibla"), KeyboardButton(text="📿 Elektron tasbeh")],
            [KeyboardButton(text="💰 Zakot kalkulyatori"), KeyboardButton(text="✨ Asmo ul-Husna")],
            [KeyboardButton(text="🔍 Qidiruv"), KeyboardButton(text="⚙️ Sozlamalar")]
        ]
    else:
        kb = [
            [KeyboardButton(text="📖 Қуръон ўқиш ва тинглаш")],
            [KeyboardButton(text="🕌 Намоз вақтлари"), KeyboardButton(text="🌙 Саҳарлик / Ифторлик")],
            [KeyboardButton(text="🤲 Дуолар"), KeyboardButton(text="✨ Кун ояти")],
            [KeyboardButton(text="🧭 Қибла"), KeyboardButton(text="📿 Электрон тасбеҳ")],
            [KeyboardButton(text="💰 Закот калькулятори"), KeyboardButton(text="✨ Асмо ул-Ҳусна")],
            [KeyboardButton(text="🔍 Қидирув"), KeyboardButton(text="⚙️ Созламалар")]
        ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
