"""База данных записей (SQLite)."""

import sqlite3
from datetime import date

DB_PATH = "bookings.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
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
                UNIQUE (day, time)             -- на одно время — одна запись
            )
            """
        )


def taken_times(day: str) -> set[str]:
    """Какие слоты в этот день уже заняты."""
    with get_connection() as conn:
        rows = conn.execute("SELECT time FROM bookings WHERE day = ?", (day,)).fetchall()
    return {row["time"] for row in rows}


def create_booking(user_id: int, name: str, phone: str, service: str, day: str, time: str):
    """Создаёт запись. Возвращает её id или None, если время уже успели занять."""
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
    """Будущие записи пользователя."""
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM bookings WHERE user_id = ? AND day >= ? ORDER BY day, time",
            (user_id, date.today().isoformat()),
        ).fetchall()


def upcoming_bookings():
    """Все будущие записи — для администратора."""
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM bookings WHERE day >= ? ORDER BY day, time",
            (date.today().isoformat(),),
        ).fetchall()


def cancel_booking(booking_id: int, user_id: int):
    """Отменяет запись пользователя. Возвращает удалённую запись или None."""
    with get_connection() as conn:
        booking = conn.execute(
            "SELECT * FROM bookings WHERE id = ? AND user_id = ?", (booking_id, user_id)
        ).fetchone()
        if booking:
            conn.execute("DELETE FROM bookings WHERE id = ?", (booking_id,))
        return booking
