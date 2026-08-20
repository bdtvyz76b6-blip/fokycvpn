import os
import asyncio
from datetime import datetime

from aiohttp import web
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    LabeledPrice,
    PreCheckoutQuery,
)

from database import (
    init_db,
    add_user,
    get_user,
    get_all_users,
    activate_subscription,
    activate_trial,
    trial_used,
    add_payment,
    add_promo,
    get_promo,
    delete_promo,
    get_expired_users,
)


# =========================================================
# CONFIG
# =========================================================

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()

ADMIN_IDS = {
    int(x.strip())
    for x in os.getenv("ADMIN_IDS", "").split(",")
    if x.strip().isdigit()
}

SUBSCRIPTION_URL = os.getenv(
    "SUBSCRIPTION_URL",
    "https://raw.githubusercontent.com/bdtvyz76b6-blip/fokycvpn/main/servers.txt",
).strip()

PORT = int(os.getenv("PORT", "10000"))

TRIAL_DAYS = 3


# =========================================================
# TARIFFS
# =========================================================

TARIFFS = {
    "1": {
        "name": "1 месяц",
        "days": 30,
        "stars": 70,
    },
    "3": {
        "name": "3 месяца",
        "days": 90,
        "stars": 190,
    },
    "6": {
        "name": "6 месяцев",
        "days": 180,
        "stars": 350,
    },
    "12": {
        "name": "12 месяцев",
        "days": 365,
        "stars": 700,
    },
}


# =========================================================
# BOT
# =========================================================

bot = Bot(BOT_TOKEN)
dp = Dispatcher()


# =========================================================
# HTTP SERVER FOR RENDER
# =========================================================

async def health(request):
    return web.Response(
        text="Fokyc VPN Bot is running!"
    )


async def start_web_server():
    app = web.Application()

    app.router.add_get("/", health)
    app.router.add_get("/health", health)

    runner = web.AppRunner(app)

    await runner.setup()

    site = web.TCPSite(
        runner,
        "0.0.0.0",
        PORT,
    )

    await site.start()

    print(f"HTTP server started on port {PORT}")


# =========================================================
# KEYBOARDS
# =========================================================

def main_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="👤 Личный кабинет",
                    callback_data="cabinet",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🎁 Пробный период",
                    callback_data="trial",
                )
            ],
            [
                InlineKeyboardButton(
                    text="💳 Купить VPN",
                    callback_data="buy",
                )
            ],
        ]
    )


def cabinet_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📋 Ссылка подписки",
                    callback_data="copy_link",
                )
            ],
            [
                InlineKeyboardButton(
                    text="💳 Продлить",
                    callback_data="buy",
                )
            ],
            [
                InlineKeyboardButton(
                    text="◀️ Назад",
                    callback_data="back",
                )
            ],
        ]
    )


def tariff_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="1 месяц — ⭐70",
                    callback_data="buy_1",
                )
            ],
            [
                InlineKeyboardButton(
                    text="3 месяца — ⭐190",
                    callback_data="buy_3",
                )
            ],
            [
                InlineKeyboardButton(
                    text="6 месяцев — ⭐350",
                    callback_data="buy_6",
                )
            ],
            [
                InlineKeyboardButton(
                    text="12 месяцев — ⭐700",
                    callback_data="buy_12",
                )
            ],
            [
                InlineKeyboardButton(
                    text="◀️ Назад",
                    callback_data="back",
                )
            ],
        ]
    )


def admin_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="👥 Пользователи",
                    callback_data="admin_users",
                )
            ],
            [
                InlineKeyboardButton(
                    text="📊 Статистика",
                    callback_data="admin_stats",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🎟 Промокоды",
                    callback_data="admin_promo_help",
                )
            ],
            [
                InlineKeyboardButton(
                    text="◀️ Назад",
                    callback_data="back",
                )
            ],
        ]
    )


# =========================================================
# HELPERS
# =========================================================

def date_text(value):
    if not value:
        return "—"

    try:
        dt = datetime.fromisoformat(value)
        return dt.strftime("%d.%m.%Y %H:%M")
    except Exception:
        return value


def subscription_status(user):
    if not user:
        return "🔴 Не активна"

    if not user[4]:
        return "🔴 Не активна"

    try:
        until = datetime.fromisoformat(user[4])

        if until <= datetime.now():
            return "🔴 Истекла"

        return "🟢 Активна"

    except Exception:
        return "🟡 Неизвестно"


def ensure_user(message_or_callback):
    user = (
        message_or_callback.from_user
    )

    add_user(
        user.id,
        user.username,
        user.first_name,
    )

    return get_user(user.id)


# =========================================================
# START
# =========================================================

@dp.message(Command("start"))
async def start(message: Message):

    add_user(
        message.from_user.id,
        message.from_user.username,
        message.from_user.first_name,
    )

    await message.answer(
        "🦊 <b>Fokyc VPN</b>\n\n"
        "⚡ Быстрый и стабильный VPN\n"
        "🔐 Защищённое подключение\n\n"
        "Выбери действие:",
        reply_markup=main_keyboard(),
        parse_mode="HTML",
    )


# =========================================================
# CABINET
# =========================================================

@dp.callback_query(F.data == "cabinet")
async def cabinet(callback: CallbackQuery):

    user = ensure_user(callback)

    text = (
        "👤 <b>Личный кабинет</b>\n\n"
        f"🆔 ID: <code>{user[0]}</code>\n"
        f"👤 Username: @{user[1] or 'нет'}\n"
        f"🧑‍💻 Имя: {user[2] or '—'}\n\n"
        f"🎫 Тариф: {user[3]}\n"
        f"📊 Статус: {subscription_status(user)}\n"
        f"📅 До: {date_text(user[4])}\n\n"
        "🔗 <b>Подписка:</b>\n"
        f"<code>{user[5] or 'Нет подписки'}</code>"
    )

    await callback.message.edit_text(
        text,
        reply_markup=cabinet_keyboard(),
        parse_mode="HTML",
    )

    await callback.answer()


# =========================================================
# SUBSCRIPTION LINK
# =========================================================

@dp.callback_query(F.data == "copy_link")
async def copy_link(callback: CallbackQuery):

    user = ensure_user(callback)

    if not user[5]:
        await callback.answer(
            "❌ У тебя пока нет подписки.",
            show_alert=True,
        )
        return

    await callback.message.answer(
        "🔗 <b>Твоя ссылка подписки:</b>\n\n"
        f"<code>{user[5]}</code>\n\n"
        "Нажми и удерживай ссылку, чтобы скопировать.",
        parse_mode="HTML",
    )

    await callback.answer("Ссылка отправлена")


# =========================================================
# TRIAL
# =========================================================

@dp.callback_query(F.data == "trial")
async def trial(callback: CallbackQuery):

    user_id = callback.from_user.id

    add_user(
        user_id,
        callback.from_user.username,
        callback.from_user.first_name,
    )

    if trial_used(user_id):
        await callback.answer(
            "❌ Ты уже использовал пробный период.",
            show_alert=True,
        )
        return

    until = activate_trial(
        user_id,
        TRIAL_DAYS,
        SUBSCRIPTION_URL,
    )

    await callback.message.edit_text(
        "🎁 <b>Пробный период активирован!</b>\n\n"
        f"⏱ Срок: {TRIAL_DAYS} дня\n"
        f"📅 До: {until.strftime('%d.%m.%Y %H:%M')}\n\n"
        "🔗 <b>Ссылка подписки:</b>\n"
        f"<code>{SUBSCRIPTION_URL}</code>",
        reply_markup=cabinet_keyboard(),
        parse_mode="HTML",
    )

    await callback.answer("✅ Активировано")


# =========================================================
# BUY
# =========================================================

@dp.callback_query(F.data == "buy")
async def buy(callback: CallbackQuery):

    await callback.message.edit_text(
        "💳 <b>Выбери тариф</b>\n\n"
        "Оплата производится Telegram Stars ⭐",
        reply_markup=tariff_keyboard(),
        parse_mode="HTML",
    )

    await callback.answer()


@dp.callback_query(F.data.startswith("buy_"))
async def buy_tariff(callback: CallbackQuery):

    tariff_id = callback.data.split("_", 1)[1]

    tariff = TARIFFS.get(tariff_id)

    if not tariff:
        await callback.answer(
            "❌ Тариф не найден.",
            show_alert=True,
        )
        return

    await bot.send_invoice(
        chat_id=callback.from_user.id,
        title=f"Fokyc VPN — {tariff['name']}",
        description=(
            f"Подписка Fokyc VPN "
            f"на {tariff['name']}"
        ),
        payload=(
            f"fokyc_{tariff_id}_"
            f"{callback.from_user.id}"
        ),
        currency="XTR",
        prices=[
            LabeledPrice(
                label=(
                    f"Fokyc VPN — "
                    f"{tariff['name']}"
                ),
                amount=tariff["stars"],
            )
        ],
    )

    await callback.answer()


# =========================================================
# PRE CHECKOUT
# =========================================================

@dp.pre_checkout_query()
async def pre_checkout(
    query: PreCheckoutQuery,
):

    await query.answer(ok=True)


# =========================================================
# SUCCESSFUL PAYMENT
# =========================================================

@dp.message(F.successful_payment)
async def successful_payment(
    message: Message,
):

    payment = message.successful_payment

    payload = payment.invoice_payload

    if not payload.startswith("fokyc_"):
        return

    parts = payload.split("_")

    if len(parts) != 3:
        return

    tariff_id = parts[1]

    tariff = TARIFFS.get(tariff_id)

    if not tariff:
        return

    user_id = message.from_user.id

    add_user(
        user_id,
        message.from_user.username,
        message.from_user.first_name,
    )

    until = activate_subscription(
        user_id,
        tariff["days"],
        SUBSCRIPTION_URL,
        f"👑 Fokyc VPN — {tariff['name']}",
    )

    add_payment(
        user_id,
        tariff["days"],
        tariff["stars"],
    )

    await message.answer(
        "✅ <b>Оплата прошла успешно!</b>\n\n"
        f"🎫 Тариф: {tariff['name']}\n"
        f"⭐ Оплачено: {tariff['stars']}\n"
        f"📅 Активна до: "
        f"{until.strftime('%d.%m.%Y %H:%M')}\n\n"
        "🔗 <b>Ссылка подписки:</b>\n"
        f"<code>{SUBSCRIPTION_URL}</code>",
        reply_markup=main_keyboard(),
        parse_mode="HTML",
    )


# =========================================================
# ADMIN
# =========================================================

@dp.message(Command("admin"))
async def admin(message: Message):

    if message.from_user.id not in ADMIN_IDS:
        return

    await message.answer(
        "👑 <b>Админ-панель Fokyc VPN</b>\n\n"
        "Выбери раздел:",
        reply_markup=admin_keyboard(),
        parse_mode="HTML",
    )


# =========================================================
# ADMIN USERS
# =========================================================

@dp.callback_query(F.data == "admin_users")
async def admin_users(
    callback: CallbackQuery,
):

    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer(
            "❌ Нет доступа.",
            show_alert=True,
        )
        return

    users = get_all_users()

    text = (
        "👥 <b>Пользователи</b>\n\n"
        f"Всего: <b>{len(users)}</b>\n\n"
    )

    for user in users[:30]:

        text += (
            f"👤 {user[2] or 'Без имени'}\n"
            f"🆔 <code>{user[0]}</code>\n"
            f"🎫 {user[3]}\n"
            f"📊 {subscription_status(user)}\n\n"
        )

    await callback.message.edit_text(
        text,
        reply_markup=admin_keyboard(),
        parse_mode="HTML",
    )

    await callback.answer()


# =========================================================
# ADMIN STATS
# =========================================================

@dp.callback_query(F.data == "admin_stats")
async def admin_stats(
    callback: CallbackQuery,
):

    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer(
            "❌ Нет доступа.",
            show_alert=True,
        )
        return

    users = get_all_users()
    expired = get_expired_users()

    active = sum(
        1
        for user in users
        if subscription_status(user) == "🟢 Активна"
    )

    await callback.message.edit_text(
        "📊 <b>Статистика Fokyc VPN</b>\n\n"
        f"👥 Пользователей: {len(users)}\n"
        f"🟢 Активных: {active}\n"
        f"🔴 Истёкших: {len(expired)}",
        reply_markup=admin_keyboard(),
        parse_mode="HTML",
    )

    await callback.answer()


# =========================================================
# PROMOCODES
# =========================================================

@dp.message(Command("addpromo"))
async def addpromo(message: Message):

    if message.from_user.id not in ADMIN_IDS:
        return

    parts = message.text.split()

    if len(parts) != 3:
        await message.answer(
            "Использование:\n\n"
            "<code>/addpromo CODE DAYS</code>",
            parse_mode="HTML",
        )
        return

    code = parts[1].upper()

    try:
        days = int(parts[2])
    except ValueError:
        await message.answer(
            "❌ Количество дней должно быть числом."
        )
        return

    if days <= 0:
        await message.answer(
            "❌ Количество дней должно быть больше 0."
        )
        return

    add_promo(code, days)

    await message.answer(
        f"✅ Промокод <code>{code}</code> создан.\n\n"
        f"⏱ Дней: {days}",
        parse_mode="HTML",
    )


@dp.message(Command("promo"))
async def promo(message: Message):

    parts = message.text.split(maxsplit=1)

    if len(parts) != 2:
        await message.answer(
            "Использование:\n\n"
            "<code>/promo CODE</code>",
            parse_mode="HTML",
        )
        return

    code = parts[1].strip().upper()

    promo_data = get_promo(code)

    if not promo_data:
        await message.answer(
            "❌ Промокод не найден."
        )
        return

    days = promo_data[1]

    add_user(
        message.from_user.id,
        message.from_user.username,
        message.from_user.first_name,
    )

    until = activate_subscription(
        message.from_user.id,
        days,
        SUBSCRIPTION_URL,
        "🎟 Промокод",
    )

    delete_promo(code)

    await message.answer(
        "🎉 <b>Промокод активирован!</b>\n\n"
        f"⏱ Добавлено: {days} дней\n"
        f"📅 До: "
        f"{until.strftime('%d.%m.%Y %H:%M')}\n\n"
        "🔗 <b>Подписка:</b>\n"
        f"<code>{SUBSCRIPTION_URL}</code>",
        parse_mode="HTML",
    )


@dp.callback_query(F.data == "admin_promo_help")
async def admin_promo_help(
    callback: CallbackQuery,
):

    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer(
            "❌ Нет доступа.",
            show_alert=True,
        )
        return

    await callback.message.edit_text(
        "🎟 <b>Промокоды</b>\n\n"
        "Создать:\n"
        "<code>/addpromo CODE DAYS</code>\n\n"
        "Например:\n"
        "<code>/addpromo SUMMER 30</code>\n\n"
        "Активировать:\n"
        "<code>/promo SUMMER</code>",
        reply_markup=admin_keyboard(),
        parse_mode="HTML",
    )

    await callback.answer()


# =========================================================
# BACK
# =========================================================

@dp.callback_query(F.data == "back")
async def back(callback: CallbackQuery):

    await callback.message.edit_text(
        "🦊 <b>Fokyc VPN</b>\n\n"
        "Выбери действие:",
        reply_markup=main_keyboard(),
        parse_mode="HTML",
    )

    await callback.answer()


# =========================================================
# MAIN
# =========================================================

async def main():

    if not BOT_TOKEN:
        raise RuntimeError(
            "BOT_TOKEN не задан в Environment Variables."
        )

    init_db()

    print("Starting Fokyc VPN...")

    await start_web_server()

    print("Telegram bot started.")

    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Fokyc VPN stopped.")