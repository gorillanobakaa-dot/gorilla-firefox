# MASTER PROJECT LOG — FIREFOX 154 PERFORMANCE & COMPATIBILITY PATCHES

---

## Part 1: History, Roadmap & Overview
*(Originally from 00_PERFORMANCE_HISTORY_AND_ROADMAP.md)*

### Document Control
- **Category:** Performance & Build Compatibility
- **Last Updated:** 2026-07-10
- **Status:** Active Development
- **Verification Required:** Yes (see Validation section)
- **Related Documents:** 
  - `../DOCUMENTATION_TEMPLATES.md` (IBM format guide)
  - `../MAP.md` (cross-category index)
  - `../05.PREFS/00_PREFS_HISTORY_AND_ROADMAP.md` (actual performance tuning)
  - `../05.PREFS/StaticPrefList.yaml` (GC/timeout settings)
  - `../10.OVERRIDES/user.js` (runtime performance prefs)

---

### Executive Summary

**What This Does (Plain Language):**
Despite the name "performance," this folder is mostly about making Firefox **compile** on the new, stricter compiler (Clang-21). It contains one small but critical fix that prevents build failures, plus one privacy improvement (telemetry removal). The actual speed tuning lives in the settings folder (`05.PREFS`), not here.

**Technical Summary:**
Build compatibility fixes for Clang-21 toolchain plus telemetry lobotomy, plus IVB cycle-collector tuning. Implements: (1) SFINAE `IsComplete<T>` trait guards to prevent incomplete-type trait evaluation (ERR-BUILD-008), (2) telemetry removal in JS compile cache (`Stencil.cpp`), (3) `kICC*` cycle-collector cadence pinned for Ivy Bridge in `CCGCScheduler.cpp`. The behavioral GC/timeout *policy* is pref-driven (`05.PREFS`); the CC scheduler cadence is pinned here.

**Critical Context:**
> **The name is misleading.** This folder's job is to make the browser *build* on Clang-21, not to make it *fast*. The real performance knobs are settings in `05.PREFS`. We're honest about this rather than pretending the folder does more than it does.

---

### Mission Statement

### Mission 1: Build Compatibility (Primary)
When we upgraded to Clang-21 (newer, stricter compiler), the build broke on incomplete-type errors. The compiler tried to evaluate traits on types that weren't fully defined yet — like asking "how big is this box?" before the box exists.

**Our Response:**
Added small SFINAE `IsComplete<T>` trait guards that check "does this type exist yet?" before evaluating traits. Without this fix, Firefox 154 doesn't build at all on Clang-21.

### Mission 2: Privacy (Secondary)
One more telemetry wire cut in the JS compile cache, consistent with network stack lobotomy.

---

### Component Documentation

#### 1. MaybeStorageBase.h — SFINAE Completeness Trait (ERR-BUILD-008)
- **Status:** Modified | **Deploy Path:** `mfbt/MaybeStorageBase.h` | **Last Verified:** 2026-07-06
- **What It Does (Plain Language):** This defines a test that checks "does this type fully exist yet?" before trying to use it. It's the foundation of the Clang-21 fix.
- **Technical Description:** SFINAE completeness trait that detects whether a type is fully defined.

#### 2. CCGCScheduler.cpp — IVB Cycle-Collector Tuning (Performance, Hardcoded)
- **Status:** Modified | **Deploy Path:** `dom/base/CCGCScheduler.cpp` | **Last Verified:** 2026-07-10
- **What It Does (Plain Language):** Pins the Cycle Collector (CC) timing limits specifically to prevent micro-stuttering on your 4-core VAIO CPU.
- **Technical Description:** Pins `kICCIntersliceDelay` to 120ms and `kICCSliceBudget` to 4ms to ensure garbage collection fits cleanly within GNOME Wayland frame budgets (16.6ms at 60Hz).

---

### Chronological History (Recovered)

#### 2026-05-29
Initial completeness traits drafted under Firefox 153 compilation.

#### 2026-07-05
**Firefox 154 Migration:**
`Maybe.h` and `MaybeStorageBase.h` migrated to 154.

#### 2026-07-08
**Folder Hygiene:**
Cleaned up vanilla files (`ContentChild.cpp`, `ContentParent.cpp`, `TimeoutManager.cpp`, `nsJSEnvironment.cpp`, `RDDParent.cpp`) that carried zero Gorilla edits.

#### 2026-07-10
**Glean Scouring:**
Surgically gated JIT self-host compile cache metrics under `#ifndef GLEAN_DISABLED` inside `Stencil.cpp` to prevent runtime telemetry leaks.

---
 
## Part 3: Clang 21 Pre-Flight Guard (2026-07-11)
 
The Clang 21 migration uncovered 5 breakage patterns across the tree (see `preflight-clang21.py`). This category's `Maybe.h` / `MaybeStorageBase.h` fixes address **Pattern 1** (protected `mIsSome` accessed from template instantiations). The automated pre-flight script `preflight-clang21.py` (in `firefox-source/` root) catches all 5 patterns before every build:
 
1. `MaybeStorage::mIsSome` protected → template access error (fixed here)
2. Forward-declared union class used as field type → incomplete type
3. Duplicate union class definitions across generated headers
4. Missing required union methods (`Init`, `TraceUnion`, `ToJSVal`, etc.)
5. `UnionMember.Construct()` wrong method name (should be `.SetValue()`)
 
**Pre-flight runs automatically** via `01_build_orchestrator.py setup preflight` before every `./mach build`. UI-only changes (CSS/FTL) skip preflight.
 
---

## Part 2: Rule-Based Code Audit & Validation (2026-07-10)

We completed a static code audit of the performance patches:

1. **MaybeStorageBase.h**: Trait implementation `IsComplete` verified on lines 17-20 (declaration :17, `void_t<decltype(sizeof(U))>` specialization :20; corrected 2026-08-04 from "16-20"). Safe SFINAE guards return `false` on incomplete structures.
2. **CCGCScheduler.cpp**: Cycle-collector slice limits verified at `4ms` budget (`kICCSliceBudget` declared :31, `FromMilliseconds(4)` on line 32), keeping main thread iterations within the Wayland frame cycle.
3. **Stencil.cpp**: JS compile cache Glean triggers (`hits.AddToNumerator` and `total.Add`) are gated under `#ifndef GLEAN_DISABLED` (guards at lines **3115** and **3148**; metric blocks 3115-3118 and 3148-3150; corrected 2026-08-04 from the stale "3113-3116, 3144-3146"). There are exactly **3** `if constexpr (IsComplete<T>::value)` sites tree-wide (MaybeStorageBase.h:24, Maybe.h:106, Maybe.h:115) — not the "4 constexpr sites" the 2026-07-16 merged audit stated.

The category passes all code guidelines.


---


# ═══ CONSOLIDATION 2026-08-04 — side documents REGENERATED (dual-track toolkit) and merged VERBATIM below ═══

> **Supersedes** the 2026-08-02 consolidation of the 2026-07-16 side-docs. The docs below were
> regenerated by `dual-track code prep/render` on 2026-08-04, every claim re-verified against the
> live tree (`the source tree`) at its **current** line number, and the offline pre-check
> re-run (0 P0/P1/P2/P3). Quality-gate scores (>=85 required): **LAYMAN 98 · DEVELOPER 91 · AUDIT 95**.
> Drift corrected vs the prior versions: Stencil gate lines `3113-3116/3144-3146` -> **3115/3148**;
> `if constexpr (IsComplete<T>::value)` sites `4` -> **3**; the CCGCScheduler patch's full 5-constant
> scope is now documented (prior perf table listed only 2). The standalone
> `AUDIT_REPORT_04.PERFORMANCE.md` remains **void/superseded** (content-swapped networking body; see
> `POR_DRAFT_2026-08-03.md`) — do NOT act on its networking 'To Do'. Originals recoverable via git history.


---

# ═══ MERGED DOCUMENT: 04-performance.AUDIT.md (verbatim · sha256:f717236fcdcf6564 · merged 2026-08-04) ═══

# IBM-Style Audit Report: 04.PERFORMANCE

## SECTION A: DOCUMENT CONTROL

| Attribute | Value |
|---|---|
| **Target** | 04.PERFORMANCE |
| **Files scanned** | see payload |
| **Date / time** | 2026-08-04 07:15:49 |
| **Audit status** | PASS |

## SECTION B: EXECUTIVE SUMMARY (Plain Language)

This folder is safe to ship. Three of its four changes are build fixes that let Firefox 154 compile on a stricter compiler; they cannot touch your data. One change retunes the browser's memory-cleanup timing for a 4-core laptop, and one removes a telemetry counter. Every patch was checked line by line against the actual source code and matched exactly. Two things were not done this pass: the full build was not re-run, and the memory-cleanup timing was not benchmarked — both are noted honestly below rather than claimed as verified.

## SECTION C: TECHNICAL SUMMARY (Developer)

PASS. All four .patch files reproduce the live tree byte-exact (per POR 2026-08-03) and every documented value/marker was re-verified at its current line in the source tree this pass. mfbt/Maybe.h migrates 8 per-overload enable_if constraints to requires-clauses with polarity preserved (NOT boolean flips) plus IsComplete<T>-guarded copy/move helpers; mfbt/MaybeStorageBase.h adds the IsComplete<T> detector, an if-constexpr trivially-destructible helper, and one genuine constraint correction on the Union(U&&) ctor (is_move_constructible_v<U> -> is_constructible_v<NonConstT,U>). CCGCScheduler.cpp pins 5 cadence constants (250->120 ms delays x2, 3->4 and 2->4 ms budgets, 2->1.5 s max). Stencil.cpp gates the self-hosted compile-cache Glean metric under GLEAN_DISABLED at current lines :11/:15/:3115/:3148. Prior docs' '4 constexpr sites' (actual: 3) and stale gate line numbers (3113-3116/3144-3146) are corrected here.

## SECTION D: DETECTED DEFECTS

0 found by rules, 2 by review. Rule findings are deterministic; review findings are judgement.

### 🟢 P3-001 — P3 *(found by review)*

- **Plain English:** An old audit file in this folder describes networking code, not these performance files — like a folder label stuck on the wrong drawer. It is already marked SUPERSEDED at the top.
- **Technical:** patches/new.patches/04.PERFORMANCE/AUDIT_REPORT_04.PERFORMANCE.md — Sections B-F describe Necko/socket tuning (Sony VAIO, HTTP/3 UDP 64 MB, kGorillaUploadChunkSize) while its own header names the four performance files. Content-swapped gen-1 artifact; kept per append-only doctrine.
- **Fix:** Keep the existing SUPERSEDED banner; do NOT act on its networking 'To Do'. This regenerated audit + the MASTER_PROJECT_LOG are authoritative.
- **Effort:** 0 (already banner-flagged)

### 🟢 P3-002 — P3 *(found by review)*

- **Plain English:** The five memory-cleanup timing numbers have no comment explaining where they came from, and were never benchmarked.
- **Technical:** dom/base/CCGCScheduler.cpp:22-35 — 2 GORILLA markers (:21,:28) but no citation of the 16.6 ms/60 Hz frame-budget rationale; values unmeasured.
- **Fix:** Add a one-line rationale comment above kICCSliceBudget and capture a before/after CC-slice histogram on the reference box.
- **Effort:** 30min doc + 1h measurement

## SECTION E: PRODUCTION READINESS

**Overall readiness: 🟢 92%**

**Done:**
- [x] All 4 .patch files reproduce the live tree byte-exact (POR 2026-08-03) and re-verified at current lines this pass.
- [x] Clang-21 build-compat: IsComplete<T> detector + 3 if-constexpr helper wrappers (MaybeStorageBase.h:24, Maybe.h:106,:115).
- [x] Maybe.h: 8 enable_if->requires migrations with polarity preserved (:421,:429,:437,:445,:449,:464,:468,:485; emplace :893).
- [x] MaybeStorageBase.h Union(U&&) constraint correction is_move_constructible<U> -> is_constructible<NonConstT,U> (:51).
- [x] CC cadence full scope pinned (5 constants, :22-:35), documented completely (prior docs under-reported 3 of them).
- [x] JIT compile-cache Glean metric gated under GLEAN_DISABLED at current lines :11/:15/:3115/:3148.
- [x] Doc drift corrected: '4 constexpr sites' -> 3; gate lines 3113-3116/3144-3146 -> 3115/3148.

**To do:**
- [ ] P3: add frame-budget rationale comment above kICCSliceBudget.
- [ ] P3: retire/relocate the content-swapped AUDIT_REPORT_04.PERFORMANCE.md at next cleanup (banner is sufficient meanwhile).

**Not verified:**
- ./mach build on Clang 21 was NOT run this pass — the 'does not compile without IsComplete guards' / ERR-BUILD-008 rationale is the documented author claim, not reproduced here.
- CC cadence (4 ms / 120 ms and the other 3 constants) was NOT benchmarked; the 16.6 ms frame-budget fit is asserted rationale, not measured.
- Values were NOT re-validated against Mozilla upstream docs for optimality (the separate 2-month human doc pass); this pass verified existence and byte-exactness only.
- preflight-clang21.py coverage of the other 4 Clang-21 patterns was not exercised this pass (documented, not re-run).

## SECTION F: PHASED PLAN

### Phase 0 — `dom/base/CCGCScheduler.cpp:31 (kICCSliceBudget)`
- **Change:** Extract the 4/120 magic numbers to named constexpr with a comment linking to the 60 Hz/16.6 ms frame-budget calc.
- **Expected impact:** Maintainability; makes the tuning auditable without cross-referencing docs.

### Phase 1 — `dom/base/CCGCScheduler.cpp (whole table)`
- **Change:** Benchmark CC slice durations before/after on the reference i7-3632QM to confirm slices land <16.6 ms.
- **Expected impact:** Turns the asserted rationale into a measured claim.

## POSITIVE OBSERVATIONS

- The project log opens with 'The name is misleading' — the folder does not over-scope itself to justify its name.
- The Clang-21 fix is scoped to exactly the two mfbt files that need it; no shotgun edits across the tree.
- enable_if->requires migration preserves polarity on all 8 sites — a disciplined, mechanical modernization, not a behaviour change (the one real behaviour change, the Union ctor constraint, is isolated and correctly a widening).
- Telemetry excision uses the same GLEAN_DISABLED methodology as Necko and Topic 13 — coherent, not ad-hoc.
- Provenance markers (// GORILLA:) are present and specific at the two CC tuning sites.

## VERIFICATION COMMANDS

Run these to check the claims above rather than trusting them.

```bash
./mach build   # must succeed on Clang 21 (not re-run this pass)
grep -n 'IsComplete' mfbt/Maybe.h mfbt/MaybeStorageBase.h   # trait + 3 if-constexpr sites
grep -n 'if constexpr (IsComplete<T>::value)' mfbt/Maybe.h mfbt/MaybeStorageBase.h   # exactly 3: MSB:24, Maybe:106, Maybe:115
grep -n 'requires(' mfbt/Maybe.h   # 8 ctor/assign sites 421..485 + emplace 893; '!' retained on delete overloads
grep -n 'kCCSkippableDelay\|kICCIntersliceDelay\|kICCSliceBudget\|kIdleICCSliceBudget\|kMaxICCDuration' dom/base/CCGCScheduler.cpp   # 120/120/4/4/1.5
grep -n 'GLEAN_DISABLED' js/src/frontend/Stencil.cpp   # define :11, guards :15/:3115/:3148
```

## Claim Sources

| Claim | Basis | Evidence |
|-------|-------|----------|
| All 4 patches reproduce live tree byte-exact | 📄 stated in input | vanilla + patch == live, byte-exact |
| 3 if-constexpr IsComplete sites (not 4) | 🤖 model inference | *(none — model judgment)* |
| Gate lines corrected to 3115/3148 | 🤖 model inference | *(none — model judgment)* |
| Union ctor constraint widening is a genuine semantic change | 📄 stated in input | requires(std::is_constructible_v<NonConstT, U>) |
| 5 CC constants changed | 📄 stated in input | kCCSkippableDelay ... kMaxICCDuration |
| Standalone AUDIT_REPORT is content-swapped networking body | 🤖 model inference | *(none — model judgment)* |
| Build not re-run; ERR-BUILD-008 is author label | 🤖 model inference | *(none — model judgment)* |
| CC cadence not benchmarked | 🤖 model inference | *(none — model judgment)* |


---
**How to verify this document:**
`📄 stated in input` — the model's phrasing of something your source text said.
Find the matching line in the original to verify.
`🤖 model inference` — the model's own judgment or synthesis. Treat as opinion,
not measurement. Re-run on the same input and check whether specific numbers
stay consistent between runs.


---

# ═══ MERGED DOCUMENT: 04-performance.DEVELOPER.md (verbatim · sha256:138f2efb5d9d0741 · merged 2026-08-04) ═══

# 04.PERFORMANCE — Clang-21 Build-Compat (mfbt/Maybe.h, mfbt/MaybeStorageBase.h), IVB Cycle-Collector Cadence (dom/base/CCGCScheduler.cpp), and a JIT Compile-Cache Glean Gate (js/src/frontend/Stencil.cpp)

> Generated 2026-08-04 | Source: `04.PERFORMANCE`

---

## Purpose

Four point fixes across three unrelated subsystems, grouped by categorisation gap rather than functional cohesion. Two files (mfbt/Maybe.h, mfbt/MaybeStorageBase.h) are Clang-21 build-compatibility edits: without them Firefox 154 does not compile on Clang 21 (author label ERR-BUILD-008; not independently reproduced this pass). One file (dom/base/CCGCScheduler.cpp) retunes five Cycle-Collector cadence constants for the reference Ivy Bridge 4c/8t CPU. One file (js/src/frontend/Stencil.cpp) gates a JIT self-hosted compile-cache Glean metric behind GLEAN_DISABLED. Trust level: build-time only for three files; the CC change is runtime but touches no external input. Genuine performance policy lives in 05.PREFS and 10.OVERRIDES, not here.

## Design Rationale

Clang 21 tightened evaluation of type traits on incomplete types and no longer accepts the old enable_if-in-template-parameter idiom in these instantiation contexts. The fix has two mechanisms: (1) an IsComplete<T> detector plus if-constexpr helper wrappers that short-circuit trait evaluation to a conservative constant when T is incomplete, instead of hard-erroring; (2) a mechanical migration of eight per-overload enable_if constraints in Maybe.h to C++20 requires-clauses with IDENTICAL predicates (polarity preserved). Separately, the MaybeStorageBase Union(U&&) constructor's constraint was corrected from is_move_constructible_v<U> to is_constructible_v<NonConstT, U> — a genuine semantic widening/correction, since the constructor initialises a NonConstT member from U, not a U from U.

## Architecture

- **Pattern:** Point fixes; no shared architecture. Two subsystems are compile-time (mfbt template headers, JS frontend preprocessor); one is a runtime scheduler constant table.
- **Trust boundary:** N/A — no external/attacker-reachable input is processed by any of these changes. The mfbt and Stencil edits are compile-time; the CC constants are internal scheduler tuning.
- **Attack surface:** N/A — none introduced. One telemetry egress path (JS compile-cache Glean metric) is removed, which narrows the profiling surface.
- **Dependencies:** `Clang 21 toolchain (build-time)`, `C++20 concepts / requires-clauses`, `companion preflight-clang21.py in the source root — catches the other 4 Clang-21 breakage patterns`, `mozilla/glean/JsSrcMetrics.h (now include-gated out under GLEAN_DISABLED)`

## Flags & Configuration

| Name | Type | Default | Effect | Notes |
|------|------|---------|--------|-------|
| `GLEAN_DISABLED` | `macro` | `undefined upstream` | When defined (=1), the mozilla/glean/JsSrcMetrics.h include and all javascript_self_hosted_cache metric calls in Stencil.cpp are preprocessed out. | Defined at js/src/frontend/Stencil.cpp:11. Consumed by #ifndef guards at :15, :3115, :3148. Doctrine, not a bug — do not 'fix'. |
| `MOZ_TELEMETRY_REPORTING` | `macro` | `build-config dependent` | #undef then redefined to 0 at Stencil.cpp:9-10 as belt-and-braces alongside GLEAN_DISABLED. | Local to this translation unit; scope is Stencil.cpp only. |

## API Surface

| Symbol | Description | Side Effects |
|--------|-------------|--------------|
| `mozilla::detail::IsComplete<U>` | Trait: true iff U is a complete type at the point of instantiation. | none (compile-time) |
| `IsTriviallyDestructibleAndCopyableHelper<T>()` | Returns the trivially-destructible-and-copyable predicate when T is complete, false otherwise. | none; if constexpr (IsComplete<T>::value) at MaybeStorageBase.h:24 |
| `IsCopyConstructibleHelper<T>()` | std::is_copy_constructible_v<T> when T complete, else true (conservative). | none; if constexpr at Maybe.h:106 |
| `IsMoveConstructibleHelper<T>()` | std::is_move_constructible_v<T> when T complete, else true (conservative). | none; if constexpr at Maybe.h:115 |
| `MaybeStorageBase<T,false>::Union::Union(U&&)` | Perfect-forwarding Union constructor; constraint corrected to test the stored type NonConstT (=remove_const_t<T>), not U. | constructs the NonConstT member 'val' from forwarded U |

## Kill Switches

### `js/src/frontend/Stencil.cpp:11 (#define), :15/:3115/:3148 (#ifndef guards)`
- **Condition:** compile-time preprocessor
- **Effect:** JIT self-hosted compile-cache Glean metric (hits.AddToNumerator / total.Add) becomes a no-op and is not linked.
- reversible
- Same GLEAN_DISABLED methodology as Necko and Topic 13. Remove the #define to restore upstream telemetry.

### `dom/base/CCGCScheduler.cpp:22-35 (constant table)`
- **Condition:** always, at CC scheduler static init (MOZ_RUNINIT)
- **Effect:** Pins 5 Cycle-Collector cadence constants (see performance).
- reversible
- Reverting restores upstream cadence; observable as different CC slice timing, no correctness impact.

## Dead Code

- **`js/src/frontend/Stencil.cpp:16 (#include mozilla/glean/JsSrcMetrics.h)`** — Include is compiled out under GLEAN_DISABLED via the #ifndef at :15. (risk: None if removed together with the #define; intentional dead code — retained so the gate is auditable and reversible.)

## Performance

- **CPU:** CCGCScheduler cadence retuned (all 5 changes, full scope): kCCSkippableDelay 250->120 ms (:22), kICCIntersliceDelay 250->120 ms (:29), kICCSliceBudget 3->4 ms (:31), kIdleICCSliceBudget 2->4 ms (:33), kMaxICCDuration 2 s->1.5 s (:35). Net: more frequent CC (halved gaps), slightly larger per-slice budgets, shorter max total incremental duration. Not benchmarked topic-locally.
- **MEMORY:** No change. Reclamation semantics are identical; only scheduling cadence differs.
- **IO:** No change.
- **NOTES:** The '4 ms slice fits inside a 60 Hz / 16.6 ms Wayland frame' framing is documented design rationale, not a measurement. Note the slice budget INCREASED (3->4 ms); the eagerness comes from halved delays, not smaller slices.

## Security

- **Remote execution:** N/A — none of these changes handle remote or untrusted input.
- **Data handling:** One telemetry egress removed: the JS self-hosted compile-cache hit/total Glean metric no longer records or reports.
- **Attack surface:** Narrowed by one inferential channel (compile-cache hit patterns). No new surface added.
- **Notes:** GLEAN_DISABLED gate + GORILLA provenance markers are intentional project doctrine, not defects.

## Error Conditions

| Error | Cause | Remedy |
|-------|-------|--------|
| `ERR-BUILD-008 / incomplete-type trait evaluation error under Clang 21` | Trait (is_copy_constructible / is_move_constructible / is_trivially_*) evaluated on an incomplete T during Maybe<T> instantiation. | The IsComplete<T> + helper wrappers short-circuit to a conservative constant for incomplete T. Author label; not independently reproduced this pass. |

## Tasks

### Build on Clang 21 and confirm the folder is load-bearing

The two mfbt edits are the reason Firefox 154 compiles on Clang 21; verify the build succeeds with them applied.

**Prerequisites:**
- Clang 21 toolchain
- the four patches in this folder applied to the tree

**Step 1:** Run:

```bash
./mach build
```
  - Expected: Build succeeds. (Reverting mfbt/Maybe.h + mfbt/MaybeStorageBase.h is expected to reintroduce the incomplete-type trait error; not re-run this pass.)

**After this task:** libxul links; no incomplete-type trait errors from Maybe<T> instantiations.

### Verify the CC cadence constants (full scope)

Confirm all five tuned constants are present, not only the two most-quoted ones.

**Prerequisites:**
- source tree

**Step 1:** Run:

```bash
grep -n 'kCCSkippableDelay\|kICCIntersliceDelay\|kICCSliceBudget\|kIdleICCSliceBudget\|kMaxICCDuration' dom/base/CCGCScheduler.cpp
```
  - Expected: kCCSkippableDelay/kICCIntersliceDelay = 120 ms, kICCSliceBudget/kIdleICCSliceBudget = 4 ms, kMaxICCDuration = 1.5 s, with two '// GORILLA:' markers at :21 and :28.

**After this task:** All five deltas confirmed against the tree.

### Verify the Glean gate at the current line numbers

Upstream line drift moved the metric guards; confirm current positions.

**Prerequisites:**
- source tree

**Step 1:** Run:

```bash
grep -n 'GLEAN_DISABLED' js/src/frontend/Stencil.cpp
```
  - Expected: #define at :11; #ifndef guards at :15 (include), :3115 (hits+total), :3148 (total).

**After this task:** Gate positions confirmed; strings libxul.so | grep -c self_hosted_cache expected 0.

### Confirm the enable_if -> requires migration preserved polarity

This is the single most misreadable change: a naive review can mistake it for boolean inversion.

**Prerequisites:**
- source tree

**Step 1:** Run:

```bash
grep -n 'requires(' mfbt/Maybe.h
```
  - Expected: 8 constructor/assignment requires-clauses at :421,:429,:437,:445,:449,:464,:468,:485 (plus emplace at :893). Each '= delete' overload retains its '!'; enabled overloads have no '!'. Predicates match the pre-migration enable_if predicates exactly.

**After this task:** Polarity verified preserved; no condition inverted.

## Troubleshooting

**Symptom:** Reviewer flags the Maybe.h change as a suspected boolean flip.
**Cause:** enable_if_t<!cond> was rewritten to requires(!cond); the '!' can be missed on a skim.
**Remedy:** Diff each pair: the deleted overloads keep '!', the enabled ones do not. Meaning is identical.
**Verify:** grep -n 'requires(!' mfbt/Maybe.h shows the negated predicates exactly where the '!enable_if' predicates were.

**Symptom:** Build breaks with incomplete-type trait error after touching mfbt.
**Cause:** IsComplete<T> guard or a helper wrapper was removed/reverted.
**Remedy:** Restore the MaybeStorageBase.h IsComplete definition and the three helper wrappers.
**Verify:** grep -n 'IsComplete' mfbt/Maybe.h mfbt/MaybeStorageBase.h returns the trait + 3 if-constexpr sites.

**Symptom:** Someone claims '4 constexpr sites' for the IsComplete guards.
**Cause:** Stale over-count from the 2026-07-16 merged audit.
**Remedy:** There are exactly 3 'if constexpr (IsComplete<T>::value)' sites.
**Verify:** grep -n 'if constexpr (IsComplete<T>::value)' mfbt/Maybe.h mfbt/MaybeStorageBase.h -> MaybeStorageBase.h:24, Maybe.h:106, Maybe.h:115.

## Technical Debt

🟡 **LOW** — Five CC cadence constants are magic numbers; only 2 GORILLA marker comments (:21, :28) exist and neither cites the 16.6 ms frame-budget rationale. → Add a one-line comment above kICCSliceBudget referencing the 60 Hz / 16.6 ms frame-budget derivation, and note the values are unbenchmarked.
🟡 **LOW** — CC cadence is unbenchmarked; the 'fits inside a frame' rationale is asserted, not measured. → Capture a before/after CC-slice histogram (about:memory / profiler) on the reference box to confirm slices land <16.6 ms.
🟡 **LOW** — Folder name 04.PERFORMANCE is misleading (3 of 4 files are build-compat). → Consider renaming to 04.BUILD_COMPAT on the next re-org; cost currently outweighs benefit.

## Impact If Removed

Reverting mfbt/Maybe.h + mfbt/MaybeStorageBase.h: Firefox 154 fails to compile on Clang 21 (incomplete-type trait evaluation; author label ERR-BUILD-008). Reverting the MaybeStorageBase Union ctor constraint specifically: narrows the constructor back to is_move_constructible_v<U>, which is both less correct and can reject valid constructions from a U that the stored NonConstT can accept. Reverting CCGCScheduler.cpp: CC returns to upstream cadence (250 ms gaps, 3/2 ms budgets, 2 s max) — occasional frame-boundary hitches under heavy JS churn on a 4-core CPU; no correctness impact. Reverting the Stencil.cpp gate: the JIT compile-cache Glean metric resumes recording and reporting.

## Claim Sources

| Claim | Basis | Evidence |
|-------|-------|----------|
| Two mfbt files are the Clang-21 build fix | 📄 stated in input | mfbt/Maybe.h, mfbt/MaybeStorageBase.h |
| IsComplete<T> defined via void_t<decltype(sizeof(U))> | 📄 stated in input | struct IsComplete<U, std::void_t<decltype(sizeof(U))>> : std::true_type {}; |
| IsCopyConstructibleHelper / IsMoveConstructibleHelper added and used as default template args | 📄 stated in input | Copyable = IsCopyConstructibleHelper<T>(), Movable = IsMoveConstructibleHelper<T>() |
| IsTriviallyDestructibleAndCopyable delegates to the guarded helper | 📄 stated in input | IsTriviallyDestructibleAndCopyable = ... IsTriviallyDestructibleAndCopyableHelper<T>(); |
| Glean include is itself gated out | 📄 stated in input | #ifndef GLEAN_DISABLED ... #include mozilla/glean/JsSrcMetrics.h ... #endif |
| Three if-constexpr IsComplete sites | 🤖 model inference | *(none — model judgment)* |
| Eight enable_if->requires conversions in Maybe.h, polarity preserved | 📄 stated in input | std::enable_if_t<!std::is_constructible_v<T, const U&>, bool> becomes requires(!std::is_constructible_v<T, const U&>) |
| Union ctor constraint corrected is_move_constructible<U> -> is_constructible<NonConstT,U> | 📄 stated in input | typename = std::enable_if_t<std::is_move_constructible_v<U>> becomes requires(std::is_constructible_v<NonConstT, U>) |
| NonConstT = std::remove_const_t<T> and is the stored member | 🤖 model inference | *(none — model judgment)* |
| CC full scope: 5 constants changed | 📄 stated in input | kCCSkippableDelay ... kICCIntersliceDelay ... kICCSliceBudget ... kIdleICCSliceBudget ... kMaxICCDuration |
| kMaxICCDuration 2 s -> 1.5 s | 📄 stated in input | kMaxICCDuration = TimeDuration::FromSeconds(1.5); |
| GLEAN_DISABLED define at :11, guards at :15/:3115/:3148 | 🤖 model inference | *(none — model judgment)* |
| MOZ_TELEMETRY_REPORTING undef then set to 0 | 📄 stated in input | #undef MOZ_TELEMETRY_REPORTING; #define MOZ_TELEMETRY_REPORTING 0 |
| requires-clause line numbers in Maybe.h (421..485, 893) | 🤖 model inference | *(none — model judgment)* |
| Build not re-run this pass; ERR-BUILD-008 is author label | 🤖 model inference | *(none — model judgment)* |
| CC cadence not benchmarked | 🤖 model inference | *(none — model judgment)* |
| preflight-clang21.py covers the other 4 patterns | 🤖 model inference | *(none — model judgment)* |


---
**How to verify this document:**
`📄 stated in input` — the model's phrasing of something your source text said.
Find the matching line in the original to verify.
`🤖 model inference` — the model's own judgment or synthesis. Treat as opinion,
not measurement. Re-run on the same input and check whether specific numbers
stay consistent between runs.

*Auto-generated DITA-structured developer documentation.*


---

# ═══ MERGED DOCUMENT: 04-performance.LAYMAN.md (verbatim · sha256:312b63eb4f49ba47 · merged 2026-08-04) ═══

# The '04.PERFORMANCE' Folder — Mostly Making Firefox 154 Build on a Stricter Compiler — Plain Language Guide

> Generated 2026-08-04 from `04.PERFORMANCE`

---

## Should You Run This?

Yes — this is low risk. Three of the four changes are compiler-facing build fixes that cannot affect your data; one retunes memory-cleanup timing conservatively for a low-core laptop; one removes a telemetry counter. Nothing here opens a network connection or handles your personal files.

## Worst Case, Honestly

Realistic worst case is small. These are compiler-facing header and constant changes, not network or data code, so they cannot leak your files or run remote code. If a build-fix were wrong, the browser would fail to compile — that is caught at build time and never reaches you. If the Cycle-Collector timing were a poor fit for a given CPU, the effect would be slightly more frequent short bursts of processor work, meaning marginally worse battery on a very idle machine. This was tuned on the reference 4-core laptop and was not benchmarked.

## What Data This Touches

These are build-time changes to C++ source. Nothing here sends data to the project or to anyone else. The opposite is true for one change: js/src/frontend/Stencil.cpp switches OFF a Glean telemetry counter (javascript_self_hosted_cache hits/total) that previously recorded JavaScript compile-cache statistics. The build-compatibility edits (Maybe.h, MaybeStorageBase.h) and the Cycle-Collector timing change touch no personal data at all.

## Before You Trust It

You cannot read C++, but you can confirm that the changes are exactly what is claimed and nothing more, using simple search commands on the built source tree.

**Step 1:** Open a terminal in the built source tree and run this command:

```bash
grep -n 'GLEAN_DISABLED' js/src/frontend/Stencil.cpp
```
  - Look for: You should see '#define GLEAN_DISABLED 1' near the top and '#ifndef GLEAN_DISABLED' guards at lines 15, 3115 and 3148. That proves the telemetry counter is switched off, and nothing else network-facing is touched.
**Step 2:** Run this command to check the memory-cleanup timings:

```bash
grep -n 'kICCSliceBudget\|kICCIntersliceDelay\|kMaxICCDuration' dom/base/CCGCScheduler.cpp
```
  - Look for: You should see the slice budget set to 4 ms, the inter-slice delay to 120 ms, and the max duration to 1.5 seconds. These are the Cycle-Collector timings.
**Step 3:** Run this command to see the build fix:

```bash
grep -n 'IsComplete' mfbt/Maybe.h mfbt/MaybeStorageBase.h
```
  - Look for: You should see the IsComplete test defined in MaybeStorageBase.h and used inside the helper functions. That is the whole build fix — no runtime behaviour.

## The Big Picture

This folder holds four small patch files. Despite the name, three of them exist for one reason: to make Firefox 154 compile at all on Clang 21, a newer and stricter C++ compiler. The old source used a coding shortcut the new compiler rejects, so the shortcut was rewritten in a form the compiler accepts. No feature is added; the browser just goes back to building.

The one file that changes how the browser behaves at runtime is dom/base/CCGCScheduler.cpp. It retunes the timing of the Cycle Collector — the part of Firefox that finds and frees memory the browser no longer needs. Five timing numbers were changed so cleanup runs more often, in slightly bigger bites, on the reference machine's 4-core, 8-thread Intel i7-3632QM laptop CPU.

One more change (js/src/frontend/Stencil.cpp) cuts a telemetry wire: a counter in the JavaScript compile cache that used to report cache-hit statistics is now switched off at build time. The genuine speed and memory settings for this build live in the 05.PREFS and 10.OVERRIDES folders, not here. The project log opens by saying the folder name is misleading, and that is accurate.

## Key Concepts

| Name | What It Means | Real-World Comparison |
|------|--------------|------------------------|
| `Clang 21` | The C++ compiler that turns Firefox source code into a running program. Version 21 is stricter than before. | A stricter proofreader who rejects sentences the old proofreader let slide, even though they meant the same thing. |
| `requires-clause (vs enable_if / SFINAE)` | Two ways to tell the compiler 'only allow this code when a condition holds'. The patch swaps the old spelling (enable_if) for the modern one (requires). The condition is unchanged. | Rewriting 'no entry unless you are a member' as 'members only'. Different words, same door policy. |
| `IsComplete<T>` | A compile-time test that asks 'has this data type been fully defined yet?' before the compiler tries to measure it. | Checking that a parcel has actually arrived before you try to weigh it. |
| `Cycle Collector (CC)` | Firefox's memory janitor for a special kind of leftover memory. It runs in short slices so it never freezes the whole browser at once. | A cleaner who tidies in short passes every few minutes instead of shutting the building for one big clean. |
| `Glean` | Mozilla's telemetry system that collects usage statistics. This build switches its wires off one by one. | A meter that reports what you do; this change unplugs one more of them. |
| `60 Hz frame budget (16.6 ms)` | On a 60 Hz screen the browser has about 16.6 milliseconds to draw each frame. Work that overruns it shows up as a stutter. | A 16-millisecond commercial break: you can do a quick task in it, but not a long one. |

## How It Works — Step by Step

### Step 1: The compiler got stricter, so the constraint syntax was modernized

In mfbt/Maybe.h, eight template constraints were rewritten from the old 'enable_if' spelling to the modern 'requires(...)' spelling. Important: the meaning is preserved exactly. Every place that said 'not' still says 'not' — the deleted copy/move overloads still carry the negation. A fast read can mistake this for someone flipping a true/false somewhere; it is not. It is the same rule written in newer words so Clang 21 will accept it.

### Step 2: A guard that asks 'does this type exist yet?'

mfbt/MaybeStorageBase.h adds IsComplete<T>, a test that is true only when the compiler already knows the full definition of a type. Three helper functions use it: if the type is not complete yet, they return a conservative answer instead of forcing the compiler to measure something that does not exist. Like refusing to weigh a parcel that has not arrived, rather than crashing.

### Step 3: One constructor was taught to ask the right question

Also in MaybeStorageBase.h, one constructor used to allow itself only when the incoming value type U was movable. That was the wrong question. The stored slot is a value of the container's own type, so the new rule asks 'can that stored slot actually be built from U?' This is a genuine change in behaviour, not just a rename, and it is the one place in the folder where the meaning really moved.

### Step 4: The memory janitor was retuned for a 4-core laptop

dom/base/CCGCScheduler.cpp changes five timing numbers. Two gaps between cleanup passes drop from 250 ms to 120 ms (cleanup runs more often). Two per-pass work budgets rise (3 ms to 4 ms, and 2 ms to 4 ms), so each pass does a little more. The longest a full incremental cleanup may run drops from 2 seconds to 1.5 seconds, so it never hogs the CPU as long. The author's note calls this 'more eager cycle collection, smaller gaps.'

### Step 5: A telemetry counter was switched off at build time

js/src/frontend/Stencil.cpp defines GLEAN_DISABLED at the top. The JavaScript compile-cache counter and even the header that declares it are wrapped in '#ifndef GLEAN_DISABLED', so the compiler leaves them out of the finished program entirely. There is nothing to switch back on at runtime — the wire is simply not built in.

## Quirky Things Worth Knowing

### The 'requires' rewrite looks like a logic flip but is not

The eight constraints in Maybe.h come in matched pairs — one enabled overload and one deleted overload with a 'not' in front. After the rewrite, the 'not' is still there on every deleted overload. A reviewer skimming for changed booleans can wrongly conclude a condition was inverted. It was not; polarity is preserved. This is the single easiest thing to misread in the whole folder.

### One Cycle-Collector number went UP on purpose

You might expect a speed tuning to make every number smaller. Two of them got bigger: the per-pass work budgets rose from 3 to 4 ms and from 2 to 4 ms. The point is not 'do less' but 'do more, more often, in shorter total runs' — collect eagerly so garbage never piles up.

### The folder name is misleading, and the log admits it

Three of four files are build fixes, not performance work. The real speed knobs live in 05.PREFS and 10.OVERRIDES. Rather than dress the folder up, the project log opens with 'The name is misleading.'

## What This Means For You

### Battery, Processor & Memory

CPU: the Cycle Collector now runs more often (gaps halved from 250 ms to 120 ms), which means more frequent short bursts of cleanup work. This was not benchmarked, so no before/after CPU number is claimed. Memory: no change — the amount of memory reclaimed is the same, only the timing differs. The build-compatibility edits have zero runtime cost.

### Speed

The CC retuning aims to keep each cleanup pause short so the interface does not visibly hiccup during heavy JavaScript activity. This is a design goal, not a measured result — it was not benchmarked. The build-fix and telemetry-gate changes have no speed effect you would feel.

### Your Privacy

Slightly improved. One telemetry counter (the JavaScript compile-cache hit/total metric) is removed from the build. Small on its own; part of a consistent pattern across this build.

### Your Internet

No change. Nothing here touches the network.

## The Off Switch

**What it is:** There is no runtime toggle. Every change here is decided at build time. The telemetry off-switch is the line '#define GLEAN_DISABLED 1' at the top of js/src/frontend/Stencil.cpp, set once when the browser is compiled.

**Without it:** Without the build-compatibility edits, Firefox 154 does not compile on Clang 21 at all. Without the GLEAN_DISABLED gate, the JavaScript compile-cache telemetry counter is compiled back in.

**Think of it like:** These are welds made at the factory, not switches on the dashboard. You cannot flip them while driving; they were decided when the car was built.

## How to use this

**Before you start:**
- A built copy of the Gorilla Unleashed Firefox 154 (these changes are already compiled in).

**Step 1:** Use the browser normally.
  - You should see: There is nothing to configure. The build fixes and the telemetry gate are permanent parts of the compiled program; the Cycle-Collector timing is active from the first second the browser runs.

## If Something Goes Wrong

**You are rebuilding from source and the build fails with an 'incomplete type' error in Maybe.h or MaybeStorageBase.h.**
The IsComplete<T> guards from this folder are missing or were reverted, so Clang 21 tries to measure a type that is not defined yet.
What to do: Re-apply the mfbt/Maybe.h and mfbt/MaybeStorageBase.h patches in this folder, then rebuild.

**You notice occasional brief hitches during very heavy JavaScript pages.**
Cycle-Collector passes are landing at busy moments. The tuning here is meant to reduce, not eliminate, this.
What to do: This is expected behaviour on a 4-core CPU; the timing here already favours short, frequent passes. No action needed.

## Why a Developer Would Do This

Upgrading to Clang 21 forced the source to be rewritten in stricter, more modern C++. The author used that same pass to retune the memory janitor for a specific 4-core laptop and to cut one more telemetry wire, keeping the build honest about what it does and does not send.

## Why It Matters That You Can Read This

You can open all four .patch files in this folder and read every line that changed. Two carry plain '// GORILLA:' comments naming what changed and why (the Cycle-Collector tuning), and the telemetry change is a labelled block at the top of Stencil.cpp. If you could not read this, you would be trusting a stranger's claim that 'we only cut telemetry and fixed the build.' Because you can read it, you can confirm that claim yourself with the grep commands below — no need to trust anyone's word.

## Glossary

**Clang 21** — The C++ compiler used to build this Firefox; version 21 rejects some older code patterns.

**SFINAE / enable_if** — An older C++ way of saying 'only allow this code when a condition is true'.

**requires-clause** — The modern C++20 way of saying the same thing; this build switches to it.

**IsComplete<T>** — A compile-time test that is true only when a data type is already fully defined.

**Cycle Collector (CC)** — Firefox's janitor for reference-cycle memory; runs in short slices to avoid freezing the browser.

**Glean** — Mozilla's telemetry framework; this build disables its wires one at a time.

**Frame budget** — The time available to draw one screen frame; about 16.6 ms at 60 Hz.

## Claim Sources

| Claim | Basis | Evidence |
|-------|-------|----------|
| Folder is four patch files | 📄 stated in input | TOPIC: 04.PERFORMANCE — 4 file(s) |
| CC inter-slice delay 250 -> 120 ms | 📄 stated in input | kICCIntersliceDelay ... FromMilliseconds(250) -> FromMilliseconds(120) |
| CC slice budget 3 -> 4 ms | 📄 stated in input | kICCSliceBudget ... FromMilliseconds(3) -> FromMilliseconds(4) |
| Idle ICC budget 2 -> 4 ms | 📄 stated in input | kIdleICCSliceBudget ... FromMilliseconds(2) -> FromMilliseconds(4) |
| kCCSkippableDelay 250 -> 120 ms | 📄 stated in input | kCCSkippableDelay ... FromMilliseconds(250) -> FromMilliseconds(120) |
| kMaxICCDuration 2 s -> 1.5 s | 📄 stated in input | kMaxICCDuration ... FromSeconds(2) -> FromSeconds(1.5) |
| Author note: more eager cycle collection, smaller gaps | 📄 stated in input | GORILLA: IVB (4c/8t) tuning — more eager cycle collection, smaller gaps. |
| GLEAN_DISABLED defined to 1 in Stencil.cpp | 📄 stated in input | #define GLEAN_DISABLED 1 |
| JS compile-cache Glean metric gated out | 📄 stated in input | #ifndef GLEAN_DISABLED (guarding the javascript_self_hosted_cache metric) |
| GLEAN_DISABLED guards at lines 15, 3115, 3148 | 🤖 model inference | *(none — model judgment)* |
| enable_if -> requires conversions preserve polarity (not bool flips) | 📄 stated in input | enable_if_t<!is_constructible...> becomes requires(!is_constructible...); the negation is retained on the deleted overloads |
| Union ctor constraint changed from is_move_constructible<U> to is_constructible<NonConstT,U> | 📄 stated in input | is_move_constructible_v<U> -> is_constructible_v<NonConstT, U> |
| Patch targets IVB 4c/8t hardware | 📄 stated in input | IVB (4c/8t) tuning |
| Reference CPU is Intel i7-3632QM (IVB) | 🤖 model inference | *(none — model judgment)* |
| CC tuning not benchmarked | 🤖 model inference | *(none — model judgment)* |
| 60 Hz frame budget is ~16.6 ms | 🤖 model inference | *(none — model judgment)* |


---
**How to verify this document:**
`📄 stated in input` — the model's phrasing of something your source text said.
Find the matching line in the original to verify.
`🤖 model inference` — the model's own judgment or synthesis. Treat as opinion,
not measurement. Re-run on the same input and check whether specific numbers
stay consistent between runs.

*Human Track. Its Developer Track twin covers the same changes in technical detail. Neither is a simplified copy of the other — they are the same truth in two languages.*


---

# ═══ MERGED DOCUMENT: 04-performance.PRECHECK.md (verbatim · sha256:6ad8538b99e9bca4 · merged 2026-08-04) ═══

# Offline Pre-Check: 04-performance

*Generated 2026-08-04 07:02:46 by rules only. No model was involved, so everything below is a deterministic finding about the files as they are on disk.*

## Files Scanned

| File | Language | Lines | Code | Complexity | SHA-256 |
|---|---|---|---|---|---|
| `dom_base_CCGCScheduler.cpp.patch` | patch | 29 | 28 | 2 | `67d9b93bc965a382` |
| `js_src_frontend_Stencil.cpp.patch` | patch | 41 | 30 | 5 | `e06fa079ae95df6d` |
| `mfbt_Maybe.h.patch` | patch | 126 | 108 | 12 | `05fb542004c98165` |
| `mfbt_MaybeStorageBase.h.patch` | patch | 44 | 41 | 2 | `91e89a8d3315978a` |

## Findings

🔴 P0: 0 · 🟠 P1: 0 · 🟡 P2: 0 · 🟢 P3: 0

*No findings. The rules found nothing wrong; this is not a statement that the code is correct.*

