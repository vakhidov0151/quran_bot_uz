from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from keyboards.reply import main_menu

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message):
    welcome_text = (
        f"Assalomu alaykum, {message.from_user.full_name}!\n\n"
        "📖 **Qur'oni Karim botiga xush kelibsiz.**\n\n"
        "Quyidagi menyudan surani tanlang yoki qidirmoqchi bo'lgan sura va oyat raqamini yuboring.\n"
        "Misol uchun: `2:255` yoki `114:1`"
    )
    await message.answer(welcome_text, reply_markup=main_menu, parse_mode="Markdown")
    