"""Shared route plumbing: one templates instance, one auth guard, one render.

Every route module used to build its own Jinja2Templates and re-implement
the same three-line auth dance. Now they don't.
"""
from fastapi import Request
from fastapi.templating import Jinja2Templates

from app import auth, fields

templates = Jinja2Templates(directory="app/templates")

# Field metadata is needed by nearly every template, so expose it globally
# instead of threading it through each TemplateResponse call.
templates.env.globals.update(
    field_groups=fields.FIELD_GROUPS,
    fields_in=fields.fields_in,
    summary_fields=fields.SUMMARY_FIELDS,
    # Plain dicts so |tojson works in templates and the browser can read it.
    field_meta=[{"name": f.name, "label": f.label} for f in fields.PERSON_FIELDS],
)


def guard(request: Request):
    """Return a redirect response if the user isn't logged in, else None."""
    return auth.require_auth(request)


def render(request: Request, template: str, **context):
    return templates.TemplateResponse(request, template, context)
