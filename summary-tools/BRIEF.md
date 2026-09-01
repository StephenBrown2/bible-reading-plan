# Brief: Bible chapter summaries, three tones

Handed to every agent writing summaries. Run all commands from the repo root.

You are writing summaries for a daily Bible reading plan at
`/home/stephen/Projects/bible-reading-plan`. Run every command from that
directory.

Each entry summarises **one day's reading**, which is usually a whole chapter
but sometimes half of one, because the plan splits long chapters across days.
Write one summary per day, never per chapter.

## Length, before anything else

**45 to 90 words per summary. The checker fails anything over 140.**

This is the single most common source of rework on this project, so it is here
rather than buried in the rules below, and it applies to all three tones
equally. One earlier run turned in 200-word plain summaries for oracle
chapters, and a hundred of them had to be trimmed afterwards by hand.

**Favour a short highlight over a long drawn-out observation.** A day is one
chapter or half of one. If a summary is running past 90 words you are indexing
the chapter verse by verse rather than summarising it. Name who is involved,
the central image or event, and the outcome, then stop. A dense prophetic,
legal or genealogical chapter can honestly be three sentences.

No tone is required to be shorter than the others, and a given day may come out
longest in any of the three. What matters is that none of them sprawls: pick
the detail that carries the day and cut the rest.

Check your own length as you write. Rewriting a batch after the checker rejects
it costs far more than counting words in the first place.

## What you were assigned

Book IDs, given in your task prompt. The genre table in `../SUMMARIES-HANDOFF.md` maps every ID to its real name. Some are deuterocanonical or wider-canon books (Tobit, Sirach,
2 Esdras, Bel and the Dragon and so on); treat them exactly like the rest.

## Your genre

Your assignment is one genre on purpose. Read the note for yours before you
start; it is what keeps forty summaries from sounding like one summary repeated,
and keeps your voice matching the writers handling comparable books.

- **Torah narrative** (Exodus, Numbers, Deuteronomy). Story interrupted by long
  legal and construction blocks. Do not let the law sections blur; each has one
  oddity worth naming. Deuteronomy is one long speech retelling the other two,
  so anchor each day to what is actually new in it.
- **History** (Judges, Samuel, Kings). Character-driven, and the arcs run across
  chapters, so keep the thread visible: Saul's decline, Absalom's revolt, the
  slow collapse of both kingdoms. The repeated verdict formula on each king is
  itself the joke; use it without repeating your own phrasing.
- **Chronicler and post-exile** (Chronicles, Ezra, Nehemiah, Greek Esther,
  1 Esdras). Genealogies, temple logistics, official correspondence, name lists.
  This is the highest sameness risk in the whole project. Every list has one live
  detail in it. Find it.
- **Psalms.** Mood and argument, not plot. Say what the psalm is doing:
  complaining, gloating, panicking, repenting, cursing its enemies in detail.
  Short psalms get short summaries. Splits are poem splits, so no continuation
  lines: declare them in your `poems.txt`.
- **Wisdom** (Job, Proverbs, Ecclesiastes, Song, Wisdom, Sirach). Job is a
  cycle of speeches where the friends keep saying the same thing in different
  words, and being funny about that is fair. Proverbs and Sirach are aphorism
  collections; summarise the drift and the standout lines rather than listing.
  Song of Solomon is erotic poetry and should be handled with a light touch, not
  a smirk.
- **Major prophets** (Isaiah, Jeremiah, Ezekiel, Lamentations, Daniel, Baruch).
  Mostly oracle poetry: judgment, then comfort, on repeat. Name who is being
  addressed and what the image is, because the images are extraordinary and
  specific. Most splits here are poem splits. Lamentations is unrelieved grief;
  no jokes at all.
- **Minor prophets.** Same register, much shorter, so each book has room to keep
  its own personality. Jonah is a comedy and knows it. Habakkuk is an argument
  with God. Malachi is a series of "you say X, but" exchanges.
- **Maccabees and apocalyptic** (1-4 Maccabees, 2 Esdras). Battle chronicle and
  visionary material. 2 and 4 Maccabees include extended torture-martyrdom
  scenes: report those plainly and briefly, never for laughs.
- **Gospels and Acts.** Episodic, so the risk is a flat list of miracles. Give
  each day a shape. The passion narratives are not a place for jokes.
- **Epistles and Revelation.** Argument and mood rather than story, so
  summarise the argument. Say what Paul is annoyed about, what he is arguing
  against, where he changes the subject. Revelation is a sequence of images;
  describe them and let their strangeness do the work.

## Step 1: find out what is left to do

**Always run this first, even on a book you think is untouched.** A previous
agent may have been interrupted part way through your assignment, and its work
is on disk.

```sh
./summary-tools/summaries.py remaining GEN
```

It prints, per tone, the days still to write. Those references are your work
list. Write only those, in the order given. If it reports 0 to write for both
tones, your assignment is already finished; say so and stop.

Those references are the only valid ones. Copy them character for character
rather than constructing them yourself; anything else fails the build.

## Step 2: read the text

```sh
./summary-tools/summaries.py dump GEN
```

Dumps every day of that book, already split at the boundaries, with verse
numbers in brackets. Restrict to a range of chapters with `./summary-tools/summaries.py dump GEN:1-12`
for a book too big to read at once. Read all of it. Do not summarise from
memory: the wording, the names and the order of events have to match this text,
and several of these books are ones you will not know well.

Read in chunks that match how you will write: pull ten days of text, write those
ten days, save them, then pull the next ten. Never read a whole book before
writing any of it.

Your assignment is a whole genre and may run to a couple of hundred days across
several books. Work through it **one book at a time**, finishing and saving each
before you start the next, so the run always has a clean stopping point.

## Step 3: write three summaries per day

Three tones, all covering the same facts. Write **all three** for every day, in
this order. Same events, same names, same numbers; only the voice changes.

### Plain

Cliff's notes. What happens, in the order it happens, with no jokes and no
attitude at all. This is the one a reader who missed a day reads to find out
what they missed, so it carries the most weight of the three. Being dull is
allowed. Being wrong is not. No wry framing, no asides, no editorial.

"No jokes" is not licence to index the chapter verse by verse. An earlier run
turned in plain summaries of 200 words and more for oracle chapters, listing
every nation in turn, while its dry and cheeky came in at 90. Plain gets the
same 45 to 90 band as the others, and the same preference for a short highlight
over a drawn-out observation: name who is involved, the central image or event,
and the outcome, then stop. A dense prophetic or legal chapter can honestly be
three sentences. Dull is fine. Exhaustive is not.

> The serpent tells the woman that eating from the forbidden tree will not kill
> her but make her like God, knowing good and evil. She eats and gives some to
> her husband. They realise they are naked and sew fig leaves together. God
> finds them hiding; the man blames the woman, the woman blames the serpent. God
> curses the serpent, tells the woman she will bear children in pain, and curses
> the ground for the man's sake. He clothes them in animal skins and drives them
> out of Eden, placing cherubim and a flaming sword to guard the tree of life.

> Unable to sleep, the king has the royal records read aloud and learns Mordecai
> was never rewarded for exposing the assassination plot. Haman arrives to
> request permission to hang Mordecai. Before he can, the king asks what should
> be done for a man he wishes to honour. Assuming himself the subject, Haman
> proposes royal robes, the king's horse and a herald. The king orders him to do
> all of it for Mordecai. Haman leads the horse through the city, then goes
> home, where his wife and advisers tell him he will fall before Mordecai.

### Dry

Deadpan, wry, literary. The joke is in the framing and the timing, not in the
vocabulary. It notices what the text is doing.

> A talking snake opens with "did God really say", which is how every bad idea
> starts, and works the fine print until the fruit looks nutritious, attractive
> and educational all at once. They eat, discover they are naked, and invent
> clothing out of shrubbery. God comes walking in the cool of the day and asks
> where they are, which is not a geography question. The man blames the woman
> and, in the same sentence, God for supplying her. The woman blames the snake.
> The snake wisely says nothing.

> Sarah dies at a hundred and twenty-seven, and Abraham, who owns none of the
> land he was promised, has to buy a grave in it. What follows is a masterclass
> in negotiation conducted entirely in compliments. The first square foot of the
> promised land the family actually owns is a grave.

### Cheeky

Blunt and modern. Short sentences, slang, the joke said out loud rather than
implied. Louder, not stupider: it still has to be accurate.

> Snake slides up with "sooo, did God REALLY say," which is how every terrible
> decision begins. The fruit looks tasty, looks pretty, and allegedly makes you
> smart. They eat it, instantly notice they're naked, and staple some leaves
> together. Guy blames the woman, and in the same breath blames God for making
> her. Woman blames the snake. Snake says nothing, because the snake is not
> stupid.

> King can't sleep, so he has the royal records read to him as a bedtime story
> and finds out he never thanked Mordecai for saving his life. Haman turns up
> early to ask permission to hang that exact guy, and instead gets asked what
> should be done for a man the king really likes.

## Rules

1. **Cover the major elements** of that day's text. Brief, but not at the cost
   of leaving out something that actually happens. 45 to 90 words, per the
   length section at the top, and never over 140. Some days genuinely need
   less; a genealogy or a list of building measurements can be two sentences
   that are honest about being a list.
2. **Do not invent plot.** Every event, name and number has to be in the text.
   Exaggerating tone is the joke. Making things up is a bug.
3. **Split chapters.** If your book has a chapter split across two or more days,
   every part except the last ends on episodic TV continuation text, in the
   voice of the tone: `Next time on Genesis: somebody looks back.` Two
   exceptions. A split inside a **poem** gets no continuation line, because
   poetry has no cliffhanger; decide narrative vs poem by looking at the
   passage. And the **plain** tone never gets one in any book: the teaser is a
   joke device, and plain has no jokes. Write plain's last sentence as ordinary
   summary and stop.
4. **Poetry and law and prophecy** still get summarised. A psalm gets the gist
   of the psalm and its mood. A chapter of sacrificial regulations gets to be
   funny about being a chapter of sacrificial regulations. Do not skip a day
   because it is boring; the boring ones are where this feature earns its keep.
5. **Irreverent, not cruel.** Punch at pompous kings, bad decisions and the
   narrator's deadpan. Do not mock anyone's faith, and do not make jokes at the
   expense of victims. Where the text is genuinely grim (Judges 19, Lamentations,
   the massacres), drop the comedy and be plain and dark instead. A flat honest
   sentence is always better than a joke that lands badly.
6. **No em dashes or en dashes anywhere.** Use commas, periods, or a colon.
7. **Straight quotes and apostrophes only.** No curly quotes.
8. **One line per summary. No tab characters and no newlines inside the text.**
9. Do not start every summary the same way. Vary the openings.

## Step 4: save every ten days, as you go

**Do not hold a whole book in your head and write the files at the end.** Agents
have been killed by session limits at exactly that moment and lost forty days of
finished work. Save in small batches so an interruption costs you ten days at
most, and so the next agent can pick the book up mid-stream.

After each chunk of about ten days, save all three tones:

```sh
./summary-tools/summaries.py write plain <<'EOF'
GEN 19:1-17 Two angels arrive in Sodom and Lot brings them into his house.
GEN 19:18-38 Lot asks to flee to Zoar instead of the mountains.
EOF

./summary-tools/summaries.py write dry <<'EOF'
GEN 19:1-17 Two angels reach Sodom and Lot insists they stay with him.
GEN 19:18-38 Told to run for the mountains, Lot haggles.
EOF

./summary-tools/summaries.py write cheeky <<'EOF'
GEN 19:1-17 Two angels hit Sodom and Lot insists they crash at his place.
GEN 19:18-38 Told to run for the mountains, Lot haggles.
EOF
```

The reference and the summary are separated by an ordinary space, so a heredoc
cannot break anything. The tool routes each line to the right per-book file by
its reference, so a batch covering several books needs nothing special.

It refuses the entire batch if any line names a reference that is not a real day
boundary, is under twenty words, or contains an em dash or a curly quote. Fix
what it reports and rerun; nothing was written, so rerunning is safe. Days
already saved are skipped rather than duplicated, so rerunning an identical
batch is also safe.

Then keep going with the next chunk. Never rewrite a file by hand and never
overwrite one; appending through this tool is the only way to save.

## Step 5: check your own work before you finish

```sh
./summary-tools/summaries.py check GEN
```

It verifies both files exist, that every boundary is covered exactly once, that
no reference is invented, and that the formatting rules hold. It also checks the
split-chapter rule: in the dry and cheeky tones, a non-final part of a split
chapter must end on a "Next time on ..." line, unless the split falls inside a
poem, which you declare by piping the reference to
`./summary-tools/summaries.py poems`. The plain tone is exempt and is not
checked for it.

**Fix everything it reports and rerun until it passes.** Do not report success
until it does. If you are running out of room, it is far better to stop with
thirty days saved and checked than to push on and lose them.

Report back: the book IDs you completed, the number of days each, any
`poems.txt` declarations you made and why, and anything you were unsure about.

If you stopped early, say plainly how far you got. Your saved days are on disk
and the next agent will resume from them, so an honest partial report costs
nothing and a false "complete" costs a re-run.
