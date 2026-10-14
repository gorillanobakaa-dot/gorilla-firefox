<!-- Version: 1.1.0 · updated 26-08-26-11-46 -->
# The call that rang forever: what we found, in plain words

**Dates:** 2026-08-25 evening and 2026-08-26 morning. **Sequel to:** the
WebCodecs call-path story (WEBCODECS-CALL-PATH.LAYMAN.md).
**Status: TWO causes found, both closed. The connection problem is FIXED by
one setting, proven by a live call. The silence problem is CONVICTED with the
guilty line of our own code identified; its three-line fix ships with the
next rebuild.**

## The complaint

A WhatsApp video call from this browser did three things, every time: it rang
forever and never connected, the little box that should show your own camera
stayed black, and the red hang-up button did nothing when pressed. The person
at the other end answered, heard nothing, was heard by nothing, and after
about three minutes the call hung itself up.

## What happens when you call someone on WhatsApp

Your browser does not talk to the other person's phone directly. Both of you
connect to a Meta computer in the middle, a relay, and it passes the call
between you. Getting connected is like getting into a building: find the
door, shake hands with security, then start passing messages.

## What we measured, step by step

- **The doorbell works.** The other phone rang, the person answered. That
  whole part is fine.
- **Your browser found Meta's relay and knocked.** The relay answered the
  knock. Fine.
- **The security handshake, where both sides agree on the encryption,
  completed successfully.** Seven times, actually, because WhatsApp kept
  retrying.
- **Then your browser started sending the actual "let's talk" messages
  through that freshly opened secure tunnel. It sent them 223 times. The
  relay never answered a single one.** Not "no", not an error. Silence.
  After three minutes of shouting into a connected line, WhatsApp gave up
  and hung up on its own, which is exactly what the other person saw.

So the line was connected and the words were being thrown away. Why would a
machine shake your hand and then bin everything you say?

## The cause, found and proven

Encryption comes in versions, like editions of a dictionary. This Firefox
uses the newest edition, 1.3. Chrome, on the day a call actually worked from
this same laptop, used the older edition, 1.2. The handshake part of both
editions looks the same on the wire, so that succeeds either way. But the
envelopes the actual messages travel in changed shape in the new edition.
Meta's relay only knows the old envelope shape: it opens the door, shakes
your hand, and then throws away every letter you send, because it does not
recognise them as letters.

We added one browser setting that says "use the old envelope, edition 1.2,
the same one Chrome used when the call worked". One line, easily removed,
affects nothing else.

**The proof, next morning:** with that one setting, the same call attempt
opened four message channels and traffic flowed in BOTH directions,
measured live while the call was up, roughly ten messages a second coming
in and a steady stream going out. The blackhole is gone. One setting,
confirmed by a live call.

## What about the three symptoms?

They are all one symptom. WhatsApp checks its equipment before it commits.
When a layer keeps failing, the app never gets far enough to switch the
camera on (black box), never establishes a line (endless ringing), and its
own control code ends up in a confused state where the red button's
instructions are no longer listened to (dead button). Fix the failing layer
and these go with it.

## Things we suspected first, and what came of them

- **"The browser can speak but cannot listen."** We found early on that the
  part of the browser that decompresses incoming call audio (a format
  called Opus) was genuinely removed during this project's slimming work.
  That hole is real and stays written down, but it turned out NOT to be the
  killer: recordings of a full answered call show WhatsApp never even asks
  the browser to decompress call audio. It brings its own decompressor,
  built into the web page itself. The hole matters for other things, not
  for calls.
- **"WhatsApp demands a video format we refuse (VP8)."** That was true two
  weeks ago and it is not true any more. Today's WhatsApp tested our browser
  with H.264, the one format this browser is built to be excellent at, and
  our browser passed the whole test: it compressed a frame, decompressed it
  back, perfect result. The app has changed under us, in our favour.
- **"The building's internet is blocking things."** We tested the exact
  Meta relay computers from this same laptop, on this same connection,
  including sixty knocks at once in three rounds. Every single knock was
  answered. The network is innocent.

## The second cause: the browser lies about the speed of its sound engine

With the connection fixed, a call was measured actually moving picture both
ways, fifteen megabytes of it, while both ends stayed completely deaf. The
sound was never being produced by either side. Why?

A web page that wants to process sound asks the browser for a sound engine,
and it can ask for one that runs at a specific speed. WhatsApp asks for a
16,000-samples-per-second engine, because that is the speed its own
voice-compression machinery is built for. We watched it ask, live, during a
real call: the request is in the recording.

During this project's August audio work, a line of our own code was added
that forces EVERY sound engine to 48,000, the native speed of this laptop's
sound chip, no matter what the page asked for. And it does this silently:
no error, no warning. The page asks for 16,000, receives an engine labelled
48,000, and is simply expected not to notice.

WhatsApp notices. Its voice machinery checks what it was given, finds the
wrong speed, and shuts the sound side down entirely, both directions, while
the picture side (which never touches the sound engine) carries on. That is
the silent call, exactly as observed, and it also explains why Chrome works:
no other browser rewrites what a page asked for.

The honest rule a browser must follow is: give the page what it asked for,
or refuse openly with an error. Never lie. The fix is three lines: honor an
explicit request, and steer only the pages that expressed no preference to
the chip's native speed. It requires rebuilding the browser.

## Where it stands

The connection layer is fixed and stays fixed (the setting lives in the
browser profile, with a comment explaining why). The silence has a convicted
cause with a three-line fix waiting on a rebuild. The rebuild recipe on
GitHub was itself found stale and has a repair ready, so the path is: push
the repair, rebuild with the sample-rate fix, call again and finally hear
each other.
