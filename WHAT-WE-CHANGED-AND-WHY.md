# 🦍 What we changed in Firefox, and why

**441 patches. 644 files. 434 files deleted outright. 16 topic groups.**

This is the whole rationale, written twice: once in plain language, once for
people who want the file names and the numbers. Read whichever half you like —
they cover the same ground and neither is a summary of the other.

Every section also states the **cost**, because every one of these has one.

---

## The one-paragraph version

Firefox is built for a machine that does not exist in most of the world: fast,
new, on unmetered broadband, owned by someone who does not mind being measured.
This patch set rebuilds it for the opposite machine — a 2012 laptop, 2 GB of
RAM, data sold by the megabyte, and an owner who would rather not be counted.
It does that in four ways: **wake up hardware Firefox refuses to use**, **stop
the browser measuring itself**, **stop it phoning home**, and **seal it shut**
so nothing can be added to it later.

The reference target throughout is a **Sony VAIO SVE14A3AJ** — Intel
i7-3632QM, HD Graphics 4000, 16 GB, 2012. Where a number appears below, that is
the machine it was measured on.

---

# Part 1 — Make the old hardware work

## 01.MEDIA — 20 patches

**Plain language.** Your laptop has a dedicated video chip that can play
H.264 video without waking the main processor. Firefox refuses to use it,
because Mozilla's compatibility list says a 2012 chip is too old to trust. So
video plays on the CPU instead: hot, loud, and it drains the battery. These
patches tell Firefox to use the chip, and go further — they make the browser
*refuse* to play video any way other than in hardware. If the chip cannot do
it, you get nothing rather than a melted laptop.

**Developer.** VA-API decode forced on for the i965 driver; `PDMFactory` gates
every decoder on `DecodeSupport::HardwareDecode`; `media.gorilla.hardware_only_mode`
introduced as the policy switch. `DecoderTraits` returns `CANPLAY_NO` for
VP9/AV1/WebM so sites negotiate H.264 MP4 rather than attempting an MSE
SourceBuffer that would fall back to software. `AudioStream` and the buffer
sizing are tuned alongside.

**Cost.** Real and specific: **YouTube caps at 1080p**, because 1440p and 4K
are only served as VP9 and AV1, which this chip cannot decode. That is the
trade — cool and quiet at 1080p, versus hot and stuttering at 4K.

> **On Windows this group is disabled.** VA-API is a Linux interface. Windows
> uses Media Foundation, and the codec policy is enforced by preferences alone
> rather than by the C++ gate. See `windows/README.md`.

## 02.GPU — 4 patches

**Plain language.** The same argument, one layer down. Firefox keeps a
blocklist of graphics chips it will not accelerate. The HD 4000 is on it. With
acceleration refused, the CPU draws every web page by hand. These patches take
the chip off the list.

**Developer.** `GfxInfoBase`/`GfxDriverInfo`/`gfxPlatform` overrides so
WebRender rasterisation and DMABuf are permitted on IVB GT2 rather than
blocklisted. Companion to 01.MEDIA — the two are documented as a required pair.

**Cost.** Mozilla blocklists hardware for reasons, usually driver bugs. You are
overriding a judgement made by people with a crash-report database. On this
specific chip and driver it was tested and holds; on a different old GPU it
might not.

## 03.NETWORKING — 4 patches

**Plain language.** Two unrelated things. It rips the measurement code out of
the network layer, and it retunes the network buffers to match the custom Linux
kernel this was built for — bigger buffers for video over UDP, twice as many
simultaneous DNS lookups, and connections held open more aggressively so they
do not have to be re-established.

**Developer.** Glean instrumentation removed from `nsSocketTransport2`,
`nsHttpTransaction`, `HttpConnectionUDP`. `nsHostResolver` concurrency 8 → 16.
Socket buffers and TCP keepalive sized against a BBR-tuned kernel.

**Cost.** The tuning assumes that kernel. On a stock kernel these numbers are
merely different, not better.

## 04.PERFORMANCE — 4 patches

**Plain language.** Mostly not about performance at all — it is what makes the
browser *compile* on a modern compiler. One genuine tuning change adjusts how
often the browser tidies its own memory, pitched for a slow chip.

**Developer.** SFINAE `IsComplete<T>` guards in `mfbt/Maybe.h` to stop
incomplete-type trait evaluation under Clang-21 (ERR-BUILD-008); telemetry
removed from `Stencil.cpp`'s JS compile cache; `kICC*` cycle-collector cadence
pinned for Ivy Bridge in `CCGCScheduler.cpp`. The behavioural GC policy is
pref-driven and lives in 05.PREFS.

**Cost.** The CC cadence is tuned for one CPU. On a fast machine it is
suboptimal in the other direction.

## 06.QUOTA — 1 patch

**Plain language.** Removes a storage-quota prompt and a shutdown routine that
were costing time without buying anything on a single-user machine.

**Developer.** `dom/quota/ActorsParent.cpp`, 42 lines. Whitelist predicate is
`QuotaManager::IsOriginInternal`; an 8-line shutdown block deleted; a
`NIGHTLY_BUILD` → `EARLY_BETA_OR_EARLIER` gate swap that is a **no-op on this
milestone** and is documented as such.

**Cost.** Minimal. The group's own log is careful to say the gate swap changes
nothing here — an unusually honest bit of documentation.

## 11.FONT.SYSTEM — 5 patches

**Plain language.** Ships eight fonts inside the browser so text renders
correctly in many languages without hunting the system. It *also* contains a
switch to skip scanning your system fonts entirely at startup — which would be
much faster — but **that switch is deliberately taped over**, because nobody has
proved the eight bundled fonts cover everything. Turn it on blind and some
characters vanish.

**Developer.** `gfx.bundled_fonts.skip_system_scan`, hard-coded default `false`
at five call sites across the fontconfig, DWrite and FT2 backends; eight fonts
bundled via `FINAL_TARGET_FILES.fonts`. The pref is set nowhere and is not
registered, so it does not even appear in `about:config`.

**Cost, and an honest caveat from their own audit.** The folder claims a
startup improvement from ~40 s to a few seconds. **That was never measured** —
the log says so plainly and tells you not to trust the number. Also: the
Microsoft fonts are legal to *use* but not to *redistribute*. On Windows they
are OS-provided, which is why this group is disabled there.

---

# Part 2 — Stop it measuring you

## 13.TELEMETRY.KILL — 22 patches

**Plain language.** This is the one where privacy and speed turned out to be
the same fix. Firefox constantly measures itself — memory, timings, how you use
it — and that measurement is not free. On this laptop, during video playback,
**about one unit in every eight of the main process's effort was spent watching
itself instead of showing you the video.** Turning it off took that from ~13%
to under half a percent.

**Developer.** Layered source-level short-circuits, deliberately **not**
excision:

| what | where | CPU before → after |
|---|---|---|
| `MemoryTelemetry::GatherReports()` early-return, skipping the 60 s `/proc/self/smaps` scan | `MemoryTelemetry.cpp:239` | 8.9% → 0.02% |
| `FOG::InitializeFOG()` no-ops before `fog_init` — the `glean.dispatche` thread never spawns | `FOG.cpp:153` | 3.5% → 0.00% |
| compile-time `GORILLA_TELEMETRY_OFF` dead-code-eliminates the hot recording paths across 17 metric files | vendored `glean-core/lib.rs:115` | 0.84% → 0.39% |
| `dispatcher::global::launch()` drops tasks as an egress backstop | `global.rs:55` | — |

Measured with `perf`, 2026-07-16: **13.2% → 0.39%.**

**Why short-circuit and not delete.** They tried deleting it. It produced
`NS_ERROR_FACTORY_NOT_REGISTERED` and required 157 shim headers. Every symbol,
factory and `moz.build` reference is therefore preserved and simply made inert.

**Cost, and their own honest caveat.** The shipped browser disables this in
**17** metric files; the patch files in the folder record only **4**. Rebuilding
from that folder alone gives a weaker result. Their log describes it as "a house
wired correctly, but with two rooms missing from the blueprint." That is a
documentation debt, not a defect in the binary.

## 12.MOZAMBIQUE.DRILL — 2 patches

**Plain language.** Firefox has two background radios that wake every six hours
to ask Mozilla for new instructions — experiments to enrol you in, features to
switch on remotely. This does not rip them out. It sets their alarm clock to
**sixty years**.

Why not remove them? Because removing them crashes about 145 other parts of the
browser at startup. So the machinery stays physically in place, and simply never
wakes up.

**Developer.** `app.normandy.run_interval_seconds` in-code fallback
`21600` → `1893456000` (60 years, under the signed 32-bit ceiling) at
`RecipeRunner.sys.mjs:289` and `RemoteSettingsExperimentLoader.sys.mjs:256`.
Both still register with `nsIUpdateTimerManager`, so every dependent object
shape survives and boot does not cascade. Three-layer defence: the source
default, a locked pref in 05.PREFS (`enabled=false`, `api_url=""`), and
`policies.json` re-locking all three at runtime.

**Cost.** None functionally. The 145-dependency figure comes from the project's
own notes and was not reproduced in the audit — flagged in their log.

## 14.EGRESS.LOCKDOWN — the doctrine, not patches

**Plain language.** Not code — a written rule about which doors stay open. Its
three laws:

1. **Close** pure surveillance doors. They cost nothing to lose.
2. **Preserve** the five things that make a browser usable in the real world:
   video DRM, security keys, video calls, certificate checking, and the sandbox.
   *A privacy build that breaks Netflix, hotel wifi or your bank's login is not
   a privacy build — it is an abandoned one.*
3. **Document every door left open**, so a later over-zealous pass does not
   "harden" certificate revocation into oblivion thinking it found a leak.

**Developer.** Column A closes discovery/TAAR, Shield, Nimbus loader,
crash-report probes, ping-centre, activity-stream telemetry, coverage ping and
attribution reporting. The five preserved pillars are individually measured and
recorded. The kept-door ledger names each remaining connection with a reason.

**Cost.** The build is honest that it is *not* silent. It still contacts
Mozilla for the malicious add-on blocklist and its signature check. The claim is
**"no surveillance"**, never "contacts nothing."

## 05.PREFS + 10.OVERRIDES — 277 settings

**Plain language.** The factory settings. 277 preferences changed from
Mozilla's defaults, **85 of them locked** so that nothing — not a policy, not an
add-on, not a website — can switch them back.

**Developer.** `browser/app/profile/firefox.js` and
`modules/libpref/init/all.js`, plus the build's own `mozconfig`. 202 prefs are
new, 75 override an upstream value, 17 upstream prefs are deleted outright.
10.OVERRIDES carries the profile-level `user.js` for runtime-only settings.

**Cost, found on Windows.** Ten of these named Linux-only subsystems and were
firing on Windows anyway. Four of them inverted a deliberate upstream Windows
default and **disabled hardware video decode**. Fixed in group 17 with
`#ifndef XP_WIN` guards. A cross-platform pref file is where one platform's
assumptions hide, because data does not fail to compile.

---

# Part 3 — Seal it shut

## 07.TOOLKIT — 16 patches, "the API Lobotomy"

**Plain language.** **You cannot install add-ons. At all.** Not uBlock Origin,
not a password manager, not a theme. This is the most consequential decision in
the entire project, and its reasoning is one sentence:

> *A browser you can't extend is a browser strangers can't quietly extend
> either.*

An extension usually asks for "access your data for all websites" — every page,
every form, your banking session. The concern is not what *you* install; it is
malware, bundled installers, a workplace, or someone with five minutes at your
unlocked keyboard. Remove the install path and none of them can use it. Neither
can you. That indiscriminacy is the point.

The same group also disables translation and forces the theme. Its own notes
call the result a **"sealed appliance"** — closer to a kitchen appliance than a
program.

**Developer.** 14 rejection points across three files:
`XPIInstall.sys.mjs` (9), `AddonManager.sys.mjs` (4),
`LightweightThemeManager.sys.mjs` (1). Every route closed: AMO, web install,
drag-and-drop, Install-From-File, themes. Also `ExperimentAPI.sys.mjs` returns
empty mocks so dependent code does not throw, and `TranslationsParent.sys.mjs`
blocks model downloads.

**Cost — the largest in the project.** No ad blocker, no password manager, no
themes, no translation. Protection is built in instead (tracking, cryptominer
and fingerprinter blocking, cookie-banner dismissal, HTTPS-only) — but built-in
protection is **less thorough than uBlock Origin**, and pretending otherwise
would be dishonest.

**And a real defect in how it fails.** `installAddonFromWebpage()` calls
`install.cancel()` rather than throwing, so the add-ons site is left waiting
forever and its button simply spins. **The browser never tells you it refused.**
That silence is indefensible even if the policy is defensible.
See **[windows/THE-SEALED-APPLIANCE.md](windows/THE-SEALED-APPLIANCE.md)**.

## 09.REMOTE — 2 patches

**Plain language.** Firefox has two built-in hatches for driving it from
outside — the machinery browser-automation tools use. Both are welded shut, in
three places each.

**Developer.** Three-site dead-coding per channel (constructor default, setter
body, CLI-startup branch) in `Marionette.sys.mjs` and `RemoteAgent.sys.mjs`.
Environment variables, `--marionette` and `--remote-debugging-port` are all
inert. Two listening sockets gone.

**Worth recording:** an audit caught a change that had quietly swapped the
listen address from `127.0.0.1` (this computer only) to `0.0.0.0` (the whole
network). It was reverted on 2026-08-03. It never did harm — it sat behind a
door already welded shut — but it is exactly the kind of thing defence in depth
exists to survive.

**Cost.** No automation tooling works on this build. Deliberate.

---

# Part 4 — Make it Gorilla

## 08.Look — 235 patches, the biggest group

**Plain language.** How it looks and what it is called. Deep black with cyan
text and a pink active tab, a nebula wallpaper, and every visible "Firefox" or
"Mozilla" renamed to "Gorilla".

The one real engineering idea: **the theme is built to cost the graphics chip
almost nothing.** It uses only effects the chip handles by itself and switches
animations off, so a styled browser does not drain a 2012 battery.

**Developer.** `master-redirect.css` (315 lines) injected by a single `@import`
in `browser-shared.css:36`. Palette `#000000` / `#00FFFF` / `#FFC0CB`.
Transitions neutralised to 0.01 ms. Enforces the project's CSS invariants:
opacity and transform only, `outline` never `border`, no XUL scale transforms,
`will-change: auto` globally, `contain: layout style`. 166 of 235 patches carry
branding strings (2,535 branded lines); 31 are blank-line tidy-ups under the MPL
header, inspected and confirmed intentional.

**Cost.** Two of the three Windows UI disasters came from here — see Part 5.
A theme keyed to one Firefox version's colour tokens does not survive a version
bump quietly.

---

# Part 5 — Make it work on Windows

## 16.SNAPSHOT.DELTA — 111 patches, 434 deleted files

**Plain language.** Keeping up with upstream, plus the real AI removal. The 434
deleted files are the bulk of it: the entire vendored llama.cpp tree, the AI
Window, the genai components, the ML urlbar providers.

**Developer.** Auto-generated completeness sweep, platform-neutral. Excludes
`activity-stream.bundle.js` — a webpack build artefact whose own first line says
it is auto-generated; patching it broke 9 hunks on every version bump, so stage
35 regenerates it from the patched sources instead.

## 17.WINDOWS.FIXES — 11 patches, 4 new files, 35 artwork files

**Plain language.** The port. Every one of these was found by **building and
running the browser**, not by reading the code — none of them failed at build
time.

The AI removal deleted definitions and left the references behind. JavaScript
has no link step, so each one stayed silent until the exact line ran:

| what was left behind | what you saw |
|---|---|
| a bare global with no definition | **every new tab opened blank** |
| a lazy import with no getter | **the address bar accepted text and Enter did nothing** |
| a trailing comma in a selector list | **toolbar buttons dead** |
| one missing `.ftl` file | **every menu label in the window empty** |

That last one is worth pausing on. **One** unresolvable localisation resource
stops the *entire* window's text. Four rounds of CSS work were spent on it
before the cause was found.

Plus: the Windows icons were Mozilla's blue-globe placeholders (Linux never
opens a `.ico`); the installer artwork was eight 1×1 pixel stubs, three of them
PNGs wearing a `.bmp` name; and the ten Linux-only preferences described above.

**Developer.** `AIWindowStub.sys.mjs` (inert stand-in, chosen over editing
upstream callers), empty `genai.ftl` + its `jar.mn` mapping, `UrlbarShared`
getters restored, `closest()` selector lists repaired, `#ifndef XP_WIN` guards,
a 10-frame icon ladder to 256×256, and a branded 7-Zip SFX stub. Every patch
verified by applying it to a pristine upstream checkout and comparing
byte-for-byte.

---

# What this cost, altogether

An honest ledger. Nothing here is free:

| you lose | because |
|---|---|
| **All extensions** — uBlock Origin, password managers, themes | 07.TOOLKIT, deliberately |
| **YouTube above 1080p** | 01.MEDIA — the chip cannot decode VP9/AV1 |
| **Built-in translation** | 07.TOOLKIT |
| **Browser automation** | 09.REMOTE |
| **Automatic updates** | you update it, it does not update itself |
| **Recommendations, Pocket, sponsored tiles** | no loss, but they are gone |
| **Mozilla's hardware judgement** | 02.GPU overrides a blocklist that exists for reasons |

And what the project's own audits flag as unfinished, quoted rather than
softened:

- **13.TELEMETRY**: the shipped browser disables more than the patch files
  record. Rebuilding from the folder alone gives a weaker result.
- **11.FONT**: the "40 seconds to a few" startup claim was never measured.
- **08.Look**: three P1 findings, inspected and judged intentional deletions.
- **12.MOZAMBIQUE**: the 145-dependency crash figure is documentary, not
  reproduced.

---

# The thread running through all of it

Every group above is the same trade made twice: **give up configurability, get
back speed and privacy.** Sometimes that is obviously right — nobody misses
telemetry that was eating 13% of a CPU. Sometimes it is genuinely arguable —
a browser that cannot run uBlock Origin, in the name of blocking ads.

The build cannot tell whether you are the person who would install malware by
accident or the person who would install uBlock Origin on purpose. **It assumed
the first.** Whether that assumption fits you is the one question this
documentation cannot answer for you.

Every group is rebuildable and every group is removable. That is what the patch
set is *for*.
