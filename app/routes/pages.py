"""Main dashboard page + tree data endpoint."""
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from app import events, tree
from app.routes.common import guard, render

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
def dashboard(request: Request):
    if blocked := guard(request):
        return blocked
    return render(
        request,
        "dashboard.html",
        upcoming=events.get_upcoming_events(days_ahead=60),
    )


@router.get("/api/tree-data")
def tree_data(request: Request):
    return guard(request) or tree.build_tree_data()
