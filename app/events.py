"""Compute upcoming birthdays + reminders, sorted by days-until-next-occurrence."""
from datetime import date
from typing import Optional

from app import repository


def _next_occurrence(month: int, day: int, today: date) -> date:
    """Find the next date (this year or next) matching month/day."""
    try:
        candidate = date(today.year, month, day)
    except ValueError:
        # handle Feb 29 on non-leap years -> bump to Mar 1
        candidate = date(today.year, 3, 1)
    if candidate < today:
        try:
            candidate = date(today.year + 1, month, day)
        except ValueError:
            candidate = date(today.year + 1, 3, 1)
    return candidate


def _parse_date(value: Optional[str]) -> Optional[date]:
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def get_upcoming_events(days_ahead: int = 365) -> list[dict]:
    """Merge birthdays (from people.dob) + custom reminders into one sorted feed."""
    today = date.today()
    events = []

    for person in repository.list_people():
        dob = _parse_date(person.get("dob"))
        if dob:
            next_date = _next_occurrence(dob.month, dob.day, today)
            turning_age = next_date.year - dob.year
            events.append({
                "type": "birthday",
                "title": f"{person['first_name']}'s Birthday (turning {turning_age})",
                "date": next_date.isoformat(),
                "days_until": (next_date - today).days,
                "person_id": person["id"],
            })

    for reminder in repository.list_reminders():
        r_date = _parse_date(reminder["reminder_date"])
        if not r_date:
            continue
        if reminder["repeat_yearly"]:
            next_date = _next_occurrence(r_date.month, r_date.day, today)
        else:
            next_date = r_date
            if next_date < today:
                continue
        person_name = None
        if reminder.get("first_name"):
            person_name = f"{reminder['first_name']} {reminder.get('last_name') or ''}".strip()
        events.append({
            "type": "reminder",
            "title": reminder["title"] + (f" ({person_name})" if person_name else ""),
            "date": next_date.isoformat(),
            "days_until": (next_date - today).days,
            "person_id": reminder.get("person_id"),
            "reminder_id": reminder["id"],
            "notes": reminder.get("notes"),
        })

    events = [e for e in events if 0 <= e["days_until"] <= days_ahead]
    events.sort(key=lambda e: e["days_until"])
    return events
