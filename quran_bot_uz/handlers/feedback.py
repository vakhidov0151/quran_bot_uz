import html
import logging
from aiogram import Router, F
from aiogram.dispatcher.event.bases import SkipHandler
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from cachetools import TTLCache
from config import ADMIN_IDS
from database.db_manager import get_user_script, save_feedback_message, get_feedback_user
from keyboards.reply import get_main_keyboard

router = Router()
log = logging.getLogger("feedback")

FEEDBACK_BUTTONS = {"✉️ Taklif va shikoyat", "✉️ Таклиф ва шикоят"}
FEEDBACK_TYPES = {
    "complaint": ("⚠️ Shikoyat", "⚠️ Шикоят"),
    "idea": ("💡 Taklif", "💡 Таклиф"),
    "question": ("❓ Savol", "❓ Савол"),
}
COOLDOWN_SECONDS = 30  # bir foydalanuvchi adminni xabarga ko'mib yubormasligi uchun
last_sent = TTLCache(maxsize=20000, ttl=COOLDOWN_SECONDS)

# Asosiy menyu tugmalari: xabar yozish paytida bosilsa, murojaat bekor bo'ladi va tugma ishlaydi
MENU_BUTTONS = {btn.text for script in ('latin', 'cyrillic')
                for row in get_main_keyboard(script).keyboard for btn in row}


class FeedbackState(StatesGroup):
    waiting_for_message = State()


def tr(script, latin, cyrillic):
    return latin if script == 'latin' else cyrillic


def build_type_menu(script):
    text = tr(script, "✉️ <b>Taklif va shikoyat</b>\n\nMurojaat turini tanlang:",
              "✉️ <b>Таклиф ва шикоят</b>\n\nМурожаат турини танланг:")
    idx = 0 if script == 'latin' else 1
    rows = [[InlineKeyboardButton(text=names[idx], callback_data=f"fb_type:{key}")] for key, names in FEEDBACK_TYPES.items()]
    rows.append([InlineKeyboardButton(text=tr(script, "❌ Bekor qilish", "❌ Бекор қилиш"), callback_data="fb_cancel")])
    return text, InlineKeyboardMarkup(inline_keyboard=rows)


@router.message(Command("aloqa"))
@router.message(F.text.in_(FEEDBACK_BUTTONS))
async def feedback_start(message: Message, state: FSMContext):
    await state.clear()
    script = await get_user_script(message.from_user.id)
    text, kb = build_type_menu(script)
    await message.answer(text, reply_markup=kb, parse_mode="HTML")


@router.callback_query(F.data == "fb_menu")
async def feedback_menu_callback(call: CallbackQuery, state: FSMContext):
    await state.clear()
    script = await get_user_script(call.from_user.id)
    text, kb = build_type_menu(script)
    await call.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await call.answer()


@router.callback_query(F.data.startswith("fb_type:"))
async def feedback_type_selected(call: CallbackQuery, state: FSMContext):
    kind = call.data.split(":")[1]
    if kind not in FEEDBACK_TYPES:
        await call.answer()
        return
    script = await get_user_script(call.from_user.id)
    await state.set_state(FeedbackState.waiting_for_message)
    await state.update_data(feedback_type=kind)
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=tr(script, "❌ Bekor qilish", "❌ Бекор қилиш"), callback_data="fb_cancel")
    ]])
    await call.message.edit_text(
        tr(script, "✍️ Xabaringizni yozing. Matn, rasm, video yoki ovozli xabar yuborishingiz mumkin:",
           "✍️ Хабарингизни ёзинг. Матн, расм, видео ёки овозли хабар юборишингиз мумкин:"),
        reply_markup=kb)
    await call.answer()


@router.callback_query(F.data == "fb_cancel")
async def feedback_cancel(call: CallbackQuery, state: FSMContext):
    await state.clear()
    script = await get_user_script(call.from_user.id)
    await call.message.delete()
    await call.answer(tr(script, "Bekor qilindi", "Бекор қилинди"))


@router.message(StateFilter(FeedbackState.waiting_for_message))
async def feedback_message(message: Message, state: FSMContext):
    user_id = message.from_user.id
    script = await get_user_script(user_id)

    if message.text in MENU_BUTTONS or (message.text or "").startswith('/'):
        await state.clear()
        raise SkipHandler  # tugma yoki buyruq odatdagidek ishlasin

    if user_id in last_sent:
        await message.answer(tr(script, "⏳ Biroz kuting va qayta yuboring.", "⏳ Бироз кутинг ва қайта юборинг."))
        return

    data = await state.get_data()
    await state.clear()
    if not ADMIN_IDS:
        log.error("ADMIN_IDS o'rnatilmagan: murojaat yetkazilmadi")
        await message.answer(tr(script, "Hozircha murojaat qabul qilinmayapti. Keyinroq urinib ko'ring.",
                                "Ҳозирча мурожаат қабул қилинмаяпти. Кейинроқ уриниб кўринг."))
        return

    kind = FEEDBACK_TYPES.get(data.get('feedback_type'), ("📩 Murojaat",))[0]
    info = (f"📩 <b>Yangi murojaat: {kind}</b>\n\n"
            f"Foydalanuvchi: <a href='tg://user?id={user_id}'>{html.escape(message.from_user.first_name or '')}</a> (ID: <code>{user_id}</code>)\n")
    if message.from_user.username:
        info += f"Username: @{html.escape(message.from_user.username)}\n"
    info += "\n↩️ Javob berish uchun shu xabarga yoki keyingi xabarga Reply qiling."

    try:
        info_msg = await message.bot.send_message(ADMIN_IDS[0], info, parse_mode="HTML")
        copied = await message.copy_to(chat_id=ADMIN_IDS[0])
        await save_feedback_message(info_msg.message_id, user_id)
        await save_feedback_message(copied.message_id, user_id)
    except Exception:
        log.exception("Murojaatni adminga yuborib bo'lmadi")
        await message.answer(tr(script, "❌ Yuborib bo'lmadi. Birozdan so'ng qayta urinib ko'ring.",
                                "❌ Юбориб бўлмади. Бироздан сўнг қайта уриниб кўринг."),
                             reply_markup=get_main_keyboard(script))
        return

    last_sent[user_id] = True
    await message.answer(tr(script, "✅ Murojaatingiz adminga yuborildi! Rahmat.",
                            "✅ Мурожаатингиз админга юборилди! Раҳмат."), reply_markup=get_main_keyboard(script))


@router.message(F.reply_to_message, F.from_user.id.in_(ADMIN_IDS))
async def admin_reply(message: Message):
    user_id = await get_feedback_user(message.reply_to_message.message_id)
    if not user_id:
        raise SkipHandler  # oddiy Reply: boshqa handlerlar ko'rsin
    try:
        script = await get_user_script(user_id)
        await message.bot.send_message(user_id, tr(script, "📩 <b>Admin javobi:</b>", "📩 <b>Админ жавоби:</b>"), parse_mode="HTML")
        await message.copy_to(chat_id=user_id)
        await message.answer("✅ Javobingiz foydalanuvchiga yuborildi!")
    except Exception as e:
        log.warning("Admin javobi yetmadi (%s): %s", user_id, e)
        await message.answer("❌ Javob yetmadi: foydalanuvchi botni bloklagan bo'lishi mumkin.")
