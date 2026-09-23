"""People CRUD routes, returning HTMX-friendly partial HTML.

Form parsing is generic: whatever app.fields declares is what we accept.
"""
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse

from app import repository
from app.fields import FIELD_NAMES
from app.routes.common import guard, render, templates  # noqa: F401

router = APIRouter(prefix="/people")


async def _form_data(request: Request) -> dict:
    form = await request.form()
    return {name: form.get(name, "") for name in FIELD_NAMES}


def _render_list(request: Request):
    return render(request, "partials/people_list.html",
                  people=repository.list_people())


def _render_form(request: Request, person: dict | None):
    return render(request, "partials/person_form.html", person=person)


@router.get("", response_class=HTMLResponse)
def list_people_partial(request: Request):
    return guard(request) or _render_list(request)


@router.get("/new", response_class=HTMLResponse)
def new_person_form(request: Request):
    return guard(request) or _render_form(request, None)


@router.get("/{person_id}/edit", response_class=HTMLResponse)
def edit_person_form(request: Request, person_id: int):
    if blocked := guard(request):
        return blocked
    person = repository.get_person(person_id)
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    return _render_form(request, person)


@router.post("", response_class=HTMLResponse)
async def create_person(request: Request):
    if blocked := guard(request):
        return blocked
    repository.create_person(await _form_data(request))
    return _render_list(request)


@router.post("/{person_id}", response_class=HTMLResponse)
async def update_person(request: Request, person_id: int):
    if blocked := guard(request):
        return blocked
    repository.update_person(person_id, await _form_data(request))
    return _render_list(request)


@router.delete("/{person_id}", response_class=HTMLResponse)
def delete_person(request: Request, person_id: int):
    if blocked := guard(request):
        return blocked
    repository.delete_person(person_id)
    return _render_list(request)
