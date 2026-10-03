# Gorilla Unleashed — Firefox 154 patch set

> **This folder now holds the Firefox 157.0 set** (the Windows 157.0 build), not the 154 set
> described below. Baseline, apply order and the replay proof: [`BASELINE.txt`](BASELINE.txt). The
> text below is the original 154 guide, kept for its history; `apply.sh` does not yet write
> `REPLACE_FILES/` or remove the files in `DELETED_FILES.manifest.txt`.

**🧸 In plain words:** this folder is *every change* that turns a normal Firefox 154 into
Gorilla Unleashed — the hardware-video tuning, the low-RAM prefs, the theme, and the removal of
telemetry / AI / ads — stored as small text "patch" files. Point them at a clean copy of Firefox
154's source code and they rewrite it into our browser. You do **not** need to understand C++ to
use this: run one script.

**💻 In technical terms:** a topic-organised set of unified diffs (`patch -p1`) against a pinned
Firefox 154.0a1 baseline, plus brand-new files under `NEW_FILES/`. Verified: **all 307 patches
apply cleanly** onto the declared vanilla baseline (checked 2026-08-04). Applying them reproduces
the exact source tree behind the shipped `gorilla-unleashed_154.0a1-1_amd64.deb`.

---

## The one thing that matters most: the baseline

Firefox "154" is a *moving target* — mozilla-central changes daily. These patches were cut against
**one specific revision**. Apply them to a different 154 and the locale/theme patches may fuzz or
fail. The exact baseline is recorded in [`BASELINE.txt`](BASELINE.txt). The from-scratch
reproducer (below) fetches that revision for you; if you clone manually, check out that revision
first.

---

## Fastest path — the big green button (from nothing)

```sh
# clones the pinned vanilla tree, applies everything, builds, and packages the .deb
gorilla-firefox-toolkit/diagnostics/recreate_success.sh
```

## If you already have a clean Firefox 154 tree

```sh
# 1. dry-run: does everything apply? (touches nothing)
./apply.sh --check /path/to/firefox-154

# 2. apply for real (SRC_TREE, and optionally your Firefox PROFILE dir for user.js)
./apply.sh /path/to/firefox-154 ~/.mozilla/firefox/<profile>

# 3. build (use the hardened wrapper — see below)
```

`apply.sh` applies every `NN.TOPIC/*.patch`, copies each `NEW_FILES/` tree into the source, and
(if you pass a profile dir) installs `10.OVERRIDES/NEW_FILES/user.js` into that profile.

## Building (the hardened wrapper — do not use bare `./mach build`)

```sh
gorilla-firefox-toolkit/build-tools/run_build_and_capture.sh
```
It sets `PYTHONUNBUFFERED=1` and `DISABLE_TELEMETRY=1` — both learned the hard way: mach can
deadlock on exit in its telemetry thread, and buffered output makes a hard error look like a
silent hang. The wrapper captures a full log + summary. See the `Silent_Build_Hang_*` lesson.

## Packaging a `.deb`

```sh
gorilla-firefox-toolkit/build-tools/build_deb.sh          # version auto-read from the built binary
```

---

## The rooms (one topic each)

| Room | What it changes |
|---|---|
| 01.MEDIA | hardware H.264 codec policy, VA-API, audio DSP |
| 02.GPU | zero-copy, compositor, blocklist overrides (GPU process stays OFF on Wayland) |
| 03.NETWORKING | connection tuning (co-designed with the custom BBR/FQ-CoDel kernel) |
| 04.PERFORMANCE | Clang-21 build-compat + Stencil telemetry gate |
| 05.PREFS | `all.js`, `firefox.js`, mozconfig — the pref surface |
| 06.QUOTA | storage-quota behaviour |
| 07.TOOLKIT | add-ons / urlbar / suggest |
| 08.Look | theme + branding + locales (the largest room) |
| 09.REMOTE | Marionette / Remote Agent lockdown |
| 10.OVERRIDES | `user.js` → the **profile**, not the source |
| 11.FONT.SYSTEM | bundled fonts |
| 12.MOZAMBIQUE.DRILL | Normandy / Nimbus experiment kill |
| 13.TELEMETRY.KILL | MemoryTelemetry + Glean CPU/egress kill |
| 14.EGRESS.LOCKDOWN | outbound endpoint blackholes |

Filenames encode the target path with `_` for `/`
(`browser_app_profile_firefox.js.patch` → `browser/app/profile/firefox.js`).

## Provenance & honesty

Every change to Mozilla source carries a `// GORILLA OVERRIDE:` (or `GORILLA:`) comment saying
what changed and why — a deliberate transparency convention so a developer *and* a layperson can
audit exactly what we did. This is the Open-Source-Philosophy mandate, not vanity. Patches that
turned out to be dead no-ops were removed to `patches/quarantine/`, not shipped.
