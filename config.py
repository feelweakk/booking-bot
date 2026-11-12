"""Bot settings. For a new client you usually only change this file."""

import os

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))  # owner's Telegram ID — receives new bookings

BUSINESS_NAME = "Sharp Cut Barbershop"
BUSINESS_INFO = (
    "📍 10 Main Street\n"
    "🕙 Open daily 10:00 – 20:00\n"
    "📞 +00 000 000 000"
)
CURRENCY = "€"

# Services: code -> (name, price, duration in minutes)
SERVICES = {
    "haircut": ("Men's haircut", 25, 60),
    "beard": ("Beard trim", 15, 30),
    "combo": ("Haircut + beard", 35, 90),
    "kids": ("Kids' haircut", 18, 45),
}

# Time slots available for booking
WORK_HOURS = ["10:00", "11:00", "12:00", "13:00", "14:00", "15:00", "16:00", "17:00", "18:00", "19:00"]
DAYS_AHEAD = 7  # how many days ahead customers can book
