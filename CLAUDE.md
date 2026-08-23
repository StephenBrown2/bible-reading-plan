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

## Skills to use here

- **`/jujutsu`** before any version-control operation. This repo is jj, not git.
  Raw git commands can corrupt jj state, and the skill covers the parts that
  differ most: bookmarks don't auto-advance, the working copy is itself a commit,
  and interactive commands hang an agent. Load it even for something as small as
  checking status.
- **`/ponytail`** for code changes. This is one HTML file with no build step and
  no dependencies, and it should stay that way.

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
83 books shuffled with a seeded `mulberry32` PRNG: the 66 canonical, the 7
deuterocanon (Tobit, Judith, Wisdom, Sirach, Baruch, 1-2 Maccabees), and the
wider canon (Greek Esther, Song of the Three, Susanna, Bel and the Dragon,
1-2 Esdras, Prayer of Manasseh, Psalm 151, 3-4 Maccabees). That last group is
the WEB Apocrypha as published. It counts as 83 rather than the 81 an api.bible
edition reports because the source splits the Greek Daniel additions into three
books where api.bible's WEB carries them merged as `DAG`. Same seed string means
the same order, always. One explicit rule: if a shuffle happens to land Matthew
first, it's swapped with the second book (`shuffledOrder()`).

### Seeds
There is no default seed. A visitor with nothing stored gets a 12-character
base58 seed from `generateSeed()`, which `runPlan()` then writes into the URL
along with the locked `startDate`, so a freshly generated plan is shareable the
moment it renders. Base58 omits `0`, `O`, `I` and `l` so a seed survives being
read aloud. Clearing the seed box in the settings panel generates a new one
rather than returning to a fixed default, because there no longer is one.

Existing stored seeds are untouched: `getActiveSeed()` only generates when
storage holds nothing.

### Pacing
`time` (max minutes, default 5) and `wpm` (words per minute, default 180) set a
word ceiling of `time * wpm`. A reading is **one chapter at most**: a chapter
longer than the ceiling splits across days at a verse boundary, and a short
chapter is simply a short day. Chapters are never merged, which is why there is
no lower bound.

A split is **even, not greedy**. Filling each day to the ceiling leaves a stub
(Matthew 5 used to come out 888 words then 177); instead the words left in the
chapter decide how many days remain, `ceil(remaining / ceiling)`, and today
takes `remaining / days`. A verse joins the day while its midpoint still falls
inside that target, which lands nearer the target than stopping strictly under
it. Because it is recomputed from the current position each day, changing
`time` part-way through a chapter rebalances whatever is left rather than
stranding it. Verified across all 1,391 chapters: coverage is exact, no day
exceeds the ceiling, and the even rule needs no more days than the greedy one
did.

### State model, the important part
Progress is not "advance once per app-open." It's anchored to a `startDate`
(day 0) and computed from calendar days elapsed since then:

- `dayIndexToday = daysBetween(startDate, today)`
- if there's a gap since `lastGeneratedDate`, every owed day is built in
  sequence into `PENDING`, oldest first, ending with today. The page opens on
  the **oldest unread day**, and Next steps forward through the backlog.
- Each unique `(seed, time, wpm)` combination is tracked independently. Changing
  any of the three starts a fresh, separately-tracked plan.
- `startDate` is locked in the first time a given combination is
  used. A `startDate` URL param only seeds a *brand-new* track, it can't
  retroactively shift one already in progress.

This is what lets two people on a shared link land on the same passage on the
same calendar date without a server. See `runPlan()`.

A day is committed only when the reader steps *past* it: `commitThrough()` moves
the cursor and sets `lastGeneratedDate` to that day's date. Closing the tab half
way through a backlog therefore resumes where they stopped rather than losing
the rest, which is why `lastGeneratedDate` advances one day at a time instead of
jumping to today. Today's entry commits as soon as it is reached, so a visitor
with nothing owed behaves exactly as before. "Skip to today" and clicking ahead
in the list commit everything jumped over; stepping back only re-reads.

### The reading-order panel
83 entries in a horizontally scrolled grid of 12 rows. Columns are uniform and
as wide as the longest entry, which comes from `grid-auto-columns: 1fr` inside a
`width: max-content` grid: `fr` tracks under a max-content constraint all take
the width of the widest item. No measuring, and it is right even though the
panel is `display:none` until opened, which is what defeats the obvious
JavaScript version (a hidden element measures zero).

Entries are `white-space: nowrap`. That is not only cosmetic: it keeps every row
one line tall, so the shared row heights of a grid can't leave a gap across every
column when one name wraps.

### Single-chapter books
Ten books are one chapter (Obadiah, Philemon, 2-3 John, Jude, and five of the
wider canon), where a chapter number carries no information. `referenceRange()`
labels those by verse instead, "Verses 1-41" or "All 25 verses", and the meta
row and progress bar count verses rather than "Ch. 1 of 1". BibleGateway
addresses them the same way, so the external link takes a bare verse range.

The percentage counts verse *positions*, not verse numbers: numbering has gaps
in several of these books, so the last verse number is not the number of verses
read.

### Persistence
`localStorage` through two helpers, `load(key, fallback)` and `save(key, value)`,
which own the JSON round-trip and the try/catch. Private browsing and a full
quota both throw, so every call has to tolerate getting the fallback back.

Chapters fetched from a live provider are cached, and `pruneChapterCache()`
drops everything but the current chapter after each render. A reading is one
chapter, so yesterday's can never be read again; without the prune a year of
daily reading would put roughly 2.7MB of chapter JSON against a 5MB origin
quota, and once `save()` starts throwing the cache would silently never fill
again. The embedded text is never cached: it is decompressed into memory once
and its tier returns before the caching code.

### URL params (the sync mechanism)
```
?seed=...&time=5&wpm=180&startDate=2026-08-21&version=KJV
```
- `seed`: shuffle seed (any string); generated if absent, see below
- `time`: max minutes per reading, default 5
- `wpm`: reading speed, default 180
- `startDate`: day-0 anchor, `YYYY-MM-DD`, only applies to a new track
- `version`: optional translation code, serving two unrelated namespaces

`version` means two things at once. It selects the "Read online" BibleGateway
link's translation, where any BibleGateway code works, *and* it picks the
edition the passage text is fetched in. `TEXT_TRANSLATIONS` is the list of
codes that can do the second job; anything outside it steers the BibleGateway
link only and the text stays WEB. The text panel's label names the edition
actually shown, so a code that can't be honored fails visibly.

Adding a code means checking it against both providers first, because their ids
disagree: api.bible uses opaque hex ids, bolls is uppercase and sometimes
versioned (`CSB17`, `NIV2011`) or differently abbreviated (`DRB`, not `DRA`).
Deuterocanon narrows it further, per edition rather than per provider: an
edition without the book answers with a 404 or an empty chapter, which falls
through to the next attempt on its own.

Both `<select>` controls are built from `TEXT_TRANSLATIONS` by
`versionOptions()`. The passage one sits inside `#textPanel`, above the text it
governs, so it appears only with Show text, and applies on `change`: a
translation changes only which text is fetched, never the pacing or the plan's
position, so it needs no Apply. The "Read online" one keeps its own card and
filters to entries flagged `deutero: true` when the day's book needs it.

`version` stays out of the shareable link until it is actually chosen, since the
default option's value is `""` and `updateShareLink()` only writes the parameter
when `REQUESTED_VERSION` is set.

The shareable link is a plain `<footer class="share">` at the end of `.page`, in
normal flow. Deliberately not sticky: it is a thing to copy occasionally, not a
control, and a fixed bar would eat reading space on a phone. Clicking the text
or the button copies it; `navigator.clipboard` needs a secure context *and*
transient user activation, so the failure path selects the text instead of
pretending to have copied it.

The in-app "Shareable link" box (settings panel) regenerates this from the
*actual stored* `startDate`, so copying it mid-plan still hands a new reader the
correct anchor.

### Text sourcing, ordered by formatting rather than freshness
Providers are tried in descending order of the structure they preserve, not by
freshness or preference. Only two sources mark prose paragraphs at all: api.bible
and the embedded dataset. bolls marks line breaks but cannot tell a paragraph
from a line. So **WEB comes from the embedded copy first** (no network, no quota,
and already paragraph-marked), and everything else tries api.bible before
bolls.

1. **Live network**, in order: `api.scripture.api.bible` (real USFM structure:
   paragraphs, poetry, headings, translator-supplied words; key required; only
   some translations licensed to a given key, and deuterocanon coverage varies by
   edition rather than by provider), then `bolls.life` (line breaks and inline
   emphasis, and the sole source for the copyrighted translations api.bible is
   not licensed for). See `fetchChapter()`.

   Two providers, not more: a third only earns its place if it is the sole
   source for a translation worth having, since anything that marks no
   paragraphs sits permanently behind these two anyway.

   api.bible's JSON gives USFM para styles: `p`/`m`/`li` prose, `q*` poetry,
   `s*`/`r`/`d` headings, `b` blank line, and char style `add` for words the
   translators supplied. `fetchFromApiBible()` maps those onto the renderer's
   `\n\n` / `\n` / emphasis convention, dropping heading text while keeping the
   break it implies, matching what the other tiers do with theirs. Careful with
   the whitespace cleanup there: a verse's leading newline *is* its paragraph
   marker, so a plain `.trim()` silently flattens a whole chapter into one
   paragraph.

   Everything a provider marks is kept, footnotes included. From bolls that means `<br>` becomes the renderer's `\n`, and
   `<i>`/`<e>`/`<b>` (translator-supplied words in NKJV and KJV, AMP's bracketed
   amplifications, CSB's OT quotations) survive `escapeHtml()` as control
   characters and come back as `<em>`/`<strong>` in `renderVerseStream()`.

   Two things bolls can't give: it has no paragraph mark, so a passage carrying
   any `<br>` renders as poetry throughout, including prose; and it prepends
   section headings to a verse ahead of a `<br>`, indistinguishable from a first
   line of poetry, so headings stay part of the verse text rather than being
   guessed at. Editions also differ in how much they mark, and where they
   differ the formatted one wins for local display: `NIV` maps to bolls' 1984
   edition, which marks poetry lines and headings, rather than its `NIV2011`,
   which marks nothing. The label names the edition so the swap is visible. What
   the BibleGateway link opens is a separate question and not ours to control.

   Worth knowing: bolls serves the copyrighted translations with no licensing
   story visible, so it may be redistributing without permission. api.bible and
   the embedded copy are unambiguously licensed, and the plan still works if
   bolls goes away, just without the modern translations.

   bolls addresses books by number rather than USFM id. `BOLLS_BOOK_IDS` derives
   the 66 canonical numbers from each book's position in `BOOKS` instead of
   restating them, so reordering `BOOKS` would silently point readings at the
   wrong book. `./check-bolls-books.py` asserts the numbering bolls actually
   uses. Run it after touching `BOOKS`.
2. **Embedded dataset**: the entire WEB Bible + deuterocanon, bundled in the page
   as brotli+base64 text, decompressed client-side via the native
   `DecompressionStream('brotli')` API (no library).

   **This tier does not work in Chrome.** `DecompressionStream` accepts brotli in
   Firefox 147+ and Safari 18.4+ only; Chrome supports gzip and deflate but not
   brotli, and the constructor throws. `loadEmbeddedWeb()` catches that, memoises
   an empty result, and the chain falls through to the live providers. Measured
   consequences on Chrome: canonical books read normally from api.bible's WEB
   (paragraphs and footnotes intact), 7 of the 10 wider-canon books resolve the
   same way, but **Song of the Three, Susanna and Bel and the Dragon have no live
   source at all** and land on the word-count estimate, and offline reading is
   gone entirely. Chrome also still downloads the 1.6 MB blob it cannot use.

   That was accepted deliberately in exchange for the smaller page (brotli q11
   base64 is 1,625,908 characters against gzip's 2,181,304). The way out, when it
   is worth doing, is two sibling files chosen by feature detection: a `.br` for
   Firefox and Safari, a `.gz` for Chrome. That also drops index.html to tens of
   KB. It is on the table, not done. Best-formatted source and the
   guaranteed fallback, available regardless of network. It lives in a
   `<script type="text/plain">` tag *after* the main script, so `init()` runs on
   `DOMContentLoaded` rather than inline: reading that element too early yields
   nothing, and `getEmbeddedWeb()` memoises its result, so an early empty answer
   would stick for the whole session and every reading would silently come from
   the live providers instead. Source: `seven1m/open-bibles`
   (`eng-web.usfx.xml`), footnotes stripped, custom parser preserves paragraph
   (`<p>`) and poetry line (`<q>`) structure as `\n\n` / `\n` markers embedded in
   the verse text itself. Baruch is stored as 6 chapters: the source splits ch. 6
   out as a separate "Letter of Jeremiah" book (`LJE`), merged back into `BAR`
   chapter 6 during the build to match how the live APIs treat it.
3. **Offline word-count estimate**: last resort, uses a static per-book
   average-words-per-chapter table (`BOOKS` array) plus four hardcoded
   known-long-chapter overrides (Psalm 119, 1 Kings 8, Numbers 7,
   Deuteronomy 28). Defensive code, should essentially never trigger now that
   tier 2 covers all 83 books.

`renderVerseStream()` splits on the embedded `\n\n`/`\n` markers to produce real
`<p>` paragraphs for prose and hanging-indent `<div class="poem-line">` blocks
for poetry. A source with no structure info renders as one flowing paragraph.
That's graceful degradation, not a bug.

### Footnotes
A verse carries an optional `notes` array, and its text carries `\u0005i\u0005`
markers naming the index. `renderVerseStream()` flattens the passage's notes,
renumbers the markers, and emits a `<button popovertarget>` plus a
`<span popover>` per note: the Popover API does the opening and closing with no
script of ours, so the Invoker Commands API is not needed. Markers are lettered
(a, b, ... aa) precisely because verse numbers are numbered; the two sit side by
side and must not be confused.

Each pair gets a matching `anchor-name` / `position-anchor` so the note opens
beside its own marker. The area is `block-end span-all`, and that choice is
load-bearing: giving the note the whole inline axis means a marker near an edge
can never squeeze it into a narrow column, in any engine. Only `flip-block` is a
fallback, since only the vertical direction can genuinely run out of room.

A corner like `span-inline-end` plus `position-try-order: most-width` also
works, and was what shipped first. It was replaced because `span-all` needs no
second property to behave: with the full inline axis there is no narrower option
for an engine to pick, so nothing depends on how any given engine orders its
fallbacks. Both were reported broken in Firefox at one point; both times that
turned out to be a stale cache, not the CSS.

Anchor positioning itself needs Firefox 147+ / Chrome 125+ / Safari 26+, and
`position-anchor` specifically needs Firefox 151+ / Chrome 151+. Below those, the
`@supports` guard drops the whole block and the popover centres, which is fine.
A `<button popovertarget>` is also its popover's *implicit* anchor, so the
positioning still binds even where `position-anchor` is ignored.

Test this at a phone width, not a desktop one. Every marker sits far from the
edge on a wide viewport, so the bug is invisible there. And when checking a fix
on a real device, force a cache bypass first: Pages serves the page with
`cache-control: max-age=600`, and two separate browsers hold two separate stale
copies. Two rounds of this bug were chased as CSS before turning out to be that. Resizing the browser
window only works if it isn't maximized or tiled; otherwise the resize reports
success and is ignored, and the fallback is to pin `#textPanel` to the viewport
edge and read the geometry from there. That lives in an `@supports (anchor-name: --a)` block; without
anchor positioning the popover keeps its centred default, which is a fine
fallback rather than a broken one.

Only a marker immediately followed by *another* marker gets trailing space
(`.note-ref-abutting`). The renderer decides that by looking at the character
after the match, because CSS sibling selectors can't see the text node that
separates the common case.

Where each source keeps them:
- **Embedded**: `<f>` and `<x>` from the USFX, captured by `build-embedded.py`
  into the third element of a verse entry. 2,867 notes, which cost 74KB of the
  compressed blob.
- **api.bible**: `include-notes=true`, then `name: "note"` items whose `fr`/`ft`
  children read fine run together. Two traps there: `char` style `sup` is the
  printed punctuation *between* two note callers and would otherwise land in the
  verse as a stray comma, and api.bible brackets some dashes with `#`, which is
  markup rather than text.
- **bolls**: bodies live in a separate `comment` field, one per `<br>`, each
  opening with the marker that matches a `<sup>` in the verse. Several editions
  (ESV, NKJV, NLT) supply bodies with no marker in the text at all, so those
  attach to the end of the verse instead of being dropped. NIV has none.

### The wider canon and its fallbacks
The 10 wider-canon books deliberately have **no bolls number**. bolls renumbers
that part of the canon per translation (76 is the Prayer of Manasseh in its KJV
and 3 Maccabees in its LXXE), and a wrong number there would serve a different
book's text, which is the worst failure this app can have. They skip bolls and
use api.bible or the embedded copy, both of which address books by USFM id.
`check-bolls-books.py` fails if one of them ever acquires a number.

api.bible coverage is per edition: its WEB has Greek Esther, 1-2 Esdras, Prayer
of Manasseh, 3-4 Maccabees and Psalm 151 but not the three Daniel additions,
while its KJV and RV have the Daniel additions but not 3-4 Maccabees or Psalm
151. Anything an edition lacks falls through to the embedded copy, which has all
83, so every book is covered offline regardless.

### Regenerating the embedded dataset
`./build-embedded.py` rebuilds every book from the USFX source; `--check` parses
and reports without writing. The break rule is that the strongest break in a gap
wins, which is what makes prose resuming after poetry (Judges 5:31) a paragraph,
and `<b/>` is ignored because the `<p>` or `<q>` on either side already
describes the gap.

The manual recipe, for reference: fetch `eng-web.usfx.xml` from
`seven1m/open-bibles`, strip `<f>`/`<x>`/`<d>` blocks (footnotes, cross-refs,
Psalm superscriptions, all dropped since none are rendered anywhere), walk
`<book>`/`<c>`/`<v>`/`<ve>` tags to build
`{BOOK_ID: [[[verseNum, text, notes?], ...], ...]}` (array of chapters, each an
array of `[verseNum, text]` pairs with an optional third element holding the
verse's footnotes; verse numbers aren't always contiguous, e.g. Sirach, so don't
assume `index = verse - 1`), track `<p>`/`<q>`/`<b/>` as paragraph/line markers
per the scheme above, merge `LJE` into `BAR[5]` (0-indexed chapter 6),
filter to the 83 needed book IDs, `json.dumps(..., separators=(',',':'))`,
`brotli.compress(..., quality=11)`, `base64.b64encode`, drop into the
`<script type="text/plain" id="embeddedWebDataBr">` tag before `</body>`.

### The api.bible key
`API_BIBLE_KEY` in `index.html` holds the key XOR'd against `API_BIBLE_PAD` and
base64'd. That is a speed bump against scrapers grepping for key-shaped strings,
not a secret store: the page is public, and anyone with devtools can recover it.
The owner accepted that tradeoff and can regenerate the key at
<https://scripture.api.bible> if the quota starts moving unexpectedly.

The plaintext key lives in `.api-key`, which is gitignored and **must never be
committed**. jj snapshots new files automatically, so check `jj st` before
describing a change. `./set-api-key.py` reads that file and rewrites the
`API_BIBLE_KEY` line. With no key the provider returns `null` and the chain
carries on to the next one, so the page still works for anyone who clones it.

That key's licensing reaches CSB, AMP, NASB1995, ASV, KJV, DRA, WEB and a number
of other public-domain editions. ESV, NIV, NLT, NKJV, NRSVCE, NABRE and RSV are
*not* included: they need separate publisher approval, and until that exists they
come from bolls.

Deuterocanon on api.bible is per edition, not per provider, and the editions that
carry it are all public domain, so they cost nothing against the plan's
copyrighted-translation slots: DRA is exactly the 73 canonical and deuterocanon
books, KJV
and RV 1885 have 80, and several WEB editions have 73 to 81. CSB, AMP and
NASB1995 are 66 only. An edition that lacks a book answers with a 404, which
falls through to the next provider on its own, so no per-edition book list is
maintained here.

## Things NOT to do

- Don't re-embed the Bible text uncompressed "for simplicity." Raw JSON is
  ~5.5 MB, brotli+base64 gets it to ~1.6 MB. No reason to regress it.
- Don't "fix" Chrome by going back to gzip. The embed is brotli on purpose, and
  the Chrome gap is a known, accepted cost. See the note below.
- Don't add real per-chapter word-count data to replace the tier-3 averages.
  Tier 3 only runs if a book is missing from the embedded dataset (none are) or
  the embedded data fails to load at runtime. Sourcing exact counts for ~1,200
  chapters is real effort spent on a path expected never to execute. If tier 3
  starts triggering in practice, that's the signal to revisit.
- Don't rename `index.html`. Pages serves it at the domain root by that name.
