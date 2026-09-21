"""Login/logout routes."""
from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app import auth

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "error": None})


@router.post("/login", response_class=HTMLResponse)
def login_submit(request: Request, pin: str = Form(...)):
    if pin == auth.get_pin():
        auth.login(request)
        return RedirectResponse(url="/", status_code=303)
    return templates.TemplateResponse(
        "login.html", {"request": request, "error": "Wrong PIN, try again!"}
    )


@router.get("/logout")
def logout(request: Request):
    auth.logout(request)
    return RedirectResponse(url="/login", status_code=303)
