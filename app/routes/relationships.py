"""Relationship management routes."""
from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app import auth, repository

router = APIRouter(prefix="/relationships")
templates = Jinja2Templates(directory="app/templates")


def _guard(request: Request):
    return auth.require_auth(request)


def _render_panel(request: Request):
    people = repository.list_people()
    rels = repository.list_relationships()
    people_by_id = {p["id"]: p for p in people}
    return templates.TemplateResponse(
        request,
        "partials/relationships_panel.html",
        {"people": people, "relationships": rels, "people_by_id": people_by_id},
    )


@router.get("", response_class=HTMLResponse)
def relationships_panel(request: Request):
    redirect = _guard(request)
    if redirect:
        return redirect
    return _render_panel(request)


@router.post("", response_class=HTMLResponse)
def create_relationship(
    request: Request,
    person_a_id: int = Form(...),
    person_b_id: int = Form(...),
    relationship_type: str = Form(...),
):
    redirect = _guard(request)
    if redirect:
        return redirect
    if person_a_id != person_b_id and relationship_type in ("parent", "spouse"):
        repository.create_relationship(person_a_id, person_b_id, relationship_type)
    return _render_panel(request)


@router.delete("/{relationship_id}", response_class=HTMLResponse)
def delete_relationship(request: Request, relationship_id: int):
    redirect = _guard(request)
    if redirect:
        return redirect
    repository.delete_relationship(relationship_id)
    return _render_panel(request)
