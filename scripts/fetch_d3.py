"""One-off: find a reachable mirror for d3.min.js and vendor it locally.

Run from the project root:  python scripts/fetch_d3.py
The export feature works without this (it falls back to a CDN <script> tag),
but vendoring makes the exported HTML work fully offline.
"""
import pathlib
import urllib.request

TARGET = pathlib.Path(__file__).parent.parent / "app" / "static" / "vendor" / "d3.v7.min.js"

CANDIDATES = [
    "https://d3js.org/d3.v7.min.js",
    "https://cdn.jsdelivr.net/npm/d3@7/dist/d3.min.js",
    "https://unpkg.com/d3@7/dist/d3.min.js",
    "https://generic.ci.artifacts.walmart.com/artifactory/jsdelivr-remote/npm/d3@7/dist/d3.min.js",
    "https://generic.ci.artifacts.walmart.com/artifactory/unpkg-remote/d3@7/dist/d3.min.js",
    "https://npm.ci.artifacts.walmart.com/artifactory/api/npm/npm-npmjs/d3/-/d3-7.9.0.tgz",
    "https://npm.ci.artifacts.walmart.com/artifactory/api/npm/npmjs/d3/-/d3-7.9.0.tgz",
]


def main() -> int:
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    for url in CANDIDATES:
        try:
            with urllib.request.urlopen(url, timeout=25) as resp:
                body = resp.read()
        except Exception as exc:  # noqa: BLE001 - probing, any failure = next
            print(f"  miss  {type(exc).__name__:<18} {url}")
            continue
        if len(body) < 50_000:
            print(f"  small {len(body):<18} {url}")
            continue
        TARGET.write_bytes(body)
        print(f"\nOK  saved {len(body):,} bytes from {url}\n -> {TARGET}")
        return 0
    print("\nNo mirror reachable. Export will use the public CDN instead.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
