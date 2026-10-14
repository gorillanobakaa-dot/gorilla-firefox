<!-- Version: 1.0.0 · updated 26-08-27-13-44 -->
## 40. 2026-08-27 — 155 port: watermark re-tuned, and why the value was NOT lost

RETRIEVAL HEADER, deliberately in the vocabulary of the mistaken belief:
"the gorilla is too big on about:addons", "the icon position was lost in the
port", "we lost the watermark tuning again", "same bullshit every release".

**The tuning was NOT lost.** All four tuned watermark values survived the
154 -> 155 port intact and were verified present in the built tree:
about:addons `right calc(10% - 39px) bottom 50px / 650px`, about:telemetry and
about:studies `fixed center bottom 10px / 450px`, about:robots
`padding-inline-start: 420px`.

What changed is the page around it. Firefox 155 narrowed the `#content`
column, so an unchanged 650px occupied more of the visible page. Author chose
**450px** and confirmed on sight. 450px also matches telemetry and studies.

**Two things I got wrong, recorded so the pattern is visible:**
1. Changed the logo's intrinsic raster 800 -> 1200 on the strength of a STALE
   CODE COMMENT, without reading the doctrine. Then "corrected" it back to 800
   on an older lesson. The 2026-07-31 doctrine says 1200px. Final: 1200px.
2. Assumed the blur was a size problem. It was not. The shipped raster had
   never been Lanczos-downsampled from the canonical master at all: measured
   edge energy 6.62 versus 26.10 for a true downsample, roughly 4x softer.
   Every size check passes on a soft asset. PROVENANCE, not size.

**Now enforced instead of remembered** — `~/.agents/skills/browser-release-
pipeline/scripts/release_pipeline.py` carries these values as executable data:
  MARK-001  fails the build if any tuned watermark string goes missing
  ICON-002  fails if an injected raster is not a true downsample (edge energy)
  CSS-004   fails if an injected icon selector has no size clamp
            (this is the validator ERR-UI-004 asked for on 2026-07-10 and
             which was never built until today, seven weeks later)
  L10N-001  fails on any data-l10n-id that does not resolve. First run found
            12 blank AI rows across File menu, History menu, right-click menu,
            toolbar and app menu.
  PREF-001  fails if a proven runtime fix lives only in a profile's user.js
            instead of the build's firefox.js. Born from the WhatsApp DTLS cap,
            which was documented as "Fix (per-profile, one line, user.js)" and
            therefore shipped broken in every package.

Per §28's own note, the brain came up EMPTY on this value in 2026-07-31 and
again on 2026-08-27; author memory was the recovery tier both times. That is
the third recorded instance. The gates above exist so there is not a fourth.
