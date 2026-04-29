"""
database.py – Async SQLite operations via aiosqlite.
Tables: users, templates, generated_cards
"""

import logging
import aiosqlite
from config import DATABASE_PATH

logger = logging.getLogger(__name__)

# ─── Schema ─────────────────────────────────────────────────────────────────────
_SCHEMA = """
PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS users (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id INTEGER UNIQUE NOT NULL,
    username    TEXT,
    first_name  TEXT,
    name        TEXT    NOT NULL,
    age         INTEGER NOT NULL,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS templates (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER NOT NULL,
    template_name   TEXT    NOT NULL,
    card_type       TEXT    NOT NULL,
    org_name        TEXT    NOT NULL,
    holder_name     TEXT    NOT NULL,
    position        TEXT,
    phone           TEXT,
    email           TEXT,
    website         TEXT,
    card_number     TEXT,
    access_level    TEXT,
    membership_type TEXT,
    validity_date   TEXT,
    additional_info TEXT,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS generated_cards (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id        INTEGER NOT NULL,
    template_id    INTEGER NOT NULL,
    ai_content     TEXT,
    card_image_path TEXT,
    created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id)     REFERENCES users(id)     ON DELETE CASCADE,
    FOREIGN KEY (template_id) REFERENCES templates(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_users_tgid    ON users(telegram_id);
CREATE INDEX IF NOT EXISTS idx_tpl_user      ON templates(user_id);
CREATE INDEX IF NOT EXISTS idx_cards_user    ON generated_cards(user_id);
"""


async def init_db() -> None:
    """Create all tables and indexes."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.executescript(_SCHEMA)
        await db.commit()
    logger.info("✅ Database initialised at %s", DATABASE_PATH)


# ─── Users ──────────────────────────────────────────────────────────────────────

async def get_user(telegram_id: int) -> dict | None:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM users WHERE telegram_id = ?", (telegram_id,)
        ) as cur:
            row = await cur.fetchone()
            return dict(row) if row else None


async def create_user(
    telegram_id: int, username: str | None,
    first_name: str | None, name: str, age: int
) -> dict:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO users (telegram_id, username, first_name, name, age) "
            "VALUES (?, ?, ?, ?, ?)",
            (telegram_id, username, first_name, name, age),
        )
        await db.commit()
    return await get_user(telegram_id)


async def user_exists(telegram_id: int) -> bool:
    return await get_user(telegram_id) is not None


# ─── Templates ──────────────────────────────────────────────────────────────────

async def save_template(user_id: int, data: dict) -> int:
    """Insert a template row and return its id."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cur = await db.execute(
            """INSERT INTO templates
               (user_id, template_name, card_type, org_name, holder_name,
                position, phone, email, website, card_number, access_level,
                membership_type, validity_date, additional_info)
               VALUES (?,?,?,?,?, ?,?,?,?,?,?, ?,?,?)""",
            (
                user_id,
                data.get("template_name", "Без названия"),
                data.get("card_type", ""),
                data.get("org_name", ""),
                data.get("holder_name", ""),
                data.get("position"),
                data.get("phone"),
                data.get("email"),
                data.get("website"),
                data.get("card_number"),
                data.get("access_level"),
                data.get("membership_type"),
                data.get("validity_date"),
                data.get("additional_info"),
            ),
        )
        await db.commit()
        return cur.lastrowid


async def get_templates(user_id: int) -> list[dict]:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM templates WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,),
        ) as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]


async def get_template(template_id: int) -> dict | None:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM templates WHERE id = ?", (template_id,)
        ) as cur:
            row = await cur.fetchone()
            return dict(row) if row else None


async def delete_template(template_id: int, user_id: int) -> bool:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "DELETE FROM templates WHERE id = ? AND user_id = ?",
            (template_id, user_id),
        )
        await db.commit()
        return db.total_changes > 0


# ─── Generated Cards ────────────────────────────────────────────────────────────

async def save_card(user_id: int, template_id: int,
                    ai_content: str, image_path: str) -> int:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cur = await db.execute(
            "INSERT INTO generated_cards (user_id, template_id, ai_content, card_image_path) "
            "VALUES (?,?,?,?)",
            (user_id, template_id, ai_content, image_path),
        )
        await db.commit()
        return cur.lastrowid


# ─── Stats ──────────────────────────────────────────────────────────────────────

async def get_stats(user_id: int) -> dict:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute(
            "SELECT COUNT(*) FROM templates WHERE user_id = ?", (user_id,)
        ) as cur:
            tpl_count = (await cur.fetchone())[0]
        async with db.execute(
            "SELECT COUNT(*) FROM generated_cards WHERE user_id = ?", (user_id,)
        ) as cur:
            cards_count = (await cur.fetchone())[0]
    return {"templates": tpl_count, "generated": cards_count}
