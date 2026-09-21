"""Main dashboard page + tree data endpoint."""
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app import auth, events, tree

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
def dashboard(request: Request):
    redirect = auth.require_auth(request)
    if redirect:
        return redirect
    upcoming = events.get_upcoming_events(days_ahead=60)
    return templates.TemplateResponse(
        "dashboard.html", {"request": request, "upcoming": upcoming}
    )


@router.get("/api/tree-data")
def tree_data(request: Request):
    redirect = auth.require_auth(request)
    if redirect:
        return redirect
    return tree.build_tree_data()
