"""Relationship management routes."""
from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse

from app import repository
from app.routes.common import guard, render

router = APIRouter(prefix="/relationships")


def _render_panel(request: Request):
    people = repository.list_people()
    return render(
        request,
        "partials/relationships_panel.html",
        people=people,
        relationships=repository.list_relationships(),
        people_by_id={p["id"]: p for p in people},
    )


@router.get("", response_class=HTMLResponse)
def relationships_panel(request: Request):
    return guard(request) or _render_panel(request)


@router.post("", response_class=HTMLResponse)
def create_relationship(
    request: Request,
    person_a_id: int = Form(...),
    person_b_id: int = Form(...),
    relationship_type: str = Form(...),
):
    if blocked := guard(request):
        return blocked
    if person_a_id != person_b_id and relationship_type in ("parent", "spouse"):
        repository.create_relationship(person_a_id, person_b_id, relationship_type)
    return _render_panel(request)


@router.delete("/{relationship_id}", response_class=HTMLResponse)
def delete_relationship(request: Request, relationship_id: int):
    if blocked := guard(request):
        return blocked
    repository.delete_relationship(relationship_id)
    return _render_panel(request)
