# 💈 Booking Bot — online appointments in Telegram

A ready-to-use bot for booking customers: barbershops, beauty salons, nail artists, tutors, repair shops.
Customers book in under a minute without calling, and the owner gets notified instantly.

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)
![aiogram](https://img.shields.io/badge/aiogram-3-26A5E4?logo=telegram&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-003B57?logo=sqlite&logoColor=white)

## ✨ Features

**For customers**
- Choose a service with its price and duration
- Pick a day (up to a week ahead) and a free time slot
- Share a phone number with one tap
- Confirm the booking
- "My bookings" with the option to cancel

**For the owner**
- Instant notification about every new booking and cancellation
- `/admin` command — list of all upcoming bookings
- Booked slots are hidden automatically, double booking is impossible

## 🔄 Booking flow

```
📅 Book now → Service → Day → Time → Name → Phone → ✅ Confirm
                                                        ↓
                                          🔔 Owner gets notified
```

## ⚙️ Adapting it to your business

Everything business-specific lives in [`config.py`](config.py):

```python
BUSINESS_NAME = "Sharp Cut Barbershop"
CURRENCY = "€"

SERVICES = {
    "haircut": ("Men's haircut", 25, 60),   # name, price, minutes
    "beard":   ("Beard trim", 15, 30),
}

WORK_HOURS = ["10:00", "11:00", "12:00", ...]
```

## 🚀 Getting started

```bash
git clone https://github.com/feelweakk/booking-bot.git
cd booking-bot
pip install -r requirements.txt
```

1. Create a bot with [@BotFather](https://t.me/BotFather) and copy the token
2. Get your Telegram ID from [@userinfobot](https://t.me/userinfobot)
3. Copy `.env.example` to `.env` and fill in both values
4. Run:

```bash
python bot.py
```

## 📁 Project structure

```
├── bot.py         # logic: booking steps (FSM), handlers, admin panel
├── keyboards.py   # all buttons and keyboards
├── db.py          # bookings database (SQLite)
├── config.py      # business settings: services, opening hours
└── .env.example   # example environment file
```

## 🔮 Available as add-ons

- Reminder to the customer 2 hours before the visit
- Multiple staff members with their own schedules
- Online payments and deposits
- Export bookings to Google Sheets
- Multi-language support

---

Want a bot like this for your business? **Luka · [fykkkke](https://github.com/feelweakk)** — [Telegram](https://t.me/fykkkkke)
