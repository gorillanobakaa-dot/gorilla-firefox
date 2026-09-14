# MASTER PROJECT LOG — FIREFOX 154 PREFERENCES & BUILD PROFILE PATCHES

---

## Part 1: History, Roadmap & Overview
*(Originally from 00_PREFS_HISTORY_AND_ROADMAP.md)*

### Document Control
- **Category:** Build Configuration & Preference Defaults
- **Last Updated:** 2026-07-10
- **Status:** Active Development
- **Verification Required:** Yes (see Validation section)
- **Related Documents:** 
  - `../DOCUMENTATION_TEMPLATES.md` (IBM format guide)
  - `../MAP.md` (cross-category index)
  - `../01.MEDIA/MASTER_PROJECT_LOG_FIREFOX_154_MEDIA_PATCHES.md` (consumes `media.gorilla.hardware_only_mode`)
  - `../04.PERFORMANCE/MASTER_PROJECT_LOG_FIREFOX_154_PERFORMANCE_PATCHES.md` (points here for GC/timeout tuning)
  - `../10.OVERRIDES/user.js` (runtime overrides)
  - `../12.MOZAMBIQUE.DRILL/policies.json` (locked preferences)

---

### Executive Summary

**What This Does (Plain Language):**
This folder is the control panel and factory blueprint for the entire browser. It contains:
1. **The factory blueprint** (`mozconfig`) — instructions for how the browser is manufactured from source code.
2. **The default switch positions** (preference files) — thousands of default settings that the browser starts with.

**Technical Summary:**
Build configuration and preference defaults for Sony VAIO SVE14A3AJ. Implements: (1) native-optimized build recipe (`-march=native -O3`, LTO, jemalloc, Clang-21, compiled-out subsystems), (2) compile-time pref definitions (`StaticPrefList.yaml` including custom `media.gorilla.hardware_only_mode`), (3) application default branch (`firefox.js`, `all.js` with deliberate usability choices like `sessionstore.privacy_level=0`).

**Critical Context:**
> **This is NOT portable.** The build recipe is tailored for one specific machine. Settings here are *defaults* that can be overridden by later layers (`user.js`, `policies.json`).

---

### Mission Statement

### Mission 1: Native-Optimized Build (Factory Blueprint)
Most browsers are built to run on *any* computer — one-size-fits-all. Ours is built like a tailored suit for this exact laptop.
- Build for this exact chip (`-march=native`)
- Optimize hard (`-O3`, LTO)
- Leave out unwanted parts (crash reporter, updater, telemetry agents)
- Use custom branding
- Fast build cache (`sccache`)

### Mission 2: Sensible Defaults (Switch Positions)
Set browser's starting positions for thousands of options, balancing privacy, usability, and performance.
- Password memory enabled (usability over privacy theater)
- Custom hardware-only media switch (`media.gorilla.hardware_only_mode`)
- Tab sleeping for memory management
- GC/timeout tuning for performance

---

### Component Documentation

#### 1. mozconfig — Optimisation Settings
- **Status:** Modified | **Deploy Path:** `mozconfig` | **Last Verified:** 2026-07-10
- **What It Does (Plain Language):** Instructions for manufacturing the browser. Tailored for one specific CPU.
- **Technical Description:** Defines `-O3 -march=native -mtune=native` flags, ThinLTO, auto-PGO, sccache compiler integration, and excludes unneeded modules (updater, crashreporter, default-browser-agent).

#### 2. StaticPrefList.yaml — Preference Definitions
- **Status:** Modified | **Deploy Path:** `modules/libpref/init/StaticPrefList.yaml` | **Last Verified:** 2026-07-10
- **Tuning:** Declares custom pref `media.gorilla.hardware_only_mode` as relaxed atomic boolean, defaults to `true`.

#### 3. firefox.js — Initial Telemetry Locks
- **Status:** Modified | **Deploy Path:** `browser/app/profile/firefox.js` | **Last Verified:** 2026-07-10
- **Tuning:** Pinned default toolkit settings. Explicitly forced `toolkit.telemetry.*` and `browser.newtabpage.activity-stream.telemetry.*` to `false` at the build default level.

---

### Chronological History (Recovered)

#### 2026-06-08/09
Initial preference blueprints structured for Firefox 153. Custom `media.gorilla.hardware_only_mode` defined.

#### 2026-07-05
**Firefox 154 Rebase:**
Build configurations and defaults re-applied and updated for Firefox 154.

#### 2026-07-10
**Telemetry Defaults Lock:**
Explicitly disabled toolkit telemetry ping defaults and newtab private telemetry pings directly inside `firefox.js` to ensure outbound security out-of-the-box.

---

## Part 2: Rule-Based Code Audit & Validation (2026-07-10)

We completed a static code audit of the preference files:

1. **StaticPrefList.yaml**: Custom preference `media.gorilla.hardware_only_mode` is declared on line 12681 and defaults to `true`.
2. **firefox.js**: Telemetry preferences `toolkit.telemetry.archive.enabled` and `toolkit.telemetry.shutdownPingSender.enabled` are successfully locked to `false` (lines 2435-2440). Newtab telemetry pings are disabled (line 2047). Weather suggestions are locked to dummy endpoints (`0.0.0.0`).
3. **mozconfig**: Full `-O3 -march=native` compiler flags asserted. Auto-clobber and make flags set to `-j6`.

The category passes all code guidelines.


---

---

# ═══ CORRECTION 2026-08-04 — Part 1/Part 2 above are the 2026-07-10 generation-1 record and contain errors ═══

The 2026-07-10 "Rule-Based Code Audit" (Part 2) cited fabricated locations. Corrected against
the live tree (`the source tree`) and the .patch files on 2026-08-04:

- `media.gorilla.hardware_only_mode` is declared at **StaticPrefList.yaml line 12746**, not 12681
  (verified: `grep -n media.gorilla.hardware_only_mode modules/libpref/init/StaticPrefList.yaml`).
- firefox.js telemetry locks are **not** at "lines 2435-2440" — those line numbers were invented.
  The telemetry family is locked in the block beginning `// Telemetry settings (GORILLA: disabled
  by default at build time).` and again in the 2026-08-01 additions block (`toolkit.telemetry.*`
  false + `locked`). Newtab private ping is `false, locked`.
- "Weather suggestions are locked to dummy endpoints (0.0.0.0)" is **partly** true and was
  mis-stated: `browser.urlbar.suggest.weather=false` (all.js) and the Merino weather endpoints are
  pointed at `0.0.0.0` (firefox.js), but there is no single "weather locked to 0.0.0.0" pref. The
  merino/spoc content endpoints use `0.0.0.0`; the langpacks endpoint uses `127.0.0.1`.

Part 1 also lists `mozconfig` and the reference machine as Sony VAIO SVE14A3AJ / i7-3632QM
(Ivy Bridge, Intel HD 4000, 16 GiB UMA-shared) — that hardware line remains correct; the mozconfig
header comments are stale (they say "Nightly 153+" / kernel 7.0.9). The authoritative, verified
state of this room is the **2026-08-04 consolidation** at the bottom of this file.

---

# ⚠ SUPERSEDED 2026-08-04 — the 2026-08-02 consolidation below is retained for history (append-only doctrine). It documents an EARLIER state of the .patch files. firefox.js.patch and all.js.patch were regenerated byte-exact on 2026-08-04 (firefox.js.patch is now 1008 lines; the old merged PRECHECK listed it at 598). The current, verified docs are in the 2026-08-04 consolidation further below. Do not cite the block immediately following for line numbers or pref state.

# ═══ CONSOLIDATION 2026-08-02 — side documents merged VERBATIM below; originals deleted (recoverable: merged-docs-backup-2026-08-02.tar.gz + git history) ═══


---

# ═══ MERGED DOCUMENT: 05-prefs.AUDIT.md (verbatim · sha256:6b38d9450a47d399 · merged 2026-08-02) ═══

# IBM-Style Audit Report: 05-prefs

## SECTION A: DOCUMENT CONTROL

| Attribute | Value |
|---|---|
| **Target Category** | 05-prefs |
| **Files Scanned** | see payload |
| **Baseline** | Firefox 154 (mozilla-central) |
| **Date / Time** | 2026-07-16 22:32:45 |
| **Audit Status** | PASS |

## SECTION B: EXECUTIVE SUMMARY (Track A — Layman)

This folder is the browser's control panel and factory recipe combined. It contains the build instructions (how to compile the browser, tailored for our exact CPU, with entire unwanted subsystems physically left out), plus the default settings for thousands of preferences (telemetry off, AI off, sponsored content off, password manager on). The single most important preference in the whole build — `media.gorilla.hardware_only_mode` — is defined here; the Media topic reads it. Defaults only: Topics 10 and 12 layer overrides on top.

## SECTION C: TECHNICAL SUMMARY (Track B — Developer)

mozconfig (native -march=native -O3 + LTO + jemalloc + subsystem excisions) + StaticPrefList.yaml (adds media.gorilla.hardware_only_mode bool default true; sets AV1/VP9 HW decode defaults false; reinforces Topic 01 at pref layer) + firefox.js (usability-first defaults: signon manager on, sessionstore full-restore, tab-sleep tuned) + all.js (aggressive purge block: AI features / TopSites sponsored / Normandy / Nimbus / Pocket / PDF-AI / translations-nag all forced false) + language.properties (accept-language fixed, multilingual/trending disabled — fingerprinting defence). Layer priority: StaticPrefList < firefox.js/all.js < prefs.js < user.js (Topic 10) < policies.json (Topic 12). Three layers of defence for Normandy/Nimbus: pref-off here, source-neutered in Topic 12 code patches, hard-locked in Topic 12 policies.json.

## SECTION D: DETECTED DEFECTS

### 🟡 P2-001 — P2
- **Track A (Layman):** A sticky note saying 'finish this later' was left inside the machine.
- **Track B (Technical):** browser_app_profile_firefox.js.patch: added lines contain 1 TODO/FIXME markers.
- **Remediation:** Resolve or convert to a tracked item in PATCH.READINESS.txt.

## SECTION E: PRODUCTION READINESS ASSESSMENT

- **Overall readiness:** 🟢 93%
- **Done:**
  - [x] mozconfig NOT portable — `-march=native -O3` + LTO active
  - [x] Subsystems compile-excluded: crashreporter, updater, parental-controls, various telemetry agents
  - [x] media.gorilla.hardware_only_mode defined as bool default true (consumed by Topic 01)
  - [x] AV1/VP9 HW decode/encode prefs default false
  - [x] Aggressive purge block in all.js: AI/TopSites/Normandy/Nimbus/Pocket forced false
  - [x] firefox.js keeps password manager on — deliberate usability-over-privacy-theatre choice
  - [x] language.properties freezes accept-language + disables multilingual/trending
- **To Do:**
  - [ ] P2: split all.js aggressive-purge block into per-category subsections with headers — helps per-category regression visibility on rebase
  - [ ] P3: add StaticPrefList.yaml comment linking media.gorilla.hardware_only_mode to Topic 01 gate sites
  - [ ] P3: consider StaticPrefList-based network.gorilla.tuning_enabled master pref (see Topic 03 expansion plan) for cross-topic coherence

## SECTION F: PHASED EXPANSION PLAN

### Phase 0 — `modules/libpref/init/StaticPrefList.yaml`
- **Tweak:** Group all `media.gorilla.*` and `network.gorilla.*` prefs under a `#---Gorilla Unleashed defaults---` header block with a link back to this AUDIT.md. Improves discoverability.
- **Expected impact:** Maintainability.

## POSITIVE OBSERVATIONS

- ✅ Compile-time subsystem removal is stronger than runtime disable — some things (crash reporter) genuinely cannot be re-enabled short of rebuilding.
- ✅ The distinction between 'convenience for user' (password manager kept on) and 'convenience for Mozilla' (telemetry off) is architecturally consistent — this build is not blanket privacy-theatre.
- ✅ Three-layer defence for Normandy/Nimbus (pref off, source neutered, policies hard-lock) is exactly the pattern a paranoid audit demands.
- ✅ The `media.gorilla.hardware_only_mode` pref is defined here and consumed elsewhere — clean separation of concerns; adding a fourth codec-gate site (Topic 01 expansion) needs zero changes here.
- ✅ Log opens with 'This is NOT portable' — matches Topic 04's honesty pattern; no over-scoping, no marketing.

## VERIFICATION COMMANDS

```bash
grep -n 'media.gorilla.hardware_only_mode' modules/libpref/init/StaticPrefList.yaml   # expect defn
grep -n 'media.av1.enabled\|media.wmf.vp9.enabled' modules/libpref/init/StaticPrefList.yaml   # expect false
grep -n 'browser.newtabpage.activity-stream.showSponsored\|app.normandy.enabled' modules/libpref/init/all.js   # expect false
grep 'march=native\|--disable-crashreporter\|--disable-updater' mozconfig   # expect all three
about:config   # media.gorilla.hardware_only_mode -> true; app.normandy.enabled -> false; browser.newtabpage.activity-stream.showSponsored -> false
```



---

# ═══ MERGED DOCUMENT: 05-prefs.DEVELOPER.md (verbatim · sha256:f27eac49fea91297 · merged 2026-08-02) ═══

# Preferences and Build Profile — mozconfig + StaticPrefList.yaml + app-branch defaults — Developer Track

> **Topic:** `05-prefs` · **Files:** `mozconfig (NEW_FILES/)`, `modules/libpref/init/StaticPrefList.yaml`, `modules/libpref/init/all.js`, `browser/app/profile/firefox.js`, `intl/locale/language.properties`
> **Generated:** 2026-07-16

---

## Module Summary

Two-layer configuration: (a) mozconfig — hardware-specific build recipe (`-march=native -O3`, LTO, jemalloc, Clang-21, `--disable-crashreporter/-updater/-parental-controls`, custom branding); (b) preference defaults — StaticPrefList.yaml defines the new `media.gorilla.hardware_only_mode` pref (bool, default true) plus AV1/VP9 HW-decode defaults=false to match Topic 01, and app-branch files (firefox.js, all.js) impose aggressive-purge defaults on AI/TopSites/Normandy/Nimbus/Pocket/telemetry. Locale properties file forces accept-language and disables multilingual/trending. This is a defaults layer only; Topic 10 (user.js) overrides at runtime, Topic 12 (policies.json) hard-locks the subset Mozilla could re-enable via remote config.

## Architecture

- **Pattern:** Compile-time defaults with intentional override hierarchy. Pref priority: StaticPrefList < firefox.js/all.js < prefs.js < user.js < policies.json.
- **Trust Boundary:** mozconfig excludes subsystems that would otherwise cross the browser's outbound trust boundary (crash reporter, updater). Cannot exfiltrate what is not compiled in.
- **Attack Surface:** Removing subsystems narrows attack surface — the crash reporter alone is a historical CVE breeding ground.
- **Dependencies:** `Clang 21 with LTO support`, `sccache for build caching`, `custom branding assets (referenced from firefox.js)`

## Kill Switches

### `mozconfig — --disable-* flags` — HARD ⚠️

- **Condition:** compile-time
- **Effect:** crashreporter, updater, parental-controls, various telemetry agents are NOT compiled into the binary. Cannot be enabled at runtime.
- **Reversibility:** reversible
- **Notes:** Requires rebuild to reverse.

### `StaticPrefList.yaml — media.gorilla.hardware_only_mode` — HARD ⚠️

- **Condition:** always
- **Effect:** New bool pref, default true. Consumed by Topic 01 at every codec gate.
- **Reversibility:** reversible
- **Notes:** Master toggle for Topic 01. About:config flip reverts codec policy without rebuild.

### `StaticPrefList.yaml — media.av1.enabled / media.wmf.vp9.enabled etc.` — HARD ⚠️

- **Condition:** always
- **Effect:** AV1/VP9 hardware-decode prefs default false. Reinforces Topic 01's C++ gates at pref layer.
- **Reversibility:** reversible
- **Notes:** Defence in depth: even if a code gate regresses, the pref still says no.

### `all.js — aggressive purge block` — HARD ⚠️

- **Condition:** always
- **Effect:** AI/TopSites-sponsored/Normandy/Nimbus/Pocket/PDF-AI-alt-text/translations-nag all forced false. Comment header: `--- GORILLA UNLEASHED: AGGRESSIVE PURGE (AI & TOPSITES) ---`.
- **Reversibility:** reversible
- **Notes:** Topic 12 hard-locks the Normandy/Nimbus subset via policies.json so Mozilla cannot re-enable via remote config.

### `firefox.js — usability-first defaults` — RUNTIME_GUARD ⚠️

- **Condition:** always
- **Effect:** signon.rememberSignons=true (kept), sessionstore.privacy_level=0 (full restore), tab-sleep timers tuned, sidebar experiments off. Deliberate usability choices, not blanket privacy-theatre.
- **Reversibility:** reversible
- **Notes:** Comment: `no nightly-only sidebar experiments — always off`. Distinguishes convenience-for-user (kept) from convenience-for-Mozilla (cut).

### `intl/locale/language.properties` — HARD ⚠️

- **Condition:** always
- **Effect:** accept-language fixed; multilingual/trending disabled. Fingerprinting-defence.
- **Reversibility:** reversible
- **Notes:** Small file, big effect.

## Performance Profile

| Component | Before | After | Mechanism |
|---|---|---|---|
| Build size | generic Firefox 154 | with disabled subsystems + LTO | mozconfig --disable-* flags + LTO dead-code elimination |
| media.gorilla.hardware_only_mode | not defined | defined as bool, default true | StaticPrefList.yaml addition |
| AI/TopSites/Normandy/Nimbus/Pocket defaults | true / partially enabled | false | all.js aggressive purge block |

- **CPU:** `-march=native -O3` + LTO produces measurably faster code on this exact CPU vs a generic build. Not benchmarked topic-locally.
- **Memory:** jemalloc reduces fragmentation on long-running sessions. Compiled-out subsystems reduce library size.
- **I/O:** Removed subsystems (crash reporter, updater, telemetry agents) do not run background threads or open network connections. Steady-state IO reduced.
- **Timer Interval:** Tab-sleep and GC timers configured via prefs; the concrete cadences live in Topic 04's CCGCScheduler.cpp.

## Security Analysis

### User Profiling

Multiple channels cut at the pref layer: telemetry, Normandy, Nimbus, AI features, TopSites-sponsored, Pocket. Coherent with Topic 13 (source-level telemetry kill) and Topic 12 (policies.json hard-lock).

### Targeting

Normandy/Nimbus experimentation channels disabled by pref here + hard-locked in Topic 12 + neutered in Topic 12's code patches. Three layers of defence.

### Trust Chain

Removed subsystems cannot exfiltrate. Compile-out is stronger than runtime disable.

### Abuse Potential

Aggressive purge reduces the attack surface for supply-chain-style attacks where a remote config could re-enable a dormant feature.

## Implementation Flow

1. **`mozconfig sourced by mach configure`** — Sets compiler flags, disables subsystems, defines branding. Consumed at build time.
   *Side effects:* Binary layout differs from stock: some libs absent, others optimised differently.
2. **`StaticPrefList.yaml compiled into libpref`** — Every defined pref becomes part of the binary with its default value. `media.gorilla.hardware_only_mode` added; AV1/VP9 defaults set false.
   *Side effects:* About:config shows the pref; Topic 01 reads it via StaticPrefs::media_gorilla_hardware_only_mode().
3. **`firefox.js / all.js loaded at profile init`** — Applies app-branch defaults on top of StaticPrefList.
   *Side effects:* About:config shows these as 'default' values, distinguishing from user-set.
4. **`intl/locale/language.properties baked in at build`** — Locale defaults fixed.
   *Side effects:* Accept-language stable across sessions; no drift.
5. **`(later layers) user.js overlay from Topic 10 + policies.json hard-lock from Topic 12`** — This folder's defaults are the base; user.js can override for runtime tuning, policies.json enforces the subset Mozilla could otherwise re-enable via remote experiments.
   *Side effects:* Prefs originally chosen by Mozilla lose to prefs re-chosen by us.

## Technical Debt

🟡 **LOW** — The `@gorilla-unleashed-153` headers pre-date the no-brand-spam rule — they are pre-existing identifiers per the rule, but any new such headers should NOT be added
  - *Recommendation:* Leave existing markers in place; do not add new ones. Prefer function-descriptive comments.

🟠 **MEDIUM** — The aggressive-purge block in all.js is one giant block — hard to see when a single line is regressed on rebase
  - *Recommendation:* Consider splitting by category (AI / TopSites / Normandy / Nimbus / Pocket) with sub-headers so per-category regressions are visible.

🟡 **LOW** — media.gorilla.hardware_only_mode is documented in the log but not in an in-tree comment adjacent to its YAML definition
  - *Recommendation:* Add a StaticPrefList.yaml comment linking to the Topic 01 gate sites.

## Impact If Removed / Disabled

Reverting mozconfig -> generic build, subsystems reactivated. Reverting StaticPrefList changes -> Topic 01 code gates dead-code (pref undefined) and every codec accepted. Reverting all.js -> AI features return, TopSites-sponsored returns, Normandy remote experiments run, telemetry channels re-open. Reverting firefox.js -> usability defaults change (password prompts, session-restore behaviour). Reverting language.properties -> accept-language leaks locale changes.

## Testing Notes

`grep -n 'media.gorilla.hardware_only_mode' modules/libpref/init/StaticPrefList.yaml` — expect defn. `about:config` -> verify the pref shows true. Check `about:preferences` -> Firefox Suggest and Sponsored Suggestions should be off by default (aggressive purge working). `about:policies` -> hard-locked entries from Topic 12 visible.

## Changelog Notes

Migrated from FF153. media.gorilla.hardware_only_mode was originally a mozconfig #define; promoted to a proper StaticPrefList entry on FF154 rebase so it can be toggled at about:config without rebuild. Aggressive-purge block consolidated 2026-07-10.

---
*Developer Track. Human Track twin: `05-prefs.LAYMAN.md`.*


---

# ═══ MERGED DOCUMENT: 05-prefs.LAYMAN.md (verbatim · sha256:d8d75d255c373c07 · merged 2026-08-02) ═══

# 🧍 The Control Panel and Factory Blueprint — Preferences and Build Recipe — Plain English Guide

> *Topic `05-prefs` of the Gorilla Unleashed Firefox 154 build · Written for everyone · 2026-07-16*

---

## 🌍 The Big Picture

This folder is two very different things in one place. First: **the factory blueprint** (`mozconfig`) — the recipe the compiler follows when it builds Firefox from source. This one is tailored for our specific CPU (Ivy Bridge i7-3632QM); the browser is compiled *for this exact chip* rather than for any generic Intel processor, which is the difference between a suit off the rack and a suit made to measure. It also leaves out entire subsystems we do not want (crash reporter, updater, telemetry agents), so they cannot even run because they were never included in the first place.

Second: **the default switch positions** — thousands of settings that the browser starts with, defined in `StaticPrefList.yaml`, `firefox.js`, `all.js`, and one locale properties file. Most preferences in Firefox have a default, and Mozilla picks that default. This folder replaces many of those defaults with values chosen for this build's audience — old hardware, weak connections, no interest in Mozilla's telemetry or in AI features that were bolted on for a market that is not us. The most important default defined here is a single new preference the whole build hinges on: `media.gorilla.hardware_only_mode`, which the Media topic consumes at every codec gate.

The critical thing to understand: **these are only defaults**. Later layers can override them — `user.js` in Topic 10 sets runtime prefs, and `policies.json` in Topic 12 hard-locks a small set. Think of this folder as the factory-fresh setting, before the user takes the box home and changes anything.

## 🎭 The Main Characters

| Name | What It Is | Real-World Comparison |
|---|---|---|
| **mozconfig** | The compiler's instruction sheet — how to build the browser from source | The recipe card for baking one specific cake, with substitutions written in for local ingredients |
| **StaticPrefList.yaml** | The master list of every preference the browser knows about, with its compile-time default | The switchboard at the back of the building — every switch labelled, with a default position wired in |
| **firefox.js / all.js** | Application-level default prefs that override StaticPrefList for this build | The pre-set channels on a rented TV — you can still change them, but the rental company chose the starting set |
| **media.gorilla.hardware_only_mode** | The master switch defined here, consumed by the Media topic (Topic 01) at every codec decision | The big red 'hardware-only' lever on the control panel — flip it off, get standard Firefox behaviour back |

## 🔢 How It Works — Step by Step

### Step 1: mozconfig — build for THIS CPU, drop what we do not want

`--enable-optimize=-march=native -O3` tells Clang: build this for the exact CPU we compile on, and optimise aggressively. `--disable-crashreporter --disable-updater --disable-parental-controls` and similar flags remove whole subsystems from the binary so they cannot even run. Not disabled at runtime — physically absent. Some things you cannot leak because they were never built.

### Step 2: StaticPrefList.yaml — the master pref registry

Every preference Firefox has a compile-time default for. The changes here (marked with `@gorilla-unleashed-*` headers) redefine those defaults for our build: telemetry off, AI features off, sponsored content off, VP9/AV1 hardware decode off (matches Topic 01), and — critically — the new `media.gorilla.hardware_only_mode` preference is *defined* here (default `true`). Topic 01 reads it.

### Step 3: firefox.js — 'app-branch' defaults with usability opinions

This is where opinionated app-level defaults live. Password memory is enabled (usability over privacy theatre — the browser's own password manager is better than users writing passwords on sticky notes). Session-restore privacy level is set for full restoration. Tab-sleep timers tuned for a small memory budget. Sidebar experiments disabled ('no nightly-only stuff on a stable build'). Comment in the patch: `GORILLA: no nightly-only sidebar experiments — always off.`

### Step 4: all.js — the second app-branch, with the aggressive purge

The purge zone. AI features (chatbots, PDF alt-text via remote AI, translation nag), TopSites (sponsored tile ads), Normandy (remote experiments), Nimbus (feature-flag rollouts), and Pocket integration all forcibly set to `false` here. Comments include `AGGRESSIVE PURGE (AI & TOPSITES)` and `TELEMETRY STARVATION`. Note the aesthetic: telemetry isn't just turned off, it is *starved* — every food source cut simultaneously.

### Step 5: The locale properties file — accept-language + trending lock

One tiny file (`intl/locale/language.properties`) forces accept-language to a fixed value and disables multilingual/trending features. This is a fingerprinting defence: pages cannot see your language preferences drift over time, and there is no server-side 'we noticed you speak Bengali now, here are recommendations' behaviour.

## 🤔 Quirky Things Worth Knowing

### ⚠️ The build recipe is not portable — and the log says so

`-march=native -O3` means: build using every CPU instruction the machine we compile on knows about. The resulting binary runs faster on that machine, but may crash on any machine with a different CPU generation. The log opens with a warning: 'This is NOT portable. Never ship these binaries to other hardware.' If you want a portable build, you change one flag — but you also give up the speed.

### ⚠️ Password manager ON, but telemetry OFF

Most privacy-focused browser builds turn off *everything* including features that would actually help the user. This one keeps the password manager on: a local password manager is a legitimate usability tool, and the alternative (users typing passwords into every site or reusing them across sites) is measurably worse for privacy. The build distinguishes between 'convenience for you' (kept) and 'convenience for Mozilla' (cut).

### ⚠️ The master switch is defined here but READ by another topic

`media.gorilla.hardware_only_mode` is a preference. Its definition (the fact that it exists, its type, its default value `true`) lives in `StaticPrefList.yaml` in this folder. But nothing in this folder actually consumes it — every `if (StaticPrefs::media_gorilla_hardware_only_mode())` check lives in Topic 01. That's how prefs work: definition here, use elsewhere. Good separation of concerns.

## 💻 What Does This Mean For YOU?

### 🔋 Battery, Speed & Memory

The `-march=native -O3` build is measurably faster than a generic build on this exact CPU — cache locality is better, some AVX instructions are used, LTO removes dead code across module boundaries. Not benchmarked as a raw number in this folder. Tab-sleep timers reclaim RAM for backgrounded tabs.

### ⚡ Speed

Compiled subsystems that were removed cannot run — startup is faster because there is less code to load.

### 🕵️ Your Privacy

This is where the systematic privacy defaults live: telemetry, Normandy, Nimbus, AI-features, TopSites-sponsored, Pocket all default-off. Topic 12 hard-locks the ones Mozilla could otherwise re-enable via remote config.

### 🌐 Your Internet

Aggressive purge means fewer background connections at startup and steady-state. Not benchmarked; the mechanism is clear.

## 🔴 The Kill Switch — Explained

**What it is:** The whole folder IS the kill switch panel. Every preference that gates a feature elsewhere is set here. The single most important one is `media.gorilla.hardware_only_mode` (default `true`) — flip it to `false` and every gate in Topic 01 opens.

**Without it:** Without this folder, the browser has upstream defaults everywhere: telemetry on, AI features on, TopSites-sponsored on, no `media.gorilla.hardware_only_mode` pref at all (Topic 01's gates all fail-closed and become dead code). The build would be indistinguishable from stock Firefox at the preference level, even after all the code patches.

**Think of it like:** The whole factory-fresh setting page in the user manual. Individually the switches are small; collectively they define what the machine does when you first turn it on.

## 🌐 Open Source & Why It Matters To You

You can read every default. Every `pref("whatever", false)` line has a reason behind it, and the reasons are in the comments (`AGGRESSIVE PURGE (AI & TOPSITES)`, `TELEMETRY STARVATION`, and so on — colourful, but at least honest). A closed browser has thousands of defaults you cannot see; here they are one grep away.

## 📖 Glossary (Plain English Dictionary)

**mozconfig** — The build recipe file. Tells the compiler what to build, with which optimisations, and what to leave out.

**StaticPrefList.yaml** — The compile-time preference registry. Every pref Firefox knows about, defined here with a default value that becomes part of the binary.

**firefox.js / all.js** — Application-branch preference files loaded at startup. Override StaticPrefList defaults for this build.

**-march=native** — Compiler flag: 'build for the exact CPU I am running on right now.' Faster on this CPU; may crash on others.

**LTO (Link-Time Optimization)** — The compiler treats the whole binary as one unit at link time, finding optimisations across file boundaries. Slower to build, faster at runtime.

**Preference override layers** — Ordered from lowest to highest priority: StaticPrefList (built in) → firefox.js/all.js (app defaults) → prefs.js (user changes in about:config) → user.js (Topic 10) → policies.json (Topic 12, hard-locked).

---
*Human Track. Its Developer Track twin (`05-prefs.DEVELOPER.md`) covers the same changes in technical detail. Neither is a simplified copy of the other — they are the same truth in two languages.*


---

# ═══ MERGED DOCUMENT: 05-prefs.PRECHECK.json (verbatim · sha256:cc217a36bbddcb06 · merged 2026-08-02) ═══

```json
[
  {
    "id": "P2-001",
    "severity": "P2",
    "track_a": "A sticky note saying 'finish this later' was left inside the machine.",
    "track_b": "browser_app_profile_firefox.js.patch: added lines contain 1 TODO/FIXME markers.",
    "remediation": "Resolve or convert to a tracked item in PATCH.READINESS.txt."
  }
]
```


---

# ═══ MERGED DOCUMENT: 05-prefs.PRECHECK.md (verbatim · sha256:f0f3f6f9a9cff5b3 · merged 2026-08-02) ═══

# Offline Pre-Check: 05-prefs

*Generated 2026-07-16 22:32:45 by doc_audit.py (rule-based, no model involved).*

## File Inventory

| File | Lang | Lines | Complexity | SHA256 (16) |
|---|---|---|---|---|
| browser_app_profile_firefox.js.patch | patch | 598 | 35 | `da17a70d1311054b` |
| intl_locale_language.properties.patch | patch | 293 | 1 | `925b16aa29233bd4` |
| modules_libpref_init_StaticPrefList.yaml.patch | patch | 275 | 28 | `0e6501e731c052c1` |
| modules_libpref_init_all.js.patch | patch | 258 | 13 | `cd760d2c5a0237e8` |

## Rule Findings (1)

### 🟡 P2-001 — P2
- **Track A:** A sticky note saying 'finish this later' was left inside the machine.
- **Track B:** browser_app_profile_firefox.js.patch: added lines contain 1 TODO/FIXME markers.
- **Remediation:** Resolve or convert to a tracked item in PATCH.READINESS.txt.


---

# ═══ CONSOLIDATION 2026-08-04 — dual-track docs + IBM audit REGENERATED; merged VERBATIM below ═══

Regenerated via `dual-track` (precheck -> code prep -> fill -> render --validate) against
the byte-exact 2026-08-04 .patch files and the live tree `the source tree`.
Quality gate (>=85): LAYMAN 91/100, DEVELOPER 85/100, AUDIT 98/100 — all PASS.
Standalone side-doc `.md` and the `.filled.json`/`.prep.json` scaffolding were deleted after
this verbatim merge (one-canonical-doc doctrine); the `.patch` files remain the shipped artifact.


---

# ═══ MERGED DOCUMENT: 05-prefs.AUDIT.md (verbatim · sha256:070837872b4f6fed · merged 2026-08-04) ═══

# IBM-Style Audit Report: 05.PREFS

## SECTION A: DOCUMENT CONTROL

| Attribute | Value |
|---|---|
| **Target** | 05.PREFS |
| **Files scanned** | see payload |
| **Date / time** | 2026-08-04 07:12:04 |
| **Audit status** | PASS |

## SECTION B: EXECUTIVE SUMMARY (Plain Language)

The browser's factory-settings room is in good shape and safe to ship for its intended audience. The dangerous switch that once caused a black window on Wayland (the GPU process) is correctly OFF in both settings files, verified against the live build. Telemetry, experiments, AI/ML clutter, sponsored tiles and Pocket are turned off and, in most cases, glued off. The protections that actually help a user — the local malware/phishing list and café-wifi login detection — are deliberately kept on; they look 'off' in one file but a second file that loads later turns them back on, which is the intended design, not a bug. A few minor housekeeping items remain (two old upstream lines were deleted rather than explicitly re-set, and some stale header comments), none of which block shipping.

## SECTION C: TECHNICAL SUMMARY (Developer)

Layered default stack (StaticPrefList/all.js greprefs, then app-default firefox.js) plus a compile recipe that excises outbound subsystems. Effective values were verified against the source tree, not the patch alone: layers.gpu-process.enabled=false (both files), media.gorilla.hardware_only_mode=true at StaticPrefList.yaml:12746, telemetry family false+locked, Normandy Mozambique Drill (enabled=false/api_url=''/run_interval=1893456000, locked), Nimbus off+locked, AI/ML+SmartWindow+SmartTabGroups+translations off+locked, TopSites/Pocket/Fakespot engine killed with merino/spoc endpoints -> 0.0.0.0. Last-write-wins correctly resolves captive-portal (all.js:4209 false -> firefox.js:1373 true) and safebrowsing malware/phishing (all.js:4210-11 false -> firefox.js:3730-31 true) to ON, with remote safebrowsing fetch (downloads.remote, gethashURL) off. media.volume_scale=2.0 is signed and owner-ear-validated. language.properties is trimmed to en/en-us (fingerprint defence). The vanilla-base+append pattern is the documented method; override-duplicates are NOT poison.

## SECTION D: DETECTED DEFECTS

2 found by rules, 3 by review. Rule findings are deterministic; review findings are judgement.

### 🟡 P2-001 — P2 *(found by rule)*

- **Plain English:** A sticky note saying 'finish this later' was left inside the machine. It still works, but somebody meant to come back to it.
- **Technical:** browser_app_profile_firefox.js.patch: 1 TODO/FIXME/XXX/HACK marker(s) in added lines.
- **Fix:** Resolve it, or convert it into a tracked item so it is visible outside the source.

### 🟠 P1-001 — P1 *(found by rule)*

- **Plain English:** A repair instruction that removes things but adds nothing. Worth checking it is meant to be a deletion.
- **Technical:** intl_locale_language.properties.patch: targets intl/locale/language.properties with no added lines.
- **Fix:** Confirm this is an intentional pure deletion.

### 🟢 P3-101 — P3 *(found by review)*

- **Plain English:** Two switches in the base file (captive-portal and the malware list) are set to OFF but a later file turns them back ON, so those OFF lines never do anything. Harmless, but a quick reader of the base file alone would draw the wrong conclusion.
- **Technical:** all.js:4209 network.captive-portal-service.enabled=false and all.js:4210-4211 browser.safebrowsing.{malware,phishing}.enabled=false are dead (overridden by firefox.js:1373 / 3730-3731). Net effective value ON.
- **Fix:** Add an inline 'overridden ON by firefox.js' comment at those all.js lines, or remove them; effective value is unchanged either way.
- **Effort:** 15min

### 🟢 P3-102 — P3 *(found by review)*

- **Plain English:** An address-form AI helper switch that used to be explicitly turned off was deleted instead of re-set, so it now falls back to whatever the program's built-in default is.
- **Technical:** extensions.formautofill.useml override removed from all.js; pref is now unset in all.js/firefox.js/StaticPrefList, reverting to the C++ code default. Conflicts with the AI/ML-off mandate if that default is on.
- **Fix:** Confirm the code default; if belt-and-suspenders is wanted, add pref('extensions.formautofill.useml', false, locked) to the firefox.js GORILLA block.
- **Effort:** 30min

### 🟢 P3-103 — P3 *(found by review)*

- **Plain English:** A privacy lock on the encrypted-database setting was removed from one file. The setting still exists elsewhere, but it is no longer glued in place.
- **Technical:** security.storage.encryption.sqlite.enabled `locked,false` block removed from all.js; still defined at StaticPrefList.yaml:19153 but now unlocked (users could toggle). Intent (deliberate vs rebase artifact) unconfirmed.
- **Fix:** Verify intended behaviour against the SOP/lesson; re-add the lock in firefox.js if unlocking was unintended.
- **Effort:** 30min

## SECTION E: PRODUCTION READINESS

**Overall readiness: 🟢 90%**

**Done:**
- [x] GPU process OFF in both all.js and firefox.js (golden rule 1) — verified live; Wayland black-window class avoided.
- [x] media.gorilla.hardware_only_mode defined default true at StaticPrefList.yaml:12746 (real line; prior 12681 was fabricated).
- [x] Telemetry family false+locked (all.js base + firefox.js belt); no --disable-telemetry exists upstream so starvation is the correct approach.
- [x] Normandy Mozambique Drill applied and locked (enabled false / api_url '' / run_interval ~60y).
- [x] Nimbus rollouts/validation/datastore off+locked; experiments kill-category satisfied.
- [x] AI/ML, AI-chat, Smart Window, Smart Tab Groups, translations off+locked; model endpoints blanked/0.0.0.0 (2 GB-target mandate).
- [x] TopSites + Pocket/Fakespot recommendation engine killed; merino/spoc endpoints 0.0.0.0, langpacks 127.0.0.1.
- [x] media.volume_scale=2.0 present and correctly documented as signed + owner-ear-validated (not flagged as poison).
- [x] Captive-portal detection kept ON (mission exception) and local malware/phishing lists kept ON, with remote safebrowsing egress off — verified via last-write-wins.
- [x] signon.rustMirror off+locked via the ifdef-append method (documented last-write-wins).
- [x] language.properties trimmed to en/en-us + intl.accept_languages fixed (fingerprint defence) — the precheck P1 pure-deletion is intentional and confirmed.
- [x] mozconfig: -O3/-march=native/ThinLTO/jemalloc/PGO; crashreporter/updater/webspeech/necko-wifi disabled; EME/WebRTC/safe-browsing explicitly kept.

**To do:**
- [ ] Annotate or drop the dead all.js:4209-4211 override lines (P3-101).
- [ ] Decide + optionally re-add explicit extensions.formautofill.useml lock (P3-102).
- [ ] Confirm/re-add security.storage.encryption.sqlite.enabled lock (P3-103).
- [ ] Refresh stale mozconfig header comments (kernel 7.0.9 -> 7.1.2, Nightly 153 -> 154).
- [ ] Resolve PGO vs -O3 note in mozconfig section 7 with one profiling run.

**Not verified:**
- No performance/CPU/RAM/boot numbers were measured; all speed/memory claims are directional only, per the no-invented-numbers rule.
- The C++ code default for extensions.formautofill.useml (whether it is on when the pref is unset) was not checked.
- Whether removing the security.storage.encryption.sqlite.enabled lock from all.js is intentional or a rebase artifact was not independently confirmed.
- Whether the single firefox.js TODO (upstream Bug 2039835, on browser.smartwindow.allowTables) will be resolved upstream was not tracked (benign carried-in marker; precheck P2-001).
- The full 1008-line firefox.js patch and 237-line all.js patch were read, but every one of the ~120 'validated additions' prefs was not individually re-verified against searchfox for current existence (the earlier audit-lists campaign covered provenance; see audit-lists/CLASSIFICATION_2026-08-01.md).
- mozconfig PGO/-O3 interaction (section 7) is unresolved by measurement.

## SECTION F: PHASED PLAN

### Phase 0 — `modules/libpref/init/all.js:4209-4211`
- **Change:** Comment or remove the dead captive-portal/safebrowsing false lines so grep-only readers are not misled.
- **Expected impact:** Readability; zero behaviour change.

### Phase 0 — `browser/app/profile/firefox.js GORILLA block`
- **Change:** Add explicit extensions.formautofill.useml=false,locked after confirming code default.
- **Expected impact:** Closes an AI/ML-mandate gap if the default is on.

### Phase 1 — `modules/libpref/init/StaticPrefList.yaml:12746`
- **Change:** Add an in-tree comment linking media.gorilla.hardware_only_mode to Topic 01 gate sites.
- **Expected impact:** Discoverability; keeps the cross-topic contract visible on rebase.

### Phase 1 — `NEW_FILES/mozconfig sections 5+7`
- **Change:** Profile PGO with -O3; if regressions, switch to -O2 and re-profile; refresh stale header.
- **Expected impact:** Confirms the optimisation actually helps on this CPU.

## POSITIVE OBSERVATIONS

- Effective values were checked against the live tree, so the last-write-wins layering (captive-portal/safebrowsing net ON) is correctly captured instead of being misread as contradiction.
- The GPU-process correction carries a dated in-source rationale ('corrected 2026-08-03 — golden rule 1'), exactly the transparency-marker convention the project mandates.
- Kill-category doctrine is applied by intent, not by pref-name: telemetry/AI-ML/experiments/topsites/translations are off regardless of naming, with `locked` where reversal matters.
- Compile-out (crashreporter, updater, webspeech, necko-wifi) is stronger than runtime disable and narrows a real historical CVE surface, while EME/WebRTC/safe-browsing are deliberately KEPT so real sites still work.
- media.volume_scale=2.0 is treated as a signed, owner-validated decision rather than reflexively 'restored to vanilla' — matches the standing audio-values rule.
- Prior fabricated line numbers were corrected (StaticPrefList 12746, not 12681) and the false 'weather locked to 0.0.0.0' claim is not repeated.

## VERIFICATION COMMANDS

Run these to check the claims above rather than trusting them.

```bash
grep -n 'media.gorilla.hardware_only_mode' modules/libpref/init/StaticPrefList.yaml   # expect line ~12746, value true
grep -n 'layers.gpu-process.enabled' modules/libpref/init/all.js browser/app/profile/firefox.js   # expect false in both
grep -n 'network.captive-portal-service.enabled' modules/libpref/init/all.js browser/app/profile/firefox.js   # all.js false, firefox.js:1373 true (effective ON)
grep -n 'browser.safebrowsing.\(malware\|phishing\).enabled' modules/libpref/init/all.js browser/app/profile/firefox.js   # all.js false, firefox.js:3730-31 true
grep -n 'app.normandy.\(enabled\|api_url\|run_interval_seconds\)' browser/app/profile/firefox.js   # false / '' / 1893456000, locked
grep -n 'media.volume_scale' modules/libpref/init/all.js   # expect "2.0" with signed comment
grep -c 'accept' intl/locale/language.properties   # expect 2 (en, en-us)
grep -nE 'disable-(crashreporter|updater|webspeech|necko-wifi)' patches/new.patches/05.PREFS/NEW_FILES/mozconfig   # expect all present
```

## Claim Sources

| Claim | Basis | Evidence |
|-------|-------|----------|
| GPU process off in both files (verified live) | 📄 stated in input | grep all.js/firefox.js layers.gpu-process.enabled=false |
| hardware_only_mode at StaticPrefList.yaml:12746 | 📄 stated in input | live grep line 12746 |
| captive-portal + safebrowsing effective ON via firefox.js override | 📄 stated in input | firefox.js:1373 / 3730-3731 vs all.js:4209 / 4210-4211 |
| Normandy neutralised + locked | 📄 stated in input | firefox.js.patch Normandy hunk (enabled false, api_url '', run_interval 1893456000) |
| language.properties trimmed to en/en-us (precheck P1 intentional) | 📄 stated in input | grep -c accept = 2; PRECHECK.md P1-001 |
| firefox.js single TODO is upstream Bug 2039835 (benign) | 📄 stated in input | firefox.js patch: '// TODO (Bug 2039835): Remove pref and cleanup deprecated code paths.' on browser.smartwindow.allowTables |
| No performance numbers measured | 🤖 model inference | *(none — model judgment)* |
| formautofill.useml + sqlite-lock removals not confirmed as intentional | 🤖 model inference | *(none — model judgment)* |


---
**How to verify this document:**
`📄 stated in input` — the model's phrasing of something your source text said.
Find the matching line in the original to verify.
`🤖 model inference` — the model's own judgment or synthesis. Treat as opinion,
not measurement. Re-run on the same input and check whether specific numbers
stay consistent between runs.


---

# ═══ MERGED DOCUMENT: 05-prefs.DEVELOPER.md (verbatim · sha256:5fa970d816526546 · merged 2026-08-04) ═══

# 05.PREFS — Build Recipe (mozconfig) + Preference Defaults (StaticPrefList.yaml / all.js / firefox.js) + accept-language trim

> Generated 2026-08-04 | Source: `05.PREFS`

---

## Purpose

The defaults-and-build layer of the Gorilla Unleashed Firefox 154 fork. It is the base of the pref-precedence stack (StaticPrefList < all.js < firefox.js < prefs.js < user.js (Topic 10) < policies.json (Topic 12)) and the compile recipe that removes subsystems outright. Trust level: it defines what the binary ships with; it does not itself enforce anything a later profile layer can override, except where prefs carry the `locked` attribute or a subsystem is compiled out.

## Design Rationale

Two deliberate patterns. (1) Vanilla-base + appended-GORILLA-override, resolved by last-write-wins: files reproduce upstream defaults and then re-set the targeted prefs lower in the same file, or in firefox.js which loads after all.js. This is intentional and MUST NOT be read as contradiction — e.g. all.js sets network.captive-portal-service and browser.safebrowsing.{malware,phishing} false, firefox.js re-sets them true; the effective values are ON. (2) Defence-in-depth for kill categories: telemetry / experiments / AI-ML / topsites / translations are turned off here AND locked here AND (for Normandy/Nimbus) neutered in Topic 12 code + hard-locked in policies.json, because no single upstream off-switch exists (mozconfig has no --disable-telemetry/-normandy).

## Architecture

- **Pattern:** Layered default-pref precedence (greprefs from all.js/StaticPrefList, then app-default firefox.js) + compile-time subsystem exclusion via mozconfig; last-write-wins resolution; `locked` attribute for irreversibility short of rebuild.
- **Trust boundary:** mozconfig removes outbound-capable subsystems (crashreporter, updater, default-browser-agent, necko-wifi, webspeech) so they cannot cross the network boundary — compile-out is stronger than runtime-disable. Prefs alone are trust-only-until-overridden unless `locked`.
- **Attack surface:** Reduced: fewer compiled subsystems; blackholed ad/suggestion endpoints (0.0.0.0 / 127.0.0.1); locked experiment channels close the remote-reconfig vector where a Normandy/Nimbus rollout could re-enable a dormant feature.
- **Dependencies:** `clang-21 / clang++-21`, `lld-21`, `sccache`, `ThinLTO`, `jemalloc`, `rust target-cpu=native`, `branding: browser/branding/gorilla`, `Topic 01 media codec gates (consume media.gorilla.hardware_only_mode)`, `Topic 10 user.js`, `Topic 12 policies.json`

## Flags & Configuration

| Name | Type | Default | Effect | Notes |
|------|------|---------|--------|-------|
| `media.gorilla.hardware_only_mode` | `RelaxedAtomicBool` | `true` | Master codec gate consumed by Topic 01 (StaticPrefs::media_gorilla_hardware_only_mode()). | Defined StaticPrefList.yaml:12746 (live tree). Prior docs cited 12681 — fabricated; real line is 12746. |
| `media.ffmpeg.disable-software-fallback` | `RelaxedAtomicBool` | `true` | No software decode fallback — enforces hardware-only path. | Vanilla default was false; StaticPrefList patch flips to true. |
| `media.av1.enabled` | `RelaxedAtomicBool` | `false` | AV1 off (Intel HD 4000 has no AV1 ASIC). | StaticPrefList.yaml:13306; also set false in all.js injection. |
| `media.navigator.mediadatadecoder_vpx_enabled` | `RelaxedAtomicBool` | `false` | Blocks a WebRTC VP8/VP9 bypass path around DefaultCodecPreferences.cpp. | StaticPrefList.yaml:13651 (inside #ifdef MOZ_WEBRTC). |
| `media.volume_scale` | `string` | `"2.0"` | Doubles master HTML5 media output level. | all.js:206. SIGNED + owner ear-validated 2026-08-03; do not 'restore to 1.0' without re-tuning the audio chain. |
| `toolkit.telemetry.enabled / unified / archive / *PingSender / bhrPing / newProfilePing / updatePing` | `bool` | `false (firefox.js: locked)` | Telemetry family off; firefox.js locks them. | all.js sets false; firefox.js re-sets false+locked (belt). |
| `app.normandy.enabled / api_url / run_interval_seconds` | `bool/string/int` | `false / "" / 1893456000 (all locked)` | Mozambique Drill: master off, endpoint blanked, 6h poll -> ~60y. | firefox.js patch. Reinforced by Topic 12. |
| `nimbus.rollouts.enabled + nimbus.*datastoreservice.* + nimbus.validation.enabled` | `bool` | `false, locked` | Nimbus experiment machinery off. | firefox.js patch; vanilla had these true. |
| `browser.ml.enable / browser.ml.chat.* / browser.smartwindow.* / browser.tabs.groups.smart.* / extensions.ml.enabled` | `bool/string` | `false / "" (locked)` | On-device AI/ML + AI-chat + Smart Window + Smart Tab Groups off; model endpoints blanked/0.0.0.0. | firefox.js patch; AI/ML kill mandate (2 GB target). |
| `browser.translations.enable / select.enable / quickAction.enabled` | `bool` | `false, locked` | Bergamot translations off (kill-category). | firefox.js patch. |
| `browser.newtabpage.activity-stream.feeds.topsites / showSponsored* / feeds.section.topstories / browser.urlbar.suggest.pocket|fakespot` | `bool` | `false, locked` | Entire Top Sites + Pocket/Fakespot recommendation engine killed, not just sponsored. | firefox.js patch; endpoints merino/spoc -> 0.0.0.0. |
| `signon.rustMirror.enabled / collectFailedOrigins` | `bool` | `false, locked` | Login-failure-origin collection surface off despite NIGHTLY_BUILD enabling it. | all.js: #ifdef NIGHTLY_BUILD sets true, then UNCONDITIONAL false+locked appended (ifdef-append method, last-write-wins). |
| `layers.gpu-process.enabled / force-enabled, media.gpu-process-decoder*` | `bool` | `false` | GPU process OFF (golden rule 1; Wayland black-window class). VA-API runs in RDD. | all.js injection (corrected true->false 2026-08-03); firefox.js:938,949. |
| `network.captive-portal-service.enabled` | `bool` | `true (effective)` | Captive-portal detection kept ON (café-wifi mission exception). | all.js:4209 false; firefox.js:1373 true wins. |
| `browser.safebrowsing.malware.enabled / phishing.enabled` | `bool` | `true (effective)` | Local malware/phishing lists kept ON; remote fetch off. | all.js:4210-11 false; firefox.js:3730-31 true wins. downloads.remote.enabled=false, provider.google4.gethashURL=''. |
| `intl.accept_languages / intl.multilingual.enabled / language.properties` | `string/bool/file` | `"en-US, en" / false / en+en-us only` | Fingerprinting defence: fixed accept-language, multilingual/trending off, locale list trimmed ~290 -> 2. | firefox.js patch + language.properties pure deletion. |
| `media.navigator.video.default_fps / max_fr` | `int` | `30` | WebRTC capture default 30fps. | firefox.js:3794. The prior 60 landmine + false QuickSync comment were removed. |

## API Surface

| Symbol | Description | Side Effects |
|--------|-------------|--------------|
| `media.gorilla.hardware_only_mode` | Mirror generated from the RelaxedAtomicBool YAML entry; read by Topic 01. | none (read-only mirror) |
| `greprefs.js load order` | Determines last-write-wins outcome for prefs set in both. | firefox.js overrides all.js for shared prefs |

## Kill Switches

### `StaticPrefList.yaml:12746 media.gorilla.hardware_only_mode`
- **Condition:** always (default true)
- **Effect:** Master toggle for Topic 01 codec gates.
- reversible
- about:config flip reverts codec policy without rebuild (not locked).

### `firefox.js `locked` attribute on telemetry/AI/Normandy/Nimbus/translations/tabgroups prefs`
- **Condition:** always
- **Effect:** Rejects writes from user.js/about:config/extensions.
- reversible
- Reversible only by editing source + rebuild.

### `mozconfig --disable-* (crashreporter, updater, webspeech, necko-wifi, parental-controls, default-browser-agent, accessibility, tests)`
- **Condition:** compile-time
- **Effect:** Subsystems not in the binary.
- reversible
- Requires rebuild to reverse; EME/WebRTC/safe-browsing explicitly KEPT (mozconfig lines 62-66).

### `firefox.js app.normandy.run_interval_seconds=1893456000 (locked)`
- **Condition:** always
- **Effect:** Experiment poller effectively never fires (~60y).
- reversible
- Mozambique Drill 'Headshot'; belt with enabled=false + api_url blank.

## Dead Code

- **`all.js:4209 network.captive-portal-service.enabled=false`** — overridden by firefox.js:1373 (true) (risk: Removing it is safe (net value unchanged); leaving it is a grep-only readability trap.)
- **`all.js:4210-4211 browser.safebrowsing.{malware,phishing}.enabled=false`** — overridden by firefox.js:3730-3731 (true) (risk: Same as above — dead but harmless; net ON.)

## Performance

- **CPU:** -O3 -march=native -mtune=native + ThinLTO + PGO pipeline (mozconfig 5-7). Faster on this exact CPU vs generic; not benchmarked topic-locally.
- **MEMORY:** jemalloc with tuned MALLOC_CONF (narenas:8, dirty_decay_ms:5000, tcache); disk cache disabled, 1 GiB memory cache (firefox.js browser.cache.memory.capacity 1048576 KiB); AI/ML model loading off. Reference machine 16 GiB UMA-shared; distribution audience ~4 GB — the reason heavy features are cut. Not benchmarked.
- **IO:** Removed subsystems open no sockets/threads; DNS prefetch off; telemetry/experiment uploads gone. Steady-state IO reduced; not measured.
- **NOTES:** PGO/-O3 caveat: mozconfig section 7 warns the profile-guided pass may override -O3 and to switch section 5 to -O2 if -O3 regresses — not verified either way.

## Security

- **Remote execution:** No new remote-exec surface introduced. Experiment/rollout remote-reconfig vectors (Normandy/Nimbus) are closed by locked prefs + blanked endpoints.
- **Data handling:** Telemetry/experiment/AI/ads egress cut; local malware/phishing lists retained (privacy-preserving); accept-language fixed to reduce fingerprint entropy.
- **Attack surface:** Narrowed by compile-out (crashreporter is a historical CVE breeding ground) and by blackholing suggestion/ad endpoints.
- **Notes:** Two vanilla lines were removed rather than re-set and their intent is not independently confirmed: security.storage.encryption.sqlite.enabled `locked,false` (all.js) — pref still defined at StaticPrefList.yaml:19153 but now UNLOCKED; and extensions.formautofill.useml — now unset everywhere (reverts to code default rather than an explicit off). See technical_debt.

## Error Conditions

| Error | Cause | Remedy |
|-------|-------|--------|
| `Black window on Wayland (ERROR 9 class)` | GPU process enabled on Wayland | layers.gpu-process.enabled stays false — already enforced in both files. |
| `DesktopActorRegistry getBoolPref threw (browser.ml.chat.shortcuts.smartwindow)` | missing default for a pref the actor reads | firefox.js defines it explicitly (false, locked) — see patch comment at that line. |
| `Binary crashes on a non-Ivy-Bridge CPU` | -march=native emits instructions absent on other CPUs | Rebuild without -march=native for portability (mozconfig section 5). |

## Tasks

### Verify the load-bearing pref semantics against the tree

Confirm the effective (last-write-wins) values, not just the patch hunks.

**Prerequisites:**
- FF_SRC=the source tree
- ripgrep/grep

**Step 1:** grep -n 'network.captive-portal-service.enabled' modules/libpref/init/all.js browser/app/profile/firefox.js
  - Expected: all.js false (x2), firefox.js:1373 true -> effective ON.
**Step 2:** grep -n 'browser.safebrowsing.\(malware\|phishing\).enabled' modules/libpref/init/all.js browser/app/profile/firefox.js
  - Expected: all.js false, firefox.js:3730-31 true -> effective ON; remote fetch off.
**Step 3:** grep -n 'layers.gpu-process.enabled' modules/libpref/init/all.js browser/app/profile/firefox.js
  - Expected: false in both (golden rule 1).
**Step 4:** grep -n 'media.gorilla.hardware_only_mode' modules/libpref/init/StaticPrefList.yaml
  - Expected: line 12746, value true.

**After this task:** Effective values match the documented kill-category doctrine; no unexpected GPU-process enablement.

### Regenerate a patch after editing the source

The .patch files in the topic folder are the shipped artifact; keep them byte-current with the tree.

**Prerequisites:**
- A clean vanilla FF154 baseline for diffing
- The edited live file

**Step 1:** Diff edited file against the vanilla baseline and write to the topic .patch (a/ b/ headers).
  - Expected: Hunk offsets match the current tree (firefox.js.patch is 1008 lines as of 2026-08-04).
**Step 2:** Re-run dual-track precheck on the topic dir.
  - Expected: No new P0; the language.properties pure-deletion P1 and the firefox.js TODO P2 are known/benign.

**After this task:** Patch and tree agree; docs regenerated.

## Troubleshooting

**Symptom:** A pref reads as ON despite all.js setting it OFF
**Cause:** firefox.js re-sets it later (last-write-wins).
**Remedy:** Check firefox.js for the final value; treat all.js as the base layer.
**Verify:** grep both files; the firefox.js occurrence is authoritative.

**Symptom:** An AI/ML surface appears active
**Cause:** A newly-added upstream pref not yet covered by the kill block.
**Remedy:** Add pref(name,false,locked) in the firefox.js GORILLA block; consider a Topic 12 policies.json lock.
**Verify:** about:config shows the pref false+locked.

**Symptom:** Locked pref cannot be changed for debugging
**Cause:** The `locked` attribute rejects all writes.
**Remedy:** Temporarily remove `locked` in source and rebuild, or use policies unlock dance where applicable.
**Verify:** about:config allows the edit.

## Technical Debt

🟡 **LOW** — all.js:4209-4211 dead captive-portal/safebrowsing false lines (overridden by firefox.js). Grep-only readers can be misled. → Add an inline comment at those lines noting they are overridden ON by firefox.js, or drop them; net value is unchanged either way.
🟡 **LOW** — extensions.formautofill.useml override removed from all.js; pref now unset everywhere, reverting to the C++ code default instead of an explicit off. Conflicts with the AI/ML-off mandate if the code default is on. → If belt-and-suspenders is wanted, add pref('extensions.formautofill.useml', false, locked). First confirm the code default (not verified).
🟡 **LOW** — security.storage.encryption.sqlite.enabled `locked,false` removed from all.js; still defined at StaticPrefList.yaml:19153 but now UNLOCKED. Intent (deliberate unlock vs rebase artifact) not confirmed. → Confirm intended behaviour against the SOP/lesson; re-add the lock if unlocking was unintended.
🟡 **LOW** — mozconfig header comments are stale (Firefox Nightly 153+, kernel 7.0.9-unleashed) vs the current 154 build / 7.1.2 kernel. → Refresh the header block; comment-only, no build impact.
🟡 **LOW** — mozconfig PGO vs -O3 interaction is flagged but unresolved (section 7). → Profile once; if -O3 regresses under PGO, switch section 5 to -O2 and re-profile. Not verified.

## Impact If Removed

Revert mozconfig -> generic non-optimised build with crashreporter/updater/webspeech/etc. re-compiled in; larger attack surface. Revert StaticPrefList changes -> media.gorilla.hardware_only_mode undefined, so Topic 01's gates read an absent pref (dead code / fail path) and AV1/VP9 hardware defaults return to true. Revert all.js -> telemetry family and media.volume_scale return to stock, GPU-process correction lost (black-window risk), rustMirror collection re-enabled on nightly. Revert firefox.js -> Normandy/Nimbus/AI/translations/topsites/pocket re-enable, telemetry locks drop, captive-portal and local safebrowsing overrides vanish (all.js false would then win -> both OFF). Revert language.properties -> ~290-locale accept list returns (fingerprint entropy up).

## Claim Sources

| Claim | Basis | Evidence |
|-------|-------|----------|
| media.gorilla.hardware_only_mode default true at StaticPrefList.yaml:12746 | 📄 stated in input | live grep StaticPrefList.yaml:12746 |
| captive-portal effective ON via firefox.js:1373 over all.js:4209 | 📄 stated in input | grep all.js:4209 false; firefox.js:1373 true |
| safebrowsing malware/phishing effective ON via firefox.js:3730-31; remote fetch off | 📄 stated in input | grep firefox.js:3730-3731 true; patch downloads.remote.enabled false, gethashURL '' |
| GPU process off in both files, corrected 2026-08-03 | 📄 stated in input | all.js injection comment 'corrected 2026-08-03 — golden rule 1'; firefox.js:938 |
| Normandy Mozambique Drill: enabled false / api_url '' / run_interval 1893456000, all locked | 📄 stated in input | firefox.js.patch hunk @@ Normandy client preferences |
| media.volume_scale 2.0 signed and owner-validated | 📄 stated in input | all.js:206 + GORILLA OVERRIDE comment block |
| privacy.wallet_schemes relocated all.js -> firefox.js:1306 (same value) | 📄 stated in input | all.js patch removes it; firefox.js:1306 present |
| extensions.formautofill.useml now unset everywhere | 📄 stated in input | live grep of all.js/firefox.js/StaticPrefList returns no match |
| security.storage.encryption.sqlite.enabled still defined but all.js lock removed | 📄 stated in input | StaticPrefList.yaml:19153 present; all.js patch removes the locked,false block |
| mozconfig keeps EME/WebRTC/safe-browsing, disables crashreporter/updater/webspeech/necko-wifi | 📄 stated in input | NEW_FILES/mozconfig sections 9 and 62-66 |
| Performance not benchmarked topic-locally | 🤖 model inference | *(none — model judgment)* |


---
**How to verify this document:**
`📄 stated in input` — the model's phrasing of something your source text said.
Find the matching line in the original to verify.
`🤖 model inference` — the model's own judgment or synthesis. Treat as opinion,
not measurement. Re-run on the same input and check whether specific numbers
stay consistent between runs.

*Auto-generated DITA-structured developer documentation.*


---

# ═══ MERGED DOCUMENT: 05-prefs.LAYMAN.md (verbatim · sha256:6be1beaae1f30636 · merged 2026-08-04) ═══

# The Browser's Factory Settings — How Firefox Is Built and What It Switches On by Default — Plain Language Guide

> Generated 2026-08-04 from `05.PREFS`

---

## Should You Run This?

Yes — if you are the intended user: an older Intel laptop, Wayland/GNOME, wanting telemetry and AI-clutter gone with local protections kept. Do NOT copy the compiled binary to a different CPU; rebuild instead. If you need Firefox's experiments, AI features or sponsored suggestions, this build is deliberately not for you.

## Worst Case, Honestly

Two honest ones. (1) The build is compiled for one exact CPU family (Ivy Bridge). Copy the finished binary to a computer with a different processor and it can simply crash on start — this build is not portable, and the recipe says so. (2) Because so many switches are moved and some are locked, a website feature you expected (an experiment, an AI helper, a sponsored tile) is silently absent. Nothing is broken; it was turned off on purpose. Neither outcome loses your data.

## What Data This Touches

The direction of travel is: cut the things that phone home, keep the things that protect you locally. Telemetry, Normandy/Nimbus experiments, AI/ML features, sponsored 'top sites', and Pocket recommendations are turned off (many of them locked). Several advertising and suggestion endpoints are pointed at dead addresses (0.0.0.0, or 127.0.0.1 for the language-pack URL) so requests go nowhere. What is deliberately KEPT ON: the local malware/phishing blocklist (the list is downloaded and checked on your machine; the parts that would send a URL to Google are switched off), and captive-portal detection (so café and airport wi-fi login pages still work — a deliberate exception for the people this build is for). No performance numbers were measured, so none are claimed here.

## Before You Trust It

You do not have to read all four files. A handful of greps confirms the load-bearing claims: the hardware-only master switch exists, telemetry is off, and the GPU process is disabled (the black-window safety rule).

**Step 1:** grep -n 'media.gorilla.hardware_only_mode' modules/libpref/init/StaticPrefList.yaml
  - Look for: A definition around line 12746 with value: true. That is the master codec switch.
**Step 2:** grep -n 'layers.gpu-process.enabled' modules/libpref/init/all.js browser/app/profile/firefox.js
  - Look for: false in both files — the GPU process stays off on Wayland (prevents the black-window failure).
**Step 3:** grep -n 'toolkit.telemetry.enabled' modules/libpref/init/all.js browser/app/profile/firefox.js
  - Look for: false (firefox.js also says 'locked'). Telemetry is off and cannot be toggled back.
**Step 4:** grep -n 'network.captive-portal-service.enabled' browser/app/profile/firefox.js
  - Look for: true around line 1373 — captive-portal detection is deliberately kept on, overriding all.js.

## The Big Picture

This folder decides two things about the browser before you ever open it. First, the recipe it was built from (a file called mozconfig): which compiler, which optimisations, and which whole features get physically left out of the program — a crash reporter, an auto-updater, a text-to-speech engine, and a few others are never compiled in, so they cannot run at all.

Second, the starting position of thousands of switches (the preference files all.js, firefox.js, StaticPrefList.yaml, and one small language list). Every setting in Firefox has a factory default that Mozilla chose. This folder re-chooses a large number of them for a specific kind of user: someone on an old laptop and a weak connection who does not want telemetry, ads dressed up as 'suggestions', or AI features bolted on for a market that isn't them.

Everything here is a DEFAULT. Later folders (a user.js in Topic 10, a policies.json in Topic 12) can still override or hard-lock a subset. Think of this as how the machine leaves the factory, before anyone takes it home.

## Key Concepts

| Name | What It Means | Real-World Comparison |
|------|--------------|------------------------|
| `mozconfig` | the build recipe — how the browser is compiled and what is left out | a recipe card for one specific cake in one specific oven, with 'skip the frosting entirely' written in |
| `Preference (pref)` | one labelled switch inside the browser with an on/off or a value | a light switch on a very large switchboard; each one is small, together they decide what the building does |
| `locked pref` | a switch glued in place — not even you at about:config can move it without a rebuild | a switch with a plastic cover screwed over it |
| `last-write-wins` | when two files set the same switch, the one loaded last decides the final value | two people writing on the same whiteboard — the second one's answer is what stays |
| `media.gorilla.hardware_only_mode` | the master switch that tells the Media parts of the browser to only use the chip's built-in video decoder | the big lever on the control panel labelled 'hardware only' |

## How It Works — Step by Step

### Step 1: The recipe leaves parts out

mozconfig compiles the browser with clang-21 at -O3 tuned for this exact chip (-march=native), links it with ThinLTO, and uses the jemalloc memory allocator. It also passes --disable-crashreporter, --disable-updater, --disable-webspeech and others, so those subsystems are never built. You cannot leak through a reporter that does not exist. It deliberately KEEPS the DRM module (so Netflix works), WebRTC (so video calls work) and safe-browsing (protection). It is like baking the cake without the candles moulded in — not blown out later, never added.

### Step 2: The master pref registry sets code-level defaults

StaticPrefList.yaml is the built-in list of prefs. This build adds one new pref, media.gorilla.hardware_only_mode (default true), which the Media folder reads at every video-codec decision, and flips AV1 and WebRTC VP8/VP9 hardware-decode defaults to false to match. It is the switchboard wired at the factory before any app-level file gets a say.

### Step 3: all.js — platform defaults and the 'telemetry starvation' block

all.js is loaded first among the app-default files. It sets the audio output level (media.volume_scale 2.0 — a deliberate, ear-checked choice, not a mistake), hard-disables the telemetry family, and appends a GORILLA injection block: GPU acceleration hints, a corrected GPU-process-OFF setting (a black-window landmine that was fixed on 2026-08-03), and a purge of AI and sponsored-tile features. Some lines here are later overridden by firefox.js — that is intended.

### Step 4: firefox.js — the browser's own defaults, loaded last, so it wins

Because it loads after all.js, firefox.js has the final say on any pref both files set. It re-enables the LOCAL malware/phishing blocklist that all.js had switched off, and keeps captive-portal detection on, while pointing ad and 'suggestion' endpoints at 0.0.0.0. It applies the Mozambique Drill to Normandy (master switch off, endpoint blanked, the 6-hour poll timer stretched to ~60 years) and locks the telemetry, AI/ML, translations, tab-groups and Nimbus switches so they cannot be flipped back on. A large 'validated additions' block tunes cache, network pacing and codecs.

### Step 5: One tiny language file trims the fingerprint

intl/locale/language.properties used to list ~290 language tags as acceptable; it is cut to just English (en and en-us). Paired with firefox.js forcing intl.accept_languages to 'en-US, en', this stops the browser advertising a long, distinctive language list that websites can use to fingerprint you.

## Quirky Things Worth Knowing

### The same switch is set twice on purpose

You will find, for example, captive-portal detection set to false in all.js and to true in firefox.js, and the malware blocklist set false then true. This is NOT a bug or a contradiction — files load in order and the last one wins. all.js is the base; firefox.js is the correction layer. The net result (captive portal ON, local malware list ON) is the intended one. Reading only one file would mislead you.

### A dead switch left where you can see it

Because of last-write-wins, the false captive-portal line in all.js never takes effect. It is harmless, but if you grep only all.js you might think the feature is off. Always check firefox.js for the final word.

### Louder-than-normal audio is deliberate

media.volume_scale is 2.0, double the stock 1.0. That looks wrong until you read the comment: the whole audio chain was tuned WITH this doubling in place and ear-checked on the reference speakers. Resetting it to 1.0 without re-tuning would make everything too quiet.

### Telemetry isn't removed by the recipe — it's starved

You might expect a --disable-telemetry flag in mozconfig. There isn't one; Firefox doesn't offer it. Instead telemetry is 'starved': compile-time GLEAN_DISABLED, a 60-year timer on the experiment runner, locked prefs, and a runtime policies.json. Belt and suspenders because no single off-switch exists.

## What This Means For You

### Battery, Processor & Memory

Not measured. The direction is lower: subsystems that were never compiled in cannot run background threads; disk cache is disabled in favour of a 1 GB memory cache; AI/ML features that would load models are off. The reference machine has 16 GiB (shared with the GPU); the distribution audience runs ~4 GB, which is why the AI/ML and heavy features are cut. No before/after CPU or RAM figure is claimed.

### Speed

Not measured as a number. A -O3/-march=native/LTO build produces faster code for this one CPU than a generic build, and fewer startup subsystems means less to load. No benchmark is asserted here.

### Your Privacy

This is where most of the privacy posture lives: telemetry, experiments, AI, sponsored tiles and Pocket are default-off, many locked; ad/suggestion endpoints are blackholed. Local protection (malware/phishing list, tracking protection, HTTPS-only) is kept on.

### Your Internet

Fewer background connections: no telemetry uploads, no experiment polling, no contile ad fetch, DNS prefetch off. Captive-portal detection stays, so café wi-fi still works. Not measured as bytes saved.

## The Off Switch

**What it is:** The whole folder is a panel of kill switches. The single most important one is media.gorilla.hardware_only_mode (StaticPrefList.yaml line 12746, default true), which the Media folder reads at every codec gate. The 'locked' keyword on many prefs (telemetry, AI, Normandy, tab groups) is a second kind of kill switch: it refuses changes from about:config, user.js, or extensions.

**Without it:** Remove media.gorilla.hardware_only_mode and every codec gate in the Media folder loses its master control. Remove the locked prefs and a remote experiment or a stray user.js could switch telemetry or AI features back on.

**Think of it like:** A breaker panel. Each breaker is small; together they decide what has power when you walk in. The locked ones have a padlock through the switch.

## See these defaults in the running browser

**Before you start:**
- A built Gorilla Unleashed Firefox 154
- The address bar

**Step 1:** Open about:config and search media.gorilla.hardware_only_mode
  - You should see: It shows true. (It will refuse to matter unless the Media codec gates are present.)
**Step 2:** Search app.normandy.run_interval_seconds
  - You should see: 1893456000 (~60 years) and locked — the experiment poller effectively never runs.
**Step 3:** Open about:preferences and look at Firefox Suggest / Sponsored suggestions
  - You should see: Off by default; the sponsored/quicksuggest toggles are locked off.

## If Something Goes Wrong

**The browser crashes immediately on a different computer**
It was compiled for one exact CPU family (-march=native). Another machine's processor lacks the instructions.
What to do: Rebuild with a portable optimisation flag (e.g. -O2 without -march=native), or run the build only on the machine it was made for.

**A feature you wanted (an AI helper, a suggested site) is simply gone**
It was turned off on purpose here, and often locked.
What to do: If it is not locked, set it in user.js (Topic 10). If it is locked, it needs a rebuild — that is by design.

**Audio is much louder than other browsers**
media.volume_scale is 2.0, a deliberate, ear-checked choice.
What to do: Lower your system volume. Do not reset the pref to 1.0 without re-tuning the whole audio chain.

## Why a Developer Would Do This

A developer moves these defaults because the stock ones are chosen for Mozilla's average user and Mozilla's business, not for a kid on a 4 GB laptop and metered wi-fi. The choices are consistent: convenience-for-you (password manager, malware list, captive-portal) is kept; convenience-for-Mozilla (telemetry, experiments, ad tiles) is cut. And they are written down so you can disagree with any single one and see exactly where to change it.

## Why It Matters That You Can Read This

Every default here is a line of plain text you can read and grep. The reasons are written next to the switches ('TELEMETRY STARVATION', 'Mozambique Drill', 'corrected 2026-08-03 — golden rule 1'). A closed browser has thousands of defaults you must take on trust; here, 'what does it turn on when I first run it?' is one grep away, and so is 'why?'. That readability is the point — it is how a non-expert, or a suspicious expert, can verify the build is doing what it claims instead of trusting a marketing page.

## Glossary

**mozconfig** — The build recipe: compiler, optimisations, and which whole features to leave out.

**preference (pref)** — One named setting in the browser with a value or on/off state.

**locked pref** — A pref that refuses changes from about:config, user.js, or extensions without a rebuild.

**last-write-wins** — When two default files set the same pref, the file loaded later decides the value.

**-march=native** — Compiler flag meaning 'build for the exact CPU I'm compiling on' — faster here, may crash elsewhere.

**LTO** — Link-Time Optimization: the compiler optimises across the whole program at link time.

**telemetry** — Usage and diagnostic data a browser can send back to its maker; off in this build.

**captive portal** — The login page café/airport wi-fi shows before you get internet; detection is kept on.

**0.0.0.0 / 127.0.0.1** — Dead addresses; pointing an endpoint here makes its requests go nowhere.

## Claim Sources

| Claim | Basis | Evidence |
|-------|-------|----------|
| media.gorilla.hardware_only_mode is defined default true at StaticPrefList.yaml line 12746 | 📄 stated in input | live tree grep: modules/libpref/init/StaticPrefList.yaml:12746:- name: media.gorilla.hardware_only_mode |
| media.volume_scale is 2.0, a deliberate ear-validated choice | 📄 stated in input | all.js patch: 'GORILLA OVERRIDE: media.volume_scale 2.0 is a DELIBERATE output-level choice ... owner ear-validated'; live all.js:206 |
| GPU process stays off in both files (golden rule 1) | 📄 stated in input | all.js patch: 'layers.gpu-process.enabled', false + comment 'corrected 2026-08-03 — golden rule 1'; firefox.js:938 |
| Captive-portal detection is kept on via firefox.js overriding all.js | 📄 stated in input | live firefox.js:1373 network.captive-portal-service.enabled true; all.js:4209 false |
| Local malware/phishing blocklist kept on; remote parts off | 📄 stated in input | firefox.js:3730-3731 malware/phishing true; firefox.js patch: browser.safebrowsing.downloads.remote.enabled false, provider.google4.gethashURL '' |
| Normandy neutralised: enabled false, api_url '', run_interval ~60 years, locked | 📄 stated in input | firefox.js patch: app.normandy.enabled false locked; api_url '' locked; run_interval_seconds 1893456000 locked |
| Language list cut to English only | 📄 stated in input | language.properties applied file has exactly en.accept and en-us.accept; firefox.js patch intl.accept_languages 'en-US, en' |
| mozconfig compiles -O3 -march=native, ThinLTO, jemalloc, and disables crashreporter/updater/webspeech | 📄 stated in input | NEW_FILES/mozconfig sections 5,6,11 and 9 (--disable-crashreporter/--disable-updater/--disable-webspeech) |
| No performance numbers were measured | 🤖 model inference | *(none — model judgment)* |


---
**How to verify this document:**
`📄 stated in input` — the model's phrasing of something your source text said.
Find the matching line in the original to verify.
`🤖 model inference` — the model's own judgment or synthesis. Treat as opinion,
not measurement. Re-run on the same input and check whether specific numbers
stay consistent between runs.

*Human Track. Its Developer Track twin covers the same changes in technical detail. Neither is a simplified copy of the other — they are the same truth in two languages.*


---

# ═══ MERGED DOCUMENT: 05-prefs.PRECHECK.md (verbatim · sha256:6f7261624eab6cb8 · merged 2026-08-04) ═══

# Offline Pre-Check: 05-prefs

*Generated 2026-08-04 07:04:52 by rules only. No model was involved, so everything below is a deterministic finding about the files as they are on disk.*

## Files Scanned

| File | Language | Lines | Code | Complexity | SHA-256 |
|---|---|---|---|---|---|
| `audit-lists/apply_step2.py` | py | 112 | 95 | 34 | `afdb9051d8724a24` |
| `audit-lists/classify_absent.py` | py | 181 | 155 | 30 | `892320b8b3baa13c` |
| `audit-lists/run_audit.py` | py | 112 | 92 | 27 | `6623b217d4f753fe` |
| `audit-lists/step3_values.py` | py | 105 | 86 | 26 | `41245ee95120efa2` |
| `browser_app_profile_firefox.js.patch` | patch | 1008 | 759 | 47 | `afaab2a185917a66` |
| `intl_locale_language.properties.patch` | patch | 293 | 290 | 1 | `925b16aa29233bd4` |
| `modules_libpref_init_StaticPrefList.yaml.patch` | patch | 275 | 200 | 28 | `0e6501e731c052c1` |
| `modules_libpref_init_all.js.patch` | patch | 237 | 201 | 8 | `ffa8bff656efd167` |

## Findings

🔴 P0: 0 · 🟠 P1: 1 · 🟡 P2: 1 · 🟢 P3: 0

### 🟡 P2-001 — P2

- **Plain English:** A sticky note saying 'finish this later' was left inside the machine. It still works, but somebody meant to come back to it.
- **Technical:** browser_app_profile_firefox.js.patch: 1 TODO/FIXME/XXX/HACK marker(s) in added lines.
- **Fix:** Resolve it, or convert it into a tracked item so it is visible outside the source.

### 🟠 P1-001 — P1

- **Plain English:** A repair instruction that removes things but adds nothing. Worth checking it is meant to be a deletion.
- **Technical:** intl_locale_language.properties.patch: targets intl/locale/language.properties with no added lines.
- **Fix:** Confirm this is an intentional pure deletion.

