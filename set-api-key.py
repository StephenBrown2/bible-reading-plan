#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# ///
"""Write the api.bible key into index.html, lightly obfuscated.

The page is public, so this is a speed bump against scrapers grepping for key
patterns, not a secret store. Anyone who opens devtools can recover the key.
Regenerate it at https://scripture.api.bible if the quota starts moving oddly.

Reads .api-key (gitignored) and rewrites the API_BIBLE_KEY line in index.html.
Usage: ./set-api-key.py
"""

import base64
import pathlib
import re
import sys

PAD = "bible-reading-plan"  # must match the same constant in index.html
LINE = re.compile(r'^const API_BIBLE_KEY = "[^"]*";$', re.M)


def obfuscate(key: str, pad: str) -> str:
    xored = bytes(b ^ ord(pad[i % len(pad)]) for i, b in enumerate(key.encode()))
    return base64.b64encode(xored).decode()


def main() -> int:
    key_file = pathlib.Path(".api-key")
    if not key_file.exists():
        return print("no .api-key file; nothing to do") or 1
    key = key_file.read_text().strip()
    if not key:
        return print(".api-key is empty") or 1

    html = pathlib.Path("index.html")
    text = html.read_text()
    if not LINE.search(text):
        return print("could not find the API_BIBLE_KEY line in index.html") or 1

    packed = obfuscate(key, PAD)
    # Round-trip before writing: a wrong pad here would ship a dead key.
    unpacked = bytes(
        b ^ ord(PAD[i % len(PAD)]) for i, b in enumerate(base64.b64decode(packed))
    ).decode()
    assert unpacked == key, "obfuscation did not round-trip"

    html.write_text(LINE.sub(f'const API_BIBLE_KEY = "{packed}";', text))
    print(f"wrote a {len(key)}-character key into index.html as {len(packed)} base64 characters")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
