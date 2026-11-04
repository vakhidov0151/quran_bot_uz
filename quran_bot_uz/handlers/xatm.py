import datetime
import html
import math
from aiogram import Router, F
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from config import HIZB_STARTS, XATM_PLANS
from database.db_manager import (
    get_user_script, get_user_location, get_xatm_plan, start_xatm_plan, update_xatm_plan,
    complete_xatm_day, get_verses_between
)

router = Router()

QURAN_END = (115, 1)  # oxirgi oyatdan keyingi chegara
PAGE_MAX_VERSES = 10
PAGE_MAX_CHARS = 3600     # Telegram limiti 4096
TRANSLATION_MAX = 900     # juda uzun izohli tarjima sahifani to'ldirib yubormasligi uchun
SNOOZE_HOURS = 3

PRAYER_MODES = {
    "fajr": ("Fajr", "Bomdoddan keyin", "Бомдоддан кейин"),
    "dhuhr": ("Dhuhr", "Peshindan keyin", "Пешиндан кейин"),
    "asr": ("Asr", "Asrdan keyin", "Асрдан кейин"),
    "maghrib": ("Maghrib", "Shomdan keyin", "Шомдан кейин"),
    "isha": ("Isha", "Xuftondan keyin", "Хуфтондан кейин"),
}
HOUR_MODES = {f"h{h:02d}": h for h in (6, 8, 12, 18, 20, 22)}


def tr(script, latin, cyrillic):
    return latin if script == 'latin' else cyrillic


def btn(text, data):
    return InlineKeyboardButton(text=text, callback_data=data)


def part_range(plan_days: int, day: int):
    """Rejaning shu kunidagi vird chegarasi: (boshlanish, keyingi qism boshlanishi)."""
    per_day = len(HIZB_STARTS) // plan_days
    first = (day - 1) * per_day
    last = first + per_day
    return HIZB_STARTS[first], HIZB_STARTS[last] if last < len(HIZB_STARTS) else QURAN_END


def part_label(plan_days: int, day: int, script: str) -> str:
    pora, half = tr(script, "pora", "пора"), tr(script, "yarmi", "ярми")
    if plan_days == 60:
        return f"{math.ceil(day / 2)}-{pora}, {2 - day % 2}-{half}"
    per_day = 30 // plan_days
    last = day * per_day
    return f"{last}-{pora}" if per_day == 1 else f"{last - per_day + 1}–{last}-{pora}"


def plan_title(plan_days: int, script: str) -> str:
    return tr(script, f"{plan_days} kunda xatm", f"{plan_days} кунда хатм")


def progress_bar(done: int, total: int) -> str:
    filled = round(10 * done / total)
    return "▓" * filled + "░" * (10 - filled)


def mode_label(mode: str, script: str) -> str:
    if mode in PRAYER_MODES:
        return PRAYER_MODES[mode][1 if script == 'latin' else 2]
    if mode in HOUR_MODES:
        return f"{HOUR_MODES[mode]:02d}:00"
    return tr(script, "o'chirilgan", "ўчирилган")


async def range_text(plan_days: int, day: int, script: str) -> str:
    verses = await get_verses_between(*part_range(plan_days, day), script)
    a, b = verses[0], verses[-1]
    return f"{html.escape(a['surah_name_uz'])} {a['verse_id']} — {html.escape(b['surah_name_uz'])} {b['verse_id']}"


async def edit_or_send(call: CallbackQuery, text: str, keyboard):
    try:
        await call.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e):
            await call.message.answer(text, reply_markup=keyboard, parse_mode="HTML")


def plan_buttons(script, prefix="xp"):
    names = {
        60: tr(script, "🐢 60 kun — yarim pora", "🐢 60 кун — ярим пора"),
        30: tr(script, "📖 30 kun — 1 pora", "📖 30 кун — 1 пора"),
        15: tr(script, "🌿 15 kun — 2 pora", "🌿 15 кун — 2 пора"),
        10: tr(script, "🔥 10 kun — 3 pora", "🔥 10 кун — 3 пора"),
    }
    return [[btn(names[days], f"{prefix}:{days}")] for days in XATM_PLANS]


async def build_menu(user_id: int, script: str):
    plan = await get_xatm_plan(user_id)
    if not plan:
        text = tr(script,
                  "📖 <b>Xatm rejasi</b>\n\nQur'onni o'zingizga qulay sur'atda to'liq o'qib chiqing. "
                  "Bot har kuni bugungi virdni ko'rsatadi va qayerga yetganingizni eslab turadi. "
                  "Bir kun qoldirsangiz ham hech narsa yig'ilib qolmaydi — to'xtagan joyingizdan davom etasiz.\n\n"
                  "Rejani tanlang:",
                  "📖 <b>Хатм режаси</b>\n\nҚуръонни ўзингизга қулай суръатда тўлиқ ўқиб чиқинг. "
                  "Бот ҳар куни бугунги вирдни кўрсатади ва қаерга етганингизни эслаб туради. "
                  "Бир кун қолдирсангиз ҳам ҳеч нарса йиғилиб қолмайди — тўхтаган жойингиздан давом этасиз.\n\n"
                  "Режани танланг:")
        return text, InlineKeyboardMarkup(inline_keyboard=plan_buttons(script))

    done_line = tr(script, f"\n🏆 Tugatilgan xatmlar: {plan['completed_count']} ta",
                   f"\n🏆 Тугатилган хатмлар: {plan['completed_count']} та") if plan['completed_count'] else ""

    if plan['status'] == 'completed':
        text = tr(script, "🎉 <b>Xatm tugatildi!</b> Alloh qabul qilsin.", "🎉 <b>Хатм тугатилди!</b> Аллоҳ қабул қилсин.") + done_line
        text += tr(script, "\n\nYangi xatmni boshlaysizmi?", "\n\nЯнги хатмни бошлайсизми?")
        return text, InlineKeyboardMarkup(inline_keyboard=plan_buttons(script))

    day, days = plan['current_day'], plan['plan_days']
    summary = tr(script,
                 f"📖 <b>{plan_title(days, script)}</b>\n\nBugungi vird: <b>{part_label(days, day, script)}</b>\n",
                 f"📖 <b>{plan_title(days, script)}</b>\n\nБугунги вирд: <b>{part_label(days, day, script)}</b>\n")
    summary += await range_text(days, day, script) + "\n"
    summary += tr(script, f"Jarayon: {progress_bar(day - 1, days)} {day}/{days} kun\n",
                  f"Жараён: {progress_bar(day - 1, days)} {day}/{days} кун\n")
    summary += tr(script, f"🔔 Eslatma: {mode_label(plan['remind_mode'], script)}",
                  f"🔔 Эслатма: {mode_label(plan['remind_mode'], script)}") + done_line

    if plan['status'] == 'stopped':
        text = tr(script, "⏸ <b>Reja to'xtatilgan</b>\n\n", "⏸ <b>Режа тўхтатилган</b>\n\n") + summary
        rows = [[btn(tr(script, "▶️ Davom etish", "▶️ Давом этиш"), "xcont")]]
        rows += [[btn(tr(script, "🔄 Yangi xatm boshlash", "🔄 Янги хатм бошлаш"), "xnew")]]
        return text, InlineKeyboardMarkup(inline_keyboard=rows)

    rows = [
        [btn(tr(script, "📖 O'qish", "📖 Ўқиш"), "xr:-1"), btn(tr(script, "✅ O'qidim", "✅ Ўқидим"), f"xd:{day}")],
        [btn(tr(script, "🔔 Eslatma vaqti", "🔔 Эслатма вақти"), "xtime")],
        [btn(tr(script, "🔄 Rejani o'zgartirish", "🔄 Режани ўзгартириш"), "xchg")],
        [btn(tr(script, "⏸ To'xtatish", "⏸ Тўхтатиш"), "xstop")],
    ]
    return summary, InlineKeyboardMarkup(inline_keyboard=rows)


@router.message(Command("xatm"))
@router.message(F.text.in_({"📖 Xatm rejasi", "📖 Хатм режаси"}))
async def xatm_menu_message(message: Message):
    script = await get_user_script(message.from_user.id)
    text, kb = await build_menu(message.from_user.id, script)
    await message.answer(text, reply_markup=kb, parse_mode="HTML")


@router.callback_query(F.data == "xatm_menu")
async def xatm_menu_callback(call: CallbackQuery):
    script = await get_user_script(call.from_user.id)
    text, kb = await build_menu(call.from_user.id, script)
    await edit_or_send(call, text, kb)
    await call.answer()


@router.callback_query(F.data.in_({"xchg", "xnew"}))
async def xatm_choose_plan_callback(call: CallbackQuery):
    script = await get_user_script(call.from_user.id)
    if call.data == "xnew":
        # Reja faqat tanlangandan keyin nollanadi: "Orqaga" bosilsa jarayon saqlanib qoladi
        text = tr(script, "🔄 <b>Yangi xatm</b>\n\nBoshidan boshlanadi. Rejani tanlang:",
                  "🔄 <b>Янги хатм</b>\n\nБошидан бошланади. Режани танланг:")
        rows = plan_buttons(script, "xn")
    else:
        text = tr(script, "🔄 <b>Rejani o'zgartirish</b>\n\nO'qiganlaringiz saqlanadi, sur'at o'zgaradi:",
                  "🔄 <b>Режани ўзгартириш</b>\n\nЎқиганларингиз сақланади, суръат ўзгаради:")
        rows = plan_buttons(script)
    rows = rows + [[btn(tr(script, "🔙 Orqaga", "🔙 Орқага"), "xatm_menu")]]
    await edit_or_send(call, text, InlineKeyboardMarkup(inline_keyboard=rows))
    await call.answer()


@router.callback_query(F.data.startswith("xp:"))
async def xatm_plan_selected_callback(call: CallbackQuery):
    days = int(call.data.split(":")[1])
    if days not in XATM_PLANS:
        await call.answer()
        return
    plan = await get_xatm_plan(call.from_user.id)
    if plan and plan['status'] in ('active', 'paused'):
        # Sur'at o'zgaradi, o'qilgan qismlar saqlanadi
        done_hizb = (plan['current_day'] - 1) * (len(HIZB_STARTS) // plan['plan_days'])
        new_day = done_hizb // (len(HIZB_STARTS) // days) + 1
        await update_xatm_plan(call.from_user.id, plan_days=days, current_day=new_day, read_page=0, status='active')
        await xatm_menu_callback(call)
        return
    await start_xatm_plan(call.from_user.id, days)
    await xatm_time_callback(call)


@router.callback_query(F.data.startswith("xn:"))
async def xatm_new_plan_callback(call: CallbackQuery):
    days = int(call.data.split(":")[1])
    if days not in XATM_PLANS:
        await call.answer()
        return
    await start_xatm_plan(call.from_user.id, days)
    await xatm_time_callback(call)


@router.callback_query(F.data == "xtime")
async def xatm_time_callback(call: CallbackQuery):
    script = await get_user_script(call.from_user.id)
    has_location = await get_user_location(call.from_user.id)
    text = tr(script, "🔔 <b>Virdni qachon eslatay?</b>", "🔔 <b>Вирдни қачон эслатай?</b>")
    rows = []
    if has_location:
        for mode, names in PRAYER_MODES.items():
            rows.append([btn(names[1 if script == 'latin' else 2], f"xt:{mode}")])
    else:
        text += tr(script, "\n\nNamozdan keyin eslatish uchun joylashuv yoki shaharni ⚙️ Sozlamalar'dan tanlang. "
                           "Hozircha soatni tanlang (Toshkent vaqti):",
                   "\n\nНамоздан кейин эслатиш учун жойлашув ёки шаҳарни ⚙️ Созламалардан танланг. "
                   "Ҳозирча соатни танланг (Тошкент вақти):")
    hours = list(HOUR_MODES)
    for i in range(0, len(hours), 3):
        rows.append([btn(f"🕐 {HOUR_MODES[m]:02d}:00", f"xt:{m}") for m in hours[i:i + 3]])
    rows.append([btn(tr(script, "🔕 Eslatmasiz", "🔕 Эслатмасиз"), "xt:off")])
    await edit_or_send(call, text, InlineKeyboardMarkup(inline_keyboard=rows))
    await call.answer()


@router.callback_query(F.data.startswith("xt:"))
async def xatm_time_selected_callback(call: CallbackQuery):
    mode = call.data.split(":")[1]
    if mode != "off" and mode not in PRAYER_MODES and mode not in HOUR_MODES:
        await call.answer()
        return
    await update_xatm_plan(call.from_user.id, remind_mode=mode, unanswered=0)
    await xatm_menu_callback(call)


@router.callback_query(F.data == "xstop")
async def xatm_stop_callback(call: CallbackQuery):
    await update_xatm_plan(call.from_user.id, status='stopped', snooze_until=None)
    await xatm_menu_callback(call)


@router.callback_query(F.data == "xcont")
async def xatm_continue_callback(call: CallbackQuery):
    plan = await get_xatm_plan(call.from_user.id)
    if plan and plan['status'] in ('stopped', 'paused'):
        await update_xatm_plan(call.from_user.id, status='active', unanswered=0)
    await xatm_menu_callback(call)


@router.callback_query(F.data == "xs")
async def xatm_snooze_callback(call: CallbackQuery):
    script = await get_user_script(call.from_user.id)
    until = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=SNOOZE_HOURS)
    await update_xatm_plan(call.from_user.id, snooze_until=until.isoformat(), unanswered=0)
    await call.answer(tr(script, f"⏰ {SNOOZE_HOURS} soatdan keyin eslataman", f"⏰ {SNOOZE_HOURS} соатдан кейин эслатаман"))


def build_pages(verses):
    """Oyatlarni sahifalarga bo'ladi. Natija: [{'text': ..., 'verses': [(sura, oyat), ...]}, ...]."""
    pages, parts, refs, size, shown_surah = [], [], [], 0, None

    def flush():
        nonlocal parts, refs, size, shown_surah
        if parts:
            pages.append({"text": "".join(parts), "verses": refs})
        parts, refs, size, shown_surah = [], [], 0, None

    for v in verses:
        s_id, v_id = v['surah_id'], v['verse_id']
        uz = v['text_uzbek'] or ""
        if len(uz) > TRANSLATION_MAX:
            uz = uz[:TRANSLATION_MAX].rsplit(" ", 1)[0] + f"… ({s_id}:{v_id})"
        chunk = f"<b>{v_id}.</b> {html.escape(v['text_arabic'] or '')}\n<i>{html.escape(uz)}</i>\n\n"
        header = f"📖 <b>{html.escape(v['surah_name_uz'] or '')}</b>\n\n"
        if refs and (len(refs) >= PAGE_MAX_VERSES or size + len(header) + len(chunk) > PAGE_MAX_CHARS):
            flush()
        if shown_surah != s_id:
            parts.append(header)
            size += len(header)
            shown_surah = s_id
        parts.append(chunk)
        refs.append((s_id, v_id))
        size += len(chunk)
    flush()
    return pages


@router.callback_query(F.data.startswith("xr:"))
async def xatm_read_callback(call: CallbackQuery):
    script = await get_user_script(call.from_user.id)
    plan = await get_xatm_plan(call.from_user.id)
    if not plan or plan['status'] not in ('active', 'paused'):
        await xatm_menu_callback(call)
        return

    day, days = plan['current_day'], plan['plan_days']
    pages = build_pages(await get_verses_between(*part_range(days, day), script))
    wanted = int(call.data.split(":")[1])
    page = plan['read_page'] if wanted < 0 else wanted
    page = max(0, min(page, len(pages) - 1))
    # To'xtagan joyni eslab qolamiz; o'qishga kirgani uchun javob kutish hisobi ham nollanadi
    await update_xatm_plan(call.from_user.id, read_page=page, unanswered=0, status='active')

    head = f"📖 {part_label(days, day, script)} · {page + 1}/{len(pages)}\n\n"
    rows = []
    refs = pages[page]['verses']
    for i in range(0, len(refs), 5):
        rows.append([btn(f"🎧 {v}", f"play_audio:{s}:{v}") for s, v in refs[i:i + 5]])
    nav = []
    if page > 0:
        nav.append(btn(tr(script, "⬅️ Oldingi", "⬅️ Олдинги"), f"xr:{page - 1}"))
    if page < len(pages) - 1:
        nav.append(btn(tr(script, "Keyingi ➡️", "Кейинги ➡️"), f"xr:{page + 1}"))
    if nav:
        rows.append(nav)
    rows.append([btn(tr(script, "✅ O'qidim", "✅ Ўқидим"), f"xd:{day}"), btn(tr(script, "🔙 Menyu", "🔙 Меню"), "xatm_menu")])
    await edit_or_send(call, head + pages[page]['text'], InlineKeyboardMarkup(inline_keyboard=rows))
    await call.answer()


@router.callback_query(F.data.startswith("xd:"))
async def xatm_done_callback(call: CallbackQuery):
    script = await get_user_script(call.from_user.id)
    day = int(call.data.split(":")[1])
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    plan = await complete_xatm_day(call.from_user.id, day, now)
    if plan is None:
        await xatm_menu_callback(call)
        return
    if plan['status'] == 'completed':
        await xatm_menu_callback(call)
        return

    next_day, days = plan['current_day'], plan['plan_days']
    text = tr(script, "✅ <b>Alloh qabul qilsin!</b>\n\n", "✅ <b>Аллоҳ қабул қилсин!</b>\n\n")
    text += tr(script, f"Keyingi vird: <b>{part_label(days, next_day, script)}</b>\n",
               f"Кейинги вирд: <b>{part_label(days, next_day, script)}</b>\n")
    text += await range_text(days, next_day, script) + "\n"
    text += tr(script, f"Jarayon: {progress_bar(next_day - 1, days)} {next_day - 1}/{days} kun",
               f"Жараён: {progress_bar(next_day - 1, days)} {next_day - 1}/{days} кун")
    rows = [
        [btn(tr(script, "📖 Keyingisini ham o'qish", "📖 Кейингисини ҳам ўқиш"), "xr:-1")],
        [btn(tr(script, "🔙 Menyu", "🔙 Меню"), "xatm_menu")],
    ]
    await edit_or_send(call, text, InlineKeyboardMarkup(inline_keyboard=rows))
    await call.answer()


async def build_reminder(plan: dict, script: str):
    day, days = plan['current_day'], plan['plan_days']
    text = tr(script, f"📖 <b>Bugungi vird: {part_label(days, day, script)}</b>\n",
              f"📖 <b>Бугунги вирд: {part_label(days, day, script)}</b>\n")
    text += await range_text(days, day, script) + "\n"
    text += tr(script, f"Jarayon: {progress_bar(day - 1, days)} {day}/{days} kun",
               f"Жараён: {progress_bar(day - 1, days)} {day}/{days} кун")
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        btn(tr(script, "📖 O'qish", "📖 Ўқиш"), "xr:-1"),
        btn(tr(script, "✅ O'qidim", "✅ Ўқидим"), f"xd:{day}"),
        btn(tr(script, "⏰ Keyinroq", "⏰ Кейинроқ"), "xs"),
    ]])
    return text, kb


def build_pause_question(script: str):
    text = tr(script, "📖 Bir necha kundan beri xatm eslatmasiga javob bo'lmadi.\n\nDavom etamizmi yoki to'xtataylikmi? "
                      "Javob bermaguningizcha boshqa eslatma yubormayman.",
              "📖 Бир неча кундан бери хатм эслатмасига жавоб бўлмади.\n\nДавом этамизми ёки тўхтатайликми? "
              "Жавоб бермагунингизча бошқа эслатма юбормайман.")
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        btn(tr(script, "▶️ Davom etamiz", "▶️ Давом этамиз"), "xcont"),
        btn(tr(script, "⏸ To'xtatish", "⏸ Тўхтатиш"), "xstop"),
    ]])
    return text, kb
