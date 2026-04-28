from __future__ import annotations

import aiosqlite
from datetime import datetime
from pathlib import Path
from typing import Any

from config import settings

SCHEMA = """
PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id INTEGER UNIQUE NOT NULL,
    first_name TEXT NOT NULL,
    age INTEGER NOT NULL,
    username TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    card_type TEXT NOT NULL,
    organization TEXT NOT NULL,
    full_name TEXT NOT NULL,
    position TEXT,
    phone TEXT,
    email TEXT,
    website TEXT,
    address TEXT,
    slogan TEXT,
    colors TEXT,
    expiry TEXT,
    notes TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY(user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS generated_cards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    template_id INTEGER,
    image_path TEXT NOT NULL,
    ai_text TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY(user_id) REFERENCES users(id),
    FOREIGN KEY(template_id) REFERENCES templates(id)
);
"""


class Database:
    def __init__(self, path: str):
        self.path = path
        self._conn: aiosqlite.Connection | None = None

    async def connect(self) -> None:
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = await aiosqlite.connect(self.path)
        self._conn.row_factory = aiosqlite.Row
        await self._conn.executescript(SCHEMA)
        await self._conn.commit()

    async def close(self) -> None:
        if self._conn:
            await self._conn.close()
            self._conn = None

    @property
    def conn(self) -> aiosqlite.Connection:
        if not self._conn:
            raise RuntimeError("Database is not connected")
        return self._conn

    async def get_user(self, telegram_id: int):
        cur = await self.conn.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
        return await cur.fetchone()

    async def create_or_update_user(self, telegram_id: int, first_name: str, age: int, username: str | None):
        existing = await self.get_user(telegram_id)
        now = datetime.utcnow().isoformat()
        if existing:
            await self.conn.execute(
                "UPDATE users SET first_name = ?, age = ?, username = ? WHERE telegram_id = ?",
                (first_name, age, username, telegram_id),
            )
        else:
            await self.conn.execute(
                "INSERT INTO users (telegram_id, first_name, age, username, created_at) VALUES (?, ?, ?, ?, ?)",
                (telegram_id, first_name, age, username, now),
            )
        await self.conn.commit()
        return await self.get_user(telegram_id)

    async def get_templates(self, user_id: int):
        cur = await self.conn.execute(
            "SELECT * FROM templates WHERE user_id = ? ORDER BY id DESC",
            (user_id,),
        )
        return await cur.fetchall()

    async def get_template(self, template_id: int):
        cur = await self.conn.execute("SELECT * FROM templates WHERE id = ?", (template_id,))
        return await cur.fetchone()

    async def create_template(self, user_id: int, data: dict[str, Any]):
        now = datetime.utcnow().isoformat()
        await self.conn.execute(
            """
            INSERT INTO templates
            (user_id, name, card_type, organization, full_name, position, phone, email, website, address, slogan, colors, expiry, notes, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                data["name"],
                data["card_type"],
                data["organization"],
                data["full_name"],
                data.get("position", ""),
                data.get("phone", ""),
                data.get("email", ""),
                data.get("website", ""),
                data.get("address", ""),
                data.get("slogan", ""),
                data.get("colors", ""),
                data.get("expiry", ""),
                data.get("notes", ""),
                now,
            ),
        )
        await self.conn.commit()
        cur = await self.conn.execute("SELECT last_insert_rowid()")
        row = await cur.fetchone()
        return int(row[0])

    async def save_generated_card(self, user_id: int, template_id: int | None, image_path: str, ai_text: str | None):
        now = datetime.utcnow().isoformat()
        await self.conn.execute(
            "INSERT INTO generated_cards (user_id, template_id, image_path, ai_text, created_at) VALUES (?, ?, ?, ?, ?)",
            (user_id, template_id, image_path, ai_text, now),
        )
        await self.conn.commit()

    async def get_stats(self, user_id: int) -> dict[str, int]:
        cur = await self.conn.execute("SELECT COUNT(*) FROM templates WHERE user_id = ?", (user_id,))
        templates = (await cur.fetchone())[0]
        cur = await self.conn.execute("SELECT COUNT(*) FROM generated_cards WHERE user_id = ?", (user_id,))
        cards = (await cur.fetchone())[0]
        return {"templates": templates, "cards": cards}


db = Database(settings.database_url)
