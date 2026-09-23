"""Main dashboard page, tree data endpoint, and the user guide."""
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import FileResponse, HTMLResponse

from app import events, tree
from app.routes.common import guard, render

router = APIRouter()

GUIDE_PATH = Path(__file__).parent.parent / "static" / "guide.html"


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


@router.get("/guide", response_class=HTMLResponse)
def user_guide():
    """The how-to manual. Deliberately public so it can be linked from
    exported files, which are opened by people with no login."""
    return FileResponse(GUIDE_PATH, media_type="text/html")
