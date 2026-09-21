"""Simple PIN-based session auth. Not Fort Knox, but keeps randoms out."""
import os

from fastapi import Request
from fastapi.responses import RedirectResponse

SESSION_KEY = "authenticated"
DEFAULT_PIN = "1234"  # overridden via FAMILY_PIN env var, please change it!


def get_pin() -> str:
    return os.environ.get("FAMILY_PIN", DEFAULT_PIN)


def is_authenticated(request: Request) -> bool:
    return bool(request.session.get(SESSION_KEY))


def login(request: Request) -> None:
    request.session[SESSION_KEY] = True


def logout(request: Request) -> None:
    request.session.clear()


def require_auth(request: Request):
    """Dependency-style guard; returns a redirect if not logged in, else None."""
    if not is_authenticated(request):
        return RedirectResponse(url="/login", status_code=303)
    return None
