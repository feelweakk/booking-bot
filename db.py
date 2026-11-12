"""Bookings database (SQLite)."""

import sqlite3
from datetime import date

DB_PATH = "bookings.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # access columns by name
    return conn


def init_db():
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS bookings (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id    INTEGER NOT NULL,
                name       TEXT    NOT NULL,
                phone      TEXT    NOT NULL,
                service    TEXT    NOT NULL,
                day        TEXT    NOT NULL,   -- 2026-11-20
                time       TEXT    NOT NULL,   -- 14:00
                created_at TEXT    NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (day, time)             -- one booking per time slot
            )
            """
        )


def taken_times(day: str) -> set[str]:
    """Time slots that are already booked on this day."""
    with get_connection() as conn:
        rows = conn.execute("SELECT time FROM bookings WHERE day = ?", (day,)).fetchall()
    return {row["time"] for row in rows}


def create_booking(user_id: int, name: str, phone: str, service: str, day: str, time: str):
    """Creates a booking. Returns its id, or None if the slot was just taken."""
    try:
        with get_connection() as conn:
            cur = conn.execute(
                "INSERT INTO bookings (user_id, name, phone, service, day, time) VALUES (?, ?, ?, ?, ?, ?)",
                (user_id, name, phone, service, day, time),
            )
            return cur.lastrowid
    except sqlite3.IntegrityError:
        return None


def user_bookings(user_id: int):
    """Upcoming bookings of one customer."""
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM bookings WHERE user_id = ? AND day >= ? ORDER BY day, time",
            (user_id, date.today().isoformat()),
        ).fetchall()


def upcoming_bookings():
    """All upcoming bookings — for the admin."""
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM bookings WHERE day >= ? ORDER BY day, time",
            (date.today().isoformat(),),
        ).fetchall()


def cancel_booking(booking_id: int, user_id: int):
    """Cancels a customer's booking. Returns the deleted booking or None."""
    with get_connection() as conn:
        booking = conn.execute(
            "SELECT * FROM bookings WHERE id = ? AND user_id = ?", (booking_id, user_id)
        ).fetchone()
        if booking:
            conn.execute("DELETE FROM bookings WHERE id = ?", (booking_id,))
        return booking
