"""People CRUD routes, returning HTMX-friendly partial HTML."""
from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from typing import Optional

from app import auth, repository

router = APIRouter(prefix="/people")
templates = Jinja2Templates(directory="app/templates")


def _guard(request: Request):
    return auth.require_auth(request)


@router.get("", response_class=HTMLResponse)
def list_people_partial(request: Request):
    redirect = _guard(request)
    if redirect:
        return redirect
    people = repository.list_people()
    return templates.TemplateResponse(
        "partials/people_list.html", {"request": request, "people": people}
    )


@router.get("/new", response_class=HTMLResponse)
def new_person_form(request: Request):
    redirect = _guard(request)
    if redirect:
        return redirect
    people = repository.list_people()
    return templates.TemplateResponse(
        "partials/person_form.html",
        {"request": request, "person": None, "people": people},
    )


@router.get("/{person_id}/edit", response_class=HTMLResponse)
def edit_person_form(request: Request, person_id: int):
    redirect = _guard(request)
    if redirect:
        return redirect
    person = repository.get_person(person_id)
    people = [p for p in repository.list_people() if p["id"] != person_id]
    return templates.TemplateResponse(
        "partials/person_form.html",
        {"request": request, "person": person, "people": people},
    )


@router.post("", response_class=HTMLResponse)
def create_person(
    request: Request,
    first_name: str = Form(...),
    last_name: str = Form(""),
    dob: str = Form(""),
    dod: str = Form(""),
    gender: str = Form(""),
    notes: str = Form(""),
):
    redirect = _guard(request)
    if redirect:
        return redirect
    repository.create_person({
        "first_name": first_name,
        "last_name": last_name or None,
        "dob": dob or None,
        "dod": dod or None,
        "gender": gender or None,
        "notes": notes or None,
    })
    people = repository.list_people()
    return templates.TemplateResponse(
        "partials/people_list.html", {"request": request, "people": people}
    )


@router.post("/{person_id}", response_class=HTMLResponse)
def update_person(
    request: Request,
    person_id: int,
    first_name: str = Form(...),
    last_name: str = Form(""),
    dob: str = Form(""),
    dod: str = Form(""),
    gender: str = Form(""),
    notes: str = Form(""),
):
    redirect = _guard(request)
    if redirect:
        return redirect
    repository.update_person(person_id, {
        "first_name": first_name,
        "last_name": last_name or None,
        "dob": dob or None,
        "dod": dod or None,
        "gender": gender or None,
        "notes": notes or None,
    })
    people = repository.list_people()
    return templates.TemplateResponse(
        "partials/people_list.html", {"request": request, "people": people}
    )


@router.delete("/{person_id}", response_class=HTMLResponse)
def delete_person(request: Request, person_id: int):
    redirect = _guard(request)
    if redirect:
        return redirect
    repository.delete_person(person_id)
    people = repository.list_people()
    return templates.TemplateResponse(
        "partials/people_list.html", {"request": request, "people": people}
    )
