import aiohttp
from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message
from keyboards.reply import get_main_keyboard
from database.db_manager import save_user_location, get_user_location

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message):
    welcome_text = (
        f"Assalomu alaykum, {message.from_user.full_name}!\n\n"
        "📖 **Qur'oni Karim botiga xush kelibsiz.**\n\n"
        "Quyidagi menyudan kerakli bo'limni tanlang yoki qidirmoqchi bo'lgan sura va oyat raqamini yuboring.\n"
        "Misol uchun: `2:255` yoki `114:1`"
    )
    await message.answer(welcome_text, reply_markup=get_main_keyboard(), parse_mode="Markdown")

@router.message(F.location)
async def handle_location(message: Message):
    lat = message.location.latitude
    lon = message.location.longitude
    user_id = message.from_user.id
    
    await save_user_location(user_id, lat, lon)
    
    text = (
        "✅ Joylashuvingiz muvaffaqiyatli saqlandi!\n\n"
        "Endi «🕌 Namoz vaqtlari» tugmasini bossangiz, aynan siz turgan hudud vaqti ko'rsatiladi.\n"
        "Boshqa shaharga borsangiz, shu tugmani yana bir marta bosib qo'yish kifoya."
    )
    await message.answer(text, reply_markup=get_main_keyboard())

# ==========================================
# YANGI: Namoz vaqtlarini ko'rsatuvchi qism
# ==========================================
@router.message(F.text == "🕌 Namoz vaqtlari")
async def prayer_times_handler(message: Message):
    user_id = message.from_user.id
    
    # 1. Bazadan foydalanuvchi qayerda turganini (manzilini) qidiramiz
    location = await get_user_location(user_id)
    
    # Agar manzil yo'q bo'lsa, yuborishni so'raymiz
    if not location:
        await message.answer("Siz hali joylashuvingizni yubormagansiz. Iltimos, pastdagi «📍 Joylashuvni jo'natish» tugmasini bosing.")
        return

    # Kordinatalarni ajratib olamiz
    lat = location['latitude']
    lon = location['longitude']
    
    # 2. Aladhan API tizimidan vaqtlarni so'raymiz
    url = f"http://api.aladhan.com/v1/timings?latitude={lat}&longitude={lon}&method=3"
    
    try:
        # Internatdan ma'lumotni yuklab olamiz
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                data = await response.json()
                
        # Agar javob to'g'ri kelsa (200), vaqtlarni ajratib xabar yasaymiz
        if data['code'] == 200:
            timings = data['data']['timings']
            date = data['data']['date']['readable']
            
            text = (
                f"🕌 **Namoz vaqtlari**\n"
                f"🗓 Sana: {date}\n\n"
                f"🌅 Bomdod: {timings['Fajr']}\n"
                f"🌄 Quyosh: {timings['Sunrise']}\n"
                f"☀️ Peshin: {timings['Dhuhr']}\n"
                f"🌇 Asr: {timings['Asr']}\n"
                f"🌆 Shom: {timings['Maghrib']}\n"
                f"🌃 Xufton: {timings['Isha']}\n"
            )
            await message.answer(text, parse_mode="Markdown")
        else:
            await message.answer("Kechirasiz, vaqtlarni olishda xatolik yuz berdi. Keyinroq urinib ko'ring.")
            
    except Exception as e:
        await message.answer("Internetga ulanishda xatolik yuz berdi. Iltimos, qayta urinib ko'ring.")
        print(f"API xatosi: {e}")
