import sqlite3
from typing import Optional

from config import DB_NAME, AVAILABLE_TIMES, get_available_dates


class Database:
    def __init__(self, db_name: str = DB_NAME):
        self.db_name = db_name
        self.init_db()

    def get_connection(self):
        return sqlite3.connect(self.db_name)

    def init_db(self):
        conn = self.get_connection()
        cur = conn.cursor()

        # Таблица Telegram-пользователей (отдельная от users веб-сайта)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS telegram_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER UNIQUE NOT NULL,
            full_name TEXT NOT NULL,
            age INTEGER NOT NULL,
            gender TEXT NOT NULL
        )
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS slots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            slot_date TEXT NOT NULL,
            slot_time TEXT NOT NULL,
            is_booked INTEGER NOT NULL DEFAULT 0,
            UNIQUE(slot_date, slot_time)
        )
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            slot_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT NOT NULL DEFAULT 'active',
            FOREIGN KEY(user_id) REFERENCES telegram_users(id),
            FOREIGN KEY(slot_id) REFERENCES slots(id)
        )
        """)

        conn.commit()
        conn.close()

        self.seed_slots()

    def seed_slots(self):
        conn = self.get_connection()
        cur = conn.cursor()

        for date in get_available_dates():
            for time in AVAILABLE_TIMES:
                cur.execute("""
                INSERT OR IGNORE INTO slots (slot_date, slot_time, is_booked)
                VALUES (?, ?, 0)
                """, (date, time))

        conn.commit()
        conn.close()

    def get_user_by_telegram_id(self, telegram_id: int) -> Optional[tuple]:
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute("""
        SELECT id, telegram_id, full_name, age, gender
        FROM telegram_users
        WHERE telegram_id = ?
        """, (telegram_id,))
        user = cur.fetchone()
        conn.close()
        return user

    def create_or_update_user(self, telegram_id: int, full_name: str, age: int, gender: str) -> int:
        existing_user = self.get_user_by_telegram_id(telegram_id)

        conn = self.get_connection()
        cur = conn.cursor()

        if existing_user:
            cur.execute("""
            UPDATE telegram_users
            SET full_name = ?, age = ?, gender = ?
            WHERE telegram_id = ?
            """, (full_name, age, gender, telegram_id))
            user_id = existing_user[0]
        else:
            cur.execute("""
            INSERT INTO telegram_users (telegram_id, full_name, age, gender)
            VALUES (?, ?, ?, ?)
            """, (telegram_id, full_name, age, gender))
            user_id = cur.lastrowid

        conn.commit()
        conn.close()
        return user_id

    def get_free_times_by_date(self, selected_date: str) -> list[str]:
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute("""
        SELECT slot_time
        FROM slots
        WHERE slot_date = ? AND is_booked = 0
        ORDER BY slot_time
        """, (selected_date,))
        times = [row[0] for row in cur.fetchall()]
        conn.close()
        return times

    def get_slot_id(self, selected_date: str, selected_time: str) -> Optional[int]:
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute("""
        SELECT id
        FROM slots
        WHERE slot_date = ? AND slot_time = ?
        """, (selected_date, selected_time))
        row = cur.fetchone()
        conn.close()
        return row[0] if row else None

    def is_slot_free(self, slot_id: int) -> bool:
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute("""
        SELECT is_booked
        FROM slots
        WHERE id = ?
        """, (slot_id,))
        row = cur.fetchone()
        conn.close()
        return bool(row) and row[0] == 0

    def create_appointment(self, user_id: int, slot_id: int) -> bool:
        conn = self.get_connection()
        cur = conn.cursor()

        try:
            cur.execute("BEGIN IMMEDIATE")

            cur.execute("""
            SELECT is_booked
            FROM slots
            WHERE id = ?
            """, (slot_id,))
            row = cur.fetchone()

            if not row or row[0] == 1:
                conn.rollback()
                conn.close()
                return False

            cur.execute("""
            UPDATE slots
            SET is_booked = 1
            WHERE id = ? AND is_booked = 0
            """, (slot_id,))

            if cur.rowcount == 0:
                conn.rollback()
                conn.close()
                return False

            cur.execute("""
            INSERT INTO appointments (user_id, slot_id, status)
            VALUES (?, ?, 'active')
            """, (user_id, slot_id))

            conn.commit()
            conn.close()
            return True

        except sqlite3.IntegrityError:
            conn.rollback()
            conn.close()
            return False
        except Exception:
            conn.rollback()
            conn.close()
            return False

    def get_user_active_appointment(self, telegram_id: int) -> Optional[tuple]:
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute("""
        SELECT a.id, s.slot_date, s.slot_time, u.full_name
        FROM appointments a
        JOIN telegram_users u ON a.user_id = u.id
        JOIN slots s ON a.slot_id = s.id
        WHERE u.telegram_id = ? AND a.status = 'active'
        ORDER BY a.created_at DESC
        LIMIT 1
        """, (telegram_id,))
        row = cur.fetchone()
        conn.close()
        return row

    def cancel_appointment(self, appointment_id: int, telegram_id: int) -> bool:
        conn = self.get_connection()
        cur = conn.cursor()

        try:
            cur.execute("BEGIN IMMEDIATE")

            cur.execute("""
            SELECT a.slot_id
            FROM appointments a
            JOIN telegram_users u ON a.user_id = u.id
            WHERE a.id = ? AND u.telegram_id = ? AND a.status = 'active'
            """, (appointment_id, telegram_id))
            row = cur.fetchone()

            if not row:
                conn.rollback()
                conn.close()
                return False

            slot_id = row[0]

            cur.execute("""
            UPDATE appointments
            SET status = 'cancelled'
            WHERE id = ?
            """, (appointment_id,))

            cur.execute("""
            UPDATE slots
            SET is_booked = 0
            WHERE id = ?
            """, (slot_id,))

            conn.commit()
            conn.close()
            return True

        except Exception:
            conn.rollback()
            conn.close()
            return False
