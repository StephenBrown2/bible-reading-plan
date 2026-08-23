# Shared Bible Reading Plan

A deterministic daily Bible reading plan in a single self-contained HTML file.
Pick a seed, pick a target reading time, and it gives you one passage a day in a
shuffled but reproducible book order, paced to fit that time. Two people in
different timezones who open the same URL land on the same passage on the same
calendar date, with no server involved.

Live at **<https://bible.sibii.space>**

83 books: the 66 canonical, the 7 deuterocanon (Tobit, Judith, Wisdom, Sirach,
Baruch, 1-2 Maccabees), and the wider canon (Greek Esther, Song of the Three,
Susanna, Bel and the Dragon, 1-2 Esdras, Prayer of Manasseh, Psalm 151,
3-4 Maccabees).

## Sharing a plan

Open the page. It generates a seed, locks today as day 0, and rewrites the
address bar with everything needed to reproduce that plan:

```
https://bible.sibii.space/?seed=cisVXBmDX6Bq&time=5&wpm=180&startDate=2026-08-22
```

Send that URL to someone and they get the identical plan on the identical
schedule. The settings panel has a "Shareable link" box with the same thing,
regenerated from your stored start date, so copying it mid-plan still hands a
new reader the correct day-0 anchor.

## URL parameters

All are optional. Anything you leave out falls back to what you used last time,
then to the default.

### `seed`

The shuffle seed. Any string. The same seed always produces the same book order.

If you don't supply one and none is stored, a 12-character seed is generated
from a base58 alphabet (`123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz`,
which omits `0`, `O`, `I` and `l` so a seed survives being read aloud or
retyped) and written back into the URL. Changing the seed starts a completely
separate plan, tracked independently.

```
?seed=cisVXBmDX6Bq          generated, or any string you like
?seed=lent-2026             human-chosen seeds work just as well
```

### `time`

Maximum minutes per reading. **Default 5.** Combined with `wpm` this sets a word
ceiling: at the default 5 minutes and 180 wpm, 900 words.

A reading is always one chapter at most. A chapter longer than the ceiling is
split across days at a verse boundary, and a chapter shorter than it is simply a
short day. Chapters are never merged to fill the time, so there is no minimum.

Splits are even rather than greedy: Matthew 5 comes out as two days of about 515
and 550 words, not 888 and a dangling 177.

```
?time=5      the default
?time=15     longer daily readings
```

### `wpm`

Your reading speed in words per minute, used to turn `time` into a word count.
**Default 180**, an unhurried silent-reading pace. Raise it for more text per
day, lower it for less.

```
?wpm=180     the default
?wpm=250     faster reader, so more text in the same minutes
```

### `startDate`

The day-0 anchor, as `YYYY-MM-DD`. Progress is not "advance once per visit": it
is computed from the number of calendar days between this date and today, which
is what keeps two readers in sync without a server.

Miss a week and nothing is skipped. The page opens on the oldest reading you
still owe and a "Catching up" panel steps you forward one day at a time, or
straight to today if you would rather. A day only counts as read once you move
past it, so you can stop half way and pick up there next time.

**It only applies to a brand-new plan.** Once a given combination of settings
has a start date, that date is locked and a `startDate` in the URL is ignored,
so sharing a link can't retroactively shift someone's plan.

```
?startDate=2026-08-22
```

### `version`

The translation. This parameter does two jobs at once.

It picks the translation for the **"Read online" link**, where any
[BibleGateway](https://www.biblegateway.com) code works, including ones no free
API carries.

It also picks the translation for the **passage text shown in the page**, but
only for codes a text provider actually has. Anything else leaves the displayed
text as the World English Bible. The text panel always names the edition you are
actually reading, so a code that can't be honored is visible rather than silent.

Codes that change the displayed text:

| Code | Translation | | Code | Translation |
|---|---|---|---|---|
| `WEB` | World English Bible (default) | | `NKJV` | New King James Version |
| `KJV` | King James Version | | `CSB` | Christian Standard Bible |
| `ASV` | American Standard Version | | `NASB` | New American Standard Bible |
| `BSB` | Berean Standard Bible | | `MSG` | The Message |
| `DRA` | Douay-Rheims | | `AMP` | Amplified Bible |
| `NET` | NET Bible | | `RSV` | Revised Standard Version |
| `YLT` | Young's Literal Translation | | `NRSVCE` | NRSV Catholic Edition |
| `ESV` | English Standard Version | | `RSVCE` | RSV Second Catholic Edition |
| `NIV` | New International Version, 1984 | | `NABRE` | New American Bible, Revised Edition |
| `NLT` | New Living Translation | | `CEB` | Common English Bible |

Deuterocanon coverage varies by translation. Where an edition doesn't carry a
book, that day's reading falls back to the World English Bible rather than
failing.

```
?version=CSB        Christian Standard Bible
?version=NRSVCE     a Catholic edition, deuterocanon included
?version=ESV        text from the ESV where available
```

## How the text is fetched

Sources are tried in descending order of how much formatting they preserve,
not by freshness:

1. **api.bible** for translations licensed to this deployment's key. The only
   live source with real paragraph structure, plus poetry lines, headings and
   translator-supplied words shown in italics.
2. **bolls.life** for the modern copyrighted translations no one else carries.
   Line breaks and inline emphasis, no paragraph marks.
3. **The embedded copy.** The entire World English Bible, all 83 books,
   brotli-compressed into the page itself and decompressed in your browser. It
   carries full paragraph and poetry structure, so it is the *first* choice for
   WEB rather than a last resort, and it means the plan works with no network at
   all.

   Chrome is the exception: it has no brotli in `DecompressionStream` (Firefox
   147+ and Safari 18.4+ do). There the copy is skipped and the text comes from
   the network instead, so reading works but offline reading does not, and a
   few books of the wider canon have no source left.

## Footnotes

Translator notes and cross-references appear as small lettered markers in the
text. Click one and it opens in a popover beside the marker; click anywhere
else, or press Escape, to dismiss it. In browsers without CSS anchor
positioning the note opens centred instead. Coverage depends on the translation: the World English Bible and
the api.bible editions carry them throughout, and of the bolls-served
translations the ESV, NKJV, NLT and CSB have them while the NIV has none.

## Privacy

There is no backend and no analytics. Your seed, settings and progress live in
your browser's `localStorage` and go nowhere else. The current chapter is cached
there too, and older ones are dropped as the plan moves on. The only outbound requests
are for passage text, and even those stop if you read the WEB translation.

## Development

One file, `index.html`, no build step and no dependencies. Open it and it runs.

| Script | Purpose |
|---|---|
| `build-embedded.py` | Rebuild the embedded WEB text from the USFX source |
| `check-bolls-books.py` | Check the bolls book numbers against the live provider |
| `set-api-key.py` | Write the api.bible key from `.api-key` into the page |

See `CLAUDE.md` for architecture notes and the reasoning behind the parts that
look arbitrary.

## Text credits

World English Bible, public domain, via [seven1m/open-bibles](https://github.com/seven1m/open-bibles).
Other translations are fetched live from their respective providers and remain
the property of their publishers.
