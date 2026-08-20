import os
import asyncio
from datetime import datetime

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    LabeledPrice,
    PreCheckoutQuery
)
from dotenv import load_dotenv

from database import (
    init_db,
    add_user,
    get_user,
    get_all_users,
    get_user_ids,
    activate_subscription,
    activate_trial,
    trial_used,
    add_payment,
    add_promo,
    get_promo,
    delete_promo,
    get_expired_users
)

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")

ADMIN_IDS = {
    int(x.strip())
    for x in os.getenv("ADMIN_IDS", "").split(",")
    if x.strip().isdigit()
}

# Ссылка на servers.txt в GitHub
SUBSCRIPTION_URL = os.getenv(
    "SUBSCRIPTION_URL",
    "https://raw.githubusercontent.com/bdtvyz76b6-blip/fokycvpn/main/servers.txt"
)

TRIAL_DAYS = 3


# =========================
# ТАРИФЫ
# =========================

TARIFFS = {
    "1": {
        "name": "1 месяц",
        "days": 30,
        "stars": 70
    },
    "3": {
        "name": "3 месяца",
        "days": 90,
        "stars": 190
    },
    "6": {
        "name": "6 месяцев",
        "days": 180,
        "stars": 350
    },
    "12": {
        "name": "12 месяцев",
        "days": 365,
        "stars": 700
    }
}


bot = Bot(BOT_TOKEN)
dp = Dispatcher()


# =========================
# КЛАВИАТУРЫ
# =========================

def main_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="👤 Личный кабинет",
                    callback_data="cabinet"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🎁 Пробный период",
                    callback_data="trial"
                )
            ],
            [
                InlineKeyboardButton(
                    text="💳 Купить VPN",
                    callback_data="buy"
                )
            ]
        ]
    )


def cabinet_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📋 Скопировать ссылку",
                    callback_data="copy_link"
                )
            ],
            [
                InlineKeyboardButton(
                    text="💳 Продлить",
                    callback_data="buy"
                )
            ],
            [
                InlineKeyboardButton(
                    text="◀️ Назад",
                    callback_data="back"
                )
            ]
        ]
    )


def tariff_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="1 месяц — ⭐70",
                    callback_data="buy_1"
                )
            ],
            [
                InlineKeyboardButton(
                    text="3 месяца — ⭐190",
                    callback_data="buy_3"
                )
            ],
            [
                InlineKeyboardButton(
                    text="6 месяцев — ⭐350",
                    callback_data="buy_6"
                )
            ],
            [
                InlineKeyboardButton(
                    text="12 месяцев — ⭐700",
                    callback_data="buy_12"
                )
            ],
            [
                InlineKeyboardButton(
                    text="◀️ Назад",
                    callback_data="back"
                )
            ]
        ]
    )


def admin_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="👥 Пользователи",
                    callback_data="admin_users"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📊 Статистика",
                    callback_data="admin_stats"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🎟 Промокод",
                    callback_data="admin_promo_help"
                )
            ],
            [
                InlineKeyboardButton(
                    text="◀️ Назад",
                    callback_data="back"
                )
            ]
        ]
    )


# =========================
# ВСПОМОГАТЕЛЬНЫЕ
# =========================

def date_text(value):
    if not value:
        return "—"

    try:
        dt = datetime.fromisoformat(value)
        return dt.strftime("%d.%m.%Y %H:%M")
    except Exception:
        return value


def subscription_status(user):
    if not user or not user[4]:
        return "🔴 Не активна"

    try:
        until = datetime.fromisoformat(user[4])

        if until <= datetime.now():
            return "🔴 Истекла"

        return "🟢 Активна"

    except Exception:
        return "🟡 Неизвестно"


# =========================
# START
# =========================

@dp.message(Command("start"))
async def start(message: Message):

    user = message.from_user

    add_user(
        user.id,
        user.username,
        user.first_name
    )

    await message.answer(
        "🦊 <b>Fokyc VPN</b>\n\n"
        "⚡ Быстрый и стабильный VPN\n"
        "🔐 Защищённое подключение\n\n"
        "Выбери действие:",
        reply_markup=main_keyboard(),
        parse_mode="HTML"
    )


# =========================
# КАБИНЕТ
# =========================

@dp.callback_query(F.data == "cabinet")
async def cabinet(callback: CallbackQuery):

    add_user(
        callback.from_user.id,
        callback.from_user.username,
        callback.from_user.first_name
    )

    user = get_user(callback.from_user.id)

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
        parse_mode="HTML"
    )

    await callback.answer()


# =========================
# КОПИРОВАНИЕ
# =========================

@dp.callback_query(F.data == "copy_link")
async def copy_link(callback: CallbackQuery):

    user = get_user(callback.from_user.id)

    if not user or not user[5]:
        await callback.answer(
            "❌ У тебя пока нет подписки.",
            show_alert=True
        )
        return

    await callback.message.answer(
        "🔗 <b>Твоя ссылка подписки:</b>\n\n"
        f"<code>{user[5]}</code>\n\n"
        "Нажми и удерживай ссылку, чтобы скопировать.",
        parse_mode="HTML"
    )

    await callback.answer("Ссылка отправлена")


# =========================
# ПРОБНИК
# =========================

@dp.callback_query(F.data == "trial")
async def trial(callback: CallbackQuery):

    user_id = callback.from_user.id

    add_user(
        user_id,
        callback.from_user.username,
        callback.from_user.first_name
    )

    if trial_used(user_id):
        await callback.answer(
            "❌ Ты уже использовал пробный период.",
            show_alert=True
        )
        return

    until = activate_trial(
        user_id,
        TRIAL_DAYS,
        SUBSCRIPTION_URL
    )

    await callback.message.edit_text(
        "🎁 <b>Пробный период активирован!</b>\n\n"
        f"⏱ Срок: {TRIAL_DAYS} дня\n"
        f"📅 До: {until.strftime('%d.%m.%Y %H:%M')}\n\n"
        "🔗 <b>Ссылка подписки:</b>\n"
        f"<code>{SUBSCRIPTION_URL}</code>",
        reply_markup=cabinet_keyboard(),
        parse_mode="HTML"
    )

    await callback.answer("✅ Активировано")


# =========================
# ПОКУПКА
# =========================

@dp.callback_query(F.data == "buy")
async def buy(callback: CallbackQuery):

    await callback.message.edit_text(
        "💳 <b>Выбери тариф</b>\n\n"
        "Оплата производится Telegram Stars ⭐",
        reply_markup=tariff_keyboard(),
        parse_mode="HTML"
    )

    await callback.answer()


@dp.callback_query(F.data.startswith("buy_"))
async def buy_tariff(callback: CallbackQuery):

    key = callback.data.split("_")[1]

    tariff = TARIFFS.get(key)

    if not tariff:
        await callback.answer("Ошибка тарифа")
        return

    await bot.send_invoice(
        chat_id=callback.from_user.id,
        title=f"Fokyc VPN — {tariff['name']}",
        description=f"Подписка Fokyc VPN на {tariff['name']}",
        payload=f"fokyc_{key}_{callback.from_user.id}",
        currency="XTR",
        prices=[
            LabeledPrice(
                label=f"Fokyc VPN — {tariff['name']}",
                amount=tariff["stars"]
            )
        ]
    )

    await callback.answer()


# =========================
# PRE-CHECKOUT
# =========================

@dp.pre_checkout_query()
async def pre_checkout(query: PreCheckoutQuery):

    await query.answer(ok=True)


# =========================
# УСПЕШНАЯ ОПЛАТА
# =========================

@dp.message(F.successful_payment)
async def successful_payment(message: Message):

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
        message.from_user.first_name
    )

    until = activate_subscription(
        user_id,
        tariff["days"],
        SUBSCRIPTION_URL,
        f"👑 Fokyc VPN — {tariff['name']}"
    )

    add_payment(
        user_id,
        tariff["days"],
        tariff["stars"]
    )

    await message.answer(
        "✅ <b>Оплата прошла успешно!</b>\n\n"
        f"🎫 Тариф: {tariff['name']}\n"
        f"⭐ Оплачено: {tariff['stars']}\n"
        f"📅 Активна до: {until.strftime('%d.%m.%Y %H:%M')}\n\n"
        "🔗 <b>Ссылка подписки:</b>\n"
        f"<code>{SUBSCRIPTION_URL}</code>",
        reply_markup=main_keyboard(),
        parse_mode="HTML"
    )


# =========================
# АДМИН
# =========================

@dp.message(Command("admin"))
async def admin(message: Message):

    if message.from_user.id not in ADMIN_IDS:
        return

    await message.answer(
        "👑 <b>Админ-панель Fokyc VPN</b>\n\n"
        "Выбери раздел:",
        reply_markup=admin_keyboard(),
        parse_mode="HTML"
    )


@dp.callback_query(F.data == "admin_users")
async def admin_users(callback: CallbackQuery):

    if callback.from_user.id not in ADMIN_IDS:
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
        parse_mode="HTML"
    )

    await callback.answer()


@dp.callback_query(F.data == "admin_stats")
async def admin_stats(callback: CallbackQuery):

    if callback.from_user.id not in ADMIN_IDS:
        return

    users = get_all_users()
    expired = get_expired_users()

    active = 0

    for user in users:
        if subscription_status(user) == "🟢 Активна":
            active += 1

    await callback.message.edit_text(
        "📊 <b>Статистика Fokyc VPN</b>\n\n"
        f"👥 Пользователей: {len(users)}\n"
        f"🟢 Активных подписок: {active}\n"
        f"🔴 Истёкших: {len(expired)}",
        reply_markup=admin_keyboard(),
        parse_mode="HTML"
    )

    await callback.answer()


# =========================
# ПРОМОКОДЫ
# =========================

@dp.message(Command("promo"))
async def promo(message: Message):

    parts = message.text.split(maxsplit=1)

    if len(parts) != 2:
        await message.answer(
            "🎟 Использование:\n"
            "<code>/promo CODE</code>",
            parse_mode="HTML"
        )
        return

    code = parts[1].strip().upper()
    promo_data = get_promo(code)

    if not promo_data:
        await message.answer("❌ Промокод не найден.")
        return

    days = promo_data[1]

    add_user(
        message.from_user.id,
        message.from_user.username,
        message.from_user.first_name
    )

    until = activate_subscription(
        message.from_user.id,
        days,
        SUBSCRIPTION_URL,
        "🎟 Промокод"
    )

    delete_promo(code)

    await message.answer(
        "🎉 <b>Промокод активирован!</b>\n\n"
        f"⏱ Добавлено: {days} дней\n"
        f"📅 До: {until.strftime('%d.%m.%Y %H:%M')}\n\n"
        f"🔗 <code>{SUBSCRIPTION_URL}</code>",
        parse_mode="HTML"
    )


@dp.message(Command("addpromo"))
async def addpromo(message: Message):

    if message.from_user.id not in ADMIN_IDS:
        return

    parts = message.text.split()

    if len(parts) != 3:
        await message.answer(
            "Использование:\n"
            "<code>/addpromo CODE DAYS</code>",
            parse_mode="HTML"
        )
        return

    code = parts[1].upper()

    try:
        days = int(parts[2])
    except ValueError:
        await message.answer("❌ DAYS должно быть числом.")
        return

    add_promo(code, days)

    await message.answer(
        f"✅ Промокод <code>{code}</code> создан.\n"
        f"⏱ Дней: {days}",
        parse_mode="HTML"
    )


@dp.callback_query(F.data == "admin_promo_help")
async def admin_promo_help(callback: CallbackQuery):

    if callback.from_user.id not in ADMIN_IDS:
        return

    await callback.message.edit_text(
        "🎟 <b>Промокоды</b>\n\n"
        "Создание:\n"
        "<code>/addpromo CODE DAYS</code>\n\n"
        "Например:\n"
        "<code>/addpromo SUMMER 30</code>\n\n"
        "Пользователь активирует:\n"
        "<code>/promo SUMMER</code>",
        reply_markup=admin_keyboard(),
        parse_mode="HTML"
    )

    await callback.answer()


# =========================
# BACK
# =========================

@dp.callback_query(F.data == "back")
async def back(callback: CallbackQuery):

    await callback.message.edit_text(
        "🦊 <b>Fokyc VPN</b>\n\n"
        "Выбери действие:",
        reply_markup=main_keyboard(),
        parse_mode="HTML"
    )

    await callback.answer()


# =========================
# ЗАПУСК
# =========================

async def main():

    if not BOT_TOKEN:
        raise RuntimeError(
            "BOT_TOKEN не задан."
        )

    init_db()

    print("Fokyc VPN started")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())