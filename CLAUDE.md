# CLAUDE.md — Shared Bible Reading Plan

Handoff notes for whichever agent (Claude Code or otherwise) picks this up next.
Read this whole file before touching code — several decisions below look
arbitrary until you know why they were made.

## What this is

A single self-contained HTML file (`bible-reading-plan.html`, ~2 MB) that
generates a deterministic, seeded daily Bible reading plan — pick a seed,
pick a target reading time, and it gives you one passage a day, in a
shuffled-but-reproducible book order, paced to fit that time. Built so two
people (three timezones apart) can read the same passage on the same day
by sharing one URL.

No backend. No build step. Open the file and it runs.

## ⚠️ Do this first: `window.storage` will not work outside Claude.ai

The single biggest thing to fix before this is useful anywhere else:
**all persistence currently goes through `window.storage.get/set`**, which
is a Claude-artifact-runtime API. It does not exist in a normal browser.
Outside claude.ai (i.e. once this is hosted on GitHub Pages), every call
silently fails — they're all wrapped in `try/catch` — meaning:

- the day-by-day reading pointer never advances correctly (resets to day 0
  on every load)
- the catch-up logic never sees a `lastGeneratedDate`, so it never triggers
  correctly
- seed / time / wpm preferences don't persist between visits
- the live-fetch chapter cache doesn't cache (minor — embedded text doesn't
  depend on this)

**Fix:** replace the `window.storage` calls with `localStorage` (or a tiny
wrapper function that tries `localStorage` and no-ops on failure for
private-browsing edge cases). There are exactly 8 call sites — search for
`window.storage` in the file. All of them already have the
`get(key, false) → {value}` / `set(key, value, false)` shape; `localStorage`
just needs `JSON.stringify`/`JSON.parse` at the same points (already being
done) and drops the `false` shared-flag argument.

Everything else in the file is standard Web APIs (`fetch`, `Blob`,
`DecompressionStream`, `atob`, `history.replaceState`) and will work fine
on GitHub Pages unchanged.

**Bonus once hosted outside Claude:** the published-artifact sandbox
apparently blocks `fetch()` to third-party domains (confirmed via user
testing — live text never worked when published as a Claude artifact,
worked fine locally). GitHub Pages has no such restriction, so live fetch
to `bible.helloao.org` / `bible-api.dws-cloud.com` should actually start
working there, on top of the embedded fallback. Worth verifying once
deployed, but not a blocker.

## Architecture

### Book order
73 books (66 canonical + 7 deuterocanon: Tobit, Judith, Wisdom, Sirach,
Baruch, 1–2 Maccabees) shuffled with a seeded `mulberry32` PRNG. Same seed
string → same order, always. One explicit rule: if a shuffle happens to
land Matthew first, it's swapped with the second book (`shuffledOrder()`).

### Pacing
`time` (max minutes, default 10) and `wpm` (words per minute, default 180)
together set a word-count target: `min = max(1, time - 5)`,
`max = time`. A day's reading is built by walking chapters/verses until
that range is hit — grouping short chapters together, splitting long
chapters at verse boundaries (see "text sourcing" below for how word
counts are known).

### State model — the important part
Progress is **not** "advance once per app-open." It's anchored to a
`startDate` (day 0) and computed as a pure-ish function of calendar days
elapsed since then:

- `dayIndexToday = daysBetween(startDate, today)`
- if there's a gap since `lastGeneratedDate`, it walks forward through
  **every** missed day in sequence (not skipping), showing a "Catching up"
  list, landing on today's reading last.
- Each unique `(seed, time, wpm)` combination is tracked independently —
  changing any of the three starts a fresh, separately-tracked plan.
- `startDate` is locked in the first time a given `(seed, time, wpm)` combo
  is used; a `startDate` URL param only seeds a *brand-new* track, it can't
  retroactively shift an in-progress one.

This is what lets two people on a shared link land on the same passage on
the same calendar date without a server — see the `runPlan()` function.

### URL params (the sync mechanism)
```
?seed=...&time=10&wpm=180&startDate=2026-08-21&version=KJV
```
- `seed` — shuffle seed (any string)
- `time` — max minutes per reading
- `wpm` — reading speed
- `startDate` — day-0 anchor, `YYYY-MM-DD`, only applies to a new track
- `version` — optional translation code, tried against the live API first,
  falls back to WEB (or the embedded Apocrypha-inclusive edition for
  deuterocanon)

The in-app "Shareable link" box (settings panel) regenerates this from the
*actual stored* `startDate`, so copying it later — even mid-plan — still
hands a new reader the correct anchor.

### Text sourcing (three tiers, in order)
1. **Live network**: `bible.helloao.org` (WEB, canonical books only) tried
   first, `bible-api.dws-cloud.com` (WEB, has deuterocanon) as fallback —
   see `fetchChapter()`. Currently non-functional when published as a
   Claude artifact (see the warning above); should work on GitHub Pages.
2. **Embedded dataset**: the entire WEB Bible + deuterocanon, bundled in
   the page itself as gzip+base64 text, decompressed client-side via the
   native `DecompressionStream('gzip')` API (no library). This is the
   guaranteed fallback — always available regardless of network. Source:
   `seven1m/open-bibles` (`eng-web.usfx.xml`), footnotes stripped, custom
   parser preserves paragraph (`<p>`) and poetry line (`<q>`) structure as
   `\n\n` / `\n` markers embedded in the verse text itself. Deuterocanon's
   Baruch is stored as 6 chapters — the source splits ch. 6 out as a
   separate "Letter of Jeremiah" book (`LJE`), which gets merged back into
   `BAR` chapter 6 during the build to match how the live APIs treat it.
3. **Offline word-count estimate**: last resort, uses a static per-book
   average-words-per-chapter table (`BOOKS` array) plus four hardcoded
   known-long-chapter overrides (Psalm 119, 1 Kings 8, Numbers 7,
   Deuteronomy 28). Should essentially never trigger now that tier 2 covers
   all 73 books — it's defensive code, not expected to be load-bearing.

Rendering (`renderVerseStream()`) splits on the embedded `\n\n`/`\n`
markers to produce real `<p>` paragraphs for prose and hanging-indent
`<div class="poem-line">` blocks for poetry. Sources with no structure
info (tier 3, and tier 1's dws-cloud specifically) just render as one
flowing paragraph — graceful degradation, not a bug.

### Regenerating the embedded dataset
The build scripts that produced the embedded blob were run locally against
`raw.githubusercontent.com` (not committed to this repo). If it ever needs
regenerating: fetch `eng-web.usfx.xml` from `seven1m/open-bibles`, strip
`<f>`/`<x>`/`<d>` blocks (footnotes/cross-refs/Psalm superscriptions —
dropped entirely, not currently rendered anywhere), walk `<book>`/`<c>`/
`<v>`/`<ve>` tags to build `{BOOK_ID: [[[verseNum, text], ...], ...]}`
(array of chapters, each an array of `[verseNum, text]` pairs — verse
numbers aren't always contiguous, e.g. Sirach, so don't assume
index = verse - 1), track `<p>`/`<q>`/`<b/>` as paragraph/line markers per
the scheme above, merge `LJE` into `BAR[5]` (0-indexed chapter 6), filter
to the 73 needed book IDs, `json.dumps(..., separators=(',',':'))`,
`gzip.compress(..., 9)`, `base64.b64encode`, drop into the
`<script type="text/plain" id="embeddedWebDataGz">` tag before `</body>`.

## Deployment target

GitHub Pages, custom subdomain (not yet set up as of this handoff). Plan
discussed with the user:

1. Repo created, this file pushed as **`index.html`** at the repo root (not
   `bible-reading-plan.html` — GitHub Pages only auto-serves `index.html`
   at the bare domain root; anything else requires the full filename in
   the URL). `/docs` as the Pages source also works, same filename rule
   applies there instead.
2. Pages enabled via `gh api -X POST repos/{owner}/{repo}/pages -f
   source[branch]=main -f source[path]=/`.
3. Custom domain (subdomain preferred over apex — simpler DNS) set via
   `gh api -X PUT repos/{owner}/{repo}/pages -f cname=<chosen-subdomain>`.
4. **User still needs to manually add a CNAME record** at their DNS
   provider pointing `<subdomain>` → `<username>.github.io`. This cannot be
   automated from the GitHub side — ask the user for the domain/DNS
   provider if this hasn't happened yet.
5. Poll `gh api repos/{owner}/{repo}/pages` for
   `https_certificate.state` until ready, then `gh api -X PUT
   repos/{owner}/{repo}/pages -f https_enforced=true`.

## Things NOT to do

- Don't reintroduce `localStorage`/`sessionStorage` calls guarded by
  "Claude artifacts don't support this" — that constraint doesn't apply
  once this is a plain static file. `window.storage` is the one that needs
  removing, not avoiding `localStorage`.
- Don't re-embed the Bible text uncompressed "for simplicity" — raw JSON
  is ~4.65 MB, gzip+base64 gets it to ~1.9 MB. This was a deliberate
  tradeoff after the file failed to publish as a Claude artifact at the
  larger size; keep it compressed even though that constraint is gone on
  GitHub Pages (no reason to regress it).
- Don't switch the embed compression to Brotli — smaller (~1.5 MB total)
  but native `DecompressionStream('brotli')` browser support is
  inconsistent enough that it's not worth the two-code-path complexity for
  the savings. Gzip's been Baseline-supported everywhere since 2023.
- Don't add real per-chapter word-count data to replace the tier-3
  averages. Reasoning: tier 3 only runs if a book is missing from the
  embedded dataset (it isn't — all 73 are covered) or the embedded data
  fails to load at runtime (e.g. `DecompressionStream` unsupported, or the
  `<script>` tag itself didn't parse) — both edge cases, not the normal
  path. Sourcing and maintaining exact word counts for ~1,200 chapters is
  real effort to spend on a fallback that's already "good enough" (rough
  per-book averages, plus four hardcoded long-chapter overrides for the
  worst offenders) for a path expected to almost never execute. If tier 3
  starts triggering in practice — e.g. because `DecompressionStream`
  support turns out to be less universal than assumed — that's a signal to
  revisit this, not a reason to preemptively harden it now.

## Open items / possible next steps

- Custom domain not yet live — see Deployment target above.
- `window.storage` → `localStorage` swap is the one functional blocker;
  everything else in the file should work as-is once hosted.
- Consider verifying live-fetch actually works once off Claude's
  infrastructure (see the "Bonus" note above) — if so, the tier ordering
  (live-first) means most days will show live text with the embedded copy
  rarely invoked, which is fine, just worth confirming end-to-end once.
