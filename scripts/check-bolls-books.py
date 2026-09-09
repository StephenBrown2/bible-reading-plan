#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["httpx"]
# ///
"""Check the bolls book numbers index.html derives against the live provider.

index.html numbers the 66 canonical books by their position in BOOKS rather than
restating them, so reordering BOOKS would silently point readings at a different
book's text. This asserts the numbering bolls actually uses.

Usage: ./check-bolls-books.py
"""

import sys

import httpx

# The seven deuterocanon books whose bolls numbers agree across every edition
# carrying them. The wider canon is deliberately absent from index.html's map:
# bolls renumbers it per translation, so no static number is safe.
DEUTERO = {"Tobit": 68, "Judith": 69, "Wisdom": 70, "Sirach": 71,
           "Baruch": 73, "1 Maccabees": 74, "2 Maccabees": 75}
# NRSVCE carries all 73 books index.html maps, in the order it assumes.
CANONICAL_LAST = ("Revelation", 66)


def main() -> int:
    books = httpx.get("https://bolls.life/get-books/NRSVCE/", timeout=30).raise_for_status().json()
    by_num = {b["bookid"]: b["name"] for b in books}

    problems = [f"  bolls {n} is {by_num.get(n)!r}, expected {name!r}"
                for name, n in DEUTERO.items() if by_num.get(n) != name]
    if by_num.get(CANONICAL_LAST[1]) != CANONICAL_LAST[0]:
        problems.append(f"  bolls {CANONICAL_LAST[1]} is {by_num.get(CANONICAL_LAST[1])!r},"
                        f" expected {CANONICAL_LAST[0]!r}, so 1-66 are not in canonical order")
    if problems:
        print("bolls numbering has moved:", *problems, sep="\n")
        return 1
    print(f"bolls numbering matches: 1-66 canonical, {len(DEUTERO)} deuterocanon books")
    return 0


if __name__ == "__main__":
    sys.exit(main())
