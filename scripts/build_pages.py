"""Build the static site published to GitHub Pages.

Produces a `docs/` folder containing a single self-contained index.html --
the same standalone export the Share button generates, just written to the
path GitHub Pages serves from.

    python -m scripts.build_pages                 # fictional demo family
    python -m scripts.build_pages --real          # your actual database

IMPORTANT: GitHub Pages on a free account is PUBLIC. Anything built with
--real puts real names and birth dates on the open internet where search
engines will index them. That is why the demo family is the default and
--real makes you type a confirmation.
"""
import argparse
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
#: Committed to the repo and published by CI. Demo data only.
DOCS = ROOT / "docs"
#: Gitignored. Real family data is written here so it can never be
#: committed and pushed to a public site by accident.
PRIVATE = ROOT / "docs-private"


def _load_demo_into_memory() -> None:
    """Point the repository at a throwaway DB seeded with the demo family.

    Keeps the published site free of real data without touching data/family.db.
    """
    import tempfile

    from app import database

    tmp = Path(tempfile.mkdtemp(prefix="familytree-pages-"))
    database.DATA_DIR = tmp
    database.DB_PATH = tmp / "demo.db"
    database.init_db()

    from scripts import seed_demo

    seed_demo.main()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--real",
        action="store_true",
        help="publish your ACTUAL family data (public!) instead of the demo",
    )
    parser.add_argument("--title", default=None, help="heading shown on the site")
    args = parser.parse_args()

    if args.real:
        print("\n  WARNING: --real publishes actual names and birth dates to a")
        print("  PUBLIC website that search engines will index.\n")
        if input('  Type "publish real data" to continue: ').strip() != "publish real data":
            print("\nAborted. Nothing was written.")
            return 1
        title = args.title or "Our Family Tree"
        out_dir = PRIVATE
    else:
        _load_demo_into_memory()
        title = args.title or "The Hale Family (Demo)"
        out_dir = DOCS

    from app import export, repository

    people = repository.list_people()
    if not people:
        print("No people found. Run `python -m scripts.seed_demo` first.")
        return 1

    out_dir.mkdir(exist_ok=True)
    (out_dir / "index.html").write_text(export.build_export(title), encoding="utf-8")
    # Stop Jekyll from trying to process the file and mangling it.
    (out_dir / ".nojekyll").write_text("", encoding="utf-8")
    # Publish the user guide next to the tree so the in-app Help link resolves.
    shutil.copyfile(ROOT / "app" / "static" / "guide.html", out_dir / "guide.html")

    size = (out_dir / "index.html").stat().st_size
    rel = out_dir.name
    print(f"\nBuilt {rel}/index.html  ({size:,} bytes, {len(people)} people)")
    print(f"Title: {title}")
    print("Mode : " + ("REAL DATA" if args.real else "demo data"))
    if args.real:
        print("\n  docs-private/ is gitignored on purpose. To publish this you")
        print("  must copy it into docs/ deliberately -- it will never happen")
        print("  by accident. Consider emailing the file instead.")
    else:
        print("\nCommit and push; CI publishes it to GitHub Pages.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
