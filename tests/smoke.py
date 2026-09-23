"""End-to-end smoke test: migration, CRUD, tree shape, and export integrity.

Run from the project root:  .venv\\Scripts\\python.exe -m tests.smoke
Uses a throwaway database so your real family data is never touched.
"""
import os
import tempfile
from pathlib import Path

# Point the app at a temp DB *before* importing anything that opens it.
TMP = Path(tempfile.mkdtemp(prefix="familytree-test-"))
os.environ["FAMILY_PIN"] = "test-pin"

import app.database as database  # noqa: E402

database.DATA_DIR = TMP
database.DB_PATH = TMP / "test.db"

from fastapi.testclient import TestClient  # noqa: E402

from app import export, repository, tree  # noqa: E402
from app.fields import FIELD_NAMES, PERSON_FIELDS  # noqa: E402
from app.main import app  # noqa: E402

PASSED, FAILED = [], []


def check(label: str, condition: bool, detail: str = "") -> None:
    (PASSED if condition else FAILED).append(label)
    mark = "PASS" if condition else "FAIL"
    print(f"  [{mark}] {label}" + (f"  <- {detail}" if detail and not condition else ""))


def seed() -> dict[str, int]:
    """Three generations so the layered view has something to stack."""
    grandpa = repository.create_person({
        "first_name": "Arthur", "last_name": "Hale", "dob": "1940-04-02",
        "dod": "2015-11-30", "gender": "male", "occupation": "Railway engineer",
        "birth_place": "Leeds, UK", "fun_fact": "Could whistle in harmony.",
    })
    grandma = repository.create_person({
        "first_name": "Mary", "last_name": "Hale", "dob": "1943-08-19",
        "gender": "female", "occupation": "Teacher", "nickname": "Mim",
    })
    dad = repository.create_person({
        "first_name": "Peter", "last_name": "Hale", "dob": "1968-01-15",
        "gender": "male", "occupation": "Architect", "education": "Manchester",
    })
    mum = repository.create_person({
        "first_name": "Susan", "last_name": "Hale", "dob": "1970-06-23",
        "gender": "female", "occupation": "Nurse",
    })
    kid = repository.create_person({
        "first_name": "Ella", "last_name": "Hale", "dob": "1998-09-05",
        "gender": "female", "occupation": "Designer", "notes": "Loves climbing.",
    })
    repository.create_relationship(grandpa, grandma, "spouse")
    repository.create_relationship(dad, mum, "spouse")
    for parent in (grandpa, grandma):
        repository.create_relationship(parent, dad, "parent")
    for parent in (dad, mum):
        repository.create_relationship(parent, kid, "parent")
    return {"grandpa": grandpa, "dad": dad, "kid": kid, "mum": mum}


def test_schema():
    print("\n[schema]")
    database.init_db()
    with database.db_session() as conn:
        cols = {r["name"] for r in conn.execute("PRAGMA table_info(people)")}
    missing = set(FIELD_NAMES) - cols
    check("every declared field exists as a column", not missing, str(missing))


def test_migration():
    print("\n[migration]")
    # Simulate an old database that predates the new fields.
    legacy = TMP / "legacy.db"
    original = database.DB_PATH
    database.DB_PATH = legacy
    with database.db_session() as conn:
        conn.executescript(
            "CREATE TABLE people (id INTEGER PRIMARY KEY AUTOINCREMENT,"
            " first_name TEXT NOT NULL, last_name TEXT, dob TEXT);"
            "INSERT INTO people (first_name, last_name) VALUES ('Old', 'Record');"
        )
    added = database.init_db()
    with database.db_session() as conn:
        cols = {r["name"] for r in conn.execute("PRAGMA table_info(people)")}
        rows = conn.execute("SELECT * FROM people").fetchall()
    database.DB_PATH = original
    check("new columns added to legacy db", "occupation" in cols and bool(added))
    check("existing row survived migration", len(rows) == 1 and rows[0]["first_name"] == "Old")


def test_crud(ids):
    print("\n[crud]")
    people = repository.list_people()
    check("seeded five people", len(people) == 5, str(len(people)))
    arthur = repository.get_person(ids["grandpa"])
    check("extended fields persist", arthur["occupation"] == "Railway engineer")
    check("fun_fact persists", arthur["fun_fact"] == "Could whistle in harmony.")

    repository.update_person(ids["kid"], {
        "first_name": "Ella", "last_name": "Hale-Moss",
        "occupation": "Lead Designer", "dob": "1998-09-05",
    })
    ella = repository.get_person(ids["kid"])
    check("update writes new values", ella["last_name"] == "Hale-Moss")
    check("update clears omitted fields", ella["notes"] is None)

    blank = repository.create_person({"first_name": "  Spacey  ", "last_name": "   "})
    person = repository.get_person(blank)
    check("whitespace trimmed", person["first_name"] == "Spacey")
    check("blank string stored as NULL", person["last_name"] is None)
    repository.delete_person(blank)
    check("delete removes the row", repository.get_person(blank) is None)


def test_tree(ids):
    print("\n[tree]")
    data = tree.build_tree_data()
    gens = {n["id"]: n["generation"] for n in data["nodes"]}
    check("grandparent is generation 0", gens[ids["grandpa"]] == 0)
    check("parent is generation 1", gens[ids["dad"]] == 1)
    check("child is generation 2", gens[ids["kid"]] == 2)
    check("spouse inherits deepest generation", gens[ids["mum"]] == gens[ids["dad"]])
    check("links carry both types",
          {l["type"] for l in data["links"]} == {"parent", "spouse"})
    node = next(n for n in data["nodes"] if n["id"] == ids["grandpa"])
    check("node exposes every field", all(f in node for f in FIELD_NAMES))
    check("node has a display name", node["name"] == "Arthur Hale")


def test_cycle_safety():
    print("\n[cycle safety]")
    a = repository.create_person({"first_name": "Loop", "last_name": "A"})
    b = repository.create_person({"first_name": "Loop", "last_name": "B"})
    repository.create_relationship(a, b, "parent")
    repository.create_relationship(b, a, "parent")
    try:
        tree.build_tree_data()
        check("cyclic data does not hang or crash", True)
    except Exception as exc:  # noqa: BLE001
        check("cyclic data does not hang or crash", False, repr(exc))
    repository.delete_person(a)
    repository.delete_person(b)


def test_export():
    print("\n[export]")
    html = export.build_export("Hale Family")
    check("no unreplaced tokens", "__PAYLOAD__" not in html and "__STYLES__" not in html
          and "__TREE_CORE__" not in html and "__EDITOR__" not in html
          and "__TITLE__" not in html and "__D3__" not in html)
    check("renderer is inlined", "FamilyTree" in html and "forceSimulation" in html)
    check("editor is inlined", "Save / Share file" in html or "save-file" in html)
    check("data is embedded", "Arthur" in html and "Railway engineer" in html)
    check("title applied", "Hale Family" in html)
    check("single file: no local asset refs",
          '"/static/' not in html and "'/static/" not in html)
    check("document is well-formed", html.strip().startswith("<!DOCTYPE html>")
          and html.strip().endswith("</html>"))
    check("filename is sane", export.suggested_filename("Hale Family").startswith("hale-family-"))

    # Every element the editor wires up by id must exist in the shell,
    # otherwise the export dies on load with a null reference.
    required_ids = [
        "ft-payload", "tree-container", "people-list", "rel-list", "rel-form",
        "rel-a", "rel-b", "rel-type", "person-dialog", "person-form", "form-body",
        "add-person", "cancel-form", "save-file", "export-json", "reset-data",
        "status", "panel-tree", "panel-people", "panel-rel",
    ]
    missing = [i for i in required_ids if f'id="{i}"' not in html]
    check("all editor hooks present in template", not missing, str(missing))

    # The editor must defend against D3 rewriting link endpoints into objects.
    check("export normalises link endpoints", "function normalize(" in html)
    check("renderer copies links before simulating", "const linkId =" in html)


def test_export_payload_shape():
    """The embedded JSON must be parseable and use plain numeric endpoints.

    Regression guard: object-shaped source/target silently detaches every
    parent link, which flattens the whole tree into a single row.
    """
    print("\n[export payload]")
    import json
    import re

    html = export.build_export("Hale Family")
    match = re.search(
        r'<script type="application/json" id="ft-payload">(.*?)</script>',
        html, re.DOTALL,
    )
    check("payload block found", match is not None)
    if not match:
        return
    payload = json.loads(match.group(1).replace("<\\/", "</"))
    data = payload["data"]
    check("payload carries nodes", len(data["nodes"]) > 0)
    check("link endpoints are integers",
          all(isinstance(l["source"], int) and isinstance(l["target"], int)
              for l in data["links"]))
    node_ids = {n["id"] for n in data["nodes"]}
    check("every link points at a real person",
          all(l["source"] in node_ids and l["target"] in node_ids
              for l in data["links"]))
    check("generations survive serialisation",
          len({n["generation"] for n in data["nodes"]}) >= 3)
    check("field metadata travels with the data",
          {f["name"] for f in payload["fields"]} == set(FIELD_NAMES))


def test_routes():
    print("\n[routes]")
    client = TestClient(app)
    check("dashboard redirects when logged out",
          client.get("/", follow_redirects=False).status_code == 303)
    check("export blocked when logged out",
          client.get("/export/html", follow_redirects=False).status_code == 303)

    client.post("/login", data={"pin": "test-pin"}, follow_redirects=False)
    check("dashboard loads after login", client.get("/").status_code == 200)
    check("people partial loads", client.get("/people").status_code == 200)
    check("person form loads", "fld-occupation" in client.get("/people/new").text)
    check("tree api returns json", "nodes" in client.get("/api/tree-data").json())

    resp = client.get("/export/html?title=Hale%20Family")
    check("export downloads", resp.status_code == 200)
    check("export sets attachment header",
          "attachment" in resp.headers.get("content-disposition", ""))
    check("preview renders inline", client.get("/export/preview").status_code == 200)
    check("missing person returns 404", client.get("/people/99999/edit").status_code == 404)


def main() -> int:
    print(f"Family Tree smoke test  (temp db: {database.DB_PATH})")
    print(f"{len(PERSON_FIELDS)} person fields declared")
    test_schema()
    test_migration()
    ids = seed()
    test_crud(ids)
    test_tree(ids)
    test_cycle_safety()
    test_export()
    test_export_payload_shape()
    test_routes()
    total = len(PASSED) + len(FAILED)
    print(f"\n{'=' * 52}\n{len(PASSED)}/{total} checks passed")
    if FAILED:
        print("FAILED: " + ", ".join(FAILED))
    return 1 if FAILED else 0


if __name__ == "__main__":
    raise SystemExit(main())
