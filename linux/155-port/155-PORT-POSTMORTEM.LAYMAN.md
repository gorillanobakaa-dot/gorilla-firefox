<!-- Version: 1.0.0 · updated 26-08-27-12-44 -->
# What happened when we moved the browser from Firefox 154 to 155

Version: 1.0.0 · updated 26-08-27-13-00

This is the plain-English account. There is a matching developer version next to
it with the exact commands and code. Neither one is a summary of the other. They
are the same story told twice, for two different readers.

---

## What we were doing

Gorilla Unleashed is Firefox with about 430 changes made to it. Those changes
are stored as "patches": small files that each say "in this file, at this spot,
replace these lines with those lines".

Every few months Mozilla releases a new Firefox. To move our browser onto it, we
take the fresh Firefox source code and apply our 430 patches to it. That is the
"port". This time we moved from Firefox 154 to Firefox 155.

## The thing that went wrong, and it is not what anyone thought

When you apply 430 patches, some of them fail. Mozilla moved the code, so the
patch can no longer find the spot it was meant to change. The tool prints a list
of failures. Ours said **63 failed**.

A status document was then written saying 63 changes were missing from the
browser. That document was wrong, and the way it was wrong is the most useful
thing we learned all day.

**A failure report tells you what the TOOL managed to do. It does not tell you
what is in the browser.**

When a patch fails, a human goes in and makes the change by hand. Once they do,
the file matches neither the old version nor the patch's idea of the new
version. So the tool keeps reporting it as failed, forever, no matter how
completely the work was finished.

That one word, "failed", was hiding three completely different situations:

1. Nobody ever made this change. Real outstanding work.
2. Mozilla already does this thing now, so there is nothing to do.
3. Somebody already made the change by hand. Finished. Just mislabelled.

Counting properly: of the 63, **41 were already done by hand**, 13 were
pointless, 7 were genuinely outstanding, and 2 we chose to skip on purpose.

The document said 63 were missing. The real number was closer to 7. If the next
person had believed it, they would have spent a day redoing 41 finished jobs,
quite possibly damaging them in the process.

## The same mistake, four times in one day

This is the part worth remembering, because it kept happening in different
disguises and I made three of the four myself.

**Once:** reading the failure list as if it described the browser.

**Twice:** we found files with names like `GenAIChild.sys.mjs` sitting inside
the installed browser. Firefox's AI features, apparently still shipping. Alarming.

They were signposts pointing at a building that had been demolished. In computing
these are called symbolic links: a name that says "the real thing is over there".
The "over there" folder had been deleted months ago. Following any of them led
nowhere. There was no AI code. There were ten labels and no stock behind them.

Checking would have cost one extra character in the command. Two separate people
skipped it, on the same files, on the same day.

**Three times:** I announced that the text files feeding the browser's menus
were all correct. I had checked the source code folder. The browser actually
running on the machine had been built the night before, from an older copy. I
audited a thing and reported on a different thing.

**Four times:** twenty minutes ago I looked at the freshly built installer,
saw it was 800 bytes instead of 100 megabytes, and started writing up a fourth
disaster. The file was still being written when I looked. It finished at
102,576,532 bytes, exactly right.

Four variations on one habit: treating a convenient signal as proof, when the
real thing was sitting right there waiting to be checked.

## The menu with no words in it

The browser worked. Web pages loaded, video played, the address bar was fine.
But clicking the hamburger button (the three lines, top right) opened a menu
with **no text in it**. Empty rows where words should be.

Two theories were on the table. Theory one, from the status document: the text
is black on a black background. Theory two: the words are missing from the
translation files.

Rather than argue, we ran an experiment. Two minutes of work: force every menu
label to be **bright red on a yellow background**. Whatever happens next tells
you which theory is right.

The result: **yellow boxes with no red text in them.**

That kills both theories at once. Not a colour problem, because the colour was
forced and no text appeared. And there was one exception: the "100%" zoom
indicator did show up. That number is put there by the program itself, not by
the translation system.

So: text that the program writes directly, appears. Text that comes from the
translation system, does not. That is a precise, narrow answer, and two minutes
of experiment beat several hours of reading code that turned out to be
irrelevant.

## What was actually broken

Running the browser and recording its complaints (70 lines) gave us the answer
in about thirty seconds.

Every single error was the same shape: the browser asking the translation system
for a phrase and getting **nothing** back. Not the wrong phrase. Nothing.

And in the list of translation files the browser loads, there were three
belonging to the AI features we had removed. Those three were signposts to the
demolished building from earlier.

Meanwhile, a second and separate bug turned up in the same log, and it is a good
illustration of how a careless removal does damage far from where you cut.

Somebody had removed the AI machine-learning code from a file. But they cut it
out of the **middle of a sentence**, leaving the sentence's opening words in
front of their replacement and its last three words dangling behind it.

The result was not "a file with one thing removed". It was gibberish, and the
browser refused to read **the entire file**. Every other feature that depended
on it saw the file as simply not existing.

Nothing pointed at the guilty file. Nothing in the build complained. It looked
finished, and it had a neat comment on it explaining the removal. Only running
the browser and reading its complaints found it, in one line.

## What we fixed

- **The find bar** (the search box at the bottom, Ctrl+F). Not one of its 41
  styling rules had been carried over. Our own notes said the styling lived in
  that file. It did not. Fixed.
- **The add-ons page**, which had started showing Mozilla's advertising and
  recommended themes again. Removed.
- **Settings and private browsing pages**, back to the black and cyan look.
- **Search**, reduced back to one engine.
- **The AI text files** that should never have shipped. Gone, and verified gone
  from the actual installer rather than assumed.
- **The broken file** described above, rewritten properly and checked.
- **Ten dead signposts** cleared out of the installed browser, so nobody makes
  that mistake a third time.

## What we deliberately did NOT fix, and why

Three of the "missing" patches turned out not to be our changes at all. They
were the difference between two versions of files that Mozilla generates
automatically. One of them would have **deleted 173 lines** of legitimate new
Firefox code, and it contained not one of our customisations.

A patch that only removes things and adds nothing of ours is not a change we
made. It is an accident of how the patch was recorded. Applying it because it
was on a list would have caused real damage.

Recorded as skipped, with the reason, so the next person does not "fix" it.

## The lesson, in one line

**If a report's rows are about ATTEMPTS, it cannot tell you about the STATE of
things.** Run the thing, catch what it complains about, and read that before
believing any tidy-looking audit, including one you wrote yourself.

The neat document with line numbers and severity ratings was wrong about two
thirds of its headline number. The messy 70-line spew from actually running the
browser was right about everything. Looking careful and being correct are not
the same property, and the careful-looking one is more dangerous, because it
survives a spot-check.
