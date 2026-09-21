"""SQLite database connection and schema setup."""
import sqlite3
from contextlib import contextmanager
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)
DB_PATH = DATA_DIR / "family.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS people (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT NOT NULL,
    last_name TEXT,
    dob TEXT,
    dod TEXT,
    gender TEXT,
    photo_url TEXT,
    notes TEXT,
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


def init_db() -> None:
    with db_session() as conn:
        conn.executescript(SCHEMA)
