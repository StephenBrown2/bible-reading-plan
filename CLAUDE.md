# CLAUDE.md: Shared Bible Reading Plan

## What this is

A single self-contained HTML file (`index.html`, ~2 MB) that generates a
deterministic, seeded daily Bible reading plan: pick a seed, pick a target
reading time, and it gives you one passage a day, in a shuffled-but-reproducible
book order, paced to fit that time. Built so two people in different timezones
can read the same passage on the same day by sharing one URL.

No backend, no build step, no dependencies. Open the file and it runs.

Live at <https://bible.sibii.space> (GitHub Pages, `StephenBrown2/bible-reading-plan`,
`main` branch / repo root, `CNAME` file at root, HTTPS enforced). The repo is
public because Pages on a private repo needs a paid plan. Pages only auto-serves
`index.html` at the domain root, so the file has to keep that name.

Version control is **jj**, not git. See the `jujutsu` skill.

## Maintaining this file

Keep it current. Anything a future agent has to know before touching the code
belongs here: a new constraint, a decision that looks arbitrary from the code
alone, a rule about how the repo is deployed or named. Add it in the same commit
as the change it describes, and delete anything the change made untrue.

Describe the code as it is now. No changelog, no migration notes, no "this used
to be X." That is what `jj --no-pager log` and `jj --no-pager diff` are for, and
a stale account of a previous state is worse than no account at all. Rationale
for a *current* choice is not history, keep that.

## Architecture

### Book order
73 books (66 canonical + 7 deuterocanon: Tobit, Judith, Wisdom, Sirach, Baruch,
1-2 Maccabees) shuffled with a seeded `mulberry32` PRNG. Same seed string means
the same order, always. One explicit rule: if a shuffle happens to land Matthew
first, it's swapped with the second book (`shuffledOrder()`).

### Pacing
`time` (max minutes, default 10) and `wpm` (words per minute, default 180)
together set a word-count target: `min = max(1, time - 5)`, `max = time`. A day's
reading is built by walking chapters/verses until that range is hit, grouping
short chapters together and splitting long chapters at verse boundaries.

### State model, the important part
Progress is not "advance once per app-open." It's anchored to a `startDate`
(day 0) and computed from calendar days elapsed since then:

- `dayIndexToday = daysBetween(startDate, today)`
- if there's a gap since `lastGeneratedDate`, it walks forward through **every**
  missed day in sequence (not skipping), showing a "Catching up" list, landing on
  today's reading last.
- Each unique `(seed, time, wpm)` combination is tracked independently. Changing
  any of the three starts a fresh, separately-tracked plan.
- `startDate` is locked in the first time a given `(seed, time, wpm)` combo is
  used. A `startDate` URL param only seeds a *brand-new* track, it can't
  retroactively shift one already in progress.

This is what lets two people on a shared link land on the same passage on the
same calendar date without a server. See `runPlan()`.

### Persistence
`localStorage`, reached through a small `window.storage` shim near the top of the
script: `get(key)` returns `{value}` or `null`, `set(key, value)` writes. Every
call site wraps its call in try/catch, so private browsing and quota-exceeded
degrade to "nothing persists" rather than breaking.

### URL params (the sync mechanism)
```
?seed=...&time=10&wpm=180&startDate=2026-08-21&version=KJV
```
- `seed`: shuffle seed (any string)
- `time`: max minutes per reading
- `wpm`: reading speed
- `startDate`: day-0 anchor, `YYYY-MM-DD`, only applies to a new track
- `version`: optional translation code, tried against the live API first, falls
  back to WEB (or the embedded Apocrypha-inclusive edition for deuterocanon)

The in-app "Shareable link" box (settings panel) regenerates this from the
*actual stored* `startDate`, so copying it mid-plan still hands a new reader the
correct anchor.

### Text sourcing (three tiers, in order)
1. **Live network**: `bible.helloao.org` (WEB, canonical books only) tried first,
   `bible-api.dws-cloud.com` (WEB, has deuterocanon) as fallback. See
   `fetchChapter()`. Confirmed working on the live site, so this is the normal
   path most days.
2. **Embedded dataset**: the entire WEB Bible + deuterocanon, bundled in the page
   as gzip+base64 text, decompressed client-side via the native
   `DecompressionStream('gzip')` API (no library). Guaranteed fallback,
   available regardless of network. Source: `seven1m/open-bibles`
   (`eng-web.usfx.xml`), footnotes stripped, custom parser preserves paragraph
   (`<p>`) and poetry line (`<q>`) structure as `\n\n` / `\n` markers embedded in
   the verse text itself. Baruch is stored as 6 chapters: the source splits ch. 6
   out as a separate "Letter of Jeremiah" book (`LJE`), merged back into `BAR`
   chapter 6 during the build to match how the live APIs treat it.
3. **Offline word-count estimate**: last resort, uses a static per-book
   average-words-per-chapter table (`BOOKS` array) plus four hardcoded
   known-long-chapter overrides (Psalm 119, 1 Kings 8, Numbers 7,
   Deuteronomy 28). Defensive code, should essentially never trigger now that
   tier 2 covers all 73 books.

`renderVerseStream()` splits on the embedded `\n\n`/`\n` markers to produce real
`<p>` paragraphs for prose and hanging-indent `<div class="poem-line">` blocks
for poetry. Sources with no structure info (tier 3, and tier 1's dws-cloud
specifically) render as one flowing paragraph. That's graceful degradation, not a
bug.

### Regenerating the embedded dataset
The build scripts that produced the embedded blob were run locally and aren't
committed. If it ever needs regenerating: fetch `eng-web.usfx.xml` from
`seven1m/open-bibles`, strip `<f>`/`<x>`/`<d>` blocks (footnotes, cross-refs,
Psalm superscriptions, all dropped since none are rendered anywhere), walk
`<book>`/`<c>`/`<v>`/`<ve>` tags to build
`{BOOK_ID: [[[verseNum, text], ...], ...]}` (array of chapters, each an array of
`[verseNum, text]` pairs; verse numbers aren't always contiguous, e.g. Sirach, so
don't assume `index = verse - 1`), track `<p>`/`<q>`/`<b/>` as paragraph/line
markers per the scheme above, merge `LJE` into `BAR[5]` (0-indexed chapter 6),
filter to the 73 needed book IDs, `json.dumps(..., separators=(',',':'))`,
`gzip.compress(..., 9)`, `base64.b64encode`, drop into the
`<script type="text/plain" id="embeddedWebDataGz">` tag before `</body>`.

## Things NOT to do

- Don't re-embed the Bible text uncompressed "for simplicity." Raw JSON is
  ~4.65 MB, gzip+base64 gets it to ~1.9 MB. No reason to regress it.
- Don't switch the embed compression to Brotli. Smaller (~1.5 MB total) but
  native `DecompressionStream('brotli')` support is inconsistent enough that it
  isn't worth two code paths. Gzip has been Baseline-supported since 2023.
- Don't add real per-chapter word-count data to replace the tier-3 averages.
  Tier 3 only runs if a book is missing from the embedded dataset (none are) or
  the embedded data fails to load at runtime. Sourcing exact counts for ~1,200
  chapters is real effort spent on a path expected never to execute. If tier 3
  starts triggering in practice, that's the signal to revisit.
- Don't rename `index.html`. Pages serves it at the domain root by that name.
