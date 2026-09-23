"""Reminder CRUD routes."""
from typing import Optional

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse

from app import events, repository
from app.routes.common import guard, render

router = APIRouter(prefix="/reminders")


def _render_panel(request: Request):
    return render(
        request,
        "partials/reminders_panel.html",
        people=repository.list_people(),
        reminders=repository.list_reminders(),
    )


@router.get("", response_class=HTMLResponse)
def reminders_panel(request: Request):
    return guard(request) or _render_panel(request)


@router.post("", response_class=HTMLResponse)
def create_reminder(
    request: Request,
    title: str = Form(...),
    reminder_date: str = Form(...),
    person_id: Optional[str] = Form(None),
    repeat_yearly: Optional[str] = Form(None),
    notes: str = Form(""),
):
    if blocked := guard(request):
        return blocked
    repository.create_reminder({
        "person_id": int(person_id) if person_id else None,
        "title": title,
        "reminder_date": reminder_date,
        "repeat_yearly": bool(repeat_yearly),
        "notes": notes or None,
    })
    return _render_panel(request)


@router.delete("/{reminder_id}", response_class=HTMLResponse)
def delete_reminder(request: Request, reminder_id: int):
    if blocked := guard(request):
        return blocked
    repository.delete_reminder(reminder_id)
    return _render_panel(request)


@router.get("/upcoming", response_class=HTMLResponse)
def upcoming_widget(request: Request):
    if blocked := guard(request):
        return blocked
    return render(
        request,
        "partials/upcoming_widget.html",
        upcoming=events.get_upcoming_events(days_ahead=60),
    )
