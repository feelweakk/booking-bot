"""Все клавиатуры бота."""

from datetime import date, datetime, timedelta

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

from config import DAYS_AHEAD, SERVICES, WORK_HOURS

BTN_BOOK = "📅 Записаться"
BTN_MY = "📋 Мои записи"
BTN_INFO = "ℹ️ О нас"

WEEKDAYS = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]

main_menu = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text=BTN_BOOK)], [KeyboardButton(text=BTN_MY), KeyboardButton(text=BTN_INFO)]],
    resize_keyboard=True,
)

phone_keyboard = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="📱 Отправить номер", request_contact=True)]],
    resize_keyboard=True,
    one_time_keyboard=True,
)


def format_day(day: date) -> str:
    return f"{WEEKDAYS[day.weekday()]} {day.strftime('%d.%m')}"


def services_keyboard() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=f"{name} — {price} ₽", callback_data=f"service:{code}")]
        for code, (name, price, _) in SERVICES.items()
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def days_keyboard() -> InlineKeyboardMarkup:
    today = date.today()
    buttons = [
        InlineKeyboardButton(text=format_day(d), callback_data=f"day:{d.isoformat()}")
        for d in (today + timedelta(days=i) for i in range(DAYS_AHEAD))
    ]
    rows = [buttons[i : i + 3] for i in range(0, len(buttons), 3)]  # по 3 в ряд
    rows.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="back:services")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def times_keyboard(free_times: list[str]) -> InlineKeyboardMarkup:
    buttons = [InlineKeyboardButton(text=t, callback_data=f"time:{t}") for t in free_times]
    rows = [buttons[i : i + 4] for i in range(0, len(buttons), 4)]  # по 4 в ряд
    rows.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="back:days")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def confirm_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm:yes"),
                InlineKeyboardButton(text="❌ Отмена", callback_data="confirm:no"),
            ]
        ]
    )


def cancel_booking_keyboard(booking_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="Отменить запись", callback_data=f"cancel:{booking_id}")]]
    )


def free_times_for(day: str, taken: set[str]) -> list[str]:
    """Свободные слоты. Для сегодняшнего дня убираем уже прошедшее время."""
    now = datetime.now()
    result = []
    for t in WORK_HOURS:
        if t in taken:
            continue
        if day == now.date().isoformat() and t <= now.strftime("%H:%M"):
            continue
        result.append(t)
    return result
