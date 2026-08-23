#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# ///
"""Rebuild the embedded WEB dataset in index.html from the USFX source.

Produces {BOOK_ID: [[[verseNum, text], ...], ...]} - a list of chapters, each a
list of [verse number, text] pairs. Verse numbers are not always contiguous
(Sirach), so never assume index == verse - 1. Paragraph and poetry structure
rides along inside the verse text as "\\n\\n" and "\\n" prefixes, which is what
renderVerseStream() splits on.

Only text between <v> and <ve/> is kept, which drops titles, section headings
and Psalm superscriptions for free since those sit outside verse ranges.
Footnotes and cross-references are dropped explicitly, being inside them.

Usage: ./build-embedded.py [--check]
  --check  parse and report, without touching index.html
"""

import base64
import gzip
import json
import pathlib
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET

SOURCE = "https://raw.githubusercontent.com/seven1m/open-bibles/master/eng-web.usfx.xml"
CACHE = pathlib.Path("/tmp/eng-web.usfx.xml")

# The 66 canonical books, then the wider canon this plan reads. LJE is parsed
# but never appears here: it is merged into Baruch chapter 6, matching how the
# live providers present it.
CANON = """GEN EXO LEV NUM DEU JOS JDG RUT 1SA 2SA 1KI 2KI 1CH 2CH EZR NEH EST JOB
PSA PRO ECC SNG ISA JER LAM EZK DAN HOS JOL AMO OBA JON MIC NAM HAB ZEP HAG ZEC
MAL MAT MRK LUK JHN ACT ROM 1CO 2CO GAL EPH PHP COL 1TH 2TH 1TI 2TI TIT PHM HEB
JAS 1PE 2PE 1JN 2JN 3JN JUD REV""".split()
DEUTERO = "TOB JDT WIS SIR BAR 1MA 2MA".split()
WIDER = "ESG S3Y SUS BEL 1ES 2ES MAN PS2 3MA 4MA".split()
WANTED = set(CANON) | set(DEUTERO) | set(WIDER)

DROP = {"d", "id", "ide", "h", "toc", "cl", "rem", "fig"}
NOTES = {"f", "x"}          # footnote and cross-reference, kept and marked
PARA_BREAK, LINE_BREAK = "\n\n", "\n"
NOTE_MARK = "\u0005"        # renderVerseStream() turns these into popover buttons


def parse(xml_text: str) -> dict:
    root = ET.fromstring(xml_text)
    books, state = {}, {}

    def reset(book_id):
        state.update(book=[], chapter=None, verse=None, pending="", id=book_id, note=None)

    def emit(text):
        """Append text to the open verse, if one is open.

        Spacing is preserved rather than stripped per piece: dropping a footnote
        leaves its tail carrying the separating space, so "God<f>..</f> created"
        must not become "Godcreated". Runs are tidied once in finalise().
        """
        if state["note"] is not None:
            state["note"].append(text)
            return
        if state["verse"] is None or not text:
            return
        piece = re.sub(r"\s+", " ", text)
        pair = state["verse"]
        if piece.strip():
            pair[1] += state["pending"] + piece
            state["pending"] = ""
        elif pair[1]:
            pair[1] += piece            # a separator, not a reason to spend the break

    def mark(kind):
        # The strongest break in a gap wins. A gap containing a <p> is a new
        # paragraph however many <q> surround it, which is what makes prose
        # resuming after poetry (Judges 5:31) a paragraph rather than a line,
        # and a heading followed by poetry (Psalm 1:1) a paragraph too.
        if kind == PARA_BREAK or not state["pending"]:
            state["pending"] = kind if state["pending"] != PARA_BREAK else PARA_BREAK

    def walk(elem):
        tag = elem.tag
        if tag in DROP:
            return
        if tag in NOTES:
            # A note interrupts the verse: mark its position, collect its text
            # aside, then carry on. Nested <fr>/<ft>/<fq> just add their text.
            verse = state["verse"]
            if verse is None:
                return
            notes = verse[2] if len(verse) > 2 else None
            if notes is None:
                notes = []
                verse.append(notes)
            state["note"] = []
            if elem.text:
                state["note"].append(elem.text)
            for child in elem:
                walk(child)
                if child.tail:
                    state["note"].append(child.tail)
            body = re.sub(r"\s+", " ", "".join(state["note"])).strip()
            state["note"] = None
            if body:
                verse[1] += f"{NOTE_MARK}{len(notes)}{NOTE_MARK}"
                notes.append(body)
            return
        if tag == "book":
            reset(elem.get("id"))
        elif tag == "c":
            state["chapter"] = []
            state["book"].append(state["chapter"])
            state["verse"] = None
            # No break of its own: the <p> or <q> that opens the chapter decides,
            # so a chapter starting in poetry (Psalm 2:1) opens as a line.
            state["pending"] = ""
        elif tag == "v":
            num = re.sub(r"\D.*$", "", elem.get("id") or "")
            if num and state["chapter"] is not None:
                state["verse"] = [int(num), ""]
                state["chapter"].append(state["verse"])
        elif tag == "ve":
            state["verse"] = None
        elif tag == "p":
            mark(PARA_BREAK)
        elif tag == "q":
            mark(LINE_BREAK)
        # <b/> is a blank line between stanzas, not a break of its own: the gap
        # around it is already described by the <p> or <q> on either side.

        if elem.text:
            emit(elem.text)
        for child in elem:
            walk(child)
            if child.tail:
                emit(child.tail)

        if tag == "book" and state["id"]:
            books[state["id"]] = state["book"]

    for book in root.iter("book"):
        walk(book)

    # The source splits the Letter of Jeremiah out as its own book; the live
    # providers and this plan both treat it as Baruch chapter 6.
    if "LJE" in books and "BAR" in books:
        books["BAR"] = books["BAR"][:5] + [c for c in books["LJE"] if c]
    def finalise(text):
        # A marker can end up with a space in front of it when the note sat after
        # a word; the reader adds its own spacing, so close that gap here.
        text = re.sub(r" +(" + NOTE_MARK + r")", r"\1", text)
        text = re.sub(r" +", " ", text)
        text = re.sub(r" *\n *", "\n", text)
        return re.sub(r"^ +", "", text.rstrip())

    def clean(chapter):
        # Verse numbers that carry no text (Sirach 1:5, 1:7, 1:21) are dropped,
        # which is why verse numbers are not contiguous and index != verse - 1.
        out = []
        for entry in chapter:
            text = finalise(entry[1])
            if not text:
                continue
            notes = entry[2] if len(entry) > 2 else []
            out.append([entry[0], text, notes] if notes else [entry[0], text])
        return out

    return {
        b: [c for c in (clean(ch) for ch in chapters) if c]
        for b, chapters in books.items()
        if b in WANTED
    }


def main() -> int:
    if not CACHE.exists():
        print(f"fetching {SOURCE}")
        CACHE.write_bytes(urllib.request.urlopen(SOURCE).read())
    data = parse(CACHE.read_text(encoding="utf-8"))

    missing = WANTED - set(data)
    if missing:
        print(f"source is missing {sorted(missing)}")
        return 1
    print(f"parsed {len(data)} books, {sum(len(c) for c in data.values())} chapters")

    if "--check" in sys.argv:
        pathlib.Path("/tmp/rebuilt-embedded.json").write_text(json.dumps(data))
        print("wrote /tmp/rebuilt-embedded.json")
        return 0

    html_path = pathlib.Path("index.html")
    html = html_path.read_text()
    if 'id="embeddedWebDataGz"' not in html:
        print("could not find the embeddedWebDataGz script tag")
        return 1
    packed = base64.b64encode(
        gzip.compress(json.dumps(data, separators=(",", ":")).encode(), 9)
    ).decode()
    new = re.sub(
        r'(<script type="text/plain" id="embeddedWebDataGz">)[^<]+(</script>)',
        lambda m: m.group(1) + packed + m.group(2),
        html,
        count=1,
    )
    html_path.write_text(new)
    print(f"embedded {len(data)} books as {len(packed):,} base64 characters")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
