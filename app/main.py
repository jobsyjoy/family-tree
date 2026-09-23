"""FastAPI application entry point."""
import os

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.database import init_db
from app.routes import auth, export, pages, people, relationships, reminders

app = FastAPI(title="Family Tree Dashboard")

app.add_middleware(
    SessionMiddleware,
    secret_key=os.environ.get("SESSION_SECRET", "change-me-please-woof"),
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(auth.router)
app.include_router(pages.router)
app.include_router(people.router)
app.include_router(relationships.router)
app.include_router(reminders.router)
app.include_router(export.router)


@app.on_event("startup")
def startup():
    added = init_db()
    if added:
        print(f"[db] added new person columns: {', '.join(added)}")
