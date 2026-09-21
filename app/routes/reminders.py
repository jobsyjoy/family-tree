"""Reminder CRUD routes."""
from typing import Optional

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app import auth, events, repository

router = APIRouter(prefix="/reminders")
templates = Jinja2Templates(directory="app/templates")


def _guard(request: Request):
    return auth.require_auth(request)


def _render_panel(request: Request):
    people = repository.list_people()
    reminders = repository.list_reminders()
    return templates.TemplateResponse(
        request, "partials/reminders_panel.html", {"people": people, "reminders": reminders}
    )


@router.get("", response_class=HTMLResponse)
def reminders_panel(request: Request):
    redirect = _guard(request)
    if redirect:
        return redirect
    return _render_panel(request)


@router.post("", response_class=HTMLResponse)
def create_reminder(
    request: Request,
    title: str = Form(...),
    reminder_date: str = Form(...),
    person_id: Optional[str] = Form(None),
    repeat_yearly: Optional[str] = Form(None),
    notes: str = Form(""),
):
    redirect = _guard(request)
    if redirect:
        return redirect
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
    redirect = _guard(request)
    if redirect:
        return redirect
    repository.delete_reminder(reminder_id)
    return _render_panel(request)


@router.get("/upcoming", response_class=HTMLResponse)
def upcoming_widget(request: Request):
    redirect = _guard(request)
    if redirect:
        return redirect
    upcoming = events.get_upcoming_events(days_ahead=60)
    return templates.TemplateResponse(
        request, "partials/upcoming_widget.html", {"upcoming": upcoming}
    )
