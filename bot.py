"""Бот для онлайн-записи клиентов (барбершоп, салон, репетитор, сервис).

Запуск:
    pip install -r requirements.txt
    скопируй .env.example в .env и заполни
    python bot.py
"""

import asyncio
import logging
from datetime import date
from html import escape

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

import db
import keyboards as kb
from config import ADMIN_ID, BOT_TOKEN, BUSINESS_INFO, BUSINESS_NAME, SERVICES

dp = Dispatcher()


class Booking(StatesGroup):
    """Шаги записи. Бот запоминает, на каком шаге сейчас клиент."""

    service = State()
    day = State()
    time = State()
    name = State()
    phone = State()
    confirm = State()


def booking_summary(data: dict) -> str:
    name, price, duration = SERVICES[data["service"]]
    return (
        f"💈 Услуга: <b>{name}</b> ({duration} мин)\n"
        f"💰 Цена: <b>{price} ₽</b>\n"
        f"📅 Дата: <b>{kb.format_day(date.fromisoformat(data['day']))}</b>\n"
        f"🕐 Время: <b>{data['time']}</b>"
    )


# ---------- Главное меню ----------

@dp.message(CommandStart())
async def start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        f"Здравствуйте! 👋 Это бот <b>{BUSINESS_NAME}</b>.\n\n"
        "Здесь можно записаться за минуту — без звонков и ожидания.",
        reply_markup=kb.main_menu,
    )


@dp.message(F.text == kb.BTN_INFO)
async def info(message: Message):
    await message.answer(f"<b>{BUSINESS_NAME}</b>\n\n{BUSINESS_INFO}")


@dp.message(F.text == kb.BTN_MY)
async def my_bookings(message: Message):
    bookings = db.user_bookings(message.from_user.id)
    if not bookings:
        await message.answer("У вас нет активных записей.")
        return
    for b in bookings:
        await message.answer(booking_summary(dict(b)), reply_markup=kb.cancel_booking_keyboard(b["id"]))


# ---------- Запись: шаг 1 — услуга ----------

@dp.message(F.text == kb.BTN_BOOK)
async def book_start(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(Booking.service)
    await message.answer("Выберите услугу:", reply_markup=kb.services_keyboard())


@dp.callback_query(Booking.service, F.data.startswith("service:"))
async def choose_service(callback: CallbackQuery, state: FSMContext):
    await state.update_data(service=callback.data.split(":")[1])
    await state.set_state(Booking.day)
    await callback.message.edit_text("Выберите день:", reply_markup=kb.days_keyboard())
    await callback.answer()


# ---------- Шаг 2 — день ----------

@dp.callback_query(Booking.day, F.data.startswith("day:"))
async def choose_day(callback: CallbackQuery, state: FSMContext):
    day = callback.data.split(":")[1]
    free = kb.free_times_for(day, db.taken_times(day))
    if not free:
        await callback.answer("На этот день свободного времени нет 😔", show_alert=True)
        return
    await state.update_data(day=day)
    await state.set_state(Booking.time)
    await callback.message.edit_text("Выберите время:", reply_markup=kb.times_keyboard(free))
    await callback.answer()


# ---------- Шаг 3 — время ----------

@dp.callback_query(Booking.time, F.data.startswith("time:"))
async def choose_time(callback: CallbackQuery, state: FSMContext):
    await state.update_data(time=callback.data.split(":", 1)[1])
    await state.set_state(Booking.name)
    await callback.message.edit_text("Как к вам обращаться? Напишите имя:")
    await callback.answer()


# ---------- Кнопки «Назад» ----------

@dp.callback_query(F.data == "back:services")
async def back_to_services(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Booking.service)
    await callback.message.edit_text("Выберите услугу:", reply_markup=kb.services_keyboard())
    await callback.answer()


@dp.callback_query(F.data == "back:days")
async def back_to_days(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Booking.day)
    await callback.message.edit_text("Выберите день:", reply_markup=kb.days_keyboard())
    await callback.answer()


# ---------- Шаг 4 — имя и телефон ----------

@dp.message(Booking.name, F.text)
async def enter_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text.strip()[:50])
    await state.set_state(Booking.phone)
    await message.answer(
        "Отправьте номер телефона кнопкой ниже или напишите его:",
        reply_markup=kb.phone_keyboard,
    )


@dp.message(Booking.phone, F.contact | F.text)
async def enter_phone(message: Message, state: FSMContext):
    phone = message.contact.phone_number if message.contact else message.text.strip()
    digits = "".join(ch for ch in phone if ch.isdigit())
    if not 10 <= len(digits) <= 15:
        await message.answer("Похоже, номер неверный. Попробуйте ещё раз:")
        return

    await state.update_data(phone=phone)
    await state.set_state(Booking.confirm)
    data = await state.get_data()
    await message.answer("Почти готово!", reply_markup=kb.main_menu)
    await message.answer(
        f"Проверьте запись:\n\n{booking_summary(data)}\n👤 {escape(data['name'])}, {escape(phone)}",
        reply_markup=kb.confirm_keyboard(),
    )


# ---------- Шаг 5 — подтверждение ----------

@dp.callback_query(Booking.confirm, F.data.startswith("confirm:"))
async def confirm(callback: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    await state.clear()

    if callback.data == "confirm:no":
        await callback.message.edit_text("Запись отменена.")
        await callback.answer()
        return

    booking_id = db.create_booking(
        callback.from_user.id, data["name"], data["phone"], data["service"], data["day"], data["time"]
    )
    if booking_id is None:
        await callback.message.edit_text("😔 Это время только что заняли. Попробуйте выбрать другое.")
        await callback.answer()
        return

    await callback.message.edit_text(f"✅ Вы записаны!\n\n{booking_summary(data)}\n\nЖдём вас!")
    await callback.answer()

    # Уведомление владельцу
    if ADMIN_ID:
        await bot.send_message(
            ADMIN_ID,
            f"🆕 <b>Новая запись #{booking_id}</b>\n\n{booking_summary(data)}\n"
            f"👤 {escape(data['name'])}, {escape(data['phone'])}",
        )


# ---------- Отмена записи клиентом ----------

@dp.callback_query(F.data.startswith("cancel:"))
async def cancel(callback: CallbackQuery, bot: Bot):
    booking = db.cancel_booking(int(callback.data.split(":")[1]), callback.from_user.id)
    if booking is None:
        await callback.answer("Запись не найдена", show_alert=True)
        return
    await callback.message.edit_text("❌ Запись отменена")
    await callback.answer()
    if ADMIN_ID:
        await bot.send_message(
            ADMIN_ID, f"❌ Клиент отменил запись #{booking['id']}\n\n{booking_summary(dict(booking))}"
        )


# ---------- Панель администратора ----------

@dp.message(Command("admin"), F.from_user.id == ADMIN_ID)
async def admin(message: Message):
    bookings = db.upcoming_bookings()
    if not bookings:
        await message.answer("Предстоящих записей нет.")
        return
    lines = ["📋 <b>Предстоящие записи</b>\n"]
    for b in bookings:
        service_name = SERVICES[b["service"]][0]
        day = kb.format_day(date.fromisoformat(b["day"]))
        lines.append(f"<b>{day} {b['time']}</b> — {service_name}\n   {escape(b['name'])}, {escape(b['phone'])}")
    await message.answer("\n".join(lines))


async def main():
    logging.basicConfig(level=logging.INFO)
    if not BOT_TOKEN:
        raise SystemExit("Не найден BOT_TOKEN. Создай файл .env по примеру .env.example")
    db.init_db()
    bot = Bot(BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
