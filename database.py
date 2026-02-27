import aiosqlite
from datetime import datetime
from typing import Any, Dict, List, Optional

from config import settings


DB_PATH = settings.database_path


CREATE_QUERIES = [
    """
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        phone TEXT,
        room_number TEXT,
        language TEXT DEFAULT 'ru',
        registered_at TIMESTAMP,
        last_active TIMESTAMP
        consent_accepted INTEGER DEFAULT 0,          -- Флаг согласия с политикой
        consent_timestamp TIMESTAMP
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS breakfast_orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        date DATE,
        time TEXT,
        dishes TEXT,
        quantity INTEGER,
        status TEXT,
        rating INTEGER,
        created_at TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(user_id)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS support_tickets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        issue TEXT,
        urgency TEXT,
        status TEXT DEFAULT 'new',
        rating INTEGER,
        created_at TIMESTAMP,
        resolved_at TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(user_id)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS linen_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        type TEXT,
        quantity INTEGER,
        preferred_time TEXT,
        status TEXT DEFAULT 'pending',
        rating INTEGER,
        created_at TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(user_id)
    );
    """,
]


async def init_db() -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        for query in CREATE_QUERIES:
            await db.execute(query)
        await db.commit()


async def upsert_user(
    user_id: int, phone: str, room_number: str, language: str, consent_accepted: bool = False
) -> None:
    now = datetime.utcnow().isoformat()
    consent_val = int(consent_accepted)
    consent_time = now if consent_val else None

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO users (
                user_id, phone, room_number, language, 
                registered_at, last_active, 
                consent_accepted, consent_timestamp
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                phone = excluded.phone,
                room_number = excluded.room_number,
                language = excluded.language,
                last_active = excluded.last_active,
                consent_accepted = COALESCE(excluded.consent_accepted, consent_accepted),
                consent_timestamp = COALESCE(excluded.consent_timestamp, consent_timestamp);
            """,
            (
                user_id,
                phone,
                room_number,
                language,
                now,
                now,
                consent_val,
                consent_time,
            ),
        )
        await db.commit()


async def get_user(user_id: int) -> Optional[Dict[str, Any]]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM users WHERE user_id = ?", (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


async def set_user_language(user_id: int, language: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET language = ? WHERE user_id = ?",
            (language, user_id),
        )
        await db.commit()


async def add_breakfast_order(
    user_id: int, date: str, time: str, dishes: str, quantity: int
) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """
            INSERT INTO breakfast_orders (user_id, date, time, dishes, quantity, status, created_at)
            VALUES (?, ?, ?, ?, ?, 'new', ?)
            """,
            (user_id, date, time, dishes, quantity, datetime.utcnow().isoformat()),
        )
        await db.commit()
        return cursor.lastrowid


async def get_breakfast_orders(user_id: int) -> List[Dict[str, Any]]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM breakfast_orders WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,),
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]


async def set_breakfast_rating(order_id: int, rating: int) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE breakfast_orders SET rating = ? WHERE id = ?",
            (rating, order_id),
        )
        await db.commit()


async def add_support_ticket(
    user_id: int, issue: str, urgency: str='normal'
) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """
            INSERT INTO support_tickets (user_id, issue, urgency, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (user_id, issue, urgency, datetime.utcnow().isoformat()),
        )
        await db.commit()
        return cursor.lastrowid


async def set_support_rating(ticket_id: int, rating: int) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE support_tickets SET rating = ? WHERE id = ?",
            (rating, ticket_id),
        )
        await db.commit()


async def add_linen_request(
    user_id: int, type_: str, quantity: int, preferred_time: str
) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """
            INSERT INTO linen_requests (user_id, type, quantity, preferred_time, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (user_id, type_, quantity, preferred_time, datetime.utcnow().isoformat()),
        )
        await db.commit()
        return cursor.lastrowid


async def set_linen_rating(request_id: int, rating: int) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE linen_requests SET rating = ? WHERE id = ?",
            (rating, request_id),
        )
        await db.commit()

