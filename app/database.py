"""SQLite connection, schema setup, and lightweight auto-migration."""
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from app.fields import PERSON_FIELDS, column_definitions

DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)
DB_PATH = DATA_DIR / "family.db"

SCHEMA = f"""
CREATE TABLE IF NOT EXISTS people (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    {column_definitions()},
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS relationships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    person_a_id INTEGER NOT NULL REFERENCES people(id) ON DELETE CASCADE,
    person_b_id INTEGER NOT NULL REFERENCES people(id) ON DELETE CASCADE,
    relationship_type TEXT NOT NULL CHECK(relationship_type IN ('parent','spouse')),
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(person_a_id, person_b_id, relationship_type)
);

CREATE TABLE IF NOT EXISTS reminders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    person_id INTEGER REFERENCES people(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    reminder_date TEXT NOT NULL,
    repeat_yearly INTEGER DEFAULT 1,
    notes TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
"""


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def db_session():
    """Context manager yielding a connection, committing on success."""
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def _migrate_people(conn: sqlite3.Connection) -> list[str]:
    """Add any person columns missing from an older database.

    SQLite can only ADD COLUMN, which is all we need: new fields are
    always nullable extras. Existing rows keep their data.
    """
    existing = {row["name"] for row in conn.execute("PRAGMA table_info(people)")}
    added = []
    for field in PERSON_FIELDS:
        if field.name not in existing:
            # NOT NULL can't be added to a populated table without a default,
            # so migrated columns are always nullable.
            conn.execute(f"ALTER TABLE people ADD COLUMN {field.name} {field.sql_type}")
            added.append(field.name)
    return added


def init_db() -> list[str]:
    """Create tables if needed, then backfill any new columns."""
    with db_session() as conn:
        conn.executescript(SCHEMA)
        return _migrate_people(conn)
