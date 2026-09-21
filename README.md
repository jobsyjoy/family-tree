# 🌳 Family Tree Dashboard

An interactive family tree dashboard: add people, link relationships (parents/spouses),
visualize an interactive D3 tree, and get reminders for upcoming birthdays + custom events.

## Stack
- FastAPI (backend + routes)
- HTMX (interactivity without a JS framework)
- Tailwind CSS (styling, Walmart brand colors)
- D3.js (interactive force-directed tree: pan, zoom, drag, click for details)
- SQLite (storage)

## Setup

```bash
uv venv
uv pip install -r requirements.txt --index-url https://pypi.ci.artifacts.walmart.com/artifactory/api/pypi/external-pypi/simple --allow-insecure-host pypi.ci.artifacts.walmart.com
```

## Run

```bash
# Set your own PIN (default is 1234 - please change it!)
set FAMILY_PIN=your-secret-pin
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8420
```

Then open http://localhost:8420

## Sharing with family
Since this needs a live backend + database, it can't be a static GitHub Pages site.
Options to share with family outside this machine:
- Run it on a small always-on machine/VM and share the URL + PIN
- Deploy to a free-tier host like Render/Railway/Fly.io (SQLite persists on a volume)

**Security note:** The PIN is basic protection, not enterprise-grade auth. Don't put
highly sensitive info (SSNs, financial data) in notes fields.

## Features
- Add/edit/delete family members (name, DOB, DOD, gender, notes)
- Link relationships: parent → child, spouse ↔ spouse
- Interactive tree: zoom, pan, drag nodes, click for details
- Upcoming birthdays auto-calculated from DOB
- Custom reminders (anniversaries, appointments, etc.) with optional yearly repeat
