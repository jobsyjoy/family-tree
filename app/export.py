"""Export the whole family tree as one self-contained, editable HTML file.

Design goal: the output must survive being emailed to a relative who has
never heard of a terminal. So it is a single file, opens with a double-click,
needs no server, and can be edited and re-saved from the browser.

The heavy lifting (D3 rendering) is the exact same tree-core.js the live
dashboard uses -- inlined here rather than reimplemented. DRY applies across
deployment targets too.
"""
import json
from datetime import datetime
from pathlib import Path

from app import tree
from app.fields import PERSON_FIELDS

STATIC_DIR = Path(__file__).parent / "static"
VENDOR_D3 = STATIC_DIR / "vendor" / "d3.v7.min.js"
D3_CDN = "https://d3js.org/d3.v7.min.js"


def _read_static(name: str) -> str:
    return (STATIC_DIR / name).read_text(encoding="utf-8")


def _d3_script_tag() -> str:
    """Inline D3 when vendored, else fall back to the public CDN."""
    if VENDOR_D3.exists():
        return f"<script>{VENDOR_D3.read_text(encoding='utf-8')}</script>"
    return (
        f'<script src="{D3_CDN}"></script>\n'
        '<!-- D3 loaded from CDN: needs internet on first open. '
        'Run scripts/fetch_d3.py to inline it instead. -->'
    )


def _field_meta() -> list[dict]:
    return [
        {
            "name": f.name,
            "label": f.label,
            "kind": f.kind,
            "required": f.required,
            "options": list(f.options),
            "group": f.group,
            "placeholder": f.placeholder,
        }
        for f in PERSON_FIELDS
    ]


def build_export(title: str = "Our Family Tree") -> str:
    """Render the standalone HTML document as a string."""
    payload = {
        "title": title,
        "exported_at": datetime.now().strftime("%d %b %Y, %H:%M"),
        "fields": _field_meta(),
        "data": tree.build_tree_data(),
    }
    # Token replacement, not str.format: the template is full of CSS and JS
    # braces that would make format() lose its mind.
    substitutions = {
        "__TITLE__": title,
        "__D3__": _d3_script_tag(),
        "__STYLES__": _read_static("styles.css"),
        "__TREE_CORE__": _read_static("tree-core.js"),
        "__EDITOR__": _read_static("export-editor.js"),
        # Split the closing tag so a stray </script> in the data can't
        # terminate the inline script block early.
        "__PAYLOAD__": json.dumps(payload).replace("</", "<\\/"),
    }
    html = _read_static("export_template.html")
    for token, value in substitutions.items():
        html = html.replace(token, value)
    return html


def suggested_filename(title: str = "Our Family Tree") -> str:
    safe = "".join(c if c.isalnum() or c in " -_" else "" for c in title).strip()
    stamp = datetime.now().strftime("%Y-%m-%d")
    return f"{(safe or 'family-tree').replace(' ', '-').lower()}-{stamp}.html"
