"""Export routes: download the tree as a standalone, editable HTML file."""
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from app import export
from app.routes.common import guard

router = APIRouter(prefix="/export")

DEFAULT_TITLE = "Our Family Tree"


@router.get("/html")
def export_html(request: Request, title: str = DEFAULT_TITLE):
    """Return the whole tree as one self-contained file, as a download."""
    if blocked := guard(request):
        return blocked
    return HTMLResponse(
        content=export.build_export(title),
        headers={
            "Content-Disposition":
                f'attachment; filename="{export.suggested_filename(title)}"'
        },
    )


@router.get("/preview")
def export_preview(request: Request, title: str = DEFAULT_TITLE):
    """Same document, rendered inline so you can eyeball it before sharing."""
    if blocked := guard(request):
        return blocked
    return HTMLResponse(content=export.build_export(title))
