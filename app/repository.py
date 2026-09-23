"""Data-access functions for people, relationships, and reminders.

Kept separate from routes so route handlers stay thin (SRP FTW).
Person SQL is generated from app.fields, so adding a field is a one-liner.
"""
from typing import Optional

from app.database import db_session
from app.fields import FIELD_NAMES, clean

_COLUMNS = ", ".join(FIELD_NAMES)
_PLACEHOLDERS = ", ".join("?" for _ in FIELD_NAMES)
_ASSIGNMENTS = ", ".join(f"{name}=?" for name in FIELD_NAMES)


def _values(data: dict) -> tuple:
    cleaned = clean(data)
    return tuple(cleaned[name] for name in FIELD_NAMES)


# ---------- People ----------

def list_people() -> list[dict]:
    with db_session() as conn:
        rows = conn.execute(
            "SELECT * FROM people ORDER BY first_name COLLATE NOCASE"
        ).fetchall()
        return [dict(r) for r in rows]


def get_person(person_id: int) -> Optional[dict]:
    with db_session() as conn:
        row = conn.execute("SELECT * FROM people WHERE id = ?", (person_id,)).fetchone()
        return dict(row) if row else None


def create_person(data: dict) -> int:
    with db_session() as conn:
        cur = conn.execute(
            f"INSERT INTO people ({_COLUMNS}) VALUES ({_PLACEHOLDERS})",
            _values(data),
        )
        return cur.lastrowid


def update_person(person_id: int, data: dict) -> None:
    with db_session() as conn:
        conn.execute(
            f"UPDATE people SET {_ASSIGNMENTS} WHERE id=?",
            _values(data) + (person_id,),
        )


def delete_person(person_id: int) -> None:
    with db_session() as conn:
        conn.execute("DELETE FROM people WHERE id = ?", (person_id,))


# ---------- Relationships ----------

def list_relationships() -> list[dict]:
    with db_session() as conn:
        rows = conn.execute("SELECT * FROM relationships").fetchall()
        return [dict(r) for r in rows]


def create_relationship(person_a_id: int, person_b_id: int, rel_type: str) -> None:
    with db_session() as conn:
        conn.execute(
            """INSERT OR IGNORE INTO relationships (person_a_id, person_b_id, relationship_type)
               VALUES (?, ?, ?)""",
            (person_a_id, person_b_id, rel_type),
        )


def delete_relationship(relationship_id: int) -> None:
    with db_session() as conn:
        conn.execute("DELETE FROM relationships WHERE id = ?", (relationship_id,))


def get_children(person_id: int) -> list[dict]:
    """People where person_id is the parent (person_a_id)."""
    with db_session() as conn:
        rows = conn.execute(
            """SELECT p.* FROM people p
               JOIN relationships r ON r.person_b_id = p.id
               WHERE r.person_a_id = ? AND r.relationship_type = 'parent'""",
            (person_id,),
        ).fetchall()
        return [dict(r) for r in rows]


def get_parents(person_id: int) -> list[dict]:
    with db_session() as conn:
        rows = conn.execute(
            """SELECT p.* FROM people p
               JOIN relationships r ON r.person_a_id = p.id
               WHERE r.person_b_id = ? AND r.relationship_type = 'parent'""",
            (person_id,),
        ).fetchall()
        return [dict(r) for r in rows]


def get_spouses(person_id: int) -> list[dict]:
    with db_session() as conn:
        rows = conn.execute(
            """SELECT p.* FROM people p
               JOIN relationships r ON (r.person_a_id = p.id OR r.person_b_id = p.id)
               WHERE (r.person_a_id = ? OR r.person_b_id = ?)
                 AND r.relationship_type = 'spouse' AND p.id != ?""",
            (person_id, person_id, person_id),
        ).fetchall()
        return [dict(r) for r in rows]


# ---------- Reminders ----------

def list_reminders() -> list[dict]:
    with db_session() as conn:
        rows = conn.execute(
            """SELECT r.*, p.first_name, p.last_name FROM reminders r
               LEFT JOIN people p ON p.id = r.person_id
               ORDER BY r.reminder_date"""
        ).fetchall()
        return [dict(r) for r in rows]


def create_reminder(data: dict) -> int:
    with db_session() as conn:
        cur = conn.execute(
            """INSERT INTO reminders (person_id, title, reminder_date, repeat_yearly, notes)
               VALUES (?, ?, ?, ?, ?)""",
            (
                data.get("person_id"),
                data["title"],
                data["reminder_date"],
                1 if data.get("repeat_yearly", True) else 0,
                data.get("notes"),
            ),
        )
        return cur.lastrowid


def delete_reminder(reminder_id: int) -> None:
    with db_session() as conn:
        conn.execute("DELETE FROM reminders WHERE id = ?", (reminder_id,))
