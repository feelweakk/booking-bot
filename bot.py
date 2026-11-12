"""Telegram bot for online booking (barbershop, beauty salon, tutor, repair shop).

Run:
    pip install -r requirements.txt
    copy .env.example to .env and fill it in
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
from config import ADMIN_ID, BOT_TOKEN, BUSINESS_INFO, BUSINESS_NAME, CURRENCY, SERVICES

dp = Dispatcher()


class Booking(StatesGroup):
    """Booking steps. The bot remembers which step each customer is on."""

    service = State()
    day = State()
    time = State()
    name = State()
    phone = State()
    confirm = State()


def booking_summary(data: dict) -> str:
    name, price, duration = SERVICES[data["service"]]
    return (
        f"💈 Service: <b>{name}</b> ({duration} min)\n"
        f"💰 Price: <b>{CURRENCY}{price}</b>\n"
        f"📅 Date: <b>{kb.format_day(date.fromisoformat(data['day']))}</b>\n"
        f"🕐 Time: <b>{data['time']}</b>"
    )


# ---------- Main menu ----------

@dp.message(CommandStart())
async def start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        f"Hi there! 👋 This is the <b>{BUSINESS_NAME}</b> bot.\n\n"
        "Book an appointment in under a minute — no calls, no waiting.",
        reply_markup=kb.main_menu,
    )


@dp.message(F.text == kb.BTN_INFO)
async def info(message: Message):
    await message.answer(f"<b>{BUSINESS_NAME}</b>\n\n{BUSINESS_INFO}")


@dp.message(F.text == kb.BTN_MY)
async def my_bookings(message: Message):
    bookings = db.user_bookings(message.from_user.id)
    if not bookings:
        await message.answer("You have no upcoming bookings.")
        return
    for b in bookings:
        await message.answer(booking_summary(dict(b)), reply_markup=kb.cancel_booking_keyboard(b["id"]))


# ---------- Booking: step 1 — service ----------

@dp.message(F.text == kb.BTN_BOOK)
async def book_start(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(Booking.service)
    await message.answer("Choose a service:", reply_markup=kb.services_keyboard())


@dp.callback_query(Booking.service, F.data.startswith("service:"))
async def choose_service(callback: CallbackQuery, state: FSMContext):
    await state.update_data(service=callback.data.split(":")[1])
    await state.set_state(Booking.day)
    await callback.message.edit_text("Choose a day:", reply_markup=kb.days_keyboard())
    await callback.answer()


# ---------- Step 2 — day ----------

@dp.callback_query(Booking.day, F.data.startswith("day:"))
async def choose_day(callback: CallbackQuery, state: FSMContext):
    day = callback.data.split(":")[1]
    free = kb.free_times_for(day, db.taken_times(day))
    if not free:
        await callback.answer("Sorry, this day is fully booked 😔", show_alert=True)
        return
    await state.update_data(day=day)
    await state.set_state(Booking.time)
    await callback.message.edit_text("Choose a time:", reply_markup=kb.times_keyboard(free))
    await callback.answer()


# ---------- Step 3 — time ----------

@dp.callback_query(Booking.time, F.data.startswith("time:"))
async def choose_time(callback: CallbackQuery, state: FSMContext):
    await state.update_data(time=callback.data.split(":", 1)[1])
    await state.set_state(Booking.name)
    await callback.message.edit_text("What's your name?")
    await callback.answer()


# ---------- "Back" buttons ----------

@dp.callback_query(F.data == "back:services")
async def back_to_services(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Booking.service)
    await callback.message.edit_text("Choose a service:", reply_markup=kb.services_keyboard())
    await callback.answer()


@dp.callback_query(F.data == "back:days")
async def back_to_days(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Booking.day)
    await callback.message.edit_text("Choose a day:", reply_markup=kb.days_keyboard())
    await callback.answer()


# ---------- Step 4 — name and phone ----------

@dp.message(Booking.name, F.text)
async def enter_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text.strip()[:50])
    await state.set_state(Booking.phone)
    await message.answer(
        "Share your phone number with the button below, or type it in:",
        reply_markup=kb.phone_keyboard,
    )


@dp.message(Booking.phone, F.contact | F.text)
async def enter_phone(message: Message, state: FSMContext):
    phone = message.contact.phone_number if message.contact else message.text.strip()
    digits = "".join(ch for ch in phone if ch.isdigit())
    if not 7 <= len(digits) <= 15:
        await message.answer("That doesn't look like a valid number. Please try again:")
        return

    await state.update_data(phone=phone)
    await state.set_state(Booking.confirm)
    data = await state.get_data()
    await message.answer("Almost done!", reply_markup=kb.main_menu)
    await message.answer(
        f"Please check your booking:\n\n{booking_summary(data)}\n👤 {escape(data['name'])}, {escape(phone)}",
        reply_markup=kb.confirm_keyboard(),
    )


# ---------- Step 5 — confirmation ----------

@dp.callback_query(Booking.confirm, F.data.startswith("confirm:"))
async def confirm(callback: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    await state.clear()

    if callback.data == "confirm:no":
        await callback.message.edit_text("Booking cancelled.")
        await callback.answer()
        return

    booking_id = db.create_booking(
        callback.from_user.id, data["name"], data["phone"], data["service"], data["day"], data["time"]
    )
    if booking_id is None:
        await callback.message.edit_text("😔 Someone just took this slot. Please choose another time.")
        await callback.answer()
        return

    await callback.message.edit_text(f"✅ You're booked!\n\n{booking_summary(data)}\n\nSee you soon!")
    await callback.answer()

    # Notify the owner
    if ADMIN_ID:
        await bot.send_message(
            ADMIN_ID,
            f"🆕 <b>New booking #{booking_id}</b>\n\n{booking_summary(data)}\n"
            f"👤 {escape(data['name'])}, {escape(data['phone'])}",
        )


# ---------- Customer cancels a booking ----------

@dp.callback_query(F.data.startswith("cancel:"))
async def cancel(callback: CallbackQuery, bot: Bot):
    booking = db.cancel_booking(int(callback.data.split(":")[1]), callback.from_user.id)
    if booking is None:
        await callback.answer("Booking not found", show_alert=True)
        return
    await callback.message.edit_text("❌ Booking cancelled")
    await callback.answer()
    if ADMIN_ID:
        await bot.send_message(
            ADMIN_ID, f"❌ Customer cancelled booking #{booking['id']}\n\n{booking_summary(dict(booking))}"
        )


# ---------- Admin panel ----------

@dp.message(Command("admin"), F.from_user.id == ADMIN_ID)
async def admin(message: Message):
    bookings = db.upcoming_bookings()
    if not bookings:
        await message.answer("No upcoming bookings.")
        return
    lines = ["📋 <b>Upcoming bookings</b>\n"]
    for b in bookings:
        service_name = SERVICES[b["service"]][0]
        day = kb.format_day(date.fromisoformat(b["day"]))
        lines.append(f"<b>{day} {b['time']}</b> — {service_name}\n   {escape(b['name'])}, {escape(b['phone'])}")
    await message.answer("\n".join(lines))


async def main():
    logging.basicConfig(level=logging.INFO)
    if not BOT_TOKEN:
        raise SystemExit("BOT_TOKEN not found. Create a .env file based on .env.example")
    db.init_db()
    bot = Bot(BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
