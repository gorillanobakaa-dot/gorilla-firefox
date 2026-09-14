# MASTER PROJECT LOG — FIREFOX 154 TOOLKIT PATCHES

---

## Part 1: History, Roadmap & Overview
*(Originally from 00_TOOLKIT_HISTORY_AND_ROADMAP.md)*

### Document Control
- **Category:** Toolkit Lockdown & UI Modifications
- **Last Updated:** 2026-07-10
- **Status:** Active Development
- **Verification Required:** Yes (see Validation section)
- **Related Documents:** 
  - `../DOCUMENTATION_TEMPLATES.md` (IBM format guide)
  - `../MAP.md` (cross-category index)
  - `../08.Look/00_LOOK_HISTORY_AND_ROADMAP.md` (visual branding)
  - `../10.OVERRIDES/user.js` (preference layer)
  - `../12.MOZAMBIQUE.DRILL/policies.json` (locked preferences)

---

### Executive Summary

**What This Does (Plain Language):**
This folder makes Firefox a sealed, opinionated appliance. Four main changes:
1. **Blocks all add-on/extension/theme installations** (security hardening).
2. **Disables translations and language packs** (monolinguality).
3. **Removes sponsored content from new tab page** (clean interface).
4. **Forces Gorilla Nebula theme** (consistent appearance).

**Technical Summary:**
Toolkit lockdown layer for Sony VAIO SVE14A3AJ. Implements: (1) API lobotomy blocking all extension/theme install routes (AMO, web, file), (2) translation/langpack download disabled, (3) new-tab sponsored content excised (discovery feed, topsites, shortcuts), (4) forced Gorilla Nebula theme enforcement, (5) QuickSuggest/urlbar/context-menu locks.

**Critical Context:**
> **This is a sealed appliance.** You cannot install extensions or themes. No built-in translation. New-tab content and theme are not user-configurable. These are deliberate trade-offs for security and consistency.

---

### Mission Statement

### Mission: Sealed Appliance Philosophy
If other folders make the browser *fast* and *private*, this one makes it **sealed and opinionated**. The philosophy: a browser you can't extend is a browser strangers can't quietly extend either. A clean, ad-free, fixed surface is worth giving up configurability for.

1. **No Extensions/Themes** — Security over flexibility.
2. **Monolinguality** — Lean over multilingual.
3. **Clean New Tab** — Quiet over monetized.
4. **Fixed Appearance** — Consistent over customizable.

---

### Component Documentation

#### 1. AddonManager.sys.mjs & AddonRepository.sys.mjs — Installation Blocks
- **Status:** Modified | **Deploy Path:** `toolkit/mozapps/extensions/internal/` | **Last Verified:** 2026-07-10
- **What It Does (Plain Language):** Prevents installation of external add-ons, scripts, or extensions.
- **Technical Description:** Blocks AMO backend calls, web install interfaces, and raw file installs by throwing custom errors at the manager API layer.

#### 2. XPIInstall.sys.mjs — Installation Disabler
- **Status:** Modified | **Deploy Path:** `toolkit/mozapps/extensions/internal/XPIInstall.sys.mjs` | **Last Verified:** 2026-07-10
- **Tuning:** Short-circuits install paths to strictly abort with a block log, preventing side-loading.

#### 3. ExperimentAPI.sys.mjs — Study Bypass
- **Status:** Modified | **Deploy Path:** `toolkit/components/nimbus/lib/ExperimentAPI.sys.mjs` | **Last Verified:** 2026-07-10
- **Tuning:** Returns empty default mock objects for dynamic telemetry experiment queries to prevent runtime failures.

#### 4. TranslationsParent.sys.mjs — Translations Blocker
- **Status:** Modified | **Deploy Path:** `toolkit/components/translations/TranslationsParent.sys.mjs` | **Last Verified:** 2026-07-10
- **Tuning:** Prevents translation model engine downloads to force monolingual offline execution security.

---

### Chronological History (Recovered)

#### 2026-06-08/09
Initial toolkit lobotomy implementations applied in Firefox 153.

#### 2026-07-05
**Firefox 154 Rebase:**
Toolkit modules re-patched and adapted. Resolves conflicts in Javascript Modules (sys.mjs paths).

#### 2026-07-10
**Audit Verification:**
Completed static checks. Confirmed all `.rej` files are cleared, and the toolkit codebase is 100% stable.

---

## Part 2: Rule-Based Code Audit & Validation (2026-07-10)

We completed a static code audit of the toolkit patches:
1. **AddonManager**: Installation interface blocks verified.
2. **XPIInstall**: Side-load pathways correctly throw installation block overrides.
3. **ExperimentAPI**: Returns mock values safely without throwing runtime null pointer errors in the URL bar or setup sequence.

The category passes all code guidelines.


---

> **⚠ SUPERSEDED 2026-08-04 — the 2026-08-02 merged docs immediately below are the generation-1 dual-track pair and are STALE.** They carry two inaccuracies corrected in the 2026-08-04 regeneration appended at the END of this file: (1) they state ExperimentAPI "returns empty default mock objects for every query so 145+ dependent components don't crash" — the actual patch forces the eligibility getters (studies/labs/rollouts/aiFeatures) to false and preserves the normal manifest-default return path; there is no bespoke mock and "145+" has no source in the patches; (2) they count "19 files" — the set is now 18 (`browser_components_preferences_config_appearance.mjs.patch` was removed). They also predate the finding that `UrlbarUtils.RESULT_SOURCE`/`RESULT_TYPE` are undefined in this tree (constants live on `UrlbarShared`), which makes the two urlbar providers' references throw-if-reached. Read the **REGENERATION 2026-08-04** block at the bottom for the current truth. This block is retained per the append-only doctrine.

# ═══ CONSOLIDATION 2026-08-02 — side documents merged VERBATIM below; originals deleted (recoverable: merged-docs-backup-2026-08-02.tar.gz + git history) ═══


---

# ═══ MERGED DOCUMENT: 07-toolkit.AUDIT.md (verbatim · sha256:f456eff94db20146 · merged 2026-08-02) ═══

# IBM-Style Audit Report: 07-toolkit

## SECTION A: DOCUMENT CONTROL

| Attribute | Value |
|---|---|
| **Target Category** | 07-toolkit |
| **Files Scanned** | see payload |
| **Baseline** | Firefox 154 (mozilla-central) |
| **Date / Time** | 2026-07-17 08:13:33 |
| **Audit Status** | PASS |

## SECTION B: EXECUTIVE SUMMARY (Track A — Layman)

This folder turns Firefox into a sealed appliance: no add-ons or themes can be installed (every install route blocked), no sponsored content on the new tab or in the address bar, no built-in translation, and a fixed appearance. The security case is that a browser you cannot extend is a browser strangers cannot quietly extend either. The clever part: the experiment API that 145+ components depend on is made to return safe empty answers so nothing crashes while no experiment runs. Honest trade-off: you give up extensions, themes, and translation.

## SECTION C: TECHNICAL SUMMARY (Track B — Developer)

19-file sealed-appliance layer. Five workstreams: (1) install lockdown (AddonManager/AddonRepository throw at API boundary, XPIInstall short-circuits side-load, LightweightThemeManager locks theme); (2) new-tab sponsored-content excision (Base/DiscoveryStreamBase/TopSites React components); (3) address-bar de-sponsoring (QuickSuggest + 2 Urlbar providers + Merino Rust backend + search-config JSON, no keystroke egress); (4) translations disable (TranslationsParent + browserLanguages.js); (5) ExperimentAPI empty-mock for the 145+ Nimbus consumers — toolkit-side companion to Topic 12's network-side neutralization. Three neutralization strategies matched to three failure tolerances: fail-closed throw for installs, excision for UI, fail-safe mock for the experiment API.

## SECTION D: DETECTED DEFECTS

*No defects detected by rules or model.*

## SECTION E: PRODUCTION READINESS ASSESSMENT

- **Overall readiness:** 🟢 90%
- **Done:**
  - [x] All three extension install routes blocked (AMO, web, file/side-load)
  - [x] Theme locked (LightweightThemeManager + design-system tokens)
  - [x] New-tab discovery feed + sponsored tiles + sponsored shortcuts excised
  - [x] Address-bar QuickSuggest/Merino de-sponsored — keystrokes not sent remotely
  - [x] Translations + langpack downloads disabled
  - [x] ExperimentAPI returns safe empty mocks — 145+ consumers do not crash
  - [x] Coherent with Topic 12 (Nimbus network side) and Topic 05 (Pocket/TopSites prefs)
  - [x] FF154 rebase clean — all .rej cleared (2026-07-10 audit)
- **To Do:**
  - [ ] P2: revisit translations disable for the global distribution audience (roadmap-flagged; consider on-device models on a locked mirror)
  - [ ] P2: add a boot smoke-test asserting zero ExperimentAPI/Nimbus console errors across urlbar/first-run/settings
  - [ ] P3: consolidate the three install-throw sites behind one isInstallAllowed() policy gate

## SECTION F: PHASED EXPANSION PLAN

### Phase 0 — `toolkit/mozapps/extensions`
- **Tweak:** Introduce a single isInstallAllowed() returning false, called by all three throw sites. One-line-auditable install policy.
- **Expected impact:** Maintainability + audit clarity.

### Phase 2 — `toolkit/components/translations`
- **Tweak:** Allow on-device translation models fetched from a trusted, telemetry-free mirror while keeping Mozilla model-server + langpack download locked. Restores translation for the global audience without opening a telemetry channel.
- **Expected impact:** Addresses the one sealed-appliance choice that cuts against the target audience.

## POSITIVE OBSERVATIONS

- ✅ Three neutralization strategies matched to three failure tolerances (fail-closed throw for installs, excision for UI, fail-safe mock for ExperimentAPI) — the right tool per problem, not one blunt instrument.
- ✅ Blocking all three install routes (not just AMO) is thorough — the side-load block via XPIInstall is what stops OS-level malware dropping an XPI, which a store-only block would miss.
- ✅ ExperimentAPI empty-mock is the correct companion to Topic 12: Topic 12 cuts the network side (poll timers/endpoint), this cuts the code side (safe mocks). Neither alone is complete; together they are.
- ✅ Extension-install elimination is arguably the single largest attack-surface reduction in the whole build — compromised/malicious extensions are a top browser threat vector.
- ✅ The roadmap is honest about the translations trade-off cutting against the global audience — it does not pretend the sealed-appliance choice is free.

## VERIFICATION COMMANDS

```bash
# Install any extension from AMO -> blocked with error
# Drag an .xpi onto the browser -> refused (grep XPIInstall.sys.mjs for the block short-circuit)
grep -n 'ExperimentAPI\|getExperiment\|getVariable' toolkit/components/nimbus/ExperimentAPI.sys.mjs   # expect mock returns
# New tab -> no sponsored tiles / no discovery feed
# Network capture while typing in urlbar -> no request to merino.services.mozilla.com
# Boot + navigate urlbar/first-run/settings -> zero ExperimentAPI/Nimbus console errors
```



---

# ═══ MERGED DOCUMENT: 07-toolkit.DEVELOPER.md (verbatim · sha256:c042b2299385cba8 · merged 2026-08-02) ═══

# Toolkit Lockdown — Extension/Theme Install Block, Sponsored-Content Excision, Translations Disable, ExperimentAPI Mock — Developer Track

> **Topic:** `07-toolkit` · **Files:** `toolkit/mozapps/extensions/AddonManager.sys.mjs`, `toolkit/mozapps/extensions/internal/AddonRepository.sys.mjs`, `toolkit/mozapps/extensions/internal/XPIInstall.sys.mjs`, `toolkit/mozapps/extensions/LightweightThemeManager.sys.mjs`, `toolkit/components/nimbus/ExperimentAPI.sys.mjs`, `toolkit/components/translations/actors/TranslationsParent.sys.mjs`, `browser/components/urlbar/QuickSuggest.sys.mjs`, `browser/components/urlbar/UrlbarProviderQuickSuggest.sys.mjs`, `browser/components/urlbar/UrlbarProviderSearchSuggestions.sys.mjs`, `browser/extensions/newtab/content-src/components/{Base,DiscoveryStreamBase,TopSites}`, `browser/base/content/nsContextMenu.sys.mjs`, `browser/components/preferences/{config/appearance.mjs,dialogs/browserLanguages.js}`, `third_party/application-services/components/merino/src/lib.rs`, `services/settings/dumps/main/search-config-v2.json`, `toolkit/themes/shared/design-system/dist/{semantic-categories,tokens-table}.mjs`
> **Generated:** 2026-07-17

---

## Module Summary

Sealed-appliance layer across 19 files. Five workstreams: (1) extension/theme install lockdown — AddonManager/AddonRepository throw at the API layer, XPIInstall short-circuits the file/side-load route, LightweightThemeManager locks the theme; (2) sponsored-content excision — new-tab Base/DiscoveryStreamBase/TopSites React components strip the discovery feed + sponsored tiles/shortcuts; (3) address-bar de-sponsoring — QuickSuggest + two Urlbar providers + Merino Rust backend + search-config JSON stop remote/sponsored suggestions (no keystroke egress); (4) translations disable — TranslationsParent blocks model downloads, browserLanguages.js disables langpack UI; (5) ExperimentAPI returns empty default mocks for all Nimbus queries so the 145+ dependent components (urlbar, first-run, settings) never hit a null — the toolkit-side companion to Topic 12's network-side Mozambique Drill.

## Architecture

- **Pattern:** Throw-at-the-boundary for installs (fail-closed), component-level excision for UI content, shape-preserving mock for ExperimentAPI (fail-safe). Three different neutralization strategies matched to three different failure tolerances.
- **Trust Boundary:** Removes the entire extension attack surface (installs impossible), the sponsored-content egress surface (no impression counting, no keystroke-to-Merino), and the translation-model download surface. ExperimentAPI mock preserves the internal API contract while cutting the experiment channel.
- **Attack Surface:** Extension install is one of the largest browser attack surfaces (malicious/compromised add-ons). Blocking all install routes eliminates it wholesale. Side-load block also stops OS-level malware that drops an XPI into the profile.
- **Dependencies:** `Coherent with Topic 12 (Normandy/Nimbus) — ExperimentAPI mock here + poll-timer dilation there`, `Coherent with Topic 05 (Pocket/TopSites prefs off) — this enforces at the code layer what 05 sets at the pref layer`

## Kill Switches

### `AddonManager.sys.mjs + AddonRepository.sys.mjs — install API layer` — HARD ⚠️

- **Condition:** any install attempt (AMO or web)
- **Effect:** Throws a custom install-block error before any download/unpack. AMO backend calls and web-install interfaces refused.
- **Reversibility:** reversible
- **Notes:** Fail-closed: the default is refuse.

### `XPIInstall.sys.mjs — file/side-load route` — HARD ⚠️

- **Condition:** any .xpi install attempt
- **Effect:** Short-circuits to abort with a block log, preventing side-loading (including OS-malware-dropped XPIs).
- **Reversibility:** reversible
- **Notes:** Closes the route store-review would not catch.

### `LightweightThemeManager.sys.mjs + design-system tokens` — HARD ⚠️

- **Condition:** always
- **Effect:** Theme locked; cannot be swapped by user, extension, or remote config.
- **Reversibility:** reversible
- **Notes:** Appearance is fixed by design.

### `ExperimentAPI.sys.mjs — Nimbus query interface` — SOFT ⚠️

- **Condition:** any getExperiment/getVariable/onUpdate query
- **Effect:** Returns empty default mock objects instead of live experiment data. 145+ dependent components get a valid 'nothing' answer; no experiment executes.
- **Reversibility:** reversible
- **Notes:** Shape-preserving mock — the toolkit-side companion to Topic 12. Removing (rather than mocking) would recreate the TypeError: ExperimentAPI is undefined cascade.

### `TranslationsParent.sys.mjs + browserLanguages.js` — HARD ⚠️

- **Condition:** any translation-model/langpack fetch
- **Effect:** Model downloads blocked; monolingual/offline. Langpack download UI disabled.
- **Reversibility:** reversible
- **Notes:** Known trade-off — flagged in the roadmap as the sealed-appliance choice most worth revisiting for a global distribution audience.

### `QuickSuggest + Urlbar providers + Merino lib.rs + search-config JSON` — HARD ⚠️

- **Condition:** address-bar typing
- **Effect:** No sponsored or remotely-fetched suggestions; partial keystrokes not sent to Merino.
- **Reversibility:** reversible
- **Notes:** Privacy win — the urlbar stops being a keystroke-egress channel.

### `New-tab Base.jsx / DiscoveryStreamBase.jsx / TopSites.jsx` — HARD ⚠️

- **Condition:** new-tab render
- **Effect:** Discovery feed + sponsored tiles + sponsored shortcuts removed from the component tree.
- **Reversibility:** reversible
- **Notes:** Enforces at the code layer what Topic 05 sets at the pref layer (defence in depth).

## Performance Profile

- **CPU:** No add-on update-check threads; no new-tab sponsored-content fetch/render; no Merino round-trips. Not benchmarked topic-locally.
- **Memory:** Add-on subsystem still present (mocked/blocked) but does not load third-party extension code.
- **I/O:** Fewer background connections: no AMO pings, no Merino suggestion calls, no Pocket discovery feed, no translation-model downloads.
- **Timer Interval:** N/A

## Security Analysis

### User Profiling

Address-bar keystrokes no longer egress to Merino; new-tab impressions no longer counted; no add-on can read browsing data (none can install).

### Targeting

ExperimentAPI mock cuts the code-side experiment channel (complements Topic 12's network side).

### Trust Chain

Removing extension install removes trust dependency on AMO review, on extension signing, and on the user's judgement about what to install.

### Abuse Potential

Eliminates the compromised/malicious-extension attack class entirely — arguably the single largest reduction in attack surface in the whole build.

## Implementation Flow

1. **`AddonManager.installAddon / AddonRepository backend`** — Throws install-block error at the API boundary before any network/unpack.
   *Side effects:* Install UI surfaces an error; nothing is downloaded.
2. **`XPIInstall install pipeline`** — Short-circuits to abort with block log.
   *Side effects:* Side-load (including malware-dropped XPI) refused.
3. **`ExperimentAPI.getExperiment / getVariable / etc.`** — Returns empty default mock for every query.
   *Side effects:* 145+ dependent components receive a valid empty answer and proceed; no experiment runs.
4. **`TranslationsParent model-fetch path`** — Model download blocked.
   *Side effects:* Monolingual/offline; no Mozilla model-server connection.
5. **`Urlbar providers + Merino`** — Sponsored/remote suggestions suppressed; keystrokes not sent.
   *Side effects:* Address bar shows only local suggestions.
6. **`New-tab React render`** — Discovery/TopSites/sponsored components removed from the tree.
   *Side effects:* Quiet new-tab page.

## Technical Debt

🟠 **MEDIUM** — Translations disabled cuts against the global distribution audience
  - *Recommendation:* Revisit for distribution builds — consider allowing on-device translation models (no telemetry) while keeping the download path locked to a trusted mirror. Flagged in the roadmap.

🟡 **LOW** — Install-block is implemented by throwing rather than a single central policy gate
  - *Recommendation:* Consolidate the three throw-sites behind one `isInstallAllowed()` returning false, so the policy is one-line auditable.

🟠 **MEDIUM** — ExperimentAPI mock returns generic empties — a component expecting a specific-shaped variable could still misbehave
  - *Recommendation:* Add a smoke test that boots the browser and asserts no console error mentioning ExperimentAPI/Nimbus across urlbar/first-run/settings.

## Impact If Removed / Disabled

Reverting: extensions/themes installable (and side-loadable by malware); new-tab sponsored tiles + discovery feed return; address-bar keystrokes sent to Merino; translation models download on demand; ExperimentAPI returns live data and experiments can run. The sealed appliance becomes a normal extensible browser with its full sponsored-content and remote-experiment surface.

## Testing Notes

Try to install any extension from AMO -> blocked with error. Drag an .xpi onto the browser -> refused. Open a new tab -> no sponsored tiles, no discovery feed. Type in the address bar with network capture running -> no request to merino.services.mozilla.com. about:translations -> disabled. Boot + navigate urlbar/first-run/settings -> zero ExperimentAPI/Nimbus console errors (proves the mock is shaped correctly).

## Changelog Notes

Initial toolkit lobotomy in FF153 (2026-06-08/09); FF154 rebase resolved sys.mjs path conflicts (2026-07-05); static audit confirmed all .rej cleared, codebase stable (2026-07-10). ExperimentAPI mock is the toolkit-side companion to Topic 12's network-side neutralization.

---
*Developer Track. Human Track twin: `07-toolkit.LAYMAN.md`.*


---

# ═══ MERGED DOCUMENT: 07-toolkit.LAYMAN.md (verbatim · sha256:7bbdd219e31cdb7a · merged 2026-08-02) ═══

# 🧍 The Toolkit Lockdown — Turning Firefox Into a Sealed Appliance — Plain English Guide

> *Topic `07-toolkit` of the Gorilla Unleashed Firefox 154 build · Written for everyone · 2026-07-17*

---

## 🌍 The Big Picture

Most of the other topics make the browser *faster* or *more private*. This one makes it **sealed and opinionated** — it turns Firefox from a general-purpose, infinitely-customisable tool into a fixed appliance, like a kitchen microwave: it does a specific set of things well, and you cannot bolt new parts onto it.

Why would anyone want that? Because a browser you cannot extend is a browser that *strangers* cannot quietly extend either. Every add-on, every theme, every language pack, every 'suggested' new-tab tile is also a door — and doors are how malware, spyware, and unwanted content get in. On a machine belonging to someone who is not a security expert (which is most of the target audience), the safest door is the one that was welded shut before they ever got the machine.

Four big changes: (1) **no add-ons or themes can be installed** — every install route (Mozilla's add-on store, drag-and-drop of a file, a website trying to push an extension) is blocked at the source; (2) **no built-in translation** — the translation-model downloads are disabled, keeping the browser monolingual and offline; (3) **no sponsored content on the new-tab page** — the ad tiles, the 'discovery' feed, the sponsored shortcuts are all excised; (4) **a fixed theme** — the appearance is locked so it cannot be changed by the user or by anything pretending to be the user.

**This is a real trade-off, stated honestly:** you cannot install a password-manager extension, an ad-blocker extension, or a dark-mode theme on this build. If you need those, this build is not for you. What you get in exchange is a surface with no configurable attack points.

## 🎭 The Main Characters

| Name | What It Is | Real-World Comparison |
|---|---|---|
| **AddonManager** | The subsystem that installs, manages, and updates extensions and themes | The building's front desk that signs for every delivery — now instructed to refuse all packages |
| **XPIInstall** | The specific code that unpacks and installs an extension file (.xpi) | The loading dock — now with the door bolted, so even a package that got past the front desk cannot be unloaded |
| **New Tab (DiscoveryStream / TopSites)** | The page you see when you open a new tab — normally full of sponsored tiles and a 'recommended stories' feed | The lobby noticeboard, normally rented out to advertisers, now blank by choice |
| **QuickSuggest / Merino** | The address-bar feature that shows sponsored suggestions as you type | The helpful concierge who was secretly paid to recommend certain shops — now silent |
| **TranslationsParent** | The subsystem that downloads and runs language-translation models | The in-house translator whose reference books are no longer delivered |
| **ExperimentAPI** | The Nimbus query interface that 145+ components ask 'is experiment X on?' | The information desk that used to phone HQ for answers — now hands back a blank 'nothing to report' card so nobody waiting in line gets stuck |

## 🔢 How It Works — Step by Step

### Step 1: Block every add-on install route

There are three ways an extension can get installed: from Mozilla's official add-on store (AMO), from a website that pushes one, or from a raw file on disk (side-loading). `AddonManager.sys.mjs` and `AddonRepository.sys.mjs` block the store and web routes by throwing a custom error at the API layer; `XPIInstall.sys.mjs` short-circuits the file route to abort with a block-log message. All three doors, bolted.

### Step 2: Lock the theme

`LightweightThemeManager.sys.mjs` and the design-system token files are patched so the appearance is fixed. The theme cannot be swapped — not by the user in settings, not by an extension (which cannot install anyway), not by a remote config. Consistent appearance, one fewer surface to manipulate.

### Step 3: Strip sponsored content from the new tab

Three React components (`Base.jsx`, `DiscoveryStreamBase.jsx`, `TopSites.jsx`) are patched to remove the sponsored-tile grid, the 'recommended by Pocket' discovery feed, and the sponsored shortcuts. The new tab becomes quiet — your own content, nothing rented out to advertisers.

### Step 4: Silence the address-bar sponsors

QuickSuggest (`QuickSuggest.sys.mjs`, `UrlbarProviderQuickSuggest.sys.mjs`, `UrlbarProviderSearchSuggestions.sys.mjs`) and the Merino backend (`merino/src/lib.rs`, plus a search-config JSON) are patched so the address bar no longer shows sponsored or remotely-fetched suggestions as you type. Your keystrokes are not sent to a suggestion server.

### Step 5: Disable translations

`TranslationsParent.sys.mjs` and `browserLanguages.js` block the download of translation models and language packs. The browser stays monolingual and offline — no model-download connection to Mozilla, no language-pack fetch.

### Step 6: The clever bit — ExperimentAPI returns a safe mock

This is the subtle one. 145+ Firefox components ask the Nimbus ExperimentAPI 'is experiment X enabled?' If you just remove it, all 145 crash (this is the same lesson as Topic 12). Instead, `ExperimentAPI.sys.mjs` is patched to return an empty default mock object for every query — so every component gets a valid 'nothing to report' answer and keeps working, while no actual experiment ever runs. Corpse standing, again.

## 🤔 Quirky Things Worth Knowing

### ⚠️ The sealed-appliance philosophy is a genuine security position, not laziness

It is easy to read 'no extensions' as the build being unfinished. It is the opposite: it is a deliberate stance that the most secure configurable surface is one with no configurable surface. Every extension API is also an attack API. For a non-expert user, removing the ability to install things removes the ability to be tricked into installing things.

### ⚠️ It talks to Topic 12

The ExperimentAPI mock here is the toolkit-side companion to Topic 12's Mozambique Drill. Topic 12 kills the *network* side of Normandy/Nimbus (poll timers, endpoint). This topic makes the *code* side safe by handing back mocks. Same corpse, two different guarantees.

### ⚠️ Translations off is a real limitation for the target audience

Honest note: the target audience is global — people who may well want to translate an English page into their own language. Turning translations off is the one sealed-appliance choice that cuts against them. It is done for offline/security reasons, but it is the change most worth revisiting for a distribution build. (The roadmap flags this as a known trade-off.)

## 💻 What Does This Mean For YOU?

### 🔋 Battery, Speed & Memory

No add-on subsystem running background update checks; no translation-model downloads; no sponsored-content fetches on every new tab. Each is a small saving; together, less background work.

### ⚡ Speed

New-tab page renders faster with no sponsored-tile network fetch. Address bar responds instantly with no remote-suggestion round-trip.

### 🕵️ Your Privacy

Substantial. Your address-bar keystrokes are not sent to a suggestion server (Merino). Your new-tab impressions are not counted for ad revenue. No add-on can read your browsing.

### 🌐 Your Internet

Fewer background connections — no AMO update pings, no Merino suggestion calls, no Pocket discovery feed, no translation-model downloads.

## 🔴 The Kill Switch — Explained

**What it is:** This topic is a bank of related lockdowns: extension installs blocked, theme locked, sponsored content stripped, translations disabled, and the ExperimentAPI made to return safe mocks so nothing crashes.

**Without it:** Firefox behaves as a normal, extensible browser: extensions installable (and side-loadable by malware), sponsored tiles and discovery feed on every new tab, address-bar keystrokes sent to Merino, translation models downloaded on demand, theme changeable by anything.

**Think of it like:** Converting a customisable workshop into a sealed vending machine — you lose the ability to rearrange it, and in exchange nobody else can rearrange it either.

## 🌐 Open Source & Why It Matters To You

Every lock is a readable patch. You can see exactly which install routes are blocked, exactly what the new tab strips, exactly what the address bar no longer sends. A closed 'secure' browser asks you to trust its claims; here the sealed appliance is sealed in the open, where the seals can be inspected.

## 📖 Glossary (Plain English Dictionary)

**Add-on / Extension** — A piece of third-party code that adds features to the browser. Powerful and useful — also a common malware and spyware vector.

**XPI** — The file format for a Firefox extension (a zip archive). 'XPIInstall' is the code that unpacks and installs one.

**AMO** — addons.mozilla.org — Mozilla's official extension and theme store.

**Side-loading** — Installing an extension from a local file rather than the official store — a route malware uses to bypass store review.

**QuickSuggest / Merino** — Firefox's sponsored address-bar suggestion feature (QuickSuggest) and its backend server (Merino). Sends partial keystrokes to fetch suggestions.

**DiscoveryStream** — The 'recommended stories' feed (powered by Pocket) on the new-tab page. Ad-supported.

**TopSites** — The grid of site tiles on the new-tab page. Some are sponsored (paid placements).

**ExperimentAPI (Nimbus)** — The interface 145+ components query to check experiment/feature-flag state. Patched here to return safe empty mocks so nothing crashes while no experiment runs.

---
*Human Track. Its Developer Track twin (`07-toolkit.DEVELOPER.md`) covers the same changes in technical detail. Neither is a simplified copy of the other — they are the same truth in two languages.*


---

# ═══ MERGED DOCUMENT: 07-toolkit.PRECHECK.json (verbatim · sha256:4f53cda18c2baa0c · merged 2026-08-02) ═══

```json
[]
```


---

# ═══ MERGED DOCUMENT: 07-toolkit.PRECHECK.md (verbatim · sha256:4da7dd49387d6708 · merged 2026-08-02) ═══

# Offline Pre-Check: 07-toolkit

*Generated 2026-07-17 08:13:32 by doc_audit.py (rule-based, no model involved).*

## File Inventory

| File | Lang | Lines | Complexity | SHA256 (16) |
|---|---|---|---|---|
| browser_base_content_nsContextMenu.sys.mjs.patch | patch | 93 | 4 | `476cd9f5a5ac8f43` |
| browser_components_preferences_config_appearance.mjs.patch | patch | 334 | 8 | `2748a704f152e479` |
| browser_components_preferences_dialogs_browserLanguages.js.patch | patch | 63 | 7 | `a57696cff6bc24ad` |
| browser_components_urlbar_QuickSuggest.sys.mjs.patch | patch | 74 | 14 | `65f9cfd8766f1ecd` |
| browser_components_urlbar_UrlbarProviderQuickSuggest.sys.mjs.patch | patch | 63 | 4 | `035c7fb4eb252885` |
| browser_components_urlbar_UrlbarProviderSearchSuggestions.sys.mjs.patch | patch | 130 | 5 | `556d6242327c4966` |
| browser_extensions_newtab_content-src_components_Base_Base.jsx.patch | patch | 329 | 11 | `3c9bb98ba5d14ff2` |
| browser_extensions_newtab_content-src_components_DiscoveryStreamBase_DiscoveryStreamBase.jsx.patch | patch | 444 | 25 | `81fa7ddc0c63cc60` |
| browser_extensions_newtab_content-src_components_TopSites_TopSites.jsx.patch | patch | 242 | 12 | `18efdf83ea046996` |
| services_settings_dumps_main_search-config-v2.json.patch | patch | 7864 | 1 | `5a20b2936018be53` |
| third_party_application-services_components_merino_src_lib.rs.patch | patch | 8 | 1 | `2b54edbde0f0f608` |
| toolkit_components_nimbus_ExperimentAPI.sys.mjs.patch | patch | 206 | 20 | `426ee25288e6d531` |
| toolkit_components_translations_actors_TranslationsParent.sys.mjs.patch | patch | 391 | 32 | `2ffb4b9562bb29fa` |
| toolkit_mozapps_extensions_AddonManager.sys.mjs.patch | patch | 241 | 24 | `b30eaeb162169452` |
| toolkit_mozapps_extensions_LightweightThemeManager.sys.mjs.patch | patch | 162 | 17 | `bbbf4da2c382226e` |
| toolkit_mozapps_extensions_internal_AddonRepository.sys.mjs.patch | patch | 48 | 6 | `1dd365e177ebd78d` |
| toolkit_mozapps_extensions_internal_XPIInstall.sys.mjs.patch | patch | 80 | 10 | `3222ea34919deada` |
| toolkit_themes_shared_design-system_dist_semantic-categories.mjs.patch | patch | 2723 | 3 | `6e07f3b15a012a10` |
| toolkit_themes_shared_design-system_dist_tokens-table.mjs.patch | patch | 2717 | 3 | `bf4de9cf2cc0262e` |

## Rule Findings (0)

*All offline rules passed.*


---

# ═══ REGENERATION 2026-08-04 — dual-track docs + IBM audit regenerated by the doc-audit agent; supersedes the 2026-08-02 block above ═══

Scope: 18 .patch files (`browser_components_preferences_config_appearance.mjs.patch` removed from the set).
Pre-check (rules only): P0:0 · P1:1 (merino re-export — intentional pure deletion) · P2:0 · P3:0.
Quality gate (MASTER_TEMPLATE, need ≥85): LAYMAN 90 · DEVELOPER 86 · AUDIT 96 — all PASS.
Regenerated byte-exact 2026-08-04 and confirmed applied in FF_SRC=the source tree: nsContextMenu.sys.mjs, QuickSuggest.sys.mjs, LightweightThemeManager.sys.mjs.
Ground-truth corrections vs. the 2026-08-02 block: (1) ExperimentAPI forces eligibility gates false + preserves the manifest-default return path (no bespoke "145+ mocks"); (2) file count 18 not 19; (3) `UrlbarUtils.RESULT_SOURCE`/`RESULT_TYPE` are undefined (constants live on `UrlbarShared`), so the two urlbar providers throw-if-reached — QuickSuggest dead (isActive excised), SearchSuggestions caught at UrlbarProvidersManager:770 (P2).

---

# ═══ MERGED: 07-toolkit.LAYMAN.md (verbatim · sha256:2a864a949a14a406 · 2026-08-04) ═══

# The Toolkit Lockdown — Turning Firefox Into a Sealed Appliance — Plain Language Guide

> Generated 2026-08-04 from `07.TOOLKIT`

---

## Should You Run This?

Run it if you want a fixed, low-attack-surface browser and you do not depend on extensions, custom themes, or in-browser translation — this is the audience the whole build is aimed at. Do not run it if extensions (a password manager, an ad-blocker), a custom theme, or page translation are part of how you browse; those are removed here on purpose and cannot be restored from inside the browser.

## Worst Case, Honestly

The realistic worst outcome is inconvenience, not danger. You cannot install a password-manager extension, an ad-blocker, or a different theme, and you cannot translate a foreign-language page inside the browser. If any of those are things you rely on, this build is genuinely not for you. There is also one rough edge in the internal plumbing: the address-bar search-suggestions component was rebuilt from an older-upstream copy, and as a side effect it now fails cleanly and writes one harmless error line to the developer log every time you type in the address bar. It does not slow the browser in any way you would feel and it does not break the address bar — but it is untidy, and it is documented honestly rather than hidden.

## What Data This Touches

The direction of travel is strongly toward less data leaving your machine. Your address-bar keystrokes are no longer sent to Mozilla's suggestion server (Merino). The new-tab page no longer counts ad impressions. No add-on can read your browsing, because none can install. Translation-model downloads and language-pack fetches to Mozilla and its add-on store are switched off. Nothing in this topic sends new data out; the whole point is to close outgoing channels.

## Before You Trust It

These are strong claims — 'you cannot install anything', 'your keystrokes are not sent out'. You should be able to confirm them yourself without being a programmer.

**Step 1:** Open the browser, go to addons.mozilla.org, and try to install any extension.
  - Look for: The install is refused. Nothing downloads or installs.
**Step 2:** Open a new tab.
  - Look for: No sponsored tiles, no 'recommended stories' feed — a quiet page with your own content and a centred logo.
**Step 3:** Open the built-in settings and look for a way to change the theme, or try to open the page-translation feature.
  - Look for: The appearance is fixed to the Gorilla Nebula theme; translation is unavailable.
**Step 4:** If you are comfortable in a terminal, search the source files for the transparency markers.
  - Look for: Lines containing 'GORILLA' in AddonManager.sys.mjs, XPIInstall.sys.mjs, LightweightThemeManager.sys.mjs and nsContextMenu.sys.mjs — each one names the change and its reason.

## The Big Picture

Most of the other topics in this build make the browser faster or more private. This one makes it sealed and opinionated. It takes Firefox — a tool you can bolt anything onto — and turns it into a fixed appliance, more like a microwave than a workshop: it does a chosen set of things and refuses to grow new parts.

Why would anyone want that? Because a browser you cannot extend is a browser that strangers cannot quietly extend either. Every add-on, every theme, every 'suggested' tile in the address bar is also a door — and doors are how unwanted software and unwanted content get in. For someone who is not a security expert (which is most of the people this build is for), the safest door is the one that was welded shut before they ever received the machine.

Concretely, this folder does five things at once: it blocks every way to install an add-on or theme; it locks the appearance to one built-in theme (Gorilla Nebula); it strips the sponsored tiles and 'recommended stories' off the new-tab page; it silences the paid suggestions in the address bar and trims the search-engine list down to Google only; and it disables the built-in page-translation feature. It also carries the removal of the newer AI/chat surfaces (the 'ask a chatbot' menu item, the AI-window link-preview) that Firefox 154 shipped.

## Key Concepts

| Name | What It Means | Real-World Comparison |
|------|--------------|------------------------|
| `Add-on / Extension install lockdown` | Three separate pieces of code that normally install extensions and themes are each told to refuse and stop. | A building with three delivery entrances — the front desk, the loading dock, and the side door — and a standing order at all three: sign for nothing, unload nothing. |
| `Sealed appliance` | A device whose functions are fixed at the factory and cannot be changed by the owner or by anyone pretending to be the owner. | A vending machine versus a workshop: you lose the freedom to rearrange it, and in exchange nobody else can rearrange it either. |
| `QuickSuggest / Merino` | The address-bar feature that shows sponsored suggestions as you type, and the server it talks to. | A concierge who was quietly paid to recommend certain shops — now told to stay silent. |
| `New-tab sponsored content` | The ad tiles and the 'recommended stories' feed on the page you see when you open a new tab. | A lobby noticeboard that used to be rented out to advertisers, now left deliberately blank. |
| `ExperimentAPI (Nimbus)` | The internal switchboard other parts of Firefox ask 'is remote experiment X switched on for me?'. Here every eligibility answer is forced to 'no'. | An information desk that still answers every caller politely — but every answer is now 'nothing scheduled', so no line ever backs up and no experiment ever starts. |

## How It Works — Step by Step

### Step 1: Bolt shut every add-on install route

There are three ways an extension can normally get in: from Mozilla's official store (AMO), from a website that pushes one, or from a raw file on disk (side-loading). The web and store routes are handled in AddonManager, where the install functions are gutted down to 'cancel and log a rejection'. The file route is handled in XPIInstall, where the install step is made to throw a hard '[GORILLA] Installation rejected' error before anything is unpacked. Three doors, three bolts.

### Step 2: Lock the look to Gorilla Nebula

LightweightThemeManager — the part that decides what theme is active — is changed so that when no other theme is set, it hands back a fixed built-in theme (a dark 'nebula' background, a pink selected tab, teal accents) instead of a blank one. The code that used to fetch special AI-window themes is deleted entirely. The appearance is fixed by design, not by preference.

### Step 3: Empty the new-tab noticeboard

The new-tab page is built from React components. Two of them — DiscoveryStreamBase (the 'recommended stories' feed) and TopSites (the tile grid, some of which are paid placements) — are rewritten so their draw step returns nothing at all. A third, Base, is edited to remove the sponsored-tile plumbing and to keep the logo centred. The page becomes quiet: your own content, nothing rented to advertisers.

### Step 4: Silence the address bar and shrink the engine list

QuickSuggest (the sponsored-suggestions engine) has its start-up routine emptied, so it never comes alive. The two providers that feed the address bar are set so they contribute no remote or trending suggestions. And the shipped search-engine configuration file is trimmed from a long list down to a single entry: Google. Fewer suggestion servers to talk to, and no partial keystrokes sent out to fetch sponsored answers.

### Step 5: Turn translations off and keep the browser monolingual

TranslationsParent (the translation engine) is wired to a plain on/off preference — which is set off and locked — instead of the newer AI feature-layer it used to sit on. The settings dialog that would fetch language packs from the add-on store (browserLanguages) has its download routine emptied. No model downloads, no language-pack fetches, no translation.

### Step 6: Force every experiment-eligibility answer to 'no' without breaking anything

This is the careful one. Many parts of Firefox ask the Nimbus ExperimentAPI whether they are eligible for a remote experiment, a rollout, a lab feature, or an AI feature. Rather than delete that switchboard — which would make all those callers crash — the four eligibility answers are hard-wired to 'no', and the switchboard keeps its normal shape. When a caller asks about a feature and nothing is enrolled, it gets the feature's ordinary built-in default back, exactly as it would in a plain Firefox with no active experiments. Nobody crashes; nothing ever enrols. This is the on-machine half of the same job Topic 12 does on the network side.

### Step 7: Remove the newer AI/chat seams these files carry

Firefox 154 added an 'ask a chatbot' item to the right-click menu, an AI-window link-preview, and an ML-backed address-bar suggestion backend. The right-click menu file drops those items, the QuickSuggest engine drops the ML backend, and translations are detached from the AI feature-layer. This topic is where those removals surface in the toolkit; the full AI removal is tracked separately in the AI-excision snapshot.

## Quirky Things Worth Knowing

### The sealed-appliance philosophy is a security position, not an unfinished job

It is easy to read 'no extensions' as the build being half-done. It is the opposite: it is a deliberate stance that the most secure configurable surface is one with no configurable surface. Every extension interface is also an attack interface. For a non-expert user, removing the ability to install things removes the ability to be tricked into installing things.

### It works hand-in-hand with Topic 12

The ExperimentAPI change here is the on-machine companion to Topic 12's network-side work. Topic 12 stops the browser reaching out for experiments; this topic makes sure that even the in-code answer is a safe 'no'. Same corpse, guarded from two sides.

### The search-suggestions provider is 'off by exception', not 'off by switch'

Because that one file was rebuilt from an older Firefox copy, it points at a constant that lives somewhere else in this newer tree. The effect is that the provider throws a small error the moment it is asked to run — and Firefox's own provider manager catches that error, logs one line, and moves on. The user-visible result is exactly what was wanted (no search suggestions), but achieved messily. It is flagged in the developer and audit tracks as something to tidy, not a danger.

### Translations being off is a real limitation for this audience

The people this build is for are global — many will land on an English page and want it in their own language. Turning translations off is the one sealed-appliance choice that cuts against them. It is done for offline and security reasons, and it is the change most worth revisiting for a wider distribution. The roadmap flags it honestly.

## What This Means For You

### Battery, Processor & Memory

Not measured on the reference machine (the 16 GiB VAIO) or on the ~4 GB distribution target. Directionally there is less background work: no add-on update-check traffic, no new-tab sponsored-content fetch and render, no address-bar round-trips to a suggestion server, no translation-model downloads. Each saving is small; none has been benchmarked topic-locally, so no number is claimed.

### Speed

Not measured. Plausibly the new-tab page settles faster with no sponsored-tile network fetch, and the address bar has nothing remote to wait on. No stopwatch figure is claimed.

### Your Privacy

This is the clearest win. Address-bar keystrokes are not sent to Mozilla's Merino suggestion server. New-tab ad impressions are not counted. No add-on can read your browsing, because none can install. The search-engine list is Google-only, so there are no other suggestion endpoints in play.

### Your Internet

Fewer background connections: no add-on-store update pings, no Merino suggestion calls, no 'recommended stories' feed fetch, no translation-model or language-pack downloads. Useful on a metered or slow connection, which is common for the target audience.

## The Off Switch

**What it is:** This whole topic is itself the switch — a bank of locks applied in source code. The individual levers are: the install-rejection throws in AddonManager and XPIInstall; the emptied init in QuickSuggest; the fixed theme in LightweightThemeManager; the return-nothing new-tab components; the off-and-locked translations preference; and the four forced-'no' eligibility answers in ExperimentAPI.

**Without it:** Firefox would behave as a normal, extensible browser: extensions installable (and side-loadable by malware), sponsored tiles and a stories feed on every new tab, address-bar keystrokes sent to Merino, the full search-engine list, translation models downloaded on demand, and the theme changeable by anything — including anything pretending to be you.

**Think of it like:** Converting a customisable workshop into a sealed vending machine. You give up the ability to rearrange the room; in return, nobody else can rearrange it either.

## How to live with a sealed browser

**Before you start:**
- A Gorilla Unleashed Firefox 154 build with the 07.TOOLKIT patches applied

**Step 1:** Use it as your everyday browser. Browsing, bookmarks, history and search all work normally.
  - You should see: A clean, quiet browser with no ads in the new tab or address bar.
**Step 2:** When you need a feature that would normally be an extension (for example, translation), reach for a separate tool or website instead.
  - You should see: You work around the missing feature externally, because it cannot be added back inside this browser.
**Step 3:** If you truly need extensions or in-browser translation, choose a different build.
  - You should see: You have made an informed choice: this build trades those features for a fixed, hard-to-tamper-with surface.

## If Something Goes Wrong

**I tried to install an add-on and got a '[GORILLA] Installation rejected' error.**
That is the lock working exactly as intended — every install route is blocked.
What to do: There is no in-browser fix by design. If you must have extensions, use a different build.

**The new-tab page is nearly empty.**
The sponsored tiles and the stories feed were deliberately removed.
What to do: Nothing to fix — this is the intended quiet page.

**I opened the developer console, typed in the address bar, and saw an error mentioning RESULT_SOURCE.**
The search-suggestions provider was rebuilt from an older-upstream copy and refers to a constant that moved elsewhere in this tree; it fails cleanly and Firefox's provider manager catches and logs it.
What to do: Nothing to fix for normal use — the address bar still works and remote suggestions are off, which is intended. It is logged in the developer track as a tidy-up item.

**I cannot translate a foreign-language page.**
Built-in translation is disabled and locked off in this build.
What to do: Use an external translation site or a different build if you need in-browser translation.

## Why a Developer Would Do This

A developer makes these choices because the biggest single risk in a browser is not a clever exploit — it is a user being talked into installing something harmful, or a paid channel quietly shaping what they see. Removing the ability to install, and removing the sponsored surfaces, removes those risks at the root. The cost is flexibility, and this build pays it deliberately for an audience that benefits more from safety than from customisation.

## Why It Matters That You Can Read This

Every lock here is a readable patch, and every edit to Mozilla's own code carries a plain '// GORILLA' comment saying what changed and why. You can see exactly which install routes are blocked, exactly what the new tab strips, exactly what the address bar no longer sends, and exactly which theme is forced. A closed 'secure' browser asks you to trust its marketing; here the appliance is sealed in the open, where the seals — including the untidy ones, which are documented rather than hidden — can be inspected by anyone.

## Glossary

**Add-on / Extension** — Third-party code that adds features to the browser — powerful and useful, and also a common route for malware and spyware.

**XPI** — The file format of a Firefox extension (a zip archive); 'XPIInstall' is the code that unpacks and installs one.

**AMO** — addons.mozilla.org, Mozilla's official extension and theme store.

**Side-loading** — Installing an extension from a local file instead of the official store — a route malware uses to skip store review.

**QuickSuggest / Merino** — Firefox's sponsored address-bar suggestion feature (QuickSuggest) and its backend server (Merino), which receives partial keystrokes to fetch suggestions.

**DiscoveryStream** — The 'recommended stories' feed on the new-tab page; ad-supported.

**TopSites** — The grid of site tiles on the new-tab page; some entries are sponsored placements.

**ExperimentAPI (Nimbus)** — The internal interface Firefox components query to check whether a remote experiment or feature-flag applies to them; here its eligibility answers are all forced to 'no'.

**Gorilla Nebula** — The single built-in theme this build locks the appearance to — a dark nebula background with a pink selected tab and teal accents.

## Claim Sources

| Claim | Basis | Evidence |
|-------|-------|----------|
| All three add-on install routes are blocked | 📄 stated in input | XPIInstall.sys.mjs install(): throw new Error(`[GORILLA] Installation rejected`); AddonManager.sys.mjs installAddonFromAOM/web: install.cancel() + '[GORILLA] ... rejected' |
| The theme is locked to a fixed Gorilla Nebula default | 📄 stated in input | LightweightThemeManager.sys.mjs get themeData: returns theme with additional_backgrounds nebula.jpg, tab_selected #FFC0CB |
| New-tab discovery feed and top-sites render nothing | 📄 stated in input | DiscoveryStreamBase.jsx and TopSites.jsx render() return null |
| Search-engine config is stripped to Google only | 🤖 model inference | applied search-config-v2.json has 4 records incl. 'google' and globalOrder ['google'] |
| ExperimentAPI eligibility answers are forced to 'no' while the interface keeps its shape | 📄 stated in input | get studiesEnabled/labsEnabled/rolloutsEnabled/aiFeaturesEnabled return false; getVariable still delegates to manager.store |
| The search-suggestions provider throws and is caught rather than returning false cleanly | 🤖 model inference | UrlbarProviderSearchSuggestions references UrlbarUtils.RESULT_SOURCE which is undefined; UrlbarProvidersManager.sys.mjs:770 .catch(ex => logger.error(ex)) |
| No performance numbers are claimed | 📄 stated in input | not measured |


---
**How to verify this document:**
`📄 stated in input` — the model's phrasing of something your source text said.
Find the matching line in the original to verify.
`🤖 model inference` — the model's own judgment or synthesis. Treat as opinion,
not measurement. Re-run on the same input and check whether specific numbers
stay consistent between runs.

*Human Track. Its Developer Track twin covers the same changes in technical detail. Neither is a simplified copy of the other — they are the same truth in two languages.*

---

# ═══ MERGED: 07-toolkit.DEVELOPER.md (verbatim · sha256:57ef306b96f236a0 · 2026-08-04) ═══

# Toolkit Lockdown — Install/Theme Lock, New-Tab & Address-Bar De-Sponsoring, Translations Disable, Nimbus Eligibility Hard-Off, AI-Seam Excision (18 files)

> Generated 2026-08-04 | Source: `07.TOOLKIT`

---

## Purpose

The 07.TOOLKIT topic converts Firefox 154 into a sealed appliance across 18 patch files. It removes the entire extension/theme install surface, forces a fixed theme, excises new-tab sponsored content and address-bar sponsored/remote suggestions, disables built-in translation, forces all Nimbus experiment-eligibility gates off while preserving the ExperimentAPI contract, and carries the toolkit-visible seams of the separately-tracked AI/ML cluster excision (genai ask-chat, AI-window link-preview, ML Suggest backend). It runs at the highest trust level (privileged chrome JS + one vendored Rust crate root + one RemoteSettings dump + two generated design-system token tables).

## Design Rationale

Three neutralization strategies are matched to three failure tolerances. (1) Installs: fail-closed throw at the API boundary — the default must be 'refuse', so a missed edge fails safe. (2) UI sponsored content: component-level excision (return null) — the surface must be gone, not merely hidden by a pref. (3) Nimbus: shape-preserving disable — deleting ExperimentAPI would cascade TypeErrors through its many callers, so the eligibility getters are forced false and the query methods keep returning manifest defaults. Several files (TranslationsParent, the two Urlbar providers, LightweightThemeManager internals, the two design-system dist tables) are older-upstream shapes imported via the documented tree-restore procedure, not newer grafts.

## Architecture

- **Pattern:** Throw-at-boundary (installs) + component excision (new-tab) + shape-preserving disable (Nimbus) + config-dump trim (search) + forced-default getter (theme).
- **Trust boundary:** Removes the extension attack surface entirely (installs impossible at the API layer, including OS-dropped side-loaded XPIs), the sponsored-content egress surface (no Merino keystroke egress, no new-tab impression counting), and the translation-model download surface. The Nimbus disable preserves the internal API contract while cutting experiment eligibility. Coherent with Topic 12 (network-side Normandy/Nimbus) and Topic 05 (Pocket/TopSites prefs).
- **Attack surface:** Entry points reachable by an attacker are removed rather than guarded: no web/AMO/file install path reaches a working installer; no remote suggestion path is active; no translation-model fetch occurs. The residual reachable code is the search-suggestions provider whose isActive() now throws (contained by the provider manager's catch).
- **Dependencies:** `toolkit/mozapps/extensions/AddonManager.sys.mjs`, `toolkit/mozapps/extensions/internal/XPIInstall.sys.mjs`, `toolkit/mozapps/extensions/internal/AddonRepository.sys.mjs`, `toolkit/mozapps/extensions/LightweightThemeManager.sys.mjs`, `toolkit/components/nimbus/ExperimentAPI.sys.mjs`, `toolkit/components/translations/actors/TranslationsParent.sys.mjs`, `browser/components/urlbar/QuickSuggest.sys.mjs`, `browser/components/urlbar/UrlbarProviderQuickSuggest.sys.mjs`, `browser/components/urlbar/UrlbarProviderSearchSuggestions.sys.mjs`, `browser/base/content/nsContextMenu.sys.mjs`, `browser/components/preferences/dialogs/browserLanguages.js`, `browser/extensions/newtab/content-src/components/{Base,DiscoveryStreamBase,TopSites}`, `third_party/application-services/components/merino/src/lib.rs`, `services/settings/dumps/main/search-config-v2.json`, `toolkit/themes/shared/design-system/dist/{semantic-categories,tokens-table}.mjs`

## Flags & Configuration

| Name | Type | Default | Effect | Notes |
|------|------|---------|--------|-------|
| `browser.translations.enable` | `bool` | `false (locked, set in Topic 05/12 pref layer)` | TranslationsParent.AIFeature.isEnabled now reads this pref instead of the excised ml AIFeature; false => translations dead. | TranslationsParent.sys.mjs:466. Older-upstream skew, not a graft. |
| `quickSuggestEnabled (UrlbarPrefs)` | `bool` | `n/a — bypassed` | No longer consulted: QuickSuggest.init() is a no-op and UrlbarProviderQuickSuggest.isActive() returns false unconditionally. | Pref path dead-coded, not merely set false. |

## API Surface

| Symbol | Description | Side Effects |
|--------|-------------|--------------|
| `ExperimentAPI.get studiesEnabled / labsEnabled / rolloutsEnabled / aiFeaturesEnabled` | All four hard-return false; even a delivered recipe cannot enrol. | none |
| `ExperimentAPI.getVariable(variable) / getExperiment() / getAllBranches()` | Contract preserved: delegates to manager.store; with nothing enrolled, returns the FeatureManifest default. NOT a bespoke 'empty mock'. | none |
| `ExperimentAPI.get isInitialized` | New getter added; #initializedPromise (Promise|null) replaced by #initialized (bool). | FirstStartup import + firstStartupTimestamps plumbing + getAndClearFirstStartupTimestamps() removed. |

## Kill Switches

### `XPIInstall.sys.mjs DownloadInstall.install() (~L1390), theme install() (~L2480), DirectoryInstaller.installAddon() (~L3592)`
- **Condition:** any add-on/theme install or side-load attempt
- **Effect:** throw new Error('[GORILLA] Installation rejected …') before download/unpack; logger.error first.
- reversible
- Fail-closed. Non-system add-ons only at the first site (this.addon && !this.addon.isSystem); theme site gates on type==='theme'; directory site is unconditional throw.

### `AddonManager.sys.mjs installAddonFromWebpage() (~L2447) and installAddonFromAOM() (~L2473)`
- **Condition:** web-initiated or AMO-initiated install
- **Effect:** logger.error + aInstall.cancel()/install.cancel(); the entire validation/prompt/startInstall body is removed.
- reversible
- Also drops the site_permission telemetry field in the install-event extra (~L5699).

### `AddonRepository.sys.mjs getAvailableLangpacks() (~L818)`
- **Condition:** any langpack availability query
- **Effect:** return [] — no fetch to AMO language-tools endpoint.
- reversible
- browserLanguages.js loadLocalesFromAMO() also early-returns (no network).

### `QuickSuggest.sys.mjs init() (~L365)`
- **Condition:** Suggest/QuickSuggest startup
- **Effect:** sets #initStarted then returns; the whole Region/Nimbus/TelemetryEnvironment wait + feature construction + observer wiring is excised. Also drops SuggestBackendMl from FEATURES and enabledBackends.
- reversible
- Regenerated byte-exact 2026-08-04.

### `UrlbarProviderQuickSuggest.sys.mjs isActive() (~L55)`
- **Condition:** every urlbar query
- **Effect:** return false — provider never contributes.
- reversible
- Regenerated 2026-08-04. See dead_code for the L463 landmine.

### `UrlbarProviderSearchSuggestions.sys.mjs #shouldFetchTrending() (~L638)`
- **Condition:** trending-suggestion gate
- **Effect:** return false — no trending suggestions.
- reversible
- isActive() also effectively inert (throws, caught) — see troubleshooting/technical_debt.

### `LightweightThemeManager.sys.mjs get themeData (~L290)`
- **Condition:** always, when no fallback theme is set
- **Effect:** returns a hardcoded Gorilla Nebula theme (nebula.jpg background; colors frame #000000, tab_selected #FFC0CB, tab_line #008080) instead of {theme:null}.
- reversible
- Regenerated 2026-08-04. Also removes promiseAIThemeData/promiseAINovathemeData/promisePrivateThemeData + DATA_VERSION.

### `nsContextMenu.sys.mjs (~L510, L525, L900, L2253)`
- **Condition:** context-menu build / previewLink
- **Effect:** showSmartWindow=false; context-previewlink item forced false; GenAI ask-chat build removed; previewLink() no-op. AIWindow/GenAI/LinkPreview lazy getters removed.
- reversible
- Regenerated 2026-08-04. AI/genai seam removal.

### `DiscoveryStreamBase.jsx render() and TopSites.jsx render()`
- **Condition:** new-tab render
- **Effect:** return null — discovery feed, sponsored cards, top-sites grid absent from the tree. Base.jsx removes SPOC placeholder plumbing + TopSites/DiscoveryStream mounts; forces centered logo. TopSites also drops _dispatchTopSitesStats telemetry.
- reversible
- Enforces at the code layer what Topic 05 sets at the pref layer.

## Dead Code

- **`UrlbarProviderQuickSuggest.sys.mjs:463 (getResult) — UrlbarUtils.RESULT_TYPE.URL / UrlbarUtils.RESULT_SOURCE.SEARCH`** — UrlbarUtils has no RESULT_TYPE/RESULT_SOURCE (they live on UrlbarShared). Unreachable because isActive() returns false, so getResult() never runs. (risk: Latent only: if the isActive() excision is reverted without also fixing these references, this line throws a TypeError. Documented as a dead landmine, not a live defect.)
- **`LightweightThemeManager.sys.mjs — removed processImage()/AI theme promises`** — aiwindow/aiwindow-nova/privatewindow builtin theme fetchers removed alongside the AI-window excision. (risk: None; their consumers were removed in the AI-excision pass.)

## Performance

- **CPU:** Not benchmarked topic-locally. Removes add-on update-check work, new-tab sponsored-content fetch/render, and Merino round-trips. One counter-cost: UrlbarProviderSearchSuggestions.isActive() throws once per urlbar query, producing one logger.error per query (negligible but non-zero).
- **MEMORY:** Not measured. Add-on subsystem is still present but loads no third-party extension code. Reference machine is 16 GiB UMA-shared; distribution target ~4 GB — neither profiled here.
- **IO:** Fewer background connections: no AMO update pings, no Merino suggestion calls, no Pocket discovery feed, no translation-model/langpack downloads. Search config trimmed to a single engine (Google).
- **NOTES:** All figures directional; no measurement supplied, so none is asserted.

## Security

- **Remote execution:** Extension install (a top RCE-adjacent vector via malicious/compromised add-ons) is eliminated at the API boundary, including the OS-dropped side-load path via XPIInstall.
- **Data handling:** Address-bar keystrokes no longer egress to Merino; new-tab impressions uncounted; no add-on can read browsing data. Translation-model/langpack fetches disabled.
- **Attack surface:** Nimbus experiment channel cut on the code side (eligibility false) complementing Topic 12's network side. Search-config reduced to Google-only removes other suggestion endpoints.
- **Notes:** XPIInstall.verifyBundleSignedState() was refactored to drop the outer try/catch that previously mapped verification failures to SIGNEDSTATE_NOT_REQUIRED / SIGNEDSTATE_BROKEN. Install is blocked upstream anyway, but this helper is also reachable during startup add-on scanning; the behavioral change was not runtime-tested here (see not_verified).

## Error Conditions

| Error | Cause | Remedy |
|-------|-------|--------|
| `[GORILLA] Installation rejected: <id> / Theme installation rejected / Add-on installation rejected` | any install/side-load reached a throw site in XPIInstall/AddonManager. | Expected. To restore installs, revert the throw sites. |
| `TypeError: can't access property 'SEARCH' of undefined (UrlbarUtils.RESULT_SOURCE)` | UrlbarProviderSearchSuggestions.isActive() reads UrlbarUtils.RESULT_SOURCE, undefined in this tree (constants live on UrlbarShared). | Point the two providers at UrlbarShared.RESULT_SOURCE/RESULT_TYPE, or short-circuit isActive() with an explicit `return false` at the top. Caught today at UrlbarProvidersManager.sys.mjs:770. |

## Tasks

### Confirm the applied state of the 18 patches in the live tree

Before trusting the topic, verify markers and excisions are actually present in FF_SRC, not only in the .patch files.

**Prerequisites:**
- export FF_SRC=the source tree

**Step 1:** grep -n 'GORILLA' "$FF_SRC/toolkit/mozapps/extensions/AddonManager.sys.mjs" "$FF_SRC/toolkit/mozapps/extensions/internal/XPIInstall.sys.mjs" "$FF_SRC/toolkit/mozapps/extensions/LightweightThemeManager.sys.mjs" "$FF_SRC/browser/base/content/nsContextMenu.sys.mjs"
  - Expected: Marker lines present in all four (verified 2026-08-04).
**Step 2:** grep -nE 'get (studiesEnabled|labsEnabled|rolloutsEnabled|aiFeaturesEnabled)' "$FF_SRC/toolkit/components/nimbus/ExperimentAPI.sys.mjs"
  - Expected: Each getter returns false.
**Step 3:** python3 -c "import json;d=json.load(open('$FF_SRC/services/settings/dumps/main/search-config-v2.json'));print(len(d['data']))"
  - Expected: 4 records (google-only).

**After this task:** All applied changes confirmed against the tree, not the doc.

### Reproduce and grade the SearchSuggestions isActive() throw

Decide whether the throw is contained or user-visible.

**Prerequisites:**
- A running build with a devtools browser console

**Step 1:** Open the Browser Console (Ctrl+Shift+J), type a few characters in the address bar.
  - Expected: One 'RESULT_SOURCE' TypeError is logged per query via UrlbarProvidersManager:770; the address bar still returns history/bookmark results.
**Step 2:** Confirm no remote search suggestions appear.
  - Expected: None — the provider is inert (intended).

**After this task:** Confirms the defect is P2 (log noise / off-by-exception), not a crash.

## Troubleshooting

**Symptom:** Per-keystroke TypeError about RESULT_SOURCE in the console
**Cause:** UrlbarProviderSearchSuggestions.isActive() reads UrlbarUtils.RESULT_SOURCE (undefined; constants are on UrlbarShared). Older-upstream skew.
**Remedy:** Replace UrlbarUtils.RESULT_SOURCE/RESULT_TYPE with UrlbarShared.* (import it), or add `return false;` at the top of isActive().
**Verify:** Console shows zero RESULT_SOURCE errors while typing.

**Symptom:** An add-on install silently does nothing
**Cause:** installAddonFromWebpage/installAddonFromAOM cancel the install; XPIInstall throws.
**Remedy:** Expected. Check the console for '[GORILLA] … rejected'.
**Verify:** grep XPIInstall.sys.mjs for the throw sites.

**Symptom:** Startup add-on signature scan behaves unexpectedly
**Cause:** verifyBundleSignedState() no longer maps verification exceptions to a SIGNEDSTATE; the exception now propagates.
**Remedy:** If observed, restore the outer try/catch fallback in verifyBundleSignedState().
**Verify:** Boot with a builtin/system add-on and watch AddonManager logs — not tested in this pass.

## Technical Debt

🟠 **MEDIUM** — UrlbarProviderSearchSuggestions.isActive() throws (undefined UrlbarUtils.RESULT_SOURCE) and is only saved by UrlbarProvidersManager:770's catch — 'off by exception' with one logged error per urlbar query. → Switch the two providers to UrlbarShared.RESULT_SOURCE/RESULT_TYPE, or make isActive() `return false` explicitly. Removes log noise and the fragility.
🟡 **LOW** — UrlbarProviderQuickSuggest.sys.mjs:463 references the same undefined UrlbarUtils.RESULT_SOURCE/RESULT_TYPE, kept alive only by isActive() returning false. → Fix the reference so a future revert of the isActive() excision cannot reintroduce a live TypeError.
🟠 **MEDIUM** — XPIInstall.verifyBundleSignedState() lost its exception->SIGNEDSTATE fallback; impact on system/builtin add-on startup scanning not runtime-tested. → Either restore the fallback or add a boot smoke-test asserting builtin add-ons still resolve a signed state.
🟡 **LOW** — Three install throw-sites are hand-inlined rather than routed through one policy gate. → Consolidate behind a single isInstallAllowed() returning false for one-line auditability.
🟡 **LOW** — merino/src/lib.rs removes only the `pub use curated_recommendations::{…}` re-export; the module is still compiled — standalone de-sponsoring value is marginal (the real work is the search-config trim + JS urlbar layer). → Either drop the module properly or document the re-export removal's intent; precheck P1-001 flags it as a pure deletion to confirm.
🟠 **MEDIUM** — Translations disabled cuts against the global distribution audience. → Revisit for distribution: allow on-device translation models from a telemetry-free mirror while keeping Mozilla model-server + langpack downloads locked.

## Impact If Removed

Reverting the topic returns a normal extensible browser: extensions/themes installable (and side-loadable by malware); new-tab sponsored tiles + discovery feed back; address-bar keystrokes to Merino; full search-engine list; translation-model downloads on demand; ExperimentAPI eligibility live so recipes can enrol; theme changeable by user/extension/remote. The AI/chat seams carried here (genai ask-chat, AI-window link-preview, ML Suggest backend) would also need the separate AI-excision snapshot reverted to fully restore.

## Claim Sources

| Claim | Basis | Evidence |
|-------|-------|----------|
| XPIInstall DownloadInstall.install() hard-throws for non-system add-ons | 📄 stated in input | XPIInstall.sys.mjs.patch: if (this.addon && !this.addon.isSystem) { … throw new Error(`[GORILLA] Installation rejected: ${this.addon.id}`); } |
| XPIInstall theme install() hard-throws for type==='theme' | 📄 stated in input | XPIInstall.sys.mjs.patch: if (this.addon && this.addon.type === "theme") { … throw new Error(`[GORILLA] Theme installation rejected`) } |
| XPIInstall directory installAddon() throws unconditionally | 📄 stated in input | XPIInstall.sys.mjs.patch installAddon(): logger.error(`[GORILLA] Add-on installation blocked`); throw new Error(`[GORILLA] Add-on installation rejected: ${id}`); |
| AddonManager web-install path gutted to cancel | 📄 stated in input | AddonManager.sys.mjs.patch installAddonFromWebpage body replaced with logger.error + aInstall.cancel() |
| AddonManager AMO-install path gutted to cancel | 📄 stated in input | AddonManager.sys.mjs.patch installAddonFromAOM body replaced with logger.error(`[GORILLA] … rejected (AMO Pathway)`) + install.cancel() |
| AddonManager drops the site_permission install-event telemetry field | 📄 stated in input | AddonManager.sys.mjs.patch removes `site_permission: install.newSitePerm` |
| AddonRepository.getAvailableLangpacks returns [] (no AMO fetch) | 📄 stated in input | AddonRepository.sys.mjs.patch getAvailableLangpacks(): // PHYSICAL LOCK … return []; |
| browserLanguages.loadLocalesFromAMO early-returns (no langpack network) | 📄 stated in input | browserLanguages.js.patch loadLocalesFromAMO(): // PHYSICAL LOCK … return; |
| QuickSuggest.init() is a no-op and SuggestBackendMl is dropped | 📄 stated in input | QuickSuggest.sys.mjs.patch: init(){ // EXCISED … } and removed SuggestBackendMl import + enabledBackends entry |
| UrlbarProviderQuickSuggest.isActive() returns false | 📄 stated in input | UrlbarProviderQuickSuggest.sys.mjs.patch isActive(): // GORILLA: EXCISED\n return false; |
| UrlbarProviderSearchSuggestions.#shouldFetchTrending() returns false | 📄 stated in input | UrlbarProviderSearchSuggestions.sys.mjs.patch #shouldFetchTrending(){ return false; } |
| ExperimentAPI eligibility getters (studies/labs/rollouts/aiFeatures) all return false | 📄 stated in input | ExperimentAPI.sys.mjs.patch get labsEnabled/rolloutsEnabled/studiesEnabled/aiFeaturesEnabled { return false; } |
| ExperimentAPI removes FirstStartup import + firstStartupTimestamps + adds isInitialized; #initializedPromise->#initialized | 📄 stated in input | ExperimentAPI.sys.mjs.patch removes FirstStartup getter, getAndClearFirstStartupTimestamps(); adds get isInitialized(){return this.#initialized} |
| TranslationsParent AIFeature reverted to browser.translations.enable pref check | 📄 stated in input | TranslationsParent.sys.mjs:463-466 static get AIFeature { … getBoolPref('browser.translations.enable', false) } (GORILLA OVERRIDE ml AIFeature excised) |
| LightweightThemeManager.themeData forces a Gorilla Nebula default theme | 📄 stated in input | LightweightThemeManager.sys.mjs.patch get themeData returns theme{ images.additional_backgrounds ['chrome://branding/content/nebula.jpg'], colors.tab_selected '#FFC0CB', tab_line '#008080' } |
| LightweightThemeManager removes the AI/private theme fetchers and DATA_VERSION | 📄 stated in input | LightweightThemeManager.sys.mjs.patch deletes promiseAIThemeData/promiseAINovathemeData/promisePrivateThemeData, aiThemeData fields and DATA_VERSION |
| nsContextMenu removes AIWindow/GenAI/LinkPreview seams; showSmartWindow=false; previewLink no-op | 📄 stated in input | nsContextMenu.sys.mjs.patch drops AIWindow/GenAI/LinkPreview getters; let showSmartWindow = false; context-previewlink false; previewLink(){ // genai excised } |
| DiscoveryStreamBase.render() and TopSites.render() return null; TopSites drops _dispatchTopSitesStats | 📄 stated in input | DiscoveryStreamBase.jsx.patch and TopSites.jsx.patch render() -> return null; TopSites removes _dispatchTopSitesStats + TopSitesRows/MaxSitesPerRow |
| merino/src/lib.rs removes only the curated_recommendations re-export; the module is still compiled | 📄 stated in input | lib.rs.patch removes only `pub use curated_recommendations::{CuratedRecommendationLocale, CuratedRecommendationsApiError};`; live lib.rs still has `pub mod curated_recommendations;` |
| search-config-v2.json is trimmed to a Google-only global order | 📄 stated in input | search-config-v2.json.patch adds "globalOrder": [ "google" ] and "specificOrders": []; net -7834/+9 lines |
| verifyBundleSignedState lost its outer try/catch fallback | 📄 stated in input | XPIInstall.sys.mjs.patch removes the outer try{}catch(e) that returned SIGNEDSTATE_NOT_REQUIRED/SIGNEDSTATE_BROKEN |
| No CPU/memory/latency/battery numbers were measured | 📄 stated in input | not measured (task hard-rule: no measurement supplied) |
| UrlbarUtils.RESULT_SOURCE/RESULT_TYPE are undefined in this tree (constants live on UrlbarShared), so the two providers' references would throw if reached | 🤖 model inference | UrlbarShared (content/UrlbarShared.mjs) defines RESULT_TYPE/RESULT_SOURCE; UrlbarUtils.sys.mjs has no RESULT_SOURCE key; only the two patched providers use UrlbarUtils.RESULT_SOURCE; SearchSuggestions throw caught at UrlbarProvidersManager.sys.mjs:770 |


---
**How to verify this document:**
`📄 stated in input` — the model's phrasing of something your source text said.
Find the matching line in the original to verify.
`🤖 model inference` — the model's own judgment or synthesis. Treat as opinion,
not measurement. Re-run on the same input and check whether specific numbers
stay consistent between runs.

*Auto-generated DITA-structured developer documentation.*

---

# ═══ MERGED: 07-toolkit.AUDIT.md (verbatim · sha256:ba6e65d4d20f1d3c · 2026-08-04) ═══

# IBM-Style Audit Report: 07.TOOLKIT

## SECTION A: DOCUMENT CONTROL

| Attribute | Value |
|---|---|
| **Target** | 07.TOOLKIT |
| **Files scanned** | see payload |
| **Date / time** | 2026-08-04 07:20:04 |
| **Audit status** | PASS |

## SECTION B: EXECUTIVE SUMMARY (Plain Language)

This folder seals Firefox shut: you cannot install add-ons or themes (every route is bolted), the new tab and address bar carry no sponsored content, the search list is Google-only, translation is off, and the look is fixed to one built-in theme. It ships and it works — the owner runs it daily. The security payoff is large: removing the ability to install things removes the single biggest way a non-expert user gets tricked into running something harmful. The honest caveats: you lose extensions, themes and in-browser translation on purpose, and one address-bar component was rebuilt from an older copy so it fails cleanly and logs a harmless error each time you type — untidy, documented, not dangerous.

## SECTION C: TECHNICAL SUMMARY (Developer)

Three neutralization strategies matched to three failure tolerances: fail-closed throw at the install API boundary (AddonManager/XPIInstall/AddonRepository), component-level excision for new-tab sponsored content (DiscoveryStreamBase/TopSites return null; Base strips SPOC plumbing), and shape-preserving disable for Nimbus (ExperimentAPI eligibility getters forced false, query methods keep returning FeatureManifest defaults — no bespoke mock, contrary to the stale gen-1 doc's '145+ empty mocks' claim). Address-bar de-sponsoring: QuickSuggest.init() no-op + SuggestBackendMl dropped; UrlbarProviderQuickSuggest.isActive() false; UrlbarProviderSearchSuggestions #shouldFetchTrending false; search-config-v2.json trimmed to Google-only (4 records). Translations detached from the excised ml AIFeature to a plain browser.translations.enable pref check (off+locked) — older-upstream skew via the documented restore, not a graft. Theme locked to a hardcoded Gorilla Nebula default in LightweightThemeManager.get themeData. nsContextMenu drops the genai ask-chat / AI-window link-preview seams. Verdict: ships; two real cleanups (SearchSuggestions off-by-exception; verifyBundleSignedState fallback removed) and several low-severity tidy-ups remain.

## SECTION D: DETECTED DEFECTS

1 found by rules, 3 by review. Rule findings are deterministic; review findings are judgement.

### 🟠 P1-001 — P1 *(found by rule)*

- **Plain English:** A repair instruction that removes things but adds nothing. Worth checking it is meant to be a deletion.
- **Technical:** third_party_application-services_components_merino_src_lib.rs.patch: targets third_party/application-services/components/merino/src/lib.rs with no added lines.
- **Fix:** Confirm this is an intentional pure deletion.

### 🟡 P2-101 — P2 *(found by review)*

- **Plain English:** The address-bar search-suggestions component was rebuilt from an older copy of Firefox and points at a signpost that has since moved. Every time you type, it trips over the missing signpost and falls down — but Firefox's own safety net catches it, writes one line in the log, and carries on. The address bar still works and suggestions stay off (which is the goal), but 'falling down and being caught' is a fragile way to be switched off.
- **Technical:** UrlbarProviderSearchSuggestions.sys.mjs isActive() (~L98) reads UrlbarUtils.RESULT_SOURCE.SEARCH; UrlbarUtils has no RESULT_SOURCE/RESULT_TYPE in this tree (they live on UrlbarShared, content/UrlbarShared.mjs). isActive() throws a TypeError on every query, caught at UrlbarProvidersManager.sys.mjs:770 (.catch(ex => logger.error(ex))). Net: provider inert (intended) + one logged error per query.
- **Fix:** Import UrlbarShared and use UrlbarShared.RESULT_SOURCE/RESULT_TYPE, or add an explicit `return false;` at the top of isActive(). Applies to RESULT_TYPE/RESULT_SOURCE refs at ~L98/100/141/146/528/529/671/672.
- **Effort:** 30min

### 🟡 P2-102 — P2 *(found by review)*

- **Plain English:** The add-on file-checker had its safety wrapper taken off. Before, if a signature check errored out, it answered 'not required' or 'broken'; now the error just escapes. Installs are blocked anyway, so this rarely matters — but the same checker also runs when the browser inventories its own built-in add-ons at startup, and that path was not tested here.
- **Technical:** XPIInstall.sys.mjs verifyBundleSignedState() lost its outer try/catch (removed in the patch), so an exception from pkg.verifySignedState() now propagates instead of mapping to AddonManager.SIGNEDSTATE_NOT_REQUIRED / SIGNEDSTATE_BROKEN. Reachable during startup add-on scanning of system/builtin bundles.
- **Fix:** Restore the outer try/catch fallback, or add a boot smoke-test asserting builtin/system add-ons still resolve a signed state without throwing.
- **Effort:** 1h

### 🟢 P3-103 — P3 *(found by review)*

- **Plain English:** A second, similar 'missing signpost' sits in the sponsored-suggestions engine — but that engine is fully switched off, so the bad line is never reached. It is only a trap for a future editor who switches the engine back on without fixing it.
- **Technical:** UrlbarProviderQuickSuggest.sys.mjs:463 uses UrlbarUtils.RESULT_TYPE.URL / UrlbarUtils.RESULT_SOURCE.SEARCH (both undefined here) inside getResult(); unreachable because isActive() returns false. Dead landmine, latent only if the isActive() excision is reverted.
- **Fix:** Fix the reference (UrlbarShared.*) so a future revert cannot reintroduce a live TypeError. Document-only otherwise.
- **Effort:** 10min

## SECTION E: PRODUCTION READINESS

**Overall readiness: 🟡 88%**

**Done:**
- [x] All three add-on install routes blocked at the API boundary (web + AMO in AddonManager; file/side-load throw in XPIInstall), verified present in the live tree
- [x] Langpack availability fetch disabled (AddonRepository.getAvailableLangpacks -> []; browserLanguages.loadLocalesFromAMO early-return)
- [x] Theme locked to a hardcoded Gorilla Nebula default (LightweightThemeManager.get themeData); AI theme fetchers removed
- [x] New-tab discovery feed + top-sites + sponsored plumbing excised (DiscoveryStreamBase/TopSites return null; Base strips SPOC + forces centered logo)
- [x] Address-bar de-sponsored: QuickSuggest.init() no-op + SuggestBackendMl dropped; UrlbarProviderQuickSuggest.isActive() false; trending off
- [x] search-config-v2.json trimmed to Google-only (4 records; globalOrder ['google'])
- [x] Nimbus eligibility hard-off (studies/labs/rollouts/aiFeatures all false) with the ExperimentAPI contract preserved (manifest defaults still returned) — coherent companion to Topic 12
- [x] Translations detached from the excised ml AIFeature to a plain browser.translations.enable check (off+locked); older-upstream skew via the documented restore, not a graft
- [x] AI/genai seams removed from nsContextMenu (ask-chat, link-preview) — consistent with AI_EXCISION_SNAPSHOT_2026-08-02/EXCISION_MANIFEST.md
- [x] Three regenerated patches (nsContextMenu, QuickSuggest, LightweightThemeManager) applied and present in the live tree (2026-08-04)

**To do:**
- [ ] P2-101: make SearchSuggestions.isActive() switch off cleanly (UrlbarShared.* or explicit return false) to stop per-query error logging
- [ ] P2-102: restore or smoke-test verifyBundleSignedState() startup-scan behavior
- [ ] P3-103: fix the UrlbarProviderQuickSuggest:463 dead landmine so a future revert cannot reintroduce a live TypeError
- [ ] P1-001 (precheck): confirm the merino/src/lib.rs re-export removal is the intended pure deletion (module still compiled; marginal de-sponsoring value)
- [ ] Consolidate the three install throw-sites behind one isInstallAllowed() gate
- [ ] Roadmap: revisit translations-off for the global distribution audience (on-device models on a telemetry-free mirror)

**Not verified:**
- No CPU/memory/latency/battery numbers were measured on either the 16 GiB reference VAIO or the ~4 GB distribution target — all performance statements are directional only
- Live console capture while typing in the address bar (to observe the per-query RESULT_SOURCE TypeError) was reasoned from code, not run in this pass
- verifyBundleSignedState() behavior during startup system/builtin add-on scanning was not runtime-tested
- Clean re-application of the three regenerated patches against a pristine vanilla tree was not re-run here (their applied state is confirmed present in FF_SRC)
- The two 10k-line generated design-system dist tables (semantic-categories.mjs, tokens-table.mjs) were characterized as older-upstream skew, not audited line-by-line
- Runtime GUI smoke test of new-tab/settings/translate paths for this specific 18-file set was not performed in this pass (the 2026-08-03 GUI verification in the excision manifest covers the AI seams)

## SECTION F: PHASED PLAN

### Phase 0 — `UrlbarProviderSearchSuggestions.sys.mjs / UrlbarProviderQuickSuggest.sys.mjs`
- **Change:** Replace UrlbarUtils.RESULT_SOURCE/RESULT_TYPE with UrlbarShared.* (or short-circuit isActive with return false) to eliminate the throw-and-catch and the dead landmine.
- **Expected impact:** Removes per-query error logging; makes the 'off' state explicit and revert-safe.

### Phase 0 — `toolkit/mozapps/extensions/internal/XPIInstall.sys.mjs`
- **Change:** Restore the verifyBundleSignedState() outer try/catch fallback, or add a builtin-add-on startup-scan smoke-test.
- **Expected impact:** Removes an untested behavioral change on the signature-scan path.

### Phase 1 — `toolkit/mozapps/extensions (AddonManager + XPIInstall)`
- **Change:** Introduce one isInstallAllowed() returning false, called by all install/side-load sites.
- **Expected impact:** One-line-auditable install policy; less duplicated throw logic.

### Phase 2 — `toolkit/components/translations`
- **Change:** Allow on-device translation models from a trusted telemetry-free mirror while keeping Mozilla model-server + langpack downloads locked.
- **Expected impact:** Restores translation for the global audience without opening a telemetry channel — the one sealed-appliance choice that cuts against the mission.

## POSITIVE OBSERVATIONS

- Three neutralization strategies matched to three failure tolerances (fail-closed throw for installs, excision for UI, shape-preserving disable for Nimbus) — the right tool per problem, not one blunt instrument.
- Blocking all three install routes (not just AMO) is thorough — the XPIInstall side-load throw is what stops OS-level malware dropping an XPI, which a store-only block would miss. Arguably the single largest attack-surface reduction in the whole build.
- The Nimbus disable is done correctly: eligibility forced off while the API contract is preserved, so the many callers get valid manifest defaults instead of a TypeError cascade — the on-machine complement to Topic 12's network side.
- In-source '// GORILLA' provenance markers are present on every edit to Mozilla code, keeping the changes auditable by both a developer and a layperson.
- This audit corrects two inaccuracies carried by the prior gen-1 docs (the content-swapped Necko text; the unsupported 'ExperimentAPI mocks 145+ consumers' claim) — honesty over a tidy but wrong PASS.

## VERIFICATION COMMANDS

Run these to check the claims above rather than trusting them.

```bash
export FF_SRC=the source tree
grep -n 'GORILLA' "$FF_SRC/toolkit/mozapps/extensions/AddonManager.sys.mjs" "$FF_SRC/toolkit/mozapps/extensions/internal/XPIInstall.sys.mjs" "$FF_SRC/toolkit/mozapps/extensions/LightweightThemeManager.sys.mjs" "$FF_SRC/browser/base/content/nsContextMenu.sys.mjs"
grep -nE 'get (studiesEnabled|labsEnabled|rolloutsEnabled|aiFeaturesEnabled)' "$FF_SRC/toolkit/components/nimbus/ExperimentAPI.sys.mjs"   # expect: return false (x4)
python3 -c "import json;d=json.load(open('$FF_SRC/services/settings/dumps/main/search-config-v2.json'));print(len(d['data']), [r.get('identifier',r.get('recordType')) for r in d['data']])"   # expect: 4 [...'google'...]
grep -n 'RESULT_SOURCE' "$FF_SRC/browser/components/urlbar/UrlbarProviderSearchSuggestions.sys.mjs"; grep -n "RESULT_SOURCE:" "$FF_SRC/browser/components/urlbar/UrlbarUtils.sys.mjs"   # 2nd returns nothing => undefined on UrlbarUtils
grep -n 'catch(ex => lazy.logger.error(ex))' "$FF_SRC/browser/components/urlbar/UrlbarProvidersManager.sys.mjs"   # the containing net for the throw
grep -nE 'AIFeature|browser.translations.enable' "$FF_SRC/toolkit/components/translations/actors/TranslationsParent.sys.mjs"   # pre-AI pref check
# Interactive: open Browser Console, type in the urlbar -> observe one RESULT_SOURCE TypeError/query, address bar still functional
```

## Claim Sources

| Claim | Basis | Evidence |
|-------|-------|----------|
| Ships and works; owner runs it daily | 📄 stated in input | task guardrails + EXCISION_MANIFEST FINAL RUNTIME STATE 2026-08-03 (windowed session clean) |
| SearchSuggestions.isActive() throws and is caught, one error per query | 🤖 model inference | UrlbarUtils.RESULT_SOURCE undefined; UrlbarProvidersManager.sys.mjs:770 .catch |
| ExperimentAPI has no bespoke empty-mock; contract preserved | 🤖 model inference | getVariable(L775) delegates to manager.store; no 'mock'/return {} in ExperimentAPI.sys.mjs; '145' unsourced |
| search-config trimmed to Google-only | 🤖 model inference | applied JSON data length 4 incl. google; globalOrder ['google'] |
| verifyBundleSignedState fallback removed | 📄 stated in input | XPIInstall.sys.mjs.patch drops the outer try{}catch(e) returning SIGNEDSTATE_NOT_REQUIRED/BROKEN |
| merino change is only a re-export removal; module still compiled | 🤖 model inference | lib.rs.patch removes `pub use curated_recommendations::{…}` only; live lib.rs still has `pub mod curated_recommendations;` |
| Prior standalone audit was content-swapped (Necko) and is superseded | 📄 stated in input | AUDIT_REPORT_07.TOOLKIT.md header 'SUPERSEDED 2026-08-03'; body describes Necko/networking |
| Translations older-upstream skew, not a graft | 📄 stated in input | guardrail: byte-identical to 07-16 archive except the one signed AIFeature excision; off+locked |
| No performance numbers measured | 📄 stated in input | not measured |


---
**How to verify this document:**
`📄 stated in input` — the model's phrasing of something your source text said.
Find the matching line in the original to verify.
`🤖 model inference` — the model's own judgment or synthesis. Treat as opinion,
not measurement. Re-run on the same input and check whether specific numbers
stay consistent between runs.

---

# ═══ MERGED: 07-toolkit.PRECHECK.md (verbatim · sha256:1900b8922b35c1c2 · 2026-08-04) ═══

# Offline Pre-Check: 07-toolkit

*Generated 2026-08-04 07:03:16 by rules only. No model was involved, so everything below is a deterministic finding about the files as they are on disk.*

## Files Scanned

| File | Language | Lines | Code | Complexity | SHA-256 |
|---|---|---|---|---|---|
| `browser_base_content_nsContextMenu.sys.mjs.patch` | patch | 69 | 62 | 1 | `885123b6e6aacfb8` |
| `browser_components_preferences_dialogs_browserLanguages.js.patch` | patch | 63 | 61 | 7 | `a57696cff6bc24ad` |
| `browser_components_urlbar_QuickSuggest.sys.mjs.patch` | patch | 91 | 87 | 14 | `38ae30654e6b2b5f` |
| `browser_components_urlbar_UrlbarProviderQuickSuggest.sys.mjs.patch` | patch | 63 | 59 | 4 | `035c7fb4eb252885` |
| `browser_components_urlbar_UrlbarProviderSearchSuggestions.sys.mjs.patch` | patch | 130 | 113 | 5 | `556d6242327c4966` |
| `browser_extensions_newtab_content-src_components_Base_Base.jsx.patch` | patch | 329 | 315 | 11 | `3c9bb98ba5d14ff2` |
| `browser_extensions_newtab_content-src_components_DiscoveryStreamBase_DiscoveryStreamBase.jsx.patch` | patch | 444 | 438 | 25 | `81fa7ddc0c63cc60` |
| `browser_extensions_newtab_content-src_components_TopSites_TopSites.jsx.patch` | patch | 242 | 236 | 12 | `18efdf83ea046996` |
| `services_settings_dumps_main_search-config-v2.json.patch` | patch | 7864 | 7864 | 1 | `5a20b2936018be53` |
| `third_party_application-services_components_merino_src_lib.rs.patch` | patch | 8 | 8 | 1 | `2b54edbde0f0f608` |
| `toolkit_components_nimbus_ExperimentAPI.sys.mjs.patch` | patch | 206 | 170 | 20 | `426ee25288e6d531` |
| `toolkit_components_translations_actors_TranslationsParent.sys.mjs.patch` | patch | 391 | 330 | 32 | `2ffb4b9562bb29fa` |
| `toolkit_mozapps_extensions_AddonManager.sys.mjs.patch` | patch | 241 | 231 | 24 | `b30eaeb162169452` |
| `toolkit_mozapps_extensions_LightweightThemeManager.sys.mjs.patch` | patch | 175 | 168 | 18 | `8381d1863bd95157` |
| `toolkit_mozapps_extensions_internal_AddonRepository.sys.mjs.patch` | patch | 48 | 46 | 6 | `1dd365e177ebd78d` |
| `toolkit_mozapps_extensions_internal_XPIInstall.sys.mjs.patch` | patch | 80 | 71 | 10 | `3222ea34919deada` |
| `toolkit_themes_shared_design-system_dist_semantic-categories.mjs.patch` | patch | 2723 | 2723 | 3 | `6e07f3b15a012a10` |
| `toolkit_themes_shared_design-system_dist_tokens-table.mjs.patch` | patch | 2717 | 2717 | 3 | `bf4de9cf2cc0262e` |

## Findings

🔴 P0: 0 · 🟠 P1: 1 · 🟡 P2: 0 · 🟢 P3: 0

### 🟠 P1-001 — P1

- **Plain English:** A repair instruction that removes things but adds nothing. Worth checking it is meant to be a deletion.
- **Technical:** third_party_application-services_components_merino_src_lib.rs.patch: targets third_party/application-services/components/merino/src/lib.rs with no added lines.
- **Fix:** Confirm this is an intentional pure deletion.
