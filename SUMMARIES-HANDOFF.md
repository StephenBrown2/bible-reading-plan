# Handoff: finish the chapter summaries

**If you were told "follow the handoff document and finish the task", this file
is the whole brief. Read it start to finish, then do "The job" below. You need
no other instructions.**

The feature itself is built, wired and verified. Only the prose is incomplete.
There are **three tones**, and every one of the 1,679 days needs all three:

- `plain`   3 of 1,679 written
- `dry`     271 of 1,679
- `cheeky`  271 of 1,679

Your job is to get all three to 100% and ship it.

Everything needed lives in this repo. Nothing is in `/tmp`. There is no setup
step.

When coverage reaches 100% in both tones, delete this file and the
`summary-tools/` directory: they describe work in progress, not the design. The
permanent design notes are in CLAUDE.md under "Chapter summaries".

## The job

1. Dispatch the eleven agents in the table below, in parallel, on Opus.
2. As each returns, verify it, then merge and rebuild.
3. When every genre is done, run the final checks and commit.

Details for each step follow.

## Where it stands

```sh
./build-summaries.py --check      # live coverage, per tone
```

At the time of writing: **plain 3 days, dry and cheeky 271 days**, of 1,679.

Every count in this file is a snapshot taken when it was written. The build and
`summaries.py remaining` are the truth; where they disagree with a number here,
they win. Day counts in the dispatch table are sized for context budget, so a
small drift changes nothing.

Written in dry and cheeky, not to be redone in those tones: Genesis, Leviticus,
Joshua, Ruth, Esther, Psalms 1-50, Nahum 1, Mark, James, 1-2 Peter, 1 John,
Tobit, Judith, Susanna, Bel and the Dragon, Song of the Three, Prayer of
Manasseh, Psalm 151. **Those days still need a plain summary**, which is what
batch 11 below is for.

You never need to work this out by hand. `summaries.py remaining` reports it per
assignment, and agents are told to start there.

## What a "day" is

A **day**, not a chapter. 1,679 days across 1,391 chapters, because 276 chapters
are too long for one sitting and the plan splits them at the default 5 min x
180 wpm. All three tones are written per day. Any tone may be missing for a
day; the page renders whichever exists and names it.

## The three tones

Same facts every time, three voices. The picker offers them in this order and a
new reader lands on plain.

`summaries-plain.txt` is **plain**: cliff's notes, no jokes, no attitude. The one
someone reads to find out what they missed, and the one that matters most.

> God finds them hiding; the man blames the woman, the woman blames the serpent.
> God curses the serpent, tells the woman she will bear children in pain, and
> curses the ground for the man's sake.

`summaries.txt` is **dry**: deadpan, wry, the joke in the framing rather than the
vocabulary.

> The man blames the woman and, in the same sentence, God for supplying her. The
> woman blames the snake. The snake wisely says nothing.

`summaries-cheeky.txt` is **cheeky**: blunt and modern, short sentences, the joke
said out loud.

> Guy blames the woman, and in the same breath blames God for making her. Woman
> blames the snake. Snake says nothing, because the snake is not stupid.

`summary-tools/BRIEF.md` has the full spec with more examples; every agent reads
it. A day may be missing a tone: the page renders whichever it has and labels
which one that is.

## Rules the build enforces

`./build-summaries.py` **fails**, rather than warns, on:

- A verse range that is not a real day split at the default settings.
- A duplicate reference within a tone.
- A non-final part of a split chapter whose summary has no "Next time on ..."
  line, unless that reference is listed in `summaries-poem-splits.txt`.

That last rule exists because a chapter split across days ends every part but the
last on episodic continuation text, and a split inside a **poem** does not: a
psalm has no cliffhanger. Code cannot tell those apart, so the poem-splits file
is how an omission says "deliberate" rather than "forgotten". It was added after
a batch came back with six narrative splits silently missing their continuation
lines.

## Rules the build cannot enforce

These are why a careful writer is needed and a template is not enough:

- **Do not invent plot.** Exaggerating tone is the joke. Adding events is a bug.
- **Irreverent, not cruel.** Aim at pompous kings and bad decisions. Where the
  text is genuinely grim (Judges 19, the conquest body counts, Tamar, the
  Deuteronomy 28 curses, Lamentations, the Maccabean martyrdoms), drop the comedy
  and be plain and dark. Never at a victim's expense.
- **No sameness.** The failure mode on Leviticus, Chronicles and the tribal
  boundary lists is fifty summaries that read identically. Hang each day on the
  one detail only that day has.
- No em dashes or en dashes. Straight quotes only.

## Step 1: dispatch eleven agents

Eleven agents, all independent, all safe to run at once. Use **Opus**
(`model: "opus"`), which has the context budget these assignments assume.

| # | Genre | Books | Days | Peak context |
|---|---|---|---|---|
| 1 | Major prophets | `ISA JER LAM EZK DAN BAR` | 227 | ~382k |
| 2 | History | `JDG 1SA 2SA 1KI 2KI` | 173 | ~301k |
| 3 | Wisdom | `JOB PRO ECC SNG WIS SIR` | 163 | ~257k |
| 4 | Gospels and Acts | `MAT LUK JHN ACT` | 143 | ~255k |
| 5 | Torah narrative | `EXO NUM DEU` | 143 | ~254k |
| 6 | Chronicler and post-exile | `1CH 2CH EZR NEH ESG 1ES` | 136 | ~237k |
| 7 | Maccabees and apocalyptic | `1MA 2MA 3MA 4MA 2ES` | 126 | ~230k |
| 8 | Epistles and Revelation | `ROM 1CO 2CO GAL EPH PHP COL 1TH 2TH 1TI 2TI TIT PHM HEB 2JN 3JN JUD REV` | 128 | ~208k |
| 9 | Psalms | `PSA:51-150` | 103 | ~139k |
| 10 | Minor prophets | `HOS JOL AMO OBA JON MIC NAM HAB ZEP HAG ZEC MAL` | 66 | ~111k |
| 11 | Plain retro-fit, **plain tone only** | `GEN LEV JOS RUT EST PSA:1-50 NAM:1 MRK JAS 1PE 2PE 1JN TOB JDT SUS BEL S3Y MAN PS2` | 268 | ~286k |

Batches 1 to 10 write **all three tones** for days that have none. Batch 11 is
different: those days already have dry and cheeky, and need only the plain tone
adding. Its agent must be told that explicitly, or it will waste a run
rewriting prose that already exists. `summaries.py remaining` reports per tone,
so the agent can see it directly.

Book IDs in full: ISA Isaiah, JER Jeremiah, LAM Lamentations, EZK Ezekiel, DAN
Daniel, BAR Baruch, JDG Judges, 1SA-2SA Samuel, 1KI-2KI Kings, JOB Job, PRO
Proverbs, ECC Ecclesiastes, SNG Song of Solomon, WIS Wisdom of Solomon, SIR
Sirach, EXO Exodus, NUM Numbers, DEU Deuteronomy, MAT Matthew, LUK Luke, JHN
John, ACT Acts, 1CH-2CH Chronicles, EZR Ezra, NEH Nehemiah, ESG Greek Esther,
1ES 1 Esdras, ROM Romans, 1CO-2CO Corinthians, GAL Galatians, EPH Ephesians, PHP
Philippians, COL Colossians, 1TH-2TH Thessalonians, 1TI-2TI Timothy, TIT Titus,
PHM Philemon, HEB Hebrews, 2JN-3JN John, JUD Jude, REV Revelation, 1MA-4MA
Maccabees, 2ES 2 Esdras, PSA Psalms, HOS Hosea, JOL Joel, AMO Amos, OBA Obadiah,
JON Jonah, MIC Micah, NAM Nahum, HAB Habakkuk, ZEP Zephaniah, HAG Haggai, ZEC
Zechariah, MAL Malachi.

One agent per genre is what keeps the voice consistent: the same writer handles
every psalm, every oracle, every list of returning families, and can see the
repetition it has to work against across the whole run.

Peak context is estimated as the brief, plus source text at 1.35 tokens a word,
plus three summaries a day at ~90 words, with a 2.2x allowance for drafting. The
largest lands near 51% of a 750k budget. Recompute only if the day counts change
a lot.

### The prompt to give each agent

Copy this, substituting the row's genre, books and day count. Add a sentence of
per-genre warning where the table above suggests one.

> Read `summary-tools/BRIEF.md` in this repo, in full, and follow it exactly. It
> gives you the three tones with examples, the rules, a note for your genre, and
> how to save your work as you go. Note its length section before you write
> anything: 45 to 90 words per summary, never over 140, favouring a short
> highlight over a long drawn-out observation, in every tone.
>
> Your assignment: the **\<GENRE\>** genre, books `<BOOK IDS>`, about \<N\> days.
>
> Start with `./summary-tools/summaries.py remaining <BOOK IDS>` to see what is
> left. Then work one book at a time: read a chunk of text with
> `./summary-tools/summaries.py dump <BOOK>`, write those days, save them with
> `./summary-tools/summaries.py write plain`, `... write dry` and
> `... write cheeky`, and only then read the next chunk. **Save at least every ten days.** You are carrying a lot
> of work and an unsaved run can be lost to a session limit.
>
> Finish with `./summary-tools/summaries.py check <BOOK IDS>` and fix whatever it
> reports until it passes. Do not report success until it does. If you stop
> early, say plainly how far you got: your saved days are on disk and the next
> agent resumes from them.

## Step 2: verify what comes back

**Do not trust an agent's self-report.** One returned "complete" having silently
omitted every continuation line in the book; the checker did not cover that case
at the time, and now does. Independently run:

```sh
./summary-tools/summaries.py check <BOOK IDS>      # per returned assignment
```

Then read a handful of the summaries yourself, especially in a genre with a
sameness risk (Chronicles, the tribal lists, Leviticus) and one where the text is
grim (Judges 19, Lamentations, 2 and 4 Maccabees). The checker cannot see tone.

## Step 3: merge and rebuild

```sh
./summary-tools/summaries.py merge && ./build-summaries.py
```

`merge` folds the scratch files into `summaries.txt`, `summaries-cheeky.txt` and
`summaries-poem-splits.txt`, skips references already present, and moves what it
consumed into `summary-tools/merged/`. It is safe to run repeatedly and safe to
run while other agents are still working; it only takes finished files.

`build-summaries.py` regenerates `summaries.json.br` / `.gz` and stamps a fresh
`SUMMARIES_VERSION` into `index.html`. That stamp is what makes a returning
reader pick up the new asset instead of the copy cached in their localStorage,
so never hand-edit the `.json.*` files.

## Step 4: finish

When `./build-summaries.py --check` reports 100% in both tones:

```sh
./build-summaries.py                      # final assets and version stamp
python3 -m http.server 8765               # then open localhost:8765/index.html
```

Click "Show summary", flip the Dry/Cheeky picker, and step through a few days
including one that straddles a split chapter. Then commit together:

```
summaries.txt  summaries-cheeky.txt  summaries-poem-splits.txt
summaries.json.br  summaries.json.gz  index.html
```

Delete `SUMMARIES-HANDOFF.md` and `summary-tools/` in the same commit, and drop
the two `summary-tools/` lines from `.gitignore`. This repo is **jj, not git**:
load the `/jujutsu` skill before any version-control operation.

## The tooling

One script, in the repo, no setup. Run everything from the repo root.

```sh
./summary-tools/summaries.py remaining BOOK[:lo-hi] ...   # what is still to write
./summary-tools/summaries.py dump     BOOK[:lo-hi] ...   # verse text, pre-split
./summary-tools/summaries.py write    dry|cheeky         # append a batch (stdin)
./summary-tools/summaries.py poems                       # declare poem splits (stdin)
./summary-tools/summaries.py check    BOOK[:lo-hi] ...   # validate before reporting
./summary-tools/summaries.py merge                       # fold into the real sources
```

Day boundaries are recomputed from `web.json.br` on every call, so there is no
generated index to go stale or go missing.

`summary-tools/out/` is agent scratch space and `summary-tools/merged/` is what
merge has consumed. Both are gitignored.

### Why agents write scratch files instead of the real sources

Ten writers appending to two shared files would race and interleave. Per-book
scratch files plus a merge step mean a run killed halfway leaves whole valid
files behind rather than a corrupted source.

### Interruption is the normal case

Two waves have already been killed mid-flight by session limits. One lost eight
books outright, because every agent had read its whole book, composed all the
summaries in context, and was about to write its files in one shot when it died.
Nothing reached disk.

So agents save every ten days and start by asking what is left. `remaining`
counts both the scratch directory and the merged sources, and `write` skips days
already saved, so rerunning a batch is always safe. A kill now costs at most ten
days of one agent's work, and no assignment restarts from zero.

**Re-dispatching an interrupted agent needs no special handling: give the same
prompt to a new one and it resumes.** If you hit a usage limit, wait for the
reset and re-dispatch whatever has not reported. Claude Code 2.1.234+ continues
the session automatically when the limit lifts, but it does not relaunch
subagents; that is on you.
