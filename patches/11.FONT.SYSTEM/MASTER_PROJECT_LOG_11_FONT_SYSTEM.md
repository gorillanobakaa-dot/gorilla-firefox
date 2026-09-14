# 11.FONT.SYSTEM — Master Project Log

*Canonical, one-log-per-folder. Regenerated 2026-08-04. Supersedes the 2026-08-02 consolidation and the 2026-07-16 generation-1 side-docs (recoverable via git history + merged-docs-backup-2026-08-02.tar.gz).*

---

## ═══ REGENERATION 2026-08-04 — dual-track + IBM audit rebuilt against the live tree ═══

**What changed and why.** The dual-track LAYMAN + DEVELOPER docs and the IBM A–F
audit were regenerated with the `dual-track` toolkit and validated (quality gate
≥85): **LAYMAN 90/100, DEVELOPER 90/100, AUDIT 96/100**. Offline precheck
(`.dual-track-rules.py`) reported **0 findings (P0 0 · P1 0 · P2 0 · P3 0)**.

Every claim in the regenerated docs is grounded against the LIVE tree
(`the source tree`) or the patch/script text, with `file:line` or an
authority, or is explicitly labelled **not verified / not measured**. This
corrects three overstatements carried in the 2026-07-16 generation-1 docs that the
2026-08-03 POR had flagged (POR preserved verbatim at the end of this log):

- **Startup figures are now labelled not measured.** The old README/LAYMAN
  narrative implied a `~40s → ~2–4s` / `10×` cold-boot win as fact. No benchmark
  exists (the audit lists it as an open item; the folder's own history doc gives a
  much smaller `50–200 ms` figure). The regenerated docs never state it as fact.
- **The pref is unregistered.** `gfx.bundled_fonts.skip_system_scan` is read purely
  via `Preferences::GetBool("…", false)` with a hard-coded default; it is registered
  in no `StaticPrefList.yaml` / `.js` / `.yaml` / `.mjs`, so it does **not** appear
  in `about:config` until created by hand. The old "should appear in about:config,
  default false" verification step was wrong as written and is corrected.
- **As-shipped vs. dormant is separated.** The always-active effect of this room is
  the 8 bundled fonts (packaged and loaded because `MOZ_BUNDLED_FONTS` defaults on
  for Linux — `toolkit/moz.configure:2191-2211`). The skip-scan optimisation is
  **dormant** as shipped (pref default OFF), and even if enabled only the fontconfig
  backend runs on the Linux reference target — the DWrite (Windows) and FT2 (Android)
  patches are portability spares that never execute here. The privacy/fingerprinting
  benefit is therefore conditional on enabling the pref and is not realised as shipped.

**New defects surfaced by this pass** (all P2/P3, none blocking; full detail in the
AUDIT section below): P2 no automated bundled-font glyph-coverage gate; P3 unmeasured
startup figures; P3 latent `NS_ASSERTION(mFontFamilies.Count() > kBundledCount)`
in the DWrite spare if that path is ever enabled; P3 the about:config-visibility doc
error; P3 the `get-microsoft-fonts.sh` header comment says "8 font files" while the
`NEEDED_FONTS` array fetches 7 (Twemoji excluded — CC-BY, already in-tree).

**Ground-truth verification (live tree, 2026-08-04):**

| Fact | Evidence (file:line) |
|---|---|
| Pref read, hard-coded `false` default, 4 backends | gfxFcPlatformFontList.cpp:1754,1807 · gfxFT2FontList.cpp:1551 · gfxDWriteFontList.cpp:1656,1740 · gfxPlatformFontList.cpp:791 |
| `[GORILLA]`/`[Gorilla]` provenance markers present | gfxFcPlatformFontList.cpp:1752,1759,1805,1811 · gfxFT2FontList.cpp:1549,1645 · gfxDWriteFontList.cpp:1655,1739,1748 · gfxPlatformFontList.cpp:790,793 |
| 8 fonts wired via `FINAL_TARGET_FILES.fonts` | browser/fonts/moz.build:5-16 (all 8 files physically present in `browser/fonts/`) |
| `MOZ_BUNDLED_FONTS` default-on for Linux browser build | toolkit/moz.configure:2191-2211 |
| Pref set `true` nowhere; default-OFF invariant holds | `grep -rln` across tree → docs/patches only |
| `.gitignore` excludes `*.ttf`/`*.ttc`, re-includes Twemoji | patches repo `.gitignore:62-64` |
| Script fetches 7 MS fonts (comment says 8) | get-microsoft-fonts.sh:35-43 vs header comment line 24 |

**Files in this room:** `browser_fonts_moz.build.patch`,
`gfx_thebes_gfxFcPlatformFontList.cpp.patch`, `gfx_thebes_gfxFT2FontList.cpp.patch`,
`gfx_thebes_gfxDWriteFontList.cpp.patch`, `gfx_thebes_gfxPlatformFontList.cpp.patch`,
`get-microsoft-fonts.sh`, `README.fonts.md`, `README.md`,
`00_FONT_SYSTEM_HISTORY_AND_ROADMAP.md`, `POR_DRAFT_2026-08-03.md`. Rendered
first-class outputs (source-of-truth for re-rendering): `11-font-system_audit.md`,
`11-font-system_developer.md`, `11-font-system_layman.md` (+ their `*.filled.json`).

---


# ═══ REGENERATED DOCUMENT: 11-font-system.AUDIT (verbatim · rendered 2026-08-04 · score 96/100) ═══

# IBM-Style Audit Report: 11.FONT.SYSTEM

## SECTION A: DOCUMENT CONTROL

| Attribute | Value |
|---|---|
| **Target** | 11.FONT.SYSTEM |
| **Files scanned** | see payload |
| **Date / time** | 2026-08-04 07:13:56 |
| **Audit status** | PASS |

## SECTION B: EXECUTIVE SUMMARY (Plain Language)

This is safe to ship. The one part that could break text, a switch that makes the browser skip scanning your system fonts, is turned off in the code and is turned on nowhere. As delivered, the browser handles fonts exactly like normal Firefox and simply carries eight extra font files for reliable text in many languages. Think of it as a labour-saving button that ships taped over: the button exists and works, but it stays covered until someone proves the packed fonts cover everything, because using it blind can hide characters. Two honesty notes keep this from being a clean PASS with no caveats: the folder's claim of a big startup speed-up (about 40 seconds down to a few) has not been measured and should not be trusted as a number, and the Microsoft fonts it uses are legal to use but not to hand out to others.

## SECTION C: TECHNICAL SUMMARY (Developer)

Cross-platform, pref-gated skip of OS font enumeration (gfx.bundled_fonts.skip_system_scan, bool, hard-coded default false at gfxFcPlatformFontList.cpp:1754/1807, gfxFT2FontList.cpp:1551, gfxDWriteFontList.cpp:1656/1740, gfxPlatformFontList.cpp:791), plus static bundling of eight fonts via FINAL_TARGET_FILES.fonts (browser/fonts/moz.build:5-16). On the Linux reference target only the fontconfig backend executes; the DWrite and FT2 guards are portability spares, and the base-class patch only logs. The skip is dormant as shipped (pref set true nowhere; not registered, so absent from about:config until created). The always-active effect is the bundle, loaded because MOZ_BUNDLED_FONTS defaults on for Linux (toolkit/moz.configure:2191-2211). No new attack surface; the fingerprinting-reduction benefit is conditional on enabling the pref and therefore not realized as shipped. Precheck (rule-based) found 0 issues; all five patches reproduce the live tree byte-exact per the folder POR. Verdict: PASS to ship in the default-off state; enabling the pref is blocked on unmeasured glyph coverage.

## SECTION D: DETECTED DEFECTS

0 found by rules, 5 by review. Rule findings are deterministic; review findings are judgement.

### 🟡 P2-201 — P2 *(found by review)*

- **Plain English:** There is no automatic test that the packed fonts can actually draw every alphabet before someone turns the skip switch on. Turning it on blind is like sealing a first-aid kit without checking it has bandages.
- **Technical:** Topic-wide; no coverage gate exists for gfx.bundled_fonts.skip_system_scan. Enabling it removes fontconfig fallback (gfxFcPlatformFontList.cpp:1754).
- **Fix:** Add a preflight that renders a Latin/Cyrillic/Arabic/Hebrew/Thai/CJK/emoji corpus using only the bundled set and fails on tofu.
- **Effort:** 2-4h

### 🟢 P3-301 — P3 *(found by review)*

- **Plain English:** The folder's README states the browser starts far faster (about 40 seconds down to 2-4), but nobody measured it, and another note in the same folder gives a much smaller figure. A number no one measured should not be printed as if it were fact.
- **Technical:** README.fonts.md startup claim; the topic's own audit lists the measurement as an open TODO and the history doc says 'font enumeration takes 50-200 ms'.
- **Fix:** Relabel the figures 'not measured', or run a startup benchmark on a font-heavy system and cite the real delta.
- **Effort:** 1h (benchmark) or 10min (doc fix)

### 🟢 P3-302 — P3 *(found by review)*

- **Plain English:** On the Windows-only spare code, turning the skip on would trip a built-in sanity check that expects the font count to grow. It cannot happen on this Linux build, but it is a trap left for anyone who reuses the spare.
- **Technical:** gfxDWriteFontList: kBundledCount captured before the skipped GetFontsFromCollection; NS_ASSERTION(mFontFamilies.Count() > kBundledCount, ...) then expects strictly greater.
- **Fix:** Rebase the count after the skip decision or relax the assertion, if the DWrite path is ever enabled.
- **Effort:** 30min

### 🟢 P3-303 — P3 *(found by review)*

- **Plain English:** The switch does not show up in the settings page until you create it, but a note in the folder tells you to look for it there and expect it to already exist. Following that note as written would fail.
- **Technical:** Pref is unregistered (no StaticPrefList/.js/.yaml/.mjs entry); 00_FONT_SYSTEM_HISTORY_AND_ROADMAP.md 'Post-Build Verification' claims it appears in about:config by default.
- **Fix:** Correct the doc. Do NOT add a StaticPrefList entry unless about:config visibility is intended, as that changes behaviour.
- **Effort:** 15min

### 🟢 P3-304 — P3 *(found by review)*

- **Plain English:** The font-fetch script's opening comment says it grabs eight fonts, but it grabs seven. The eighth already ships with Firefox. Harmless, but it is a wrong number in a document meant to be trustworthy.
- **Technical:** get-microsoft-fonts.sh header comment 'the 8 font files' vs NEEDED_FONTS array of 7 (Twemoji excluded, CC-BY).
- **Fix:** Change the comment to 7.
- **Effort:** 5min

## SECTION E: PRODUCTION READINESS

**Overall readiness: 🟡 88%**

**Done:**
- [x] Four backends patched consistently with one pref (gfxFcPlatformFontList, gfxFT2FontList, gfxDWriteFontList, gfxPlatformFontList).
- [x] Skip pref default false at every read site; set true nowhere; default-OFF invariant holds.
- [x] browser/fonts/moz.build wires the eight-font bundle; all eight files physically present in browser/fonts/.
- [x] MOZ_BUNDLED_FONTS defaults on for Linux, so the bundle is packaged/loaded on the reference target.
- [x] [GORILLA]/[Gorilla] provenance markers present at every edit site.
- [x] .gitignore excludes *.ttf/*.ttc with the TwemojiMozilla.ttf CC-BY exception.
- [x] get-microsoft-fonts.sh implements a legal acquisition path and README.fonts.md documents the use-vs-redistribution EULA line and the compiled-binary caveat.
- [x] All five patches reproduce the live tree byte-exact (folder POR); precheck rules found 0 issues.

**To do:**
- [ ] P2-201: automated bundled-font glyph-coverage gate before the pref is ever enabled.
- [ ] P3-301: measure or relabel the startup figures.
- [ ] P3-302: fix the DWrite spare assertion if that path is reused.
- [ ] P3-303: correct the about:config-visibility claim in the history doc.
- [ ] P3-304: fix the '8 fonts' comment in get-microsoft-fonts.sh.
- [ ] Build-time warning if Microsoft fonts are present in omni.ja at packaging (redistribution reminder).

**Not verified:**
- Startup-time delta from the skip: not measured on any hardware; the README's ~40s to ~2-4s / 10x figures are unverified and contradicted by the history doc.
- Bundled-font glyph coverage across Latin/Cyrillic/Arabic/Hebrew/Thai/CJK/emoji: the corpus test was never run.
- Runtime rendering of the bundled fonts by a running browser: inferred from MOZ_BUNDLED_FONTS defaulting on plus files present; not observed at runtime here.
- Behaviour with the pref enabled: never exercised on the reference target, so the skip and content-process filter paths are unproven in practice.
- The Segoe UI script-coverage claim (Latin/Greek/Cyrillic/Arabic/Hebrew/Thai) comes from the script comment; not independently checked against the font cmap.
- get-microsoft-fonts.sh network path (ISO download, WIM extraction, per-font sha256): not executed in this audit.

## SECTION F: PHASED PLAN

### Phase 1 — `toolchain / preflight`
- **Change:** Bundled-font coverage gate: render the multi-script corpus using only the bundled set; fail on missing glyphs.
- **Expected impact:** Removes the foot-gun of enabling the pref without proven coverage; converts P2-201 to done.

### Phase 1 — `packaging step`
- **Change:** Warn at build/packaging time if Microsoft fonts are present in omni.ja.
- **Expected impact:** Surfaces the redistribution caveat at the moment it matters instead of in a README.

### Phase 2 — `startup benchmark`
- **Change:** Measure time-to-first-paint, pref off vs on, on a machine with 500+ system fonts and on the ~4 GB target profile.
- **Expected impact:** Replaces the unverified README numbers with a real, citable delta.

## POSITIVE OBSERVATIONS

- Default-off is the mature choice: the machinery is present and documented, activation deliberate, and the tree confirms it is never enabled.
- Cross-platform parity is honest about being parity: the Windows/Android guards are labelled spares, not pretended to be active on Linux.
- README.fonts.md is candid about the EULA line, naming what is legal (use) and what is not (binary redistribution) with a concrete workaround.
- The get-microsoft-fonts.sh + .gitignore-exclude pattern cleanly ships the method, not the restricted binaries, with a CC-BY exception for Twemoji.
- Provenance markers are present at every edit, satisfying the transparency convention.

## VERIFICATION COMMANDS

Run these to check the claims above rather than trusting them.

```bash
grep -rn 'bundled_fonts.skip_system_scan' gfx/thebes/   # every hit ends in ', false)'
grep -rln 'bundled_fonts.skip_system_scan' --include='*.js' --include='*.yaml' --include='*.mjs' .   # no matches
ls browser/fonts/   # consola/segoeui/segoeuib/seguisb/SegUIVar/TwemojiMozilla/YuGothB/YuGothR
sed -n '2187,2211p' toolkit/moz.configure   # MOZ_BUNDLED_FONTS default-on for Linux browser build
grep -n 'ttf\|ttc\|Twemoji' .gitignore   # *.ttf, *.ttc, !TwemojiMozilla.ttf
grep -n 'NEEDED_FONTS\|8 font' get-microsoft-fonts.sh   # 7-entry array vs '8 font files' comment
```

## Claim Sources

| Claim | Basis | Evidence |
|-------|-------|----------|
| Pref default false at every read site | 📄 stated in input | Preferences::GetBool("gfx.bundled_fonts.skip_system_scan", false) |
| Read sites across four backends | 🤖 model inference | *(none — model judgment)* |
| Eight fonts wired via FINAL_TARGET_FILES.fonts | 📄 stated in input | FINAL_TARGET_FILES.fonts += [ |
| MOZ_BUNDLED_FONTS defaults on for Linux (toolkit/moz.configure:2191-2211) | 🤖 model inference | *(none — model judgment)* |
| Content-process list filtered to app-bundled families when on | 📄 stated in input | return !aEntry.appFontFamily(); |
| Base-class patch only logs | 📄 stated in input | Bundled-fonts-only mode active, system font scan will be skipped |
| DWrite assertion expects strictly greater count after the skipped collection | 📄 stated in input | NS_ASSERTION(mFontFamilies.Count() > kBundledCount, |
| Pref unregistered; absent from about:config until created; set true nowhere | 🤖 model inference | *(none — model judgment)* |
| .gitignore excludes *.ttf/*.ttc with TwemojiMozilla exception | 🤖 model inference | *(none — model judgment)* |
| Script fetches seven fonts; comment says eight | 📄 stated in input | out only the 8 font files this browser needs |
| EULA permits use, not redistribution; baked-in binary is redistribution | 📄 stated in input | Handing that binary to others is redistribution too |
| Startup figures unmeasured and contradicted by history doc | 🤖 model inference | *(none — model judgment)* |
| Precheck rules found 0 issues; patches byte-exact per POR | 🤖 model inference | *(none — model judgment)* |


---
**How to verify this document:**
`📄 stated in input` — the model's phrasing of something your source text said.
Find the matching line in the original to verify.
`🤖 model inference` — the model's own judgment or synthesis. Treat as opinion,
not measurement. Re-run on the same input and check whether specific numbers
stay consistent between runs.

---

# ═══ REGENERATED DOCUMENT: 11-font-system.DEVELOPER (verbatim · rendered 2026-08-04 · score 90/100) ═══

# Font System — Bundled Font Set plus Off-by-Default System-Scan Skip (gfx.bundled_fonts.skip_system_scan)

> Generated 2026-08-04 | Source: `11.FONT.SYSTEM`

---

## Purpose

This topic contains two independent mechanisms. First, browser/fonts/moz.build adds eight font files to FINAL_TARGET_FILES.fonts (verified browser/fonts/moz.build:5-16): four Segoe UI faces, two Yu Gothic collections, Consolas, and the pre-existing Twemoji. This wiring is unconditionally active on gtk and windows toolkits, and because MOZ_BUNDLED_FONTS defaults on for Linux (toolkit/moz.configure:2191-2211, bundled_fonts_default returns true when target.kernel == 'Linux' and allow_bundled_fonts is true for the browser project), the bundle is packaged and available to the browser on the reference target. Second, a runtime pref, gfx.bundled_fonts.skip_system_scan (bool, hard-coded default false), gates an early skip of OS font enumeration across four backend files. Trust level: the code reads one local preference and, when it is true, omits work; it introduces no new external input.

## Design Rationale

The skip is gated default-off because enabling it without adequate bundled-font coverage silently produces tofu for uncovered scripts. Machinery ready, activation deliberate. The same guard was added to all four backends (fontconfig, DWrite, FT2, and the cross-platform base) for parity, even though only the fontconfig path executes on this Linux build, so the option survives a platform move. The Microsoft fonts ship as an acquisition method (get-microsoft-fonts.sh) rather than committed binaries because the Microsoft EULA licenses use, not redistribution; .gitignore excludes *.ttf/*.ttc with a TwemojiMozilla.ttf exception (CC-BY).

## Architecture

- **Pattern:** Runtime-pref-gated early-skip inserted into each platform font-list PopulateFontList/InitFontList path; plus a static build-time font bundling list.
- **Trust boundary:** The code trusts one local pref value. It does not trust or parse any network or web input. The get-microsoft-fonts.sh script trusts Microsoft's evaluation ISO as the font source and verifies each extracted file only by printing a truncated sha256 (no pinned expected hash).
- **Attack surface:** No new remote attack surface. The pref read is local. The only network action in the topic is get-microsoft-fonts.sh downloading the Microsoft eval ISO, which is operator-initiated and out of the browser's runtime path.
- **Dependencies:** `mozilla::Preferences::GetBool`, `MOZ_BUNDLED_FONTS build define (toolkit/moz.configure:2208-2211)`, `fontconfig (FcConfigGetFonts / FcSetSystem) on Linux`, `FINAL_TARGET_FILES.fonts (moz.build)`, `7z or 7za and curl (get-microsoft-fonts.sh runtime)`

## Flags & Configuration

| Name | Type | Default | Effect | Notes |
|------|------|---------|--------|-------|
| `gfx.bundled_fonts.skip_system_scan` | `bool` | `false` | When true, each patched backend omits its OS font enumeration and (Linux) filters the content-process font list to app-bundled families only. | Read via Preferences::GetBool with a hard-coded false default at gfxFcPlatformFontList.cpp:1754 and :1807, gfxFT2FontList.cpp:1551, gfxDWriteFontList.cpp:1656 and :1740, gfxPlatformFontList.cpp:791. NOT registered in StaticPrefList.yaml or any .js/.yaml/.mjs, so it does not appear in about:config until created by hand. Set true nowhere in the tree; default-OFF invariant holds. |
| `MOZ_BUNDLED_FONTS` | `bool (build define)` | `on for Linux browser build` | Compiles the bundled-font loading path and packages FINAL_TARGET_FILES.fonts. | toolkit/moz.configure:2191-2211. Independent of the skip pref; this is why the eight fonts are active on the reference target while the skip stays dormant. |

## API Surface

| Symbol | Description | Side Effects |
|--------|-------------|--------------|
| `gfxFcPlatformFontList::PopulateFontList (region)` | When pref false, calls FcConfigGetFonts(nullptr, FcSetSystem) + AddFontSetFamilies; when true, logs and skips. | Populates (or does not) the platform font family table from fontconfig. |
| `gfxFcPlatformFontList content-process list filter` | When pref true, removes entries where !appFontFamily() before handing the list to content processes. | Content processes see only app-bundled families under the skip mode. |
| `gfxDWriteFontList (Windows spare)` | Windows DirectWrite enumeration, skipped when pref true. | Never executes on the Linux reference target. |
| `gfxFT2FontList (Android spare)` | Android FreeType enumeration and profile/app 'fonts' directory scans, skipped when pref true. | Never executes on the Linux desktop reference target (fontconfig is the active backend). |
| `gfxPlatformFontList::InitFontList (base)` | Reads the pref into bundledFontsOnly and emits LOG_FONTINIT only; it performs no skip itself. | Log line only; the actual skip lives in the platform subclasses. |

## Kill Switches

### `PopulateFontList / MakeFontListForContentProcess (gfxFcPlatformFontList.cpp:1754, :1807) and the sibling backends`
- **Condition:** gfx.bundled_fonts.skip_system_scan == true
- **Effect:** Skips system font enumeration; on Linux also strips non-app font entries before sending the list to content processes.
- reversible
- Reverts instantly by setting the pref false or removing it. Do not enable before verifying bundled-font glyph coverage against target pages.

### `.gitignore:62-64 (patches repo) + get-microsoft-fonts.sh`
- **Condition:** operational / repository policy
- **Effect:** *.ttf and *.ttc are excluded from version control, with !TwemojiMozilla.ttf re-included; the Microsoft fonts are fetched locally rather than committed.
- reversible
- Prevents committing MS-font binaries. See README.fonts.md for the compiled-binary redistribution caveat.

## Dead Code

- **`gfx/thebes/gfxDWriteFontList.cpp and gfx/thebes/gfxFT2FontList.cpp skip guards`** — Not dead, but unreachable on the reference target: the Linux desktop uses the fontconfig backend, so the DirectWrite and FreeType backends never execute here. They are deliberate portability spares. (risk: Removing them costs cross-platform parity with no benefit to the Linux build; keep them.)
- **`gfx/thebes/gfxPlatformFontList.cpp:791 bundledFontsOnly`** — Assigned and read only to gate a LOG_FONTINIT line at :793; the base method performs no skip. The comment 'system font scan will be skipped' describes the subclass behaviour, not this function. (risk: Harmless. Consider softening the comment to avoid implying the base function skips anything.)

## Performance

- **CPU:** Not measured. When the pref is off (as shipped) there is no change. When on, the fontconfig FcConfigGetFonts + AddFontSetFamilies pass is omitted at startup on Linux.
- **MEMORY:** Not measured at runtime. The bundle adds about 34 MB of font files on disk (measured: consola 459 KB, segoeui 975 KB, segoeuib 965 KB, seguisb 991 KB, SegUIVar 1.85 MB, TwemojiMozilla 1.47 MB, YuGothB 14.7 MB, YuGothR 13.9 MB). Bundled fonts load regardless of the pref.
- **IO:** Not measured. The skip, when on, removes the disk reads fontconfig performs to enumerate system font directories at startup.
- **NOTES:** The README's ~40s to ~2-4s startup figure and '10x cold-boot win' are unverified and are contradicted by the folder's history doc ('font enumeration takes 50-200 ms'). Do not cite them as measured.

## Security

- **Remote execution:** None. No code path here parses remote input.
- **Data handling:** Reads one local pref. get-microsoft-fonts.sh downloads a Microsoft eval ISO to a gitignored work dir and copies extracted fonts into browser/fonts; it uploads nothing.
- **Attack surface:** No new browser attack surface. The pref read is local and side-effect-free beyond skipping work.
- **Notes:** System font list is a known fingerprinting vector. With the pref on, the browser stops enumerating it and trims the content-process list to bundled-only, reducing that signal. This benefit is realized only when the pref is on; as shipped (off) there is no fingerprinting change.

## Error Conditions

| Error | Cause | Remedy |
|-------|-------|--------|
| `Tofu (missing glyphs) on non-Latin pages` | Pref enabled while bundled fonts lack coverage for the page's script; system fonts that would have covered it are skipped. | Set the pref false. Do not enable until a coverage corpus (Latin/Cyrillic/Arabic/Hebrew/Thai/CJK/emoji) renders tofu-free using only the bundled set. |
| `NS_ASSERTION(mFontFamilies.Count() > kBundledCount) firing (Windows debug)` | In gfxDWriteFontList, kBundledCount is captured before GetFontsFromCollection; skipping the collection leaves the count equal, not greater. The following assertion expects strictly greater. | If the DWrite spare is ever enabled, adjust the assertion or the count baseline. Not reachable on the Linux reference target. |
| `get-microsoft-fonts.sh exits 1 / 2 / 3` | 1 = 7z/7za or curl missing; 2 = no ISO_URL pinned and ISO absent (manual download required); 3 = install.wim not found in the ISO. | Install p7zip-full and curl; provide the eval ISO or an ISO_URL; verify the ISO edition contains sources/install.wim. |

## Tasks

### Verify the default-OFF invariant

Confirm no read site or settings file turns the skip on before trusting the build. Run:

```bash
# every hit must end in ', false)'
grep -rn 'bundled_fonts.skip_system_scan' gfx/thebes/
# must return nothing: the pref is registered/set nowhere
grep -rln 'bundled_fonts.skip_system_scan' --include='*.js' --include='*.yaml' --include='*.mjs' .
# confirm the bundle wiring and the default-on Linux build flag
grep -n 'FINAL_TARGET_FILES.fonts' browser/fonts/moz.build
sed -n '2187,2211p' toolkit/moz.configure
```


**Prerequisites:**
- A checkout of the firefox source tree
- grep

**Step 1:** grep -rn 'bundled_fonts.skip_system_scan' gfx/thebes/
  - Expected: Six read sites, each ending in ', false)'.
**Step 2:** grep -rln 'bundled_fonts.skip_system_scan' --include='*.js' --include='*.yaml' --include='*.mjs' .
  - Expected: No matches; the pref is registered/set nowhere.

**After this task:** The skip is confirmed dormant; the browser enumerates system fonts as upstream does.

### Apply or revert the five patches

Re-apply the topic against a clean tree, or back it out.

**Prerequisites:**
- A clean firefox tree at the baseline the patches target

**Step 1:** patch -p1 < gfx_thebes_gfxFcPlatformFontList.cpp.patch (and the other three gfx patches + browser_fonts_moz.build.patch)
  - Expected: All hunks apply with no .rej files.
**Step 2:** To revert: patch -p1 -R < <each>.patch
  - Expected: Clean reversal; tree returns to upstream font behaviour.

**After this task:** Tree matches (or no longer contains) the topic. Per the folder POR, vanilla + patch -p1 reproduces the live tree byte-exact for all five.

### Acquire the Microsoft fonts legally

Populate browser/fonts with the seven Microsoft faces before a build that uses them.

**Prerequisites:**
- 7z or 7za and curl installed
- ~6 GB free disk
- Right to use the fonts; awareness of the no-redistribution constraint

**Step 1:** bash get-microsoft-fonts.sh
  - Expected: Tool check passes; script requests the Win11 Enterprise eval ISO (or downloads it if ISO_URL is set).
**Step 2:** Provide the ISO per the printed instructions and re-run.
  - Expected: Each font prints [OK] with a truncated sha256 and is copied into browser/fonts.

**After this task:** browser/fonts holds all eight bundled files (seven fetched + pre-existing Twemoji).

### Gate coverage before ever enabling the skip

The skip is a foot-gun without confirmed glyph coverage.

**Prerequisites:**
- A rendering corpus spanning Latin, Cyrillic, Arabic, Hebrew, Thai, CJK, emoji

**Step 1:** Render the corpus using only the bundled set (system fonts removed or the pref on) and inspect for tofu.
  - Expected: No missing-glyph boxes. Only then is enabling the pref defensible.

**After this task:** You have evidence the bundle covers your target scripts, or you keep the pref off.

## Troubleshooting

**Symptom:** Non-Latin text renders as boxes after enabling the pref.
**Cause:** Bundled fonts lack coverage for that script; system fallback is skipped.
**Remedy:** Set gfx.bundled_fonts.skip_system_scan false.
**Verify:** Text renders again with the pref off.

**Symptom:** The pref is missing from about:config.
**Cause:** It is not registered in StaticPrefList; it exists only once created.
**Remedy:** Create it manually if needed, or leave absent for the safe default.
**Verify:** grep confirms no StaticPrefList entry.

**Symptom:** Windows debug build asserts on font count when skip is on.
**Cause:** kBundledCount captured pre-skip; assertion expects strictly greater after GetFontsFromCollection, which was skipped.
**Remedy:** Adjust the assertion/baseline in the DWrite spare if that path is ever used.
**Verify:** Assertion no longer fires with the fix; not reachable on Linux.

## Technical Debt

🟠 **MEDIUM** — No automated bundled-font glyph-coverage gate; enabling the pref without one risks tofu. → Add a preflight test that renders a Latin/Cyrillic/Arabic/Hebrew/Thai/CJK/emoji corpus using only the bundled set and fails on missing glyphs.
🟡 **LOW** — DWrite spare: skipping GetFontsFromCollection leaves mFontFamilies.Count() == kBundledCount, which trips NS_ASSERTION(mFontFamilies.Count() > kBundledCount) in debug and may force the GDI backend. → If the Windows path is ever enabled, capture the baseline after the skip decision or relax the assertion. Windows-only spare; not reachable on the reference target.
🟡 **LOW** — gfxPlatformFontList base patch computes bundledFontsOnly only to log; the comment overstates that the base function skips the scan. → Reword the comment; the skip is in the subclasses.
🟡 **LOW** — get-microsoft-fonts.sh header says '8 font files' but NEEDED_FONTS lists 7 (Twemoji excluded, CC-BY/in-tree). → Change the comment to 7 to match the array.
🟡 **LOW** — Pref unregistered contradicts 00_FONT_SYSTEM_HISTORY_AND_ROADMAP.md's 'should appear in about:config, default false' verification step. → Correct the doc, or register the pref only if about:config visibility is intended (a deliberate behaviour change).
🟡 **LOW** — README.fonts.md startup figures (~40s to ~2-4s, 10x) are unmeasured and internally contradicted. → Mark them 'not measured' or run a benchmark on a font-heavy system; do not present as fact.

## Impact If Removed

Removing the skip patches: no startup optimisation is available; every launch performs full OS font enumeration (upstream behaviour). Since the pref ships off, removing the skip changes nothing observable as delivered. Removing the bundling (browser/fonts/moz.build change): the browser loses its guaranteed cross-language font set and falls back to whatever the system provides, which on a minimal ~4 GB target install can produce tofu for scripts the system lacks. Removing get-microsoft-fonts.sh: users lose the documented legal path to obtain the Microsoft fonts, and a build expecting them would package fewer faces.

## Claim Sources

| Claim | Basis | Evidence |
|-------|-------|----------|
| moz.build bundles eight fonts via FINAL_TARGET_FILES.fonts (browser/fonts/moz.build:5-16) | 📄 stated in input | FINAL_TARGET_FILES.fonts += [ |
| Bundled set: consola, segoeui, segoeuib, seguisb, SegUIVar, TwemojiMozilla, YuGothB, YuGothR | 📄 stated in input | "SegUIVar.ttf", |
| Pref read with hard-coded false default at every site | 📄 stated in input | Preferences::GetBool("gfx.bundled_fonts.skip_system_scan", false) |
| Read sites: gfxFcPlatformFontList.cpp:1754,1807; gfxFT2FontList.cpp:1551; gfxDWriteFontList.cpp:1656,1740; gfxPlatformFontList.cpp:791 | 🤖 model inference | *(none — model judgment)* |
| Linux path filters content-process list to app-bundled families when on | 📄 stated in input | return !aEntry.appFontFamily(); |
| MOZ_BUNDLED_FONTS defaults on for Linux browser build (toolkit/moz.configure:2191-2211) | 🤖 model inference | *(none — model judgment)* |
| gfxPlatformFontList base patch only logs, does not skip | 📄 stated in input | Bundled-fonts-only mode active, system font scan will be skipped |
| DWrite kBundledCount captured before GetFontsFromCollection; NS_ASSERTION expects strictly greater | 📄 stated in input | NS_ASSERTION(mFontFamilies.Count() > kBundledCount, |
| Pref not registered in StaticPrefList/.js/.yaml/.mjs; absent from about:config until created | 🤖 model inference | *(none — model judgment)* |
| Pref set true nowhere; default-OFF invariant holds | 🤖 model inference | *(none — model judgment)* |
| .gitignore excludes *.ttf/*.ttc with TwemojiMozilla exception (patches repo .gitignore:62-64) | 🤖 model inference | *(none — model judgment)* |
| Script fetches seven Microsoft fonts; comment says eight | 📄 stated in input | out only the 8 font files this browser needs |
| EULA permits use, not redistribution; baked-in binary is redistribution too | 📄 stated in input | Handing that binary to others is redistribution too |
| Script requires 7z/7za and curl; exit codes 1/2/3 | 📄 stated in input | MISSING TOOL: $1  (install it and re-run) |
| Bundle adds ~34 MB on disk (per-file sizes measured from browser/fonts/) | 🤖 model inference | *(none — model judgment)* |
| Startup 40s-to-2-4s / 10x figures are unverified and contradicted by the history doc's 50-200 ms | 🤖 model inference | *(none — model judgment)* |
| All five patches reproduce the live tree byte-exact (folder POR) | 🤖 model inference | *(none — model judgment)* |


---
**How to verify this document:**
`📄 stated in input` — the model's phrasing of something your source text said.
Find the matching line in the original to verify.
`🤖 model inference` — the model's own judgment or synthesis. Treat as opinion,
not measurement. Re-run on the same input and check whether specific numbers
stay consistent between runs.

*Auto-generated DITA-structured developer documentation.*

---

# ═══ REGENERATED DOCUMENT: 11-font-system.LAYMAN (verbatim · rendered 2026-08-04 · score 90/100) ═══

# The Font System: Bundled Fonts Plus an Off-by-Default Switch to Skip the System Font Scan — Plain Language Guide

> Generated 2026-08-04 from `11.FONT.SYSTEM`

---

## Should You Run This?

Ship the patches as they are: the risky part is off by default, so the browser behaves like normal Firefox for font scanning and simply carries eight extra fonts. Run get-microsoft-fonts.sh only if you personally have the right to use these Microsoft fonts and you understand you must not redistribute the resulting binary. Do not turn on gfx.bundled_fonts.skip_system_scan until someone has tested that the bundled fonts cover every language you care about; until then, leave it off.

## Worst Case, Honestly

The realistic worst case is a text-rendering problem, not a security one, and only if someone turns the off-by-default switch on. If the switch is enabled but the eight bundled fonts do not cover the language on a page you visit (for example Bengali or Thai), that text can appear as empty boxes instead of letters. Whether the bundled set covers every script has not been tested, so this risk is real if you flip the switch without checking. As delivered, with the switch off, this cannot happen by accident. The Microsoft-font script carries a legal caveat, not a safety one: you may use the fonts, but you may not hand out copies or a browser binary with them baked in.

## What Data This Touches

The five code patches send nothing anywhere. They read one local on/off setting and, at most, skip a chore. Nothing about you leaves your machine. The only piece here that touches the network is the helper script get-microsoft-fonts.sh, and only if you choose to run it: it downloads a roughly 5-6 GB Windows evaluation file from Microsoft's own website. That is a normal download from Microsoft; it does not upload anything about you.

## Before You Trust It

This folder contains a switch that could break text rendering if misused, and fonts with licensing strings attached. Both are checkable in minutes without reading any C++.

**Step 1:** In the firefox source tree, run: grep -rn 'bundled_fonts.skip_system_scan' gfx/thebes/
  - Look for: Every line ends with ', false)'. That 'false' is the default-off answer. If any read hard-codes 'true', the switch would be on; it should not be.
**Step 2:** Run: grep -rln 'bundled_fonts.skip_system_scan' --include='*.js' --include='*.yaml' --include='*.mjs' .
  - Look for: No results. That confirms nothing turns the switch on anywhere in the settings files.
**Step 3:** Run: ls browser/fonts/
  - Look for: Eight font files: consola.ttf, segoeui.ttf, segoeuib.ttf, seguisb.ttf, SegUIVar.ttf, TwemojiMozilla.ttf, YuGothB.ttc, YuGothR.ttc. These are the exact eight the build packs.
**Step 4:** Open .gitignore in the patches repo and look for the font rules.
  - Look for: Lines '*.ttf', '*.ttc', and '!TwemojiMozilla.ttf'. This is the deliberate rule that keeps the Microsoft font files out of the shared code while allowing the freely-shareable Twemoji font in.

## The Big Picture

This folder does two separate things, and it helps to keep them apart. The first thing is always on: the build ships eight font files inside the browser so that web pages and menus have a dependable set of letters to draw with, even on a small, cheap computer that may not have many fonts installed. The second thing is a switch that is turned OFF when you get it: an option that would let the browser skip taking a full inventory of the fonts on your operating system every time it starts.

Because that switch ships OFF, the browser you receive still scans your system fonts at startup exactly like normal Firefox. Nothing about that behaviour changes unless someone deliberately turns the switch on. The one change you always get is the eight bundled fonts riding along inside the program.

The folder also holds a helper script, get-microsoft-fonts.sh. Some of the bundled fonts (Segoe UI, Consolas, Yu Gothic) are made by Microsoft. Microsoft lets you use them for free but does not let anyone hand out copies of the files. So instead of copies, the folder gives you a small program that fetches them from Microsoft's own free download, onto your own machine.

## Key Concepts

| Name | What It Means | Real-World Comparison |
|------|--------------|------------------------|
| `Bundled fonts` | Font files packed inside the browser itself, so it never has to rely on what the computer already has. | A traveller who packs their own toothbrush instead of hoping the hotel has one. |
| `System font scan` | The startup chore where the browser lists every font installed on your operating system. | Walking every aisle of a library to write down every book before you open the doors. |
| `gfx.bundled_fonts.skip_system_scan` | The single off-by-default switch that, if turned on, tells the browser to skip that startup chore and use only its bundled fonts. | A 'skip the inventory' button on the librarian's desk, taped over because it is only safe once you are sure the packed books cover everything. |
| `fontconfig` | The part of Linux that keeps track of installed fonts. On this build it is the piece that actually does the scan. | The library's card catalogue system. |
| `Tofu` | The empty boxes you see instead of letters when no font on hand can draw a character. | Blank price tags on shelves when the label printer ran out of a language. |

## How It Works — Step by Step

### Step 1: The browser packs eight fonts

A build file, browser/fonts/moz.build, lists eight font files to copy into the finished browser: four Segoe UI faces, two Yu Gothic files, Consolas, and Twemoji. On this Linux build the packing is switched on by default, so those eight fonts travel inside the program whether or not the skip switch is ever used. This is the one part that is always active.

### Step 2: The off switch sits in the code, set to false

Each of the font-loading files checks one setting, gfx.bundled_fonts.skip_system_scan, and every check hard-codes the answer 'false' when the setting has never been set. So out of the box the answer is always no-do-not-skip. The switch is not even registered, which means it does not appear in the about:config settings page until someone creates it by hand.

### Step 3: If the switch were on, the Linux scan is skipped

In the Linux font file (gfxFcPlatformFontList.cpp), turning the switch on makes the browser skip asking fontconfig for the system font list, and instead print a log line saying it skipped. It also trims the font list it shares with page-rendering helper processes down to only the bundled fonts. This is the actual mechanism, but it only runs if you enable the switch.

### Step 4: Three of the four patched files never run here

The same switch was added to the Windows font file (gfxDWriteFontList.cpp) and the Android font file (gfxFT2FontList.cpp), plus a shared file that only prints a log line (gfxPlatformFontList.cpp). This build is Linux and uses fontconfig, so the Windows and Android versions are spares that never execute on your machine. They are kept so the option would still exist if the project ever moved platforms.

### Step 5: The helper script fetches Microsoft's fonts, legally

get-microsoft-fonts.sh downloads Microsoft's free Windows 11 Enterprise evaluation disc image, opens it like a zip with 7-Zip, pulls out the specific font files, checks them, and copies them into browser/fonts. It does not install Windows and it does not commit the fonts into the shared code; you fetch them yourself, from Microsoft, onto your own machine.

## Quirky Things Worth Knowing

### The off switch is invisible until you create it

The setting is never registered with the browser, so it will not show up if you search for it in about:config. It only starts existing once you add it yourself. An older note in this folder that says it should already appear in about:config is wrong on that point; the safety behaviour (off by default) is still correct.

### Most of these patches do nothing on your computer

Four files were patched, but on this Linux build only the fontconfig one can ever act, and even that one is asleep because the switch is off. As shipped, the practical effect of the whole optimisation is: none yet. The real, active change from this folder is the eight bundled fonts.

### The script says eight fonts but fetches seven

A comment at the top of get-microsoft-fonts.sh says it takes out 'the 8 font files this browser needs,' but the list it actually downloads has seven. The eighth bundled font, Twemoji, is Mozilla's own and already ships with Firefox, so the script does not fetch it. The comment is just off by one.

### The 'much faster startup' numbers are not measured

A README in this folder claims startup dropped from about 40 seconds to about 2-4 seconds. No benchmark backs that up; the project's own audit still lists 'measure the startup change' as an open task, and another note in the folder gives a much smaller figure. Treat the big speed numbers as an unproven claim, not a fact.

### Legal to use, not to hand out

You may use the Microsoft fonts. You may not redistribute the font files, and a browser you compile with them baked in also counts as handing them out. If you want to share your build, either have people run the script themselves, or build with open fonts such as Noto instead.

## What This Means For You

### Battery, Processor & Memory

Not measured. When the switch is off (as shipped) there is no change from normal Firefox. The eight bundled fonts add roughly 34 MB of font files to the installed browser (measured from the files on disk), most of it the two Yu Gothic collections at about 14 MB each.

### Speed

Not measured. The folder's README claims a drop from about 40 seconds to about 2-4 seconds, but no benchmark supports that number and the project's own audit lists the measurement as still to do; treat it as unverified. What is certain: the skip switch ships off, so as delivered your startup font handling is unchanged.

### Your Privacy

As shipped, no change. If the switch were turned on, the list of your system fonts (which can help identify your specific machine) would stop being gathered by the browser's own font code, and the font list handed to page-rendering processes would be trimmed to only the bundled fonts. That privacy benefit only exists when the switch is on, and it ships off.

### Your Internet

Zero from the patches. The helper script, only if you run it, downloads a roughly 5-6 GB file from Microsoft one time.

## The Off Switch

**What it is:** The whole optimisation is one setting, gfx.bundled_fonts.skip_system_scan, and it is off (false) by default in every place the code reads it. There is nothing you can trip by accident; you would have to add the setting yourself and turn it on.

**Without it:** Without the switch, every browser start does the full system font inventory, exactly like ordinary Firefox. On a slow disk that inventory takes some time on each launch, though how much on this hardware was not measured.

**Think of it like:** A 'skip the inventory' button that ships taped over. The tape (the default-off setting) is there because skipping the inventory is only safe once you have confirmed your packed supplies cover everything you will need.

## Get the Microsoft fonts the honest way (optional)

**Before you start:**
- The tools 7z (or 7za) and curl installed. On Debian or Ubuntu: sudo apt install p7zip-full curl
- About 6 GB of free disk space for the download
- The right to use these Microsoft fonts, and an understanding that you may not redistribute them

**Step 1:** Open a terminal in this folder and run: bash get-microsoft-fonts.sh
  - You should see: The script checks for its tools and then tells you it needs the Windows 11 Enterprise evaluation ISO.
**Step 2:** Follow the printed instructions to download the ISO from Microsoft's evaluation page, or re-run with a direct link as ISO_URL.
  - You should see: The script extracts the fonts, prints an [OK] line with a checksum for each, and copies them into browser/fonts.
**Step 3:** Leave the skip switch alone. Do not turn on gfx.bundled_fonts.skip_system_scan.
  - You should see: The browser keeps using both its bundled fonts and your system fonts, which is the safe, tested state.

## If Something Goes Wrong

**Some text on web pages shows as empty boxes after you turned the switch on.**
You enabled gfx.bundled_fonts.skip_system_scan, and the bundled fonts do not cover that language. The system fonts that would have covered it are now being skipped.
What to do: Set the switch back to false (or delete it). Do not enable it until the bundled fonts are confirmed to cover every script you read.

**You cannot find gfx.bundled_fonts.skip_system_scan in about:config.**
The setting is not registered, so it does not appear until you create it.
What to do: This is expected. If you must set it, create it by hand as a Boolean. Leaving it absent keeps the safe default.

**The font script stops and says a tool is missing.**
7z (or 7za) or curl is not installed.
What to do: Install them, for example: sudo apt install p7zip-full curl, then run the script again.

**The script reports [MISS] for YuGothR.ttc or YuGothB.ttc.**
Yu Gothic lives in the Japanese language pack and may be absent from the English evaluation image.
What to do: Fetch it from a Japanese font set or a Japanese evaluation image, as the script's own message explains.

## Why a Developer Would Do This

A developer building for cheap, older machines wants two things: consistent text in many languages without depending on whatever fonts happen to be installed, and a faster start on slow disks. Bundling fonts buys the first. The skip switch is the tool for the second, but it can hide characters if the bundle is incomplete, so a careful developer builds the machinery, leaves it off, and refuses to flip it until coverage is proven. Shipping the font-fetch method instead of the font files keeps the project on the right side of Microsoft's licence.

## Why It Matters That You Can Read This

You do not have to take any of this on faith. You can search the code for the switch's name and see for yourself that it reads 'false' everywhere, in the actual shipped source, not just in a promise. You can list the browser's fonts folder to see exactly which eight files are bundled, and you can read the .gitignore to confirm the Microsoft font files are deliberately kept out of the shared code. If you could not read this, you would be trusting a stranger's word that the risky switch is off and that no proprietary fonts were quietly redistributed. Here, you can check both in about a minute.

## Glossary

**Bundled font** — A font file packed inside the browser so it is always available.

**fontconfig** — The Linux service that lists and manages installed fonts; the piece this build's scan talks to.

**System font scan** — The startup step where the browser inventories every font on your operating system.

**Tofu** — The empty boxes shown when no available font can draw a character.

**Pref (preference)** — A single on/off or value setting inside the browser.

**about:config** — The page in Firefox where preferences can be viewed and changed.

**omni.ja** — The archive file inside Firefox that holds most of its assets, and, when bundled, the fonts.

**EULA** — The licence agreement that says what you may and may not do with software or, here, fonts.

**CC-BY** — A permissive licence; Twemoji uses it, which is why that one font may be shared freely.

**SIL OFL** — The Open Font License, used by open fonts such as Noto, which may be redistributed in binary form.

## Claim Sources

| Claim | Basis | Evidence |
|-------|-------|----------|
| Eight font files are bundled via FINAL_TARGET_FILES.fonts | 📄 stated in input | FINAL_TARGET_FILES.fonts += [ |
| The bundled set is consola, segoeui, segoeuib, seguisb, SegUIVar, TwemojiMozilla, YuGothB, YuGothR | 📄 stated in input | "consola.ttf", |
| The pref defaults to false at every read site | 📄 stated in input | Preferences::GetBool("gfx.bundled_fonts.skip_system_scan", false) |
| When enabled, the Linux path skips the fontconfig system scan | 📄 stated in input | Skipped system fontconfig scan (bundled-only mode) |
| When enabled, the font list to content processes is filtered to bundled-only | 📄 stated in input | Filtered font list to bundled-only for content process |
| The DWrite (Windows) and FT2 (Android) files carry the same switch as spares | 📄 stated in input | Skipped DirectWrite system font collection (bundled-only mode) |
| The reference build is Linux and uses fontconfig, so DWrite/FT2 patches never run here | 🤖 model inference | *(none — model judgment)* |
| The pref is not registered anywhere, so it is absent from about:config until created | 🤖 model inference | *(none — model judgment)* |
| MOZ_BUNDLED_FONTS defaults on for Linux, so the bundle is packaged and loaded (toolkit/moz.configure:2191-2211) | 🤖 model inference | *(none — model judgment)* |
| The script's NEEDED_FONTS list contains seven fonts, though its comment says eight | 📄 stated in input | out only the 8 font files this browser needs |
| Twemoji is CC-BY and already ships with Firefox, so the script does not fetch it | 📄 stated in input | TwemojiMozilla.ttf is CC-BY, shipped by Mozilla |
| The startup 40s to 2-4s claim is not measured | 🤖 model inference | *(none — model judgment)* |
| The Microsoft EULA permits use but not redistribution of the font files | 📄 stated in input | Microsoft's EULA permits USE of these fonts. It does NOT grant you the right to REDISTRIBUTE |
| A compiled binary with the fonts baked in also counts as redistribution | 📄 stated in input | A browser BINARY you compile with these fonts baked in also contains them. Handing that binary to others is redistribution too |
| The script needs 7z/7za and curl | 📄 stated in input | sudo apt install p7zip-full curl |
| The two Yu Gothic collections are about 14 MB each on disk | 🤖 model inference | *(none — model judgment)* |


---
**How to verify this document:**
`📄 stated in input` — the model's phrasing of something your source text said.
Find the matching line in the original to verify.
`🤖 model inference` — the model's own judgment or synthesis. Treat as opinion,
not measurement. Re-run on the same input and check whether specific numbers
stay consistent between runs.

*Human Track. Its Developer Track twin covers the same changes in technical detail. Neither is a simplified copy of the other — they are the same truth in two languages.*

---

# ═══ APPENDIX: Room-clearing POR (verbatim · 2026-08-03 · read-only ground-truth pass that this regeneration is built on) ═══

# POR — 11.FONT.SYSTEM room clearing (2026-08-03)

Per `patches/SOP.room-clearing-and-poison-audit.md`. Method: every claim verified against the
LIVE tree (`the source tree`) and the VANILLA vault
(`<vault>`),
never against the docs. Read-only pass — the only file written is this POR.

## Friendlies (kept — verified real)

| Claim | Ground truth | Evidence |
|---|---|---|
| All 5 `.patch` files are true records | **vanilla + `patch -p1` == live, byte-exact**, all 5; dry-run clean, 0 `.rej` | staged vault copy → `patch -p1` → `cmp -s` vs live (moz.build + 4 gfx cpp) |
| Pref read at 4 platform backends, default `false` | present, hardcoded default false at every read site | gfxFcPlatformFontList.cpp:1754,1807; gfxFT2FontList.cpp:1551; gfxDWriteFontList.cpp:1656,1740; gfxPlatformFontList.cpp:791 |
| **Default-OFF invariant holds** (never enabled) | pref is set `true` **nowhere** in the working tree; no `user_pref`, no override, no `.js` | `grep -rn bundled_fonts.skip_system_scan` across `FIrefox.154.Work` → only docs + patches (default-false) |
| `[GORILLA]`/`[Gorilla]` provenance markers intact | present in all 4 live cpp | gfxFcPlatformFontList.cpp:1752,1759,1805,1811; gfxFT2FontList.cpp:1549,1645; gfxDWriteFontList.cpp:1655,1739,1748; gfxPlatformFontList.cpp:790,793 |
| moz.build wires 8 bundled fonts via `FINAL_TARGET_FILES.fonts` | present, byte-exact; all 8 files physically installed | browser/fonts/moz.build:6–15; `ls browser/fonts/` → consola/segoeui/segoeuib/seguisb/SegUIVar/YuGothB/YuGothR/TwemojiMozilla present |
| `.gitignore` excludes `*.ttf`/`*.ttc` with TwemojiMozilla CC-BY exception (AUDIT §E) | **confirmed** — the rule is in the *patches* repo, not firefox-main | `FIrefox.154.Work/.gitignore:62–64` (`*.ttf` / `*.ttc` / `!TwemojiMozilla.ttf`) |
| `get-microsoft-fonts.sh` acquisition set matches the bundle | `NEEDED_FONTS` = the 7 MS fonts in moz.build (Twemoji excluded — CC-BY, upstream in-tree) | get-microsoft-fonts.sh:35–43 vs browser/fonts/moz.build |
| the project's own notes reference (script + README.fonts.md) | resolves to a real fortress artifact (2 copies) | `the project's private notes` and `.../Firefox.154.Lessons/11.FONT.SYSTEM/microsoft_fonts.xml` |

## Tangoes (2 — both documentation, 0 code/binary)

**T1 — "pref is registered / appears in about:config by default" is FALSE.**
The 00_FONT_SYSTEM_HISTORY_AND_ROADMAP.md "Post-Build Verification" step says
`about:config → gfx.bundled_fonts.skip_system_scan → Should exist, default: false`, and its
cross-reference points at `05.PREFS/StaticPrefList.yaml for pref registration`. Ground truth:
the pref is registered **nowhere** — not in `StaticPrefList.yaml`, nor any `.yaml/.js/.mjs`
anywhere in the live tree. It is read purely via `Preferences::GetBool("...", false)` with a
hardcoded default. An **unregistered** pref does not appear in about:config until explicitly set,
so that verification step would fail as written.
*Falsifiable check:* `grep -rln bundled_fonts.skip_system_scan --include=*.yaml --include=*.js
--include=*.mjs the source tree` → **no matches**.
*Safety:* unaffected. This is the SOP's safety asymmetry — an unregistered pref read with a
`false` default is inert, and the top-line **default-OFF behavioural claim (AUDIT/LAYMAN/
DEVELOPER/README) is TRUE and verified**. Only the narrow "registered / visible in about:config"
sub-claim is wrong. **Action:** none taken (read-only); flag for a dated doc correction.
**Do NOT "fix" this by adding a StaticPrefList entry** unless that visibility change is
intended — it would alter about:config behaviour.

**T2 — README.fonts.md startup numbers are unverified and internally contradicted.**
README.fonts.md asserts `~40 seconds → ~2–4 seconds` and a `10× cold-boot win`. These are
**not measured**: the AUDIT lists "document the observed startup-time delta measurement" as an
open **P3 TODO**, and the DEVELOPER track lists the startup benchmark as a future action. They
also contradict the history doc's own Phase-1 figure ("font enumeration takes 50–200 ms").
A static-tree audit cannot measure startup, so this is flagged, not resolved. **Action:** none;
treat the `40s→4s` / `10×` figures as unverified marketing until a benchmark exists.

## Housekeeping (not poison)

- **Stale font-wiring pointer.** 00_FONT_SYSTEM_HISTORY_AND_ROADMAP.md (2026-07-07) predates
  `browser_fonts_moz.build.patch` (2026-07-16) and points font wiring at `08.Look/moz.build`.
  The actual — and only — wiring is `browser/fonts/moz.build` (verified byte-exact). The three
  `08.Look/.../moz.build` files are branding-only and wire **no** fonts (`grep FINAL_TARGET_FILES.fonts 08.Look` → none).
- **Missing rationale doc at claimed path.** The history doc references `docs/FONT_BUNDLE_RATIONALE.md`;
  no such file exists in the live tree. The content survives as a brain XML
  (`GATHERED_BRAIN_LESSONS/…font_bundle_rationale.xml`).
- **Provenance-marker style differs from canonical.** Markers are `[GORILLA]`/`[Gorilla]`, not the
  `// GORILLA OVERRIDE:` form named in the project rules file. The markers ARE present (the "keep markers" rule
  is satisfied); only the token differs.
- **Privacy benefit is conditional on the default-OFF pref.** The DEVELOPER "Trust Boundary" and
  LAYMAN "Your Privacy" notes describe reduced font fingerprinting, but that is realized **only when
  the pref is enabled** — and it ships OFF. As-shipped, there is zero fingerprinting change. The docs
  hedge this ("marginal", "when enabled") but the LAYMAN section can read as an as-shipped benefit.
- No stale generation-1 `AUDIT_REPORT_11.*` doc in this folder (unlike 03.NETWORKING); the IBM
  audit is merged verbatim into `MASTER_PROJECT_LOG_11_FONT_SYSTEM.md`. This POR supersedes it as
  the room's status.

## What this POR does NOT claim

Byte-exact patch reproduction proves the **code in the live tree matches what the patches and docs
describe**. It does **not** validate that the optimisation is correct or beneficial, and it does
**not** verify bundled-font glyph coverage — the "render Latin/Cyrillic/Arabic/Hebrew/Thai/CJK/emoji
corpus with only bundled fonts, fail on tofu" test remains an open TODO and was **not** run here.
Startup performance was **not measured** (see T2). Contamination-screened; values not
doc-validated — per the SOP's honest-label rule.

**Room status: CLEARED — 5/5 patches byte-exact, default-OFF invariant holds; 2 documentation
tangoes flagged (registration overstatement + unmeasured startup claim), 0 code/binary tangoes,
0 changes made.**
