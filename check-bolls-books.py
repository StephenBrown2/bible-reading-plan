#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["httpx"]
# ///
"""Check index.html's derived bolls book numbers against the live provider.

BOLLS_BOOK_IDS derives the 66 canonical numbers from the position of each book
in BOOKS rather than restating them, so a reordering of BOOKS would silently
point a reading at the wrong book's text. This rebuilds the same map from
index.html and compares it to what bolls reports.

Usage: ./check-bolls-books.py
"""

import re
import sys

import httpx

BOOKS_RE = re.compile(r"^const BOOKS = \[(.*?)^\];", re.S | re.M)
ENTRY_RE = re.compile(r'\["([^"]+)",\d+,\d+,"([^"]+)",(true|false)\]')
DEUTERO = {"TOB": 68, "JDT": 69, "WIS": 70, "SIR": 71, "BAR": 73, "1MA": 74, "2MA": 75}
# The wider canon deliberately has no bolls number: bolls renumbers those per
# translation, so a static map would serve the wrong book's text.
UNMAPPED = {"ESG", "S3Y", "SUS", "BEL", "1ES", "2ES", "MAN", "PS2", "3MA", "4MA"}
# BOOKS and bolls disagree on two display names only; the numbering is the point.
ALIASES = {"Psalms": "Psalm", "Revelation of John": "Revelation"}


def derived_ids() -> dict[str, tuple[int, str]]:
    """Rebuild BOLLS_BOOK_IDS from index.html: {apiId: (bolls number, name)}."""
    body = BOOKS_RE.search(open("index.html").read())
    if not body:
        sys.exit("could not find the BOOKS array in index.html")
    ids, n = {}, 0
    for name, api_id, is_deutero in ENTRY_RE.findall(body.group(1)):
        if api_id in UNMAPPED:
            continue
        if is_deutero == "true":
            ids[api_id] = (DEUTERO[api_id], name)
        else:
            n += 1
            ids[api_id] = (n, name)
    return ids


def main() -> int:
    ids = derived_ids()
    assert len(ids) == 73, f"expected 73 mappable books, parsed {len(ids)}"

    html = open("index.html").read()
    mapped = set(re.findall(r'"?([A-Z0-9]{3})"?: *\d+', html[html.index("BOLLS_BOOK_IDS"):][:400]))
    leaked = mapped & UNMAPPED
    if leaked:
        print(f"these have no stable bolls number but are mapped anyway: {sorted(leaked)}")
        return 1

    # NRSVCE is the translation carrying all 73 of the books this plan uses.
    books = httpx.get("https://bolls.life/get-books/NRSVCE/", timeout=30).raise_for_status().json()
    live = {b["bookid"]: b["name"] for b in books}

    bad = []
    for api_id, (num, name) in sorted(ids.items(), key=lambda kv: kv[1][0]):
        want = ALIASES.get(name, name)
        got = live.get(num)
        if got != want:
            bad.append(f"  {api_id}: maps to bolls {num}, which is {got!r}, not {want!r}")

    if bad:
        print(f"{len(bad)} of {len(ids)} book numbers are wrong:", *bad, sep="\n")
        return 1
    print(f"all {len(ids)} bolls book numbers match")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
