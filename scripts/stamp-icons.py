#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# ///
"""Stamp every icon URL, and the manifest's, with a hash of the file.

Phones cache icons by URL, so a redrawn icon under an unchanged URL never
reaches a home screen. Run after changing any icon; `--check` exits non-zero
if a stamp is stale.
"""

import hashlib
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REF = re.compile(r'"((?:icon[\w-]*\.(?:svg|png))|apple-touch-icon\.png|manifest\.webmanifest)(?:\?v=\w+)?"')


def stamp(path: Path) -> bool:
    text = path.read_text()
    new = REF.sub(
        lambda m: f'"{m[1]}?v={hashlib.sha256((ROOT / m[1]).read_bytes()).hexdigest()[:8]}"',
        text,
    )
    if new != text and "--check" not in sys.argv:
        path.write_text(new)
    return new != text


# The manifest first: its own hash, stamped into index.html, must cover the
# icon stamps inside it.
stale = [p.name for p in (ROOT / "manifest.webmanifest", ROOT / "index.html") if stamp(p)]
if "--check" in sys.argv and stale:
    sys.exit(f"stale icon stamps in: {', '.join(stale)}")
print(f"{'stale' if '--check' in sys.argv else 'restamped'}: {', '.join(stale) or 'nothing'}")
