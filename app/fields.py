"""Single source of truth for the columns that describe a person.

Everything else -- the SQLite schema, migrations, INSERT/UPDATE statements,
the HTML form, and the export payload -- is derived from this list. Add a
field here and it flows everywhere. That is the whole point.
"""
from dataclasses import dataclass
from typing import Literal

InputKind = Literal["text", "date", "textarea", "select", "url"]


@dataclass(frozen=True)
class Field:
    """Describes one person attribute end-to-end."""

    name: str
    label: str
    kind: InputKind = "text"
    sql_type: str = "TEXT"
    required: bool = False
    options: tuple[str, ...] = ()
    group: str = "Basics"
    placeholder: str = ""
    #: Shown on the compact person card / tree detail popup.
    summary: bool = False


PERSON_FIELDS: tuple[Field, ...] = (
    # --- Basics ---
    Field("first_name", "First name", required=True, group="Basics", summary=True),
    Field("last_name", "Last name", group="Basics", summary=True),
    Field("nickname", "Nickname", group="Basics", placeholder="What everyone calls them"),
    Field(
        "gender",
        "Gender",
        kind="select",
        options=("female", "male", "other"),
        group="Basics",
        summary=True,
    ),
    Field("photo_url", "Photo URL", kind="url", group="Basics",
          placeholder="https://..."),
    # --- Life dates ---
    Field("dob", "Date of birth", kind="date", group="Life dates", summary=True),
    Field("birth_place", "Birth place", group="Life dates",
          placeholder="City, Country"),
    Field("dod", "Date of death", kind="date", group="Life dates", summary=True),
    Field("death_place", "Death place", group="Life dates"),
    # --- Life details ---
    Field("occupation", "Occupation", group="Life details", summary=True),
    Field("education", "Education", group="Life details"),
    Field("fun_fact", "Fun fact", group="Life details",
          placeholder="Famously bad at karaoke"),
    Field("notes", "Notes / bio", kind="textarea", group="Life details"),
)

#: Ordered field groups, for rendering the form in tidy sections.
FIELD_GROUPS: tuple[str, ...] = tuple(
    dict.fromkeys(f.group for f in PERSON_FIELDS)
)

FIELD_NAMES: tuple[str, ...] = tuple(f.name for f in PERSON_FIELDS)

SUMMARY_FIELDS: tuple[Field, ...] = tuple(f for f in PERSON_FIELDS if f.summary)


def fields_in(group: str) -> tuple[Field, ...]:
    return tuple(f for f in PERSON_FIELDS if f.group == group)


def column_definitions() -> str:
    """SQL fragment declaring every person column."""
    return ",\n    ".join(
        f"{f.name} {f.sql_type}{' NOT NULL' if f.required else ''}"
        for f in PERSON_FIELDS
    )


def clean(data: dict) -> dict:
    """Keep only known fields; turn blank strings into NULL."""
    out = {}
    for f in PERSON_FIELDS:
        value = data.get(f.name)
        if isinstance(value, str):
            value = value.strip() or None
        out[f.name] = value
    return out
