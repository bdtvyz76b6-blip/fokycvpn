import os
import asyncio
import secrets

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv

from database import (
    init_db,
    add_user,
    get_user,
    activate_subscription,
    activate_trial,
    trial_used,
    get_all_users,
)

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_IDS = {
    int(x.strip())
    for x in os.getenv("ADMIN_IDS", "").split(",")
    if x.strip().isdigit()
}

TRIAL_DAYS = 3


# =========================
# BOT
# =========================

bot = Bot(BOT_TOKEN)
dp = Dispatcher()


# =========================
# KEYBOARDS
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
        ]
    )


def cabinet_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔄 Обновить",
                    callback_data="cabinet"
                )
            ],
            [
                InlineKeyboardButton(
                    text="◀️ Назад",
                    callback_data="back"
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
                    callback_data="admin_users"
                )
            ],
            [
                InlineKeyboardButton(
                    text="◀️ Назад",
                    callback_data="back"
                )
            ],
        ]
    )


# =========================
# HELPERS
# =========================

def get_subscription_link():
    """
    Временно создаём персональный идентификатор.
    Позже подключим генерацию ссылки из servers.txt.
    """
    return f"https://example.com/sub/{secrets.token_urlsafe(8)}"


def format_date(value):
    if not value:
        return "—"

    try:
        from datetime import datetime

        date = datetime.fromisoformat(value)
        return date.strftime("%d.%m.%Y %H:%M")
    except Exception:
        return value


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
        "Быстрый и стабильный VPN.\n\n"
        "Выбери нужный раздел ниже:",
        reply_markup=main_keyboard(),
        parse_mode="HTML"
    )


# =========================
# CABINET
# =========================

@dp.callback_query(F.data == "cabinet")
async def cabinet(callback):

    user_id = callback.from_user.id
    user = get_user(user_id)

    if not user:
        add_user(
            user_id,
            callback.from_user.username,
            callback.from_user.first_name
        )
        user = get_user(user_id)

    # структура:
    # 0 user_id
    # 1 username
    # 2 first_name
    # 3 tariff
    # 4 subscription_until
    # 5 subscription_link
    # 6 trial_used
    # 7 created_at

    tariff = user[3] or "Нет подписки"
    until = format_date(user[4])
    link = user[5] or "Нет"

    text = (
        "👤 <b>Личный кабинет</b>\n\n"
        f"🆔 ID: <code>{user_id}</code>\n"
        f"👤 Имя: {user[2] or '—'}\n\n"
        f"🎫 Тариф: {tariff}\n"
        f"📅 До: {until}\n\n"
        f"🔗 Подписка:\n"
        f"<code>{link}</code>"
    )

    await callback.message.edit_text(
        text,
        reply_markup=cabinet_keyboard(),
        parse_mode="HTML"
    )

    await callback.answer()


# =========================
# TRIAL
# =========================

@dp.callback_query(F.data == "trial")
async def trial(callback):

    user_id = callback.from_user.id

    add_user(
        user_id,
        callback.from_user.username,
        callback.from_user.first_name
    )

    if trial_used(user_id):
        await callback.answer(
            "❌ Вы уже использовали пробный период.",
            show_alert=True
        )
        return

    link = get_subscription_link()

    activate_trial(
        user_id,
        TRIAL_DAYS,
        link
    )

    await callback.message.edit_text(
        "🎁 <b>Пробный период активирован!</b>\n\n"
        f"⏱ Срок: {TRIAL_DAYS} дня\n\n"
        "🔗 Ваша подписка:\n"
        f"<code>{link}</code>\n\n"
        "Добавь ссылку в приложение VPN.",
        reply_markup=cabinet_keyboard(),
        parse_mode="HTML"
    )

    await callback.answer("✅ Готово!")


# =========================
# BACK
# =========================

@dp.callback_query(F.data == "back")
async def back(callback):

    await callback.message.edit_text(
        "🦊 <b>Fokyc VPN</b>\n\n"
        "Выбери нужный раздел:",
        reply_markup=main_keyboard(),
        parse_mode="HTML"
    )

    await callback.answer()


# =========================
# ADMIN
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


# =========================
# ADMIN USERS
# =========================

@dp.callback_query(F.data == "admin_users")
async def admin_users(callback):

    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("❌ Нет доступа.", show_alert=True)
        return

    users = get_all_users()

    text = (
        "👥 <b>Пользователи</b>\n\n"
        f"Всего: <b>{len(users)}</b>\n\n"
    )

    for user in users[:30]:

        user_id = user[0]
        name = user[2] or "Без имени"
        tariff = user[3] or "Нет подписки"

        text += (
            f"👤 {name}\n"
            f"🆔 <code>{user_id}</code>\n"
            f"🎫 {tariff}\n\n"
        )

    await callback.message.edit_text(
        text,
        reply_markup=admin_keyboard(),
        parse_mode="HTML"
    )

    await callback.answer()


# =========================
# RUN
# =========================

async def main():

    if not BOT_TOKEN:
        raise RuntimeError(
            "Не задан BOT_TOKEN в переменных окружения."
        )

    init_db()

    print("Fokyc VPN bot started")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())