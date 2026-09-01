#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["brotli"]
# ///
"""Toolkit for writing the chapter summaries. See ../SUMMARIES-HANDOFF.md.

Everything here works off the repo, not /tmp, so a fresh agent on a fresh
machine can run it with no setup. Day boundaries are recomputed from
web.json.br on every call through build-summaries.py, so there is no generated
index file to go stale or go missing.

    ./summary-tools/summaries.py remaining PSA:51-150
    ./summary-tools/summaries.py dump ISA:1-12
    ./summary-tools/summaries.py write dry     < lines on stdin
    ./summary-tools/summaries.py poems         < references on stdin
    ./summary-tools/summaries.py check ISA
    ./summary-tools/summaries.py merge

Writers put per-book files in summary-tools/out/ rather than editing the two
real sources, so parallel agents never race and a run killed halfway leaves
whole valid files behind. `merge` folds them in.
"""

import importlib.util
import json
import pathlib
import re
import shutil
import sys

import brotli

REPO = pathlib.Path(__file__).resolve().parent.parent
OUT = REPO / "summary-tools" / "out"
DONE = REPO / "summary-tools" / "merged"
POEM_SPLITS = REPO / "summaries-poem-splits.txt"
# Same order as build-summaries.py, which is the order the page offers them.
TONES = {"plain": REPO / "summaries-plain.txt",
         "dry": REPO / "summaries.txt",
         "cheeky": REPO / "summaries-cheeky.txt"}

LINE = re.compile(r"^(\w+ \d+:\d+-\d+)\t(\S.*)$")
LOOSE = re.compile(r"^(\w+ \d+:\d+-\d+)\s+(\S.*)$")
REFONLY = re.compile(r"^(\w+ \d+:\d+-\d+)$")
BANNED = {"—": "em dash", "–": "en dash", "‘": "curly quote",
          "’": "curly apostrophe", "“": "curly quote", "”": "curly quote"}
TEASE = "next time on"

_spec = importlib.util.spec_from_file_location("bs", REPO / "build-summaries.py")
_bs = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_bs)


def bible():
    return json.loads(brotli.decompress((REPO / "web.json.br").read_bytes()))


def all_days():
    """[(ref, book, chapter, first, last)] for every day in the plan."""
    out = []
    for book, chapters in bible().items():
        for i, ch in enumerate(chapters, 1):
            for first, last in _bs.segments_for(ch):
                out.append((f"{book} {i}:{first}-{last}", book, i, first, last))
    return out


def select(args, days=None):
    """Filter all_days() by BOOK or BOOK:lo-hi specs. Preserves canonical order."""
    days = days if days is not None else all_days()
    picked, unknown = [], []
    for arg in args:
        book, _, rng = arg.partition(":")
        lo, hi = 1, 10**6
        if rng:
            a, _, b = rng.partition("-")
            lo, hi = int(a), int(b or a)
        hits = [d for d in days if d[1] == book and lo <= d[2] <= hi]
        if not hits:
            unknown.append(arg)
        picked += hits
    if unknown:
        sys.exit(f"no such book or range: {', '.join(unknown)}")
    return picked


def refs_in(path, pattern=LINE):
    if not path.exists():
        return {}
    return {m[1]: m[2] for m in (pattern.match(l)
            for l in path.read_text(encoding="utf-8").split("\n")) if m}


def declared_poems():
    if not POEM_SPLITS.exists():
        return set()
    return {l.strip() for l in POEM_SPLITS.read_text(encoding="utf-8").splitlines()
            if l.strip() and not l.lstrip().startswith("#")}


def written(tone, books):
    """Everything already written for these books, merged sources plus scratch."""
    have = dict(refs_in(TONES[tone]))
    for book in books:
        have.update(refs_in(OUT / f"{book}.{tone}.txt"))
    return have


# --------------------------------------------------------------------------- #

def cmd_remaining(args):
    """What is still to write, per tone. Run this before anything else."""
    picked = select(args)
    books = sorted({d[1] for d in picked})
    for tone in TONES:
        have = written(tone, books)
        todo = [d[0] for d in picked if d[0] not in have]
        print(f"\n## {tone}: {len(picked) - len(todo)} of {len(picked)} done, "
              f"{len(todo)} to write")
        print("\n".join(todo))
    return 0


# Verse text carries the renderer's own markup: \x05N\x05 wraps a footnote
# index, \x01-\x04 open and close emphasis. Strip exactly those. A blanket
# digit strip would also be safe today (only three verses carry a real digit)
# but would quietly corrupt any future dataset that does use numerals.
MARKUP = re.compile("\u0005\\d+\u0005|[\u0001-\u0004]")


def cmd_dump(args):
    """Verse text for each day, already split at the day boundaries."""
    data = bible()
    for ref, book, chapter, first, last in select(args):
        verses = data[book][chapter - 1]
        body = " ".join(
            f"[{v}] " + re.sub(r"\s+", " ", MARKUP.sub("", t)).strip()
            for v, t, *_ in verses if first <= v <= last)
        print(f"\n=== {ref} ===\n{body}")
    return 0


def cmd_write(args):
    """Append a batch of finished days. Call this every ten days, not at the end."""
    if len(args) != 1 or args[0] not in TONES:
        sys.exit("usage: summaries.py write dry|cheeky   < REF summary lines")
    tone = args[0]
    valid = {d[0] for d in all_days()}
    batch, problems = [], []
    for n, line in enumerate(sys.stdin, 1):
        if not line.strip():
            continue
        m = LOOSE.match(line.strip())
        if not m:
            problems.append(f"line {n}: not `REF summary`: {line.strip()[:60]}")
            continue
        ref, text = m[1], m[2].strip()
        if ref not in valid:
            problems.append(f"line {n}: {ref} is not a real day boundary")
        for ch, name in BANNED.items():
            if ch in text:
                problems.append(f"line {n}: {ref} contains a {name}")
        if len(text.split()) < 20:
            problems.append(f"line {n}: {ref} is only {len(text.split())} words, too thin")
        batch.append((ref, text))
    if problems:
        print("\n".join(problems), file=sys.stderr)
        sys.exit(f"nothing written: fix {len(problems)} problem(s) and rerun")

    OUT.mkdir(parents=True, exist_ok=True)
    wrote = skipped = 0
    for ref, text in batch:
        path = OUT / f"{ref.split(' ')[0]}.{tone}.txt"
        if ref in refs_in(path):
            skipped += 1
            continue
        with path.open("a", encoding="utf-8") as fh:
            fh.write(f"{ref}\t{text}\n")
        wrote += 1
    print(f"{tone}: wrote {wrote}" + (f", skipped {skipped} already present" if skipped else ""))
    return 0


def cmd_poems(args):
    """Declare day splits that fall inside a poem and so carry no teaser."""
    valid = {d[0] for d in all_days()}
    nonfinal = nonfinal_refs()
    refs, problems = [], []
    for n, line in enumerate(sys.stdin, 1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        m = REFONLY.match(line.strip())
        if not m:
            problems.append(f"line {n}: expected a bare reference: {line.strip()[:60]}")
            continue
        ref = m[1]
        if ref not in valid:
            problems.append(f"line {n}: {ref} is not a real day boundary")
        elif ref not in nonfinal:
            problems.append(f"line {n}: {ref} is not a non-final part, so it needs no teaser")
        else:
            refs.append(ref)
    if problems:
        print("\n".join(problems), file=sys.stderr)
        sys.exit(f"nothing declared: fix {len(problems)} problem(s) and rerun")
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "poems.txt"
    have = {l.strip() for l in path.read_text().splitlines()} if path.exists() else set()
    new = [r for r in refs if r not in have]
    with path.open("a", encoding="utf-8") as fh:
        for r in new:
            fh.write(r + "\n")
    print(f"declared {len(new)} poem split(s)"
          + (f", {len(refs) - len(new)} already declared" if len(new) != len(refs) else ""))
    return 0


def nonfinal_refs():
    """Days that continue into another day of the same chapter."""
    by_chapter = {}
    for ref, book, chapter, first, last in all_days():
        by_chapter.setdefault((book, chapter), []).append(ref)
    return {refs[i] for refs in by_chapter.values() for i in range(len(refs) - 1)}


def cmd_check(args):
    """Validate an assignment's scratch files. Must pass before reporting done."""
    picked = select(args)
    books = sorted({d[1] for d in picked})
    wanted = [d[0] for d in picked]
    nonfinal = nonfinal_refs() & set(wanted)
    poems = declared_poems() | {
        l.strip() for l in (OUT / "poems.txt").read_text().splitlines()
    } if (OUT / "poems.txt").exists() else declared_poems()

    failed = False
    for tone in TONES:
        have = written(tone, books)
        problems = [f"missing: {r}" for r in wanted if r not in have]
        for ref in wanted:
            text = have.get(ref)
            if text is None:
                continue
            for ch, name in BANNED.items():
                if ch in text:
                    problems.append(f"{ref} contains a {name}")
            n = len(text.split())
            if n < 20:
                problems.append(f"{ref} is only {n} words, too thin")
            if n > 140:
                problems.append(f"{ref} is {n} words, trim it")
        for ref in sorted(nonfinal - poems) if tone != "plain" else []:
            if ref in have and TEASE not in have[ref].lower():
                problems.append(
                    f'{ref} continues into the next day and needs a "Next time on ..." '
                    f"line, or declare it with `summaries.py poems` if it is a poem split")
        if problems:
            failed = True
            print(f"{tone}: {len(problems)} problem(s)")
            for p in problems[:25]:
                print(f"  {p}")
            if len(problems) > 25:
                print(f"  ... and {len(problems) - 25} more")
        else:
            print(f"{tone}: OK, {len(wanted)} days")
    return 1 if failed else 0


def cmd_merge(args):
    """Fold scratch output into the two real sources and the poem-splits file."""
    if not OUT.exists():
        print("nothing to merge")
        return 0
    DONE.mkdir(parents=True, exist_ok=True)

    # Poem declarations first: the build rejects a missing teaser, so a summary
    # merged without its declaration would fail the very next build.
    poems_src = OUT / "poems.txt"
    if poems_src.exists():
        have = declared_poems()
        new = [l.strip() for l in poems_src.read_text().splitlines()
               if l.strip() and l.strip() not in have]
        if new:
            body = POEM_SPLITS.read_text(encoding="utf-8") if POEM_SPLITS.exists() else ""
            if body and not body.endswith("\n"):
                body += "\n"
            POEM_SPLITS.write_text(body + "\n".join(new) + "\n", encoding="utf-8")
        print(f"poem splits: +{len(new)}")

    for tone, target in TONES.items():
        body = target.read_text(encoding="utf-8") if target.exists() else ""
        have = set(refs_in(target))
        added, skipped = [], 0
        for src in sorted(OUT.glob(f"*.{tone}.txt")):
            for ref, text in refs_in(src).items():
                if ref in have:
                    skipped += 1
                    continue
                have.add(ref)
                added.append(f"{ref}\t{text}")
        if added:
            if body and not body.endswith("\n"):
                body += "\n"
            target.write_text(body + "\n".join(added) + "\n", encoding="utf-8")
        print(f"{tone}: +{len(added)}" + (f", {skipped} already present" if skipped else ""))

    for src in list(OUT.glob("*.txt")):
        shutil.move(str(src), DONE / src.name)
    print(f"consumed files moved to {DONE.relative_to(REPO)}/")
    return 0


COMMANDS = {"remaining": cmd_remaining, "dump": cmd_dump, "write": cmd_write,
            "poems": cmd_poems, "check": cmd_check, "merge": cmd_merge}

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        sys.exit(__doc__)
    raise SystemExit(COMMANDS[sys.argv[1]](sys.argv[2:]))
