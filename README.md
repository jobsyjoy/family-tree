# Family Tree Dashboard

An interactive family tree you can fill in, explore, and **share with relatives
outside the company** as a single self-contained HTML file.

## What it does

- **Rich member details** - name, nickname, gender, photo, birth/death dates and
  places, occupation, education, notes, and a fun fact.
- **Two interactive views**, toggled with one button:
  - **Generations** - classic top-down tree, one row per generation, elbow
    connectors, auto-fits to the panel.
  - **Web** - force-directed graph you can drag people around in.
  - Both support zoom, pan, and click-a-person-for-details.
- **Relationships** - parent -> child and spouse <-> spouse links.
- **Reminders** - birthdays are derived from dates of birth; add your own
  anniversaries and one-off events.
- **Share / Export** - download the entire tree as ONE HTML file.

## Sharing outside the organisation

The internal app needs a server and the VPN, which relatives won't have. So the
**Share / Export** button produces a single `.html` file that:

- opens by double-clicking, on any machine, with no server, login, or VPN;
- lets the recipient add people, edit details, and link relationships;
- keeps their edits in browser storage so a refresh doesn't lose work;
- has its own **Save / Share file** button that downloads an updated copy they
  can pass along -- so the tree can keep travelling around the family;
- exports the raw data as JSON if someone wants to do their own thing with it;
- has a **Reset** button to discard local edits and return to the shared data.

> The file loads D3 from a public CDN, so the first open needs internet
> (completely normal at home). To make it work fully offline, run
> `python scripts/fetch_d3.py` while you have access to a mirror -- the library
> is then inlined into every future export.

## Setup

```bash
uv venv
uv pip install -r requirements.txt --index-url https://pypi.ci.artifacts.walmart.com/artifactory/api/pypi/external-pypi/simple --allow-insecure-host pypi.ci.artifacts.walmart.com
```

## Run

```bash
set FAMILY_PIN=your-secret-pin
.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8420
```

Open http://localhost:8420 (default PIN is `1234` - change it).

Want demo data to play with first?

```bash
.venv\Scripts\python.exe -m scripts.seed_demo
```

## Tests

```bash
.venv\Scripts\python.exe -m tests.smoke
```

46 checks covering schema, migration, CRUD, generation maths, cycle safety,
export integrity, and route auth.

## Adding a new person field

Everything about a person is declared in **one place**: `app/fields.py`. Add a
`Field(...)` entry and it automatically appears in the database (via
auto-migration), the add/edit form, the person cards, the tree detail panel,
and the export. No other file needs touching.

```python
Field("hometown", "Hometown", group="Life details", summary=True)
```

Restart the app; the column is added to the existing database without data loss.

## Architecture

```
app/
  fields.py        Single source of truth for person attributes
  database.py      SQLite connection, generated schema, auto-migration
  repository.py    Data access; person SQL generated from fields.py
  tree.py          Builds nodes/links + generation depths for the front-end
  events.py        Birthday and reminder calculations
  export.py        Assembles the standalone HTML file
  auth.py          PIN session guard
  routes/
    common.py      Shared templates instance, auth guard, render helper
    pages.py       Dashboard + tree data API
    people.py      Person CRUD (form parsing driven by fields.py)
    relationships.py, reminders.py, auth.py, export.py
  static/
    tree-core.js       The renderer. Shared by the app AND the export.
    tree.js            Thin dashboard adapter (fetches live data)
    export-editor.js   Serverless CRUD for the exported file
    export_template.html
    styles.css         Shared by both targets
```

The tree renderer lives in exactly one file (`tree-core.js`) and is used by both
the live dashboard and the exported file, so the two can never drift apart.
Generation maths exists in two places by necessity (Python server-side, JS in
the offline export) and the smoke test guards that they agree.

## Security notes

- The PIN is a speed bump, not real auth. Don't put sensitive personal data
  (SSNs, medical records, financial details) in here.
- Contact fields are deliberately **not** included: an exported file is designed
  to be emailed around, and phone numbers and addresses shouldn't travel that
  way by default.
- `data/*.db` is gitignored so real family data never lands in version control.
