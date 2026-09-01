#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["brotli"]
# ///
"""Build the compressed chapter-summary assets from the summaries-*.txt sources.

Produces {BOOK_ID: [[[firstVerse, lastVerse, dry, cheeky], ...], ...]} - a list
of chapters, each a list of [verse range, one summary per tone] entries. The
trailing tone is dropped when it is empty, so a day written in one tone only
costs nothing for the other.

Segments are the day splits the plan makes at the default settings
(5 min x 180 wpm = 900 words), recomputed here from web.json.br so the prose and
the pacing code can never drift. The reader matches by verse overlap rather than
by index, so a non-default `time` or `wpm` still lands on the right summaries;
it just may show two.

Source format, one segment per line, tab-separated, one file per tone:

    EST 1:1-22<TAB>King and Queen have a really big party ...

Usage: ./build-summaries.py [--check]
  --check  parse, validate and report coverage, without writing the assets
"""

import gzip
import hashlib
import json
import math
import pathlib
import re
import sys

import brotli

# Tone order is the order they are stored in and the order the page offers them.
# Order is the storage order in the asset and the order the page offers them.
# Changing it changes the shape of every entry, which is safe only because the
# assets are build outputs and the version stamp forces readers to refetch.
TONES = [("plain", pathlib.Path("summaries-plain.txt")),
         ("dry", pathlib.Path("summaries.txt")),
         ("cheeky", pathlib.Path("summaries-cheeky.txt"))]
WEB = pathlib.Path("web.json.br")
POEM_SPLITS = pathlib.Path("summaries-poem-splits.txt")
TEASE = "next time on"
CEILING = 5 * 180  # the plan's default max minutes x default wpm
LINE_RE = re.compile(r"^(\w+) (\d+):(\d+)-(\d+)\t(.+)$")


def word_count(text):
    """Match wordCount() in index.html: whitespace-separated, structure markers
    ride along inside the text and never add a word of their own."""
    return len([w for w in re.split(r"\s+", text.strip()) if w])


def segments_for(verses):
    """Replicate buildLive()'s even split for one chapter at the default ceiling.

    Returns [(firstVerseNumber, lastVerseNumber), ...]. Kept a faithful copy of
    the JS rather than shared with it: the JS runs per day from wherever the
    reader is, this runs the whole chapter at once.
    """
    words = [word_count(text) for _, text, *_ in verses]
    out, pos = [], 1
    while pos <= len(verses):
        remaining = sum(words[pos - 1:])
        target = remaining / max(1, math.ceil(remaining / CEILING))
        end, total = pos, 0
        while end <= len(verses):
            w = words[end - 1]
            if total > 0 and (total + w / 2 > target or total + w > CEILING):
                break
            total += w
            end += 1
        out.append((verses[pos - 1][0], verses[end - 2][0]))
        pos = end
    return out


def main() -> int:
    bible = json.loads(brotli.decompress(WEB.read_bytes()))
    wanted = {
        book: [segments_for(ch) for ch in chapters]
        for book, chapters in bible.items()
    }
    total = sum(len(s) for ch in wanted.values() for s in ch)

    written, bad = {tone: {} for tone, _ in TONES}, []
    for tone, source in TONES:
        if not source.exists():
            continue
        for lineno, line in enumerate(source.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            m = LINE_RE.match(line)
            if not m:
                bad.append(f"{source}:{lineno}: unparseable: {line[:60]}")
                continue
            book, chapter, first, last, text = m[1], int(m[2]), int(m[3]), int(m[4]), m[5]
            chapters = wanted.get(book)
            if chapters is None or chapter > len(chapters):
                bad.append(f"{source}:{lineno}: no such chapter: {book} {chapter}")
                continue
            if (first, last) not in chapters[chapter - 1]:
                bad.append(
                    f"{source}:{lineno}: {book} {chapter}:{first}-{last} is not a split "
                    f"boundary; expected one of {chapters[chapter - 1]}"
                )
                continue
            key = (book, chapter, first)
            if key in written[tone]:
                bad.append(f"{source}:{lineno}: duplicate of {book} {chapter}:{first}")
                continue
            written[tone][key] = text.strip()

    for problem in bad:
        print(problem)
    for tone, _ in TONES:
        count = len(written[tone])
        print(f"{tone}: {count} of {total} segments ({count / total:.1%})")
    if bad:
        return 1

    # A chapter split across days ends every part but the last on episodic
    # continuation text, except where the split lands inside a poem. That rule
    # is prose, not code, so the only thing enforceable is that an omission was
    # deliberate: declared in summaries-poem-splits.txt rather than forgotten.
    poems = set()
    if POEM_SPLITS.exists():
        poems = {l.strip() for l in POEM_SPLITS.read_text().splitlines()
                 if l.strip() and not l.lstrip().startswith("#")}
    nonfinal = {
        f"{book} {i + 1}:{segs[j][0]}-{segs[j][1]}"
        for book, chapters in wanted.items()
        for i, segs in enumerate(chapters)
        for j in range(len(segs) - 1)
    }
    for stray in sorted(poems - nonfinal):
        print(f"summaries-poem-splits.txt: {stray} is not a non-final part of a split chapter")
        bad.append(stray)
    for tone, _ in TONES:
        if tone == "plain":
            continue  # plain is cliff's notes; an episodic teaser is a joke device
        for ref in sorted(nonfinal - poems):
            book, rest = ref.split(" ", 1)
            chapter, first = rest.split(":")[0], int(rest.split(":")[1].split("-")[0])
            text = written[tone].get((book, int(chapter), first))
            if text and TEASE not in text.lower():
                print(f"{tone}: {ref} continues into the next day but has no "
                      f'"Next time on ..." line; add one, or declare the split '
                      f"in summaries-poem-splits.txt if it falls inside a poem")
                bad.append(ref)
    if bad:
        return 1

    lead = TONES[0][0]
    missing = [
        f"{book} {i + 1}:{first}-{last}"
        for book, chapters in wanted.items()
        for i, segs in enumerate(chapters)
        for first, last in segs
        if (book, i + 1, first) not in written[lead]
    ]
    if missing:
        print(f"{len(missing)} still to write in {lead}, first: {', '.join(missing[:5])}")

    if "--check" in sys.argv:
        return 0

    def entry(book, chapter, first, last):
        """[first, last, ...one summary per tone], trailing empties trimmed."""
        texts = [written[tone].get((book, chapter, first), "") for tone, _ in TONES]
        while texts and not texts[-1]:
            texts.pop()
        return [first, last, *texts] if texts else None

    # Chapters with nothing written yet stay as empty arrays: the reader treats
    # a missing summary as "no summary", so a partial file ships fine.
    data = {
        book: [
            [e for first, last in segs if (e := entry(book, i + 1, first, last))]
            for i, segs in enumerate(chapters)
        ]
        for book, chapters in wanted.items()
    }
    packed = json.dumps(data, separators=(",", ":"), ensure_ascii=False).encode()
    for path, blob in [
        (pathlib.Path("summaries.json.br"), brotli.compress(packed, quality=11)),
        (pathlib.Path("summaries.json.gz"), gzip.compress(packed, compresslevel=9, mtime=0)),
    ]:
        path.write_bytes(blob)
        print(f"wrote {path} ({len(blob):,} bytes)")

    # The page keeps the downloaded bytes in localStorage keyed by this stamp, so
    # without bumping it a returning reader would never see a rebuilt file.
    stamp = hashlib.sha256(packed).hexdigest()[:8]
    html_path = pathlib.Path("index.html")
    html, count = re.subn(
        r'(const SUMMARIES_VERSION = ")[0-9a-f]*(")', rf"\g<1>{stamp}\g<2>",
        html_path.read_text(), count=1)
    if not count:
        print("could not find SUMMARIES_VERSION in index.html")
        return 1
    html_path.write_text(html)
    print(f"stamped index.html with SUMMARIES_VERSION {stamp}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
