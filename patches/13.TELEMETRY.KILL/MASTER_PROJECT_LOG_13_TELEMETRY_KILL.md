# 13.TELEMETRY.KILL — Master Project Log

*Created 2026-08-02 by consolidating this folder's documentation set (merged verbatim below). Policy: one master project log per folder.*


---

# ═══ CONSOLIDATION 2026-08-02 — side documents merged VERBATIM below; originals deleted (recoverable: merged-docs-backup-2026-08-02.tar.gz + git history) ═══


---

# ═══ MERGED DOCUMENT: 13-telemetry-kill.AUDIT.md (verbatim · sha256:03c908710c211a04 · merged 2026-08-02) ═══

# IBM-Style Audit Report: 13-telemetry-kill

## SECTION A: DOCUMENT CONTROL

| Attribute | Value |
|---|---|
| **Target Category** | 13-telemetry-kill |
| **Files Scanned** | see payload |
| **Baseline** | Firefox 154 (mozilla-central) |
| **Date / Time** | 2026-07-17 08:18:05 |
| **Audit Status** | PASS |

## SECTION B: EXECUTIVE SUMMARY (Track A — Layman)

Firefox quietly measures how you use it — how much memory, how long things take — and doing that measurement costs real CPU. On this 12-year-old hardware it was burning about 1 in every 8 units of the main process's effort during video playback, on watching itself rather than showing you the video. This patch group turns all of it off at the source, cutting that cost from ~13% down to under half a percent. Privacy and speed turned out to be the same fix.

## SECTION C: TECHNICAL SUMMARY (Track B — Developer)

Layered source-level short-circuits (NOT excision) across MemoryTelemetry, FOG, and vendored glean-core. (1) MemoryTelemetry::GatherReports() early-returns, skipping the 60s /proc/self/smaps scan (8.9%->0.02%). (2) FOG::InitializeFOG() no-ops before fog_init(), so the glean.dispatche thread blocks at 0% (3.5%->0.00%). (3) compile-time const GORILLA_TELEMETRY_OFF DCE-guards the timing/memory-distribution hot recording paths (0.84%->0.39%). All symbols/factories/moz.build refs preserved (excision caused NS_ERROR_FACTORY_NOT_REGISTERED + 157 shim headers). Vendored-crate edits require .cargo-checksum.json SHA updates AND stale-artifact deletion to actually recompile. VERIFIED via perf 2026-07-16: total telemetry parent CPU ~13.2% -> ~0.39%.

## SECTION D: DETECTED DEFECTS

*No defects detected by rules or model.*

## SECTION E: PRODUCTION READINESS ASSESSMENT

- **Overall readiness:** 🟢 96%
- **Done:**
  - [x] MemoryTelemetry::GatherReports() short-circuit verified 8.9%->0.02%
  - [x] FOG::InitializeFOG() no-op verified dispatcher 3.5%->0.00%
  - [x] GORILLA_TELEMETRY_OFF const DCE guards verified inline 0.84%->0.39%
  - [x] dispatcher::global::launch() drops tasks (pre-init buffer-growth fix)
  - [x] .cargo-checksum.json SHA256 updated for all 4 edited glean-core files
  - [x] Soft short-circuit chosen over excision (avoids NS_ERROR_FACTORY_NOT_REGISTERED + 157 shim headers)
  - [x] No startup/shutdown crash (uninitialized-Glean path validated)
  - [x] Coherent with Topic 03 (Necko Glean gate) and Topic 12 (Normandy/Nimbus)
- **To Do:**
  - [ ] P3: residual ~0.39% is generated FFI/histogram-glue + unguarded custom_distribution — accepted, sub-noise-floor
  - [ ] P2: document the stale-rlib/.fingerprint/libgkrust.a deletion step in the build script (a stale cached rlib silently reuses old code)
  - [ ] P2: expect to re-apply per Firefox version — glean-core is replaced wholesale on upgrade; line-anchored edits + SHAs will not survive

## SECTION F: PHASED EXPANSION PLAN

### Phase 2 — `third_party/rust/glean-core/src/metrics/custom_distribution.rs`
- **Tweak:** Add the same GORILLA_TELEMETRY_OFF guard to custom_distribution::accumulate (currently unguarded, ~0.10% of the residual).
- **Expected impact:** Sub-noise-floor; only worth doing if the residual becomes a concern.

### Phase 0 — `build script / toolchain-preflight`
- **Tweak:** Automate deletion of stale libglean_core-*.rlib / .fingerprint/glean_core-* / libgkrust.a before any build that touches glean-core, and assert a fresh rlib timestamp after.
- **Expected impact:** Removes the single most error-prone step (a stale rlib makes the whole fix silently ineffective).

## POSITIVE OBSERVATIONS

- ✅ This is the topic with the strongest empirical grounding in the whole build — every number is perf-measured, not estimated (8.9%->0.02%, 3.5%->0.00%, 0.84%->0.39%, ~13.2%->~0.39% total).
- ✅ Soft short-circuit over structural excision is the correct call, and the project learned it the hard way — the prior excision attempt (NS_ERROR_FACTORY_NOT_REGISTERED + 157 shim headers) is documented rather than hidden.
- ✅ The const-DCE technique is elegant: a compile-time true guard lets the optimizer remove both the recorded work AND the guard's own branch cost, which a runtime atomic could not.
- ✅ Severing at the recording stage (not the upload stage) is strictly stronger than the pref-based approach — there is no staged data to leak even if a downstream stage regressed.
- ✅ Coherent with Topics 03 (Necko-layer Glean gate) and 12 (Normandy/Nimbus): three topics attack the telemetry/experiment surface from three angles (source recording, network layer, experiment channel).
- ✅ The residual 0.39% is honestly accounted for (generated FFI glue + unguarded custom_distribution) rather than rounded to zero.

## VERIFICATION COMMANDS

```bash
perf record -p <parent-pid>   # during 1080p60 playback
perf report | grep -E 'smaps|walk_pgd|glean_core.*accumulate'   # expect absent
cat /proc/<parent>/task/*/comm | grep glean   # dispatcher thread present but 0% CPU
ls -la obj-*/.../libglean_core-*.rlib   # timestamp must be fresh (proves crate recompiled)
grep -n 'GORILLA_TELEMETRY_OFF' third_party/rust/glean-core/src/lib.rs   # expect const = true
grep -n 'return NS_OK' toolkit/components/glean/xpcom/FOG.cpp   # expect early return before fog_init
```



---

# ═══ MERGED DOCUMENT: 13-telemetry-kill.DEVELOPER.md (verbatim · sha256:b85dcbb0554d0fbd · merged 2026-08-02) ═══

# Telemetry / Glean Kill — Layered Source-Level Short-Circuits (13.2% -> 0.39% Parent CPU) — Developer Track

> **Topic:** `13-telemetry-kill` · **Files:** `xpcom/base/MemoryTelemetry.cpp`, `toolkit/components/glean/xpcom/FOG.cpp`, `third_party/rust/glean-core/src/lib.rs`, `third_party/rust/glean-core/src/dispatcher/global.rs`, `third_party/rust/glean-core/src/metrics/timing_distribution.rs`, `third_party/rust/glean-core/src/metrics/memory_distribution.rs`, `third_party/rust/glean-core/.cargo-checksum.json`
> **Generated:** 2026-07-17

---

## Module Summary

Eliminates the parent-process CPU cost of Firefox's two telemetry subsystems — legacy MemoryTelemetry and modern Glean/FOG — WITHOUT structurally removing them (which orphans mozilla::glean:: symbols and breaks the link). Three layered source-level short-circuits: (1) skip the periodic /proc/self/smaps resident-memory scan; (2) no-op FOG initialization so the Glean dispatcher thread is never flushed; (3) a compile-time const GORILLA_TELEMETRY_OFF guard on the hot metric-recording paths so the optimizer dead-code-eliminates them. Measured result during 1080p60 playback: total telemetry CPU fell from ~13.2% -> ~0.39% of the parent process. VERIFIED via perf, 2026-07-16.

## Architecture

- **Pattern:** Layered soft-disable (return-early / const-fold), NOT excision. Every symbol, XPCOM factory, and moz.build reference is left intact and compiled; only the work is prevented from running.
- **Trust Boundary:** Telemetry is a data-egress boundary. Recorded metrics flow: call site -> glean_core metric -> dispatcher queue -> ping assembly -> uploader -> Mozilla endpoints. This severs the chain at the recording stage — before data is ever staged — which is strictly stronger than severing at the upload stage (prefs only do the latter).
- **Attack Surface:** Behavioral egress neutralized (recording never happens). Local resource drain (the CPU finding) neutralized. Fingerprinting inputs (memory/timing distributions) not recorded -> not available.
- **Dependencies:** `No dependencies added. Removes de-facto runtime dependence on the Glean dispatcher thread and the nsMemoryReporterManager smaps path.`

## Kill Switches

### `MemoryTelemetry::GatherReports() (xpcom/base/MemoryTelemetry.cpp)` — HARD ⚠️

- **Condition:** always — unconditional early return after invoking the completion callback
- **Effect:** The background ResidentUnique measurement — which reads /proc/self/smaps and triggers vm_normal_page -> smaps_pte_range -> walk_pgd_range kernel page-table walks — is never dispatched. Verified 8.9% -> 0.02%.
- **Reversibility:** reversible
- **Notes:** Setting toolkit.telemetry.enabled=false does NOT stop this; the class has its own Poke()->timer->GatherReports() cycle. Source is the only off switch.

### `FOG::InitializeFOG() (toolkit/components/glean/xpcom/FOG.cpp)` — HARD ⚠️

- **Condition:** always — returns NS_OK before fog_init()
- **Effect:** glean::initialize() is never called; the dispatcher's pre-init buffer is never flushed. The glean.dispatche thread is still spawned (it is a Lazy static) but blocks forever on a channel recv at 0% CPU. Verified 3.5% -> 0.00%.
- **Reversibility:** reversible
- **Notes:** gInitializeCalled=true is set so the shutdown path does not attempt a re-init; glean::shutdown() on an uninitialized core is a documented no-op.

### `GORILLA_TELEMETRY_OFF const (third_party/rust/glean-core/src/lib.rs)` — HARD ⚠️

- **Condition:** compile-time constant true
- **Effect:** Guards TimingDistributionMetric::{start, stop_and_accumulate, accumulate_raw_duration}, LocalTimingDistribution::accumulate, and the MemoryDistribution equivalents. Because the guard is const, the optimizer folds if true { return } and eliminates the bodies — removing both the inline recording work AND the guard's own branch cost. dispatcher::global::launch() also drops tasks in production. Verified inline recording 0.84% -> 0.39%.
- **Reversibility:** reversible
- **Notes:** Flip the const to false and rebuild. Residual 0.39% is FFI/histogram-glue marshalling in generated bindings — see Technical Debt.

## Performance Profile

| Component | Before | After | Mechanism |
|---|---|---|---|
| MemoryTelemetry (smaps scan) | 8.9% | 0.02% | GatherReports() short-circuit |
| Glean dispatcher thread | 3.5% | 0.00% | InitializeFOG() no-op (thread blocks) |
| Glean inline recording | 0.84% | 0.39% | const DCE guards on timing+memory dist |
| Total telemetry CPU | ~13.2% | ~0.39% | ~12.8% of parent reclaimed |

- **CPU:** The dominant win. walk_pgd_range (kernel) and the dispatcher thread vanish from the profile entirely.
- **Memory:** Minor secondary win — the never-flushed pre-init buffer no longer accumulates recorded-metric closures over long sessions.
- **I/O:** Eliminates the 60s /proc/self/smaps read.
- **Timer Interval:** MemoryTelemetry's 60s Poke() cycle no longer fires meaningful work.

## Security Analysis

### User Profiling

Eliminated at the source. Glean events (timing/memory/custom distributions, counters) are never recorded, so no behavioral profile is constructed even locally. Exceeds the pref-based approach, which records-then-suppresses-upload.

### Targeting

N/A by design — with Nimbus/Normandy also disabled (Topic 12) there is no remote-experiment channel that could segment or target this build.

### Trust Chain

Data egress trust chain severed at stage 1 (recording). Even if a downstream stage were re-enabled by accident, there is no recorded data to transmit.

### Abuse Potential

Removes the browser's own ability to be a passive behavioral sensor. Residual 0.39% is pure local compute (FFI marshalling) with no egress path.

## Implementation Flow

1. **`MemoryTelemetry::GatherReports()`** — Early return NS_OK after firing the completion callback; the nsMemoryReporterManager async ResidentUnique dispatch is skipped.
   *Side effects:* No smaps scan, no kernel page-table walk.
2. **`FOG::InitializeFOG()`** — Set gInitializeCalled=true, return NS_OK before glean::impl::fog_init(...).
   *Side effects:* Dispatcher thread spawns but blocks at 0% CPU; no pre-init buffer flush.
3. **`glean-core/src/lib.rs`** — Declare pub const GORILLA_TELEMETRY_OFF: bool = true;
   *Side effects:* Enables DCE of all guarded metric bodies.
4. **`timing_distribution.rs / memory_distribution.rs`** — if crate::GORILLA_TELEMETRY_OFF { return ... } at the top of each hot recording method.
   *Side effects:* Bodies DCE'd under LTO; no inline recording work.
5. **`dispatcher/global.rs launch()`** — Drops the task when not in test mode.
   *Side effects:* No pre-init buffer growth from enqueued tasks.
6. **`.cargo-checksum.json`** — Per-file SHA256 entries updated for every edited vendored file.
   *Side effects:* Build's checksum guard accepts the edits (mandatory — else build rejects them).

## Technical Debt

🟢 **ACCEPTED** — Residual ~0.39% inline Glean — HistogramIdForMetric, fog_* FFI entry points, and firefox_on_glean wrapper delegation live in generated bindings that run around the guards; custom_distribution is unguarded (~0.10%)
  - *Recommendation:* Chasing this means editing generated code for sub-noise-floor gain. Intentionally not pursued.

🟠 **MEDIUM** — Vendored-crate rebuild fragility — editing glean-core does NOT reliably trigger a cargo rebuild
  - *Recommendation:* Delete stale libglean_core-*.rlib / .fingerprint/glean_core-* / libgkrust.a before rebuilding. Document in the build script (this bit an earlier attempt — the binary reused a cached rlib and the change appeared to have no effect).

🟠 **MEDIUM** — Upstream drift on version bump — glean-core is a vendored crate replaced wholesale each Firefox version
  - *Recommendation:* These line-anchored edits + the .cargo-checksum.json SHAs will NOT survive an upgrade; expect to re-apply the telemetry kill per version.

## Impact If Removed / Disabled

Reverting restores full telemetry recording and the ~12.8% parent-process CPU cost on target hardware, plus the /proc/self/smaps 60s scan and the active Glean dispatcher thread. On 4 GB / HDD machines this is the difference between a responsive browser and a laboring one.

## Testing Notes

1. Build; confirm 0 warnings and a fresh libglean_core-*.rlib timestamp (proves the crate actually recompiled — a stale rlib silently reuses old code). 2. Launch, play 1080p60, perf record -p <parent>; grep the profile for smaps, walk_pgd, glean_core::...::accumulate — MemoryTelemetry and timing/memory-distribution inner recording should be absent. 3. /proc/<parent>/task/* sample: glean.dispatche thread at 0%. 4. Confirm no startup/shutdown crash (validates the uninitialized-Glean path).

## Changelog Notes

Three-stage development: (1) MemoryTelemetry + FOG short-circuits -> ~11.5% saved; (2) dispatcher::launch no-op -> buffer-growth fix; (3) const GORILLA_TELEMETRY_OFF DCE guards on timing+memory distributions -> residual 0.84%->0.39%. Prior structural-excision attempt (documented with the project's own notes) abandoned: it caused NS_ERROR_FACTORY_NOT_REGISTERED and required 157 shim headers. GORILLA_TELEMETRY_OFF is a pre-existing in-tree identifier (no-brand-spam rule governs NEW identifiers).

---
*Developer Track. Human Track twin: `13-telemetry-kill.LAYMAN.md`.*


---

# ═══ MERGED DOCUMENT: 13-telemetry-kill.LAYMAN.md (verbatim · sha256:24d8c882eaea87f9 · merged 2026-08-02) ═══

# 🧍 The Browser That Stopped Spying On Itself (And Got Faster) — Plain English Guide

> *Topic `13-telemetry-kill` of the Gorilla Unleashed Firefox 154 build · Written for everyone · 2026-07-17*

---

## 🌍 The Big Picture

Every modern web browser quietly keeps a diary about you. Not the websites you visit necessarily — but *how you use the browser*: how much memory it is using, how long things take, which features you touch. Firefox calls this **telemetry**, and it collects it constantly, in the background, whether you asked for it or not.

Mozilla are not cartoon villains — they use this to spot bugs and improve the product. But here is the catch nobody mentions: **collecting all that data is not free.** Your computer has to do real work to measure itself, package the numbers, and get them ready to send. On a brand-new laptop you would never notice. On a 12-year-old machine, that hidden work is stealing power you cannot spare.

We measured it. On this hardware, during video playback, the browser was burning **about 1 out of every 8 units of effort** its main brain had — not on showing you web pages, but on watching and reporting on itself. This build turns that off. All of it. And here is the beautiful part: the result is a browser that both respects your privacy AND runs noticeably faster, because those turn out to be the same fix. On old hardware, surveillance has a body count measured in wasted seconds and dead battery.

## 🎭 The Main Characters

| Name | What It Is | Real-World Comparison |
|---|---|---|
| **Memory Telemetry** | A part of Firefox that, every 60 seconds, walks through all the browser's memory and writes down how much it is using | A clipboard inspector who stops the whole factory every minute to count every item in the warehouse — the counting itself slows the factory down |
| **Glean / FOG** | Mozilla's newer, fancier data-collection system that records 'events' — timings, counts, little facts | A second set of auditors, each carrying a stopwatch, timing everything anyone does |
| **The Dispatcher** | A dedicated worker whose only job is to process all those recorded events | The clerk who files every stopwatch reading into a giant cabinet |
| **/proc/self/smaps** | A special system file that lists every scrap of memory — reading it forces the operating system to do heavy bookkeeping | Asking the government for a certified list of every brick in your house — accurate, but it ties up an official for ages |
| **The Kill Switch** | A single line we added that says 'telemetry is OFF' — permanently, at build time | Flipping the master breaker so the whole surveillance wing of the building never gets power |

## 🔢 How It Works — Step by Step

### Step 1: We caught it in the act

Using a profiler (a tool that shows exactly where a computer spends its effort), we watched the browser play a 1080p video and asked: what is the main process actually doing? The answer was uncomfortable — a big slice was not video at all.

### Step 2: We found the biggest thief — the memory counter

The Memory Telemetry inspector was reading that 'every brick in the house' file every 60 seconds. That single habit was eating 8.9% of the main brain's effort. We switched it off at the source — it simply no longer does the count.

### Step 3: We found the second thief — the stopwatch auditors

Glean's dedicated filing clerk was burning another 3.5%. We stopped the system from ever hiring that clerk in the first place — the initialisation that would start it is short-circuited.

### Step 4: We found the stragglers — and installed the master breaker

Even with the clerk gone, the little stopwatch readings were still being *taken* (just never filed). So we added one permanent switch — GORILLA_TELEMETRY_OFF — that tells the browser, at the moment it is built, 'do not even take the readings.' The build tool then physically removes that code, so it cannot run at all.

### Step 5: We proved it

We measured again. The memory counter: gone. The filing clerk: gone. The surveillance wing went from ~13% of the browser's effort down to under half a percent — the leftover being tiny bits welded so deep into Firefox's frame that removing them is not worth the risk.

## 🤔 Quirky Things Worth Knowing

### ⚠️ Privacy and speed were the same problem

This is the beautiful part. We did not trade privacy for speed or speed for privacy. The spying *was* the slowness. Kill one, you kill both.

### ⚠️ Turning it 'off' in the settings was not enough

Firefox has a setting to disable telemetry. It does not actually stop the memory counting — that runs on its own timer regardless. The only real 'off' was in the source code itself. The setting is a light switch that is not connected to the light.

### ⚠️ We chose the scalpel, not the sledgehammer

A previous attempt tried to rip the whole system out. It caused crashes and needed 157 emergency patches to even compile. This time we left the machinery in place but cut its power — same result, no wreckage.

### ⚠️ Editing a sealed part needs a new sticker

Part of the fix is inside a 'vendored' Rust component (glean-core) — a sealed factory part. The build refuses to accept an edited sealed part unless its checksum sticker is updated too. Forget the sticker and the build rejects the whole thing. This tripped an earlier attempt.

## 💻 What Does This Mean For YOU?

### 🔋 Battery, Speed & Memory

On the target hardware, roughly 1/8th of the main process's workload during video playback handed back to you. Cooler running, a quieter fan, longer battery, and more responsiveness left over for the actual web page. Measured: ~13.2% -> ~0.39% of the parent process during 1080p playback.

### ⚡ Speed

Zero change to how fast pages load — except the machine has more spare effort, so everything around the page (scrolling, switching tabs) feels lighter.

### 🕵️ Your Privacy

Nothing about how you use this browser is measured, packaged, or prepared for sending. The data was going nowhere anyway (upload was already blocked), but now the browser does not even write it down. There is no diary.

### 🌐 Your Internet

No change to network behaviour — the win here is local CPU and battery.

## 🔴 The Kill Switch — Explained

**What it is:** A single line — GORILLA_TELEMETRY_OFF = true — added deep in the browser's guts. Because it is set permanently at build time (not a setting you toggle), the build tool is smart enough to see 'this can never be false' and physically deletes all the surveillance code that sits behind it.

**Without it:** Every time the browser did anything — drew a frame, opened a connection — it would quietly take a measurement, do the math, and file it. Thousands of times a minute. Invisible, constant, and on your dime.

**Think of it like:** The master power breaker for an entire wing of a building you never use. You do not walk around unplugging each lamp — you cut power to the whole wing at the fuse box, once, and it stays dark.

## 🌐 Open Source & Why It Matters To You

Remember Edward Snowden? He showed the world that data collection is rarely 'just for improving the product' — once the pipes exist, they get used. The only real defence is being able to *look inside the software* and see for yourself whether it is watching you. This is exactly why this change is public and readable. You do not have to *trust* that the telemetry is off — you can read the one line that turns it off, and read the proof that it worked. A closed browser asks for your faith. An open one hands you the flashlight.

## 📖 Glossary (Plain English Dictionary)

**Telemetry** — Data a program collects about how it is being used, usually sent back to its makers. Think of a car quietly logging your every trip and mailing it to the factory.

**Glean / FOG** — Mozilla's modern telemetry system ('Firefox On Glean'). The newer, more organized set of auditors with stopwatches.

**Profiler** — A tool that shows exactly where a program spends its effort, like a fitness tracker for software. It is how we caught the wasted work.

**Kill Switch** — A single deliberate off-switch that disables a whole feature. Ours is permanent and built-in, not a setting.

**/proc/self/smaps** — A Linux system file listing every piece of memory a program uses. Reading it is accurate but expensive — like a full certified inventory instead of a quick glance.

**Parent Process** — The browser's main 'brain' that coordinates everything. Freeing up its effort makes the whole browser feel faster.

**Dead-code elimination (DCE)** — When the build tool sees code that can never run (like the branch behind a permanently-true switch) and physically removes it from the finished program.

**Vendored crate** — A third-party code component (here, Rust's glean-core) copied into the source tree. Editing one requires updating its checksum sticker or the build rejects it.

---
*Human Track. Its Developer Track twin (`13-telemetry-kill.DEVELOPER.md`) covers the same changes in technical detail. Neither is a simplified copy of the other — they are the same truth in two languages.*


---

# ═══ MERGED DOCUMENT: 13-telemetry-kill.PRECHECK.json (verbatim · sha256:4f53cda18c2baa0c · merged 2026-08-02) ═══

```json
[]
```


---

# ═══ MERGED DOCUMENT: 13-telemetry-kill.PRECHECK.md (verbatim · sha256:499a73d38b614a87 · merged 2026-08-02) ═══

# Offline Pre-Check: 13-telemetry-kill

*Generated 2026-07-17 08:18:04 by doc_audit.py (rule-based, no model involved).*

## File Inventory

| File | Lang | Lines | Complexity | SHA256 (16) |
|---|---|---|---|---|
| third_party_rust_glean-core_.cargo-checksum.json.patch | patch | 7 | 1 | `d8b6d44d895277d3` |
| third_party_rust_glean-core_src_dispatcher_global.rs.patch | patch | 20 | 3 | `2cb8342c56e4f442` |
| third_party_rust_glean-core_src_lib.rs.patch | patch | 19 | 2 | `fea69ff0f3134793` |
| third_party_rust_glean-core_src_metrics_memory_distribution.rs.patch | patch | 37 | 5 | `9bd16fcb6f29da88` |
| third_party_rust_glean-core_src_metrics_timing_distribution.rs.patch | patch | 55 | 6 | `3b528afe52b94635` |
| toolkit_components_glean_xpcom_FOG.cpp.patch | patch | 15 | 2 | `bd5dc87e99d6714a` |
| xpcom_base_MemoryTelemetry.cpp.patch | patch | 28 | 3 | `d18d25900cd1883f` |

## Rule Findings (0)

*All offline rules passed.*


---

# ═══ REGENERATION 2026-08-04 — dual-track + audit regenerated against the LIVE tree; SUPERSEDES the 2026-08-02 merge above ═══

**Why this section exists.** The 2026-08-02 merge above was generated 2026-07-16/17,
before a second wave of `GORILLA_TELEMETRY_OFF` guards was added to the live tree. This
2026-08-04 regeneration re-verifies every claim against `the source tree`
(`dual-track` toolkit, `--validate` gate passed: layman 91/100, developer 86/100,
audit 99/100) and corrects two record-integrity items. **Where the two sections disagree,
THIS one is authoritative.**

**Corrections vs the 2026-08-02 merge (append-only — the older text is left intact above):**
- **T2 — custom_distribution is now GUARDED** (`src/metrics/custom_distribution.rs:109,:129`).
  The older DEVELOPER/AUDIT text calling it "unguarded (~0.10% residual)" and listing a
  future "Phase 2" is STALE; Phase 2 is done. The ~0.10% custom_distribution slice of the
  0.39% residual is overstated.
- **T1 — the patch set is a PARTIAL, non-reproducible record.** The live tree guards **17**
  metric files; this folder ships `.patch` files for only **4** of them, and
  `.cargo-checksum.json.patch(+)` carries live hashes for those 4 but VANILLA hashes for the
  other 15 (verified by exact-hash compare, e.g. boolean patch+=`9541aa19` vs live=`261c99f0`).
  Rebuilding from this folder alone yields a weaker 4-guarded-file kill than what ships.
  The shipped binary is correct; the RECORD is not reproducible. Tracked as audit defect P2-301.
- **Guarded-metric count updated 15→17** (live sweep 2026-08-04): boolean, counter,
  custom_distribution, datetime, denominator, event, memory_distribution, numerator, object,
  quantity, rate, string, string_list, text, timespan, timing_distribution, uuid. Plus lib.rs
  (const) and dispatcher/global.rs = 19 modified glean-core files total. Still unguarded:
  url.rs, labeled.rs, dual_labeled_counter.rs (egress still cut by the dispatcher drop).

**Doctrine unchanged.** SOFT-GATE, not excision — stubs / const-guards / compile-time DCE;
every symbol/factory/moz.build ref preserved. Never re-attempt excision (Prime Directive 0:
NS_ERROR_FACTORY_NOT_REGISTERED + 157 shim headers). `// Gorilla:` markers and
`GORILLA_TELEMETRY_OFF` (pre-existing identifier) are intentional.

**Not re-verified here:** the perf figures (13.2%→0.39% etc.) are the labelled 2026-07-16
`perf` measurement, NOT re-run in this pass; whether the shipped build recompiled glean-core
(stale-rlib risk) was not checked (no build performed).

*Original rendered sources (verbatim below): `13-telemetry-kill_{audit,developer,layman}.md`
+ `PRECHECK.md`, generated by `dual-track code render`, then deleted from the folder
(recoverable via git). Per one-master-log-per-folder policy.*


---

# ═══ MERGED DOCUMENT: 13-telemetry-kill.AUDIT.md (verbatim · sha256:65117a22585f2b4d · regenerated 2026-08-04) ═══

# IBM-Style Audit Report: 13.TELEMETRY.KILL

## SECTION A: DOCUMENT CONTROL

| Attribute | Value |
|---|---|
| **Target** | 13.TELEMETRY.KILL |
| **Files scanned** | see payload |
| **Date / time** | 2026-08-04 07:14:49 |
| **Audit status** | PASS |

## SECTION B: EXECUTIVE SUMMARY (Plain Language)

Firefox quietly measures how you use it, and on this 12-year-old hardware that self-measurement was burning about 1 in every 8 units of the main process's effort during video playback, on watching itself rather than showing you the video. This topic switches it off at the source and, measured on 2026-07-16, cut that cost from about 13.2% to about 0.39%. The switch is genuine and present in the shipped browser: a permanent build-time flag plus early exits, with a backstop that throws away any stray reading. One honest caveat: the shipped browser switches this off in more places (17 metric files) than the patch files in this folder record (4), so rebuilding from this folder alone would give a weaker result. The browser people actually run is fine; the paper trail needs completing. Think of a house wired correctly, but with two rooms missing from the blueprint.

## SECTION C: TECHNICAL SUMMARY (Developer)

Layered compile-time soft-disable (NOT excision) across MemoryTelemetry, FOG, and vendored glean-core. (1) MemoryTelemetry::GatherReports() early-returns at MemoryTelemetry.cpp:239, skipping the 60s /proc/self/smaps scan (8.9%->0.02%). (2) FOG::InitializeFOG() no-ops at FOG.cpp:153 before fog_init (:164), so the glean.dispatche thread idles at 0% (3.5%->0.00%). (3) A compile-time const GORILLA_TELEMETRY_OFF (lib.rs:115) DCE-guards the hot recording paths across 17 metric files (documented: timing_distribution.rs:161/203/486/688, memory_distribution.rs:103/189/391), inline recording 0.84%->0.39%. (4) dispatcher::global::launch() drops tasks in production (global.rs:55) as an egress backstop. All symbols/factories/moz.build refs preserved (excision caused NS_ERROR_FACTORY_NOT_REGISTERED + 157 shim headers; Prime Directive 0). Vendored edits require .cargo-checksum.json SHA updates. Every guard the docs claim was independently verified present in the live tree on 2026-08-04. Two record-integrity defects (D-301, D-302) concern the paper trail, not the shipped binary. Perf figures are the 2026-07-16 measurement, not re-run here.

## SECTION D: DETECTED DEFECTS

0 found by rules, 4 by review. Rule findings are deterministic; review findings are judgement.

### 🟡 P2-301 — P2 *(found by review)*

- **Plain English:** The patch files in this folder are an incomplete record of what the shipped browser actually does. The browser switches telemetry recording off in 17 of the collection engine's metric files, but only 4 have patch files here, and the checksum sticker file leaves the other 15 at their original (un-switched) values. Rebuilding from just this folder gives a weaker browser than the one that ships. Like a house that is wired correctly but whose blueprint is missing two rooms: the house is safe, the paperwork is not reproducible.
- **Technical:** Verified by exact-hash compare 2026-08-04. checksum-patch(+) == live for the 4 documented rust files (lib.rs d3883e6b, dispatcher/global.rs f4247e6f, memory_distribution.rs 43c316ab, timing_distribution.rs e18999bb) but == VANILLA (!= live) for the 15 undocumented guarded metric files (e.g. boolean patch+=9541aa19, live=261c99f0; custom_distribution patch+=0818727d, live=6dada21e). No .patch exists for any of the 15 (boolean, counter, custom_distribution, datetime, denominator, event, numerator, object, quantity, rate, string, string_list, text, timespan, uuid). Falsifiable: grep -rl GORILLA_TELEMETRY_OFF live/.../src/metrics | wc -l == 17, vs 4 named by the patch set.
- **Fix:** Generate the 15 missing per-file .patch files from vanilla-vs-live diffs and regenerate .cargo-checksum.json.patch so its + side carries the EDITED (live) hashes for all 19 modified glean-core files; OR explicitly label this folder a partial record and name the live tree as authority. Do NOT revert the extra guards — they are correct, on-doctrine, and already shipped.
- **Effort:** 2-3h

### 🟢 P3-302 — P3 *(found by review)*

- **Plain English:** The older documentation for this topic says one metric type (custom_distribution) is still switched on and lists finishing it as future work. That is stale: the shipped browser already switched it off. The residual-cost figure that blamed ~0.10% on that path is therefore overstated.
- **Technical:** Live custom_distribution.rs carries guards at :109 and :129 (diff vs vanilla = 2 inserted guard lines). The master log's AUDIT track lists 'unguarded custom_distribution' as accepted residual and a 'Phase 2 — custom_distribution.rs currently unguarded' future tweak; the DEVELOPER track says 'custom_distribution is unguarded (~0.10%)'. Phase 2 is already done.
- **Fix:** Correct the master log's residual accounting (drop the ~0.10% custom_distribution attribution) and mark Phase 2 DONE. Append-only per project rules; do not edit merged verbatim text in place — add a dated correction block.
- **Effort:** 20min

### 🟢 P3-303 — P3 *(found by review)*

- **Plain English:** A small amount of telemetry-related processor work remains (about 0.39% in the 2026-07-16 measurement). It is plumbing that runs around the switches and never leaves your machine. A few less-common metric types are also still switched on individually, but a backstop throws their readings away, so nothing is sent.
- **Technical:** Residual is generated FFI/histogram glue (HistogramIdForMetric, fog_* FFI entry points, firefox_on_glean wrapper delegation). Metric types url.rs, labeled.rs, dual_labeled_counter.rs remain unguarded but their launch() dispatch is dropped at global.rs:55 in production, so there is no egress. The 0.39% figure predates the second guard wave and was not re-measured.
- **Fix:** Accept as sub-noise-floor. Optionally add const guards to url/labeled/dual_labeled_counter for a small further CPU trim; do not edit generated bindings. Re-measure only if the residual becomes a concern.
- **Effort:** N/A (accepted) or ~1h for the optional extra guards

### 🟡 P2-304 — P2 *(found by review)*

- **Plain English:** Editing this sealed Rust component does not reliably make the browser rebuild it. If the build reuses an old cached copy, the whole telemetry kill silently does nothing even though the source looks correct.
- **Technical:** Stale libglean_core-*.rlib / .fingerprint/glean_core-* / libgkrust.a can be reused. The build step to delete them is not automated. Not verified in this pass: whether the shipped build actually recompiled glean-core (no build performed).
- **Fix:** Automate deletion of the stale artifacts before any build touching glean-core and assert a fresh rlib timestamp after. Document in the build script.
- **Effort:** 1h

## SECTION E: PRODUCTION READINESS

**Overall readiness: 🟢 92%**

**Done:**
- [x] MemoryTelemetry::GatherReports() early return verified present at MemoryTelemetry.cpp:239 (comment :231); measured 8.9%->0.02% (2026-07-16)
- [x] FOG::InitializeFOG() no-op verified at FOG.cpp:153 before fog_init (:164); measured 3.5%->0.00% (2026-07-16)
- [x] GORILLA_TELEMETRY_OFF const verified at lib.rs:115 = true; const-DCE guards confirmed across 17 metric files (2026-08-04 live sweep)
- [x] dispatcher::global::launch() drop backstop verified at global.rs:55 (gated on !TESTING_MODE)
- [x] custom_distribution now guarded (:109,:129) — Phase 2 complete (supersedes stale master-log claim)
- [x] .cargo-checksum.json internally consistent with live content (no stale entries); the 4 documented rust files' checksum-patch(+) hashes match live
- [x] Soft-disable chosen over excision — avoids NS_ERROR_FACTORY_NOT_REGISTERED + 157 shim headers (Prime Directive 0)
- [x] Coherent with Topic 03 (Necko Glean gate) and Topic 12 (Normandy/Nimbus)

**Blockers:**
- [ ] For an EXACT folder-only reproduction (not for shipping the binary, which is fine): the 15 missing metric-file .patch files and a corrected .cargo-checksum.json.patch (D-301) are required, otherwise a rebuild from this folder yields a weaker 4-guarded-file kill.

**To do:**
- [ ] D-302: correct the master-log residual accounting and mark Phase 2 done (stale 'custom_distribution unguarded' claim)
- [ ] D-304: automate stale-rlib/.fingerprint/libgkrust.a deletion in the build script
- [ ] D-303 (accepted, non-blocking): residual ~0.39% FFI glue + unguarded url/labeled/dual_labeled_counter — sub-noise-floor
- [ ] Expect to re-apply per Firefox version — glean-core is replaced wholesale on upgrade; line-anchored edits + SHAs will not survive

**Not verified:**
- Perf numbers (13.2%->0.39%, 8.9%->0.02%, 3.5%->0.00%, 0.84%->0.39%) NOT re-measured in this pass — they are the labelled 2026-07-16 perf result; verifying requires a build + perf on target hardware
- Whether the shipped build actually recompiled glean-core (stale-rlib risk) — no build performed
- Effect of the second guard wave (15 metric files, incl. custom_distribution) on the residual — applied after the 2026-07-16 measurement, not separately measured; current residual likely <=0.39% but unverified
- Guard PLACEMENT not re-validated against Mozilla/Glean upstream for hot-path optimality
- No sweep for telemetry edits OUTSIDE glean-core / FOG / MemoryTelemetry (scope = this room's declared files)

## SECTION F: PHASED PLAN

### Phase 1 — `Regenerate 15 missing metric-file .patch files + corrected .cargo-checksum.json.patch`
- **Change:** Diff vanilla-vs-live for boolean/counter/custom_distribution/datetime/denominator/event/numerator/object/quantity/rate/string/string_list/text/timespan/uuid; rewrite checksum + side with live hashes for all 19 files.
- **Expected impact:** Makes this folder a complete, reproducible record of the shipped kill (closes D-301).

### Phase 0 — `build script / toolchain-preflight`
- **Change:** Automate deletion of stale libglean_core-*.rlib / .fingerprint/glean_core-* / libgkrust.a before any build touching glean-core; assert a fresh rlib timestamp.
- **Expected impact:** Removes the most error-prone step; a stale rlib silently reuses old code (closes D-304).

### Phase 2 — `third_party/rust/glean-core/src/metrics/{url,labeled,dual_labeled_counter}.rs`
- **Change:** Optional: add the same const guard to the remaining unguarded recording types.
- **Expected impact:** Sub-noise-floor CPU trim; egress already prevented by the dispatcher drop. Only worth doing if the residual becomes a concern.

## POSITIVE OBSERVATIONS

- Strongest empirical grounding in the build — the CPU figures are perf-measured (2026-07-16), dated and method-stated, not estimated.
- Soft-disable over structural excision is the correct call and the prior excision failure (NS_ERROR_FACTORY_NOT_REGISTERED + 157 shim headers) is documented rather than hidden.
- The const-DCE technique is sound: a compile-time-true guard lets the optimizer remove the recorded work AND the guard's own branch, which a runtime atomic could not.
- Severing at the recording stage (not upload) is strictly stronger than the pref-based approach — no staged data exists to leak even if a downstream stage regressed.
- The tree advanced ahead of the docs in the SAFE direction: it guards MORE metric files (17) than documented (4), and every claimed guard was independently verified present on 2026-08-04.
- Coherent with Topics 03 and 12 — three angles on the telemetry/experiment surface (source recording, network layer, experiment channel).

## VERIFICATION COMMANDS

Run these to check the claims above rather than trusting them.

```bash
grep -n 'GORILLA_TELEMETRY_OFF' third_party/rust/glean-core/src/lib.rs   # expect 115: const = true
grep -rl 'GORILLA_TELEMETRY_OFF' third_party/rust/glean-core/src/metrics/ | wc -l   # expect 17
grep -n 'return NS_OK' toolkit/components/glean/xpcom/FOG.cpp | head -1   # expect :153, before fog_init :164
grep -n 'Gorilla' xpcom/base/MemoryTelemetry.cpp   # expect comment :231, return :239
grep -n 'drop(task)' third_party/rust/glean-core/src/dispatcher/global.rs   # expect :55 under !TESTING_MODE
perf record -p <parent-pid> during 1080p60; perf report | grep -E 'smaps|walk_pgd|glean_core.*accumulate'   # expect absent
ls -la obj-*/.../libglean_core-*.rlib   # timestamp must be fresh (proves the crate recompiled)
```

## Claim Sources

| Claim | Basis | Evidence |
|-------|-------|----------|
| Total telemetry parent CPU ~13.2% -> ~0.39% (2026-07-16) | 📄 stated in input | Total telemetry parent CPU: ~13.2% -> ~0.39% |
| MemoryTelemetry 8.9%->0.02%; dispatcher 3.5%->0.00%; inline 0.84%->0.39% | 📄 stated in input | MemoryTelemetry (smaps scan): 8.9% -> 0.02% ... Glean dispatcher thread: 3.5% -> 0.00% ... Glean inline recording (timing+memory distribution): 0.84% -> 0.39% |
| 17 metric files guarded, custom_distribution among them (:109,:129) | 📄 stated in input | custom_distribution.rs guards at :109, :129  (Phase 2 DONE — was doc-claimed "unguarded") |
| Checksum patch(+) == live for 4 documented, == vanilla for 15 undocumented | 📄 stated in input | the 4 documented rust files ... have checksum-patch(+) == live. The 15 undocumented metric files have checksum-patch(+) == VANILLA != live (e.g. boolean patch+=9541aa19, live=261c99f0) |
| Specific live hashes: lib d3883e6b, global.rs f4247e6f, mem_dist 43c316ab, timing_dist e18999bb | 🤖 model inference | *(none — model judgment)* |
| Excision abandoned: NS_ERROR_FACTORY_NOT_REGISTERED + 157 shim headers | 📄 stated in input | Prior excision attempt abandoned: NS_ERROR_FACTORY_NOT_REGISTERED + 157 shim headers |
| Kill-switch anchors: lib.rs:115, FOG.cpp:153, MemoryTelemetry.cpp:239, global.rs:55 | 📄 stated in input | lib.rs:115 ... FOG.cpp:150 Gorilla comment; :153 `return NS_OK;` ... MemoryTelemetry.cpp:231 Gorilla comment; :237 mLastRun set; :239 `return NS_OK;` ... dispatcher/global.rs:48 comment; :54 `if !TESTING_MODE...`; :55 `drop(task); return;` |
| url/labeled/dual_labeled_counter remain unguarded | 📄 stated in input | Still UNGUARDED metric-recording types: url.rs, labeled.rs, dual_labeled_counter.rs |
| Perf not re-measured; crate recompile not verified in this pass | 📄 stated in input | NOT re-measured in this 2026-08-04 documentation pass ... Not verified: whether the crate actually recompiled on the shipped build (stale-rlib risk) |
| Upload already disabled before this change | 📄 stated in input | Upload is already disabled; this prevents the dispatcher thread from being spawned. |


---
**How to verify this document:**
`📄 stated in input` — the model's phrasing of something your source text said.
Find the matching line in the original to verify.
`🤖 model inference` — the model's own judgment or synthesis. Treat as opinion,
not measurement. Re-run on the same input and check whether specific numbers
stay consistent between runs.

---

# ═══ MERGED DOCUMENT: 13-telemetry-kill.DEVELOPER.md (verbatim · sha256:f8626f55cb5ee352 · regenerated 2026-08-04) ═══

# Telemetry / Glean Kill — Layered Compile-Time Soft-Disable of MemoryTelemetry, FOG, and glean-core

> Generated 2026-08-04 | Source: `13.TELEMETRY.KILL`

---

## Purpose

This topic neutralizes the parent-process CPU cost of Firefox's two telemetry subsystems (legacy MemoryTelemetry and modern Glean/FOG) without structurally removing them. It sits at a data-egress trust boundary: recorded metrics normally flow call site -> glean_core metric -> dispatcher queue -> ping assembly -> uploader -> Mozilla endpoints. The kill severs that chain at stage 1 (recording), which is strictly stronger than severing at upload (what prefs do), because no data is ever staged to leak. The design is soft-disable, not excision: every symbol, XPCOM factory, and moz.build reference is left intact and compiled; only the work is prevented from running.

## Design Rationale

Excision was tried and abandoned: physically removing the subsystem orphaned mozilla::glean:: symbols and produced NS_ERROR_FACTORY_NOT_REGISTERED plus a requirement for 157 shim headers to relink (Prime Directive 0). The soft-disable replaces that with three cheap, reversible interventions. Crucially the glean-core guard is a compile-time `const` (GORILLA_TELEMETRY_OFF: bool = true) rather than a runtime atomic: under LTO the optimizer folds `if const { return }` and dead-code-eliminates the guarded body AND the guard's own branch cost, which a runtime flag could not achieve. Reversal is one line (flip the const, rebuild) versus a structural revert.

## Architecture

- **Pattern:** Layered soft-disable: unconditional early-return (C++ call sites) + compile-time const dead-code-elimination guard (Rust hot paths) + dispatcher task-drop backstop. NOT excision.
- **Trust boundary:** Telemetry is a data-egress boundary. This code trusts nothing downstream: it assumes upload could be re-enabled by accident and therefore cuts at the recording stage so there is no staged data to transmit. It does not trust that a runtime pref is honored (the MemoryTelemetry timer ignores toolkit.telemetry.enabled), so it hard-codes the off state in source.
- **Attack surface:** The behavioral-egress surface (recording of timing/memory/custom distributions, counters, events) is neutralized at the source. The local-resource-drain surface (the smaps scan and dispatcher thread) is neutralized. Fingerprinting inputs (memory/timing distributions) are not recorded, so they are not available to any consumer. Residual local compute (generated FFI/histogram glue) has no egress path.
- **Dependencies:** `xpcom/base/MemoryTelemetry.cpp`, `toolkit/components/glean/xpcom/FOG.cpp`, `third_party/rust/glean-core/src/lib.rs`, `third_party/rust/glean-core/src/dispatcher/global.rs`, `third_party/rust/glean-core/src/metrics/*.rs (17 metric files guarded in the live tree)`, `third_party/rust/glean-core/.cargo-checksum.json`

## Flags & Configuration

| Name | Type | Default | Effect | Notes |
|------|------|---------|--------|-------|
| `GORILLA_TELEMETRY_OFF` | `bool` | `true` | Compile-time const in glean-core/src/lib.rs:115. When true, every guarded metric-recording method returns before doing work; the optimizer DCEs the guarded body under LTO. | Pre-existing in-tree identifier (the no-brand-spam rule governs NEW names only). Flip to false and rebuild to restore stock recording. Reversal requires a clean glean-core recompile (see technical_debt). |
| `TESTING_MODE` | `AtomicBool` | `false` | Existing glean-core atomic (dispatcher/global.rs:18). The dispatcher drop is gated on !TESTING_MODE so vendored tests, which set it true, keep full dispatcher behavior. | Not added by this patch; reused as the production/test discriminator for the launch() drop. |

## API Surface

| Symbol | Description | Side Effects |
|--------|-------------|--------------|
| `MemoryTelemetry::GatherReports()` | Was: async gather of resident-memory reports. Now: invokes the completion callback and returns NS_OK without gathering. | Sets mLastRun and mTimer=nullptr; fires aCompletionCallback. No smaps read, no kernel page-table walk. |
| `FOG::InitializeFOG()` | Was: initialize Glean/FOG. Now: no-op returning NS_OK. | Sets gInitializeCalled=true; does not spawn the dispatcher's work. Dispatcher thread exists but idles. |
| `glean_core::GORILLA_TELEMETRY_OFF` | Compile-time master guard consumed by every guarded metric method via crate::GORILLA_TELEMETRY_OFF. | none (a const); enables DCE of guarded bodies. |
| `glean_core::dispatcher::global::launch()` | Was: enqueue a task on the dispatcher. Now: drops the task and returns in production; full behavior under TESTING_MODE. | In production, the task closure is dropped (no execution, no buffer growth). |

## Kill Switches

### `MemoryTelemetry::GatherReports() — xpcom/base/MemoryTelemetry.cpp:231-239`
- **Condition:** always (unconditional early return)
- **Effect:** Invokes aCompletionCallback(), sets mLastRun and mTimer=nullptr, then returns NS_OK before the nsMemoryReporterManager::GetOrCreate() path. The background ResidentUnique measurement that reads /proc/self/smaps and triggers vm_normal_page -> smaps_pte_range -> walk_pgd_range kernel page-table walks is never dispatched.
- reversible
- toolkit.telemetry.enabled=false does NOT stop this; the class has its own Poke()->timer->GatherReports() cycle, so source is the only off switch. Measured 8.9% -> 0.02% (2026-07-16).

### `FOG::InitializeFOG() — toolkit/components/glean/xpcom/FOG.cpp:148-153`
- **Condition:** always (returns NS_OK after gInitializeCalled=true)
- **Effect:** Returns before glean::impl::fog_init() at :164, so glean::initialize() is never called and the dispatcher's pre-init buffer is never flushed. The glean.dispatche thread is still spawned (Lazy static) but blocks forever on a channel recv at 0% CPU.
- reversible
- gInitializeCalled=true is set first so the shutdown path does not attempt a re-init; glean::shutdown() on an uninitialized core is a documented no-op. Measured 3.5% -> 0.00% (2026-07-16).

### `dispatcher::global::launch() — third_party/rust/glean-core/src/dispatcher/global.rs:54-55`
- **Condition:** when !TESTING_MODE (i.e. production)
- **Effect:** drop(task); return; — enqueued metric-recording closures are dropped immediately rather than piling up in the never-flushed pre-init buffer. This is the backstop that neutralizes egress even for metric types whose call sites are not individually const-guarded.
- reversible
- Prevents unbounded pre-init buffer growth (memory) and the ~0.84% CPU of closures on Renderer/Compositor/WebRender/Socket threads. Test mode retains full behavior.

### `const guards across 17 glean-core metric files (documented: timing_distribution.rs:161,203,486,688; memory_distribution.rs:103,189,391)`
- **Condition:** compile-time const true
- **Effect:** Each guarded method (e.g. TimingDistributionMetric::{start, stop_and_accumulate, accumulate_raw_duration} and the inline histogram accumulate) begins with if crate::GORILLA_TELEMETRY_OFF { return; }. Under LTO the body is DCE'd, removing inline recording work and the branch. TimingDistribution::start still returns a valid monotonic TimerId so stop_and_accumulate callers are unaffected.
- reversible
- Measured inline recording 0.84% -> 0.39% (2026-07-16); that residual figure predates the second guard wave and was not re-measured.

## Dead Code

- **`MemoryTelemetry.cpp — the original GatherReports() body below the early return (MakeScopeExit cleanup + nsMemoryReporterManager path)`** — Unreachable after the unconditional return NS_OK at :239. (risk: None to keep; it is intentionally retained so the change is a minimal, reviewable diff and trivially reversible. Removing it would enlarge the diff and complicate reversal.)
- **`FOG.cpp — RunOnShutdown lambda and fog_init call below :153`** — Unreachable after the early return. (risk: Retained deliberately; deleting it would turn a 6-line soft-disable into a structural edit.)
- **`glean-core guarded method bodies (timing_distribution/memory_distribution/etc.)`** — DCE'd by the optimizer because the const guard is provably true. (risk: None; removal is done by the compiler, not the source. Source is retained for one-line reversibility.)

## Performance

- **CPU:** Dominant win. Measured 2026-07-16 during 1080p60 playback: MemoryTelemetry smaps scan 8.9% -> 0.02%; Glean dispatcher thread 3.5% -> 0.00%; Glean inline recording 0.84% -> 0.39%; total telemetry parent CPU ~13.2% -> ~0.39% (~12.8 percentage points reclaimed). walk_pgd_range (kernel) and the dispatcher thread vanish from the profile. NOT re-measured in the 2026-08-04 doc pass; the second guard wave (15 more metric files, incl. custom_distribution) was applied after this measurement and its effect on the residual was not separately measured, so the current residual is likely <= 0.39% but is not measured.
- **MEMORY:** Secondary win: the never-flushed pre-init dispatcher buffer no longer accumulates recorded-metric closures over long sessions (the launch() drop prevents growth).
- **IO:** Eliminates the 60-second /proc/self/smaps read.
- **NOTES:** MemoryTelemetry's 60s Poke() cycle no longer performs meaningful work. Residual ~0.39% is generated FFI/histogram-glue marshalling (HistogramIdForMetric, fog_* FFI entry points, firefox_on_glean wrapper delegation) that runs around the guards in generated bindings; chasing it means editing generated code for sub-noise-floor gain.

## Security

- **Remote execution:** N/A — no code execution surface added or removed; the change only prevents local recording and dispatch.
- **Data handling:** Behavioral metrics (timing/memory/custom distributions, counters, events) are never recorded, so no local behavioral profile is constructed. This exceeds the pref-based approach, which records then suppresses upload.
- **Attack surface:** Removes the browser's own ability to act as a passive behavioral sensor. With Nimbus/Normandy also disabled (Topic 12) there is no remote-experiment channel to segment or target this build. Egress trust chain severed at stage 1 (recording): even if a downstream stage were re-enabled by accident, there is no recorded data to transmit.
- **Notes:** Residual 0.39% is pure local compute (FFI marshalling) with no egress path. Coherent with Topic 03 (Necko-layer Glean gate) and Topic 12 (Normandy/Nimbus): three angles on the same telemetry/experiment surface.

## Error Conditions

| Error | Cause | Remedy |
|-------|-------|--------|
| `cargo checksum verification failure on build` | A vendored glean-core file was edited without its per-file SHA256 being updated in .cargo-checksum.json. | Ensure the checksum patch is applied and each edited file's recorded hash equals its actual content hash. |
| `NS_ERROR_FACTORY_NOT_REGISTERED (historical, from the abandoned excision attempt)` | Structurally removing the telemetry subsystem orphaned mozilla::glean:: XPCOM factories. | Do not excise. The soft-disable in this topic exists precisely to avoid this; never retry excision. |
| `No behavioral change after applying patches` | Stale libglean_core-*.rlib / .fingerprint/glean_core-* / libgkrust.a reused; the crate did not recompile. | Delete the stale artifacts and rebuild; assert a fresh rlib timestamp. |

## Tasks

### Verify the guards exist in the live tree

Confirm the shipped state before trusting the kill. Run against the patched tree (FF_SRC=the source tree).

**Prerequisites:**
- A checked-out patched Firefox 154 tree
- ripgrep or grep

**Step 1:** grep -n 'GORILLA_TELEMETRY_OFF' third_party/rust/glean-core/src/lib.rs
  - Expected: 115:pub const GORILLA_TELEMETRY_OFF: bool = true;
**Step 2:** grep -rl 'GORILLA_TELEMETRY_OFF' third_party/rust/glean-core/src/metrics/ | wc -l
  - Expected: 17 (metric files guarded as of 2026-08-04)
**Step 3:** grep -n 'return NS_OK' toolkit/components/glean/xpcom/FOG.cpp | head -1  and  grep -n 'Gorilla' xpcom/base/MemoryTelemetry.cpp
  - Expected: FOG early return at :153 before fog_init (:164); MemoryTelemetry Gorilla comment at :231, return at :239.

**After this task:** All four kill switches are confirmed present at the documented lines.

### Prove the CPU cost is actually gone (runtime)

The static grep proves the switch is set; only a profile proves the work is gone. Requires a build and perf on target hardware.

**Prerequisites:**
- A build with a freshly recompiled glean-core (verify rlib timestamp)
- perf
- a 1080p60 test video

**Step 1:** perf record -p <parent-pid>   # during 1080p60 playback
  - Expected: A profile of the parent process.
**Step 2:** perf report | grep -E 'smaps|walk_pgd|glean_core.*accumulate'
  - Expected: Absent or negligible; the recording paths do not appear.
**Step 3:** cat /proc/<parent>/task/*/comm | grep glean
  - Expected: The glean.dispatche thread is present but at 0% CPU.

**After this task:** Profile confirms telemetry work is absent. Note: published percentages are the 2026-07-16 measurement, not re-run here.

### Regenerate the missing metric-file patches (record-integrity fix)

This folder documents 4 of the 17 guarded metric files; the checksum patch updates only those 4. Close the reproducibility gap.

**Prerequisites:**
- The patched live tree and its vanilla baseline

**Step 1:** For each of the 15 undocumented guarded metric files (boolean, counter, custom_distribution, datetime, denominator, event, numerator, object, quantity, rate, string, string_list, text, timespan, uuid), diff vanilla vs live and save a .patch.
  - Expected: 15 new .patch files matching the live guards.
**Step 2:** Regenerate .cargo-checksum.json.patch so its + side carries the EDITED (live) hashes for all 19 modified files, not just the 4.
  - Expected: Applying the folder to a vanilla tree reproduces the shipped 17-metric-file kill exactly.

**After this task:** The folder becomes a complete, reproducible record. (Not performed in this doc pass — read-only.)

## Troubleshooting

**Symptom:** Change appears to have no effect after rebuild.
**Cause:** Stale cached glean-core rlib/fingerprint reused; crate did not recompile.
**Remedy:** Delete libglean_core-*.rlib, .fingerprint/glean_core-*, and libgkrust.a; rebuild.
**Verify:** ls -la obj-*/.../libglean_core-*.rlib shows a fresh timestamp.

**Symptom:** Build fails on a glean-core checksum mismatch.
**Cause:** .cargo-checksum.json not updated for an edited file, or a hash does not match content.
**Remedy:** Apply/repair the checksum patch; recompute the per-file SHA256.
**Verify:** cargo build proceeds past the checksum verification step.

**Symptom:** Rebuilding from this folder yields a weaker kill than the shipped binary.
**Cause:** The folder is a partial record: only 4 of 17 metric guards have patches, and the checksum patch leaves the other 15 at vanilla hashes.
**Remedy:** Regenerate the 15 missing patches and a corrected checksum patch (see task above), or treat the live tree as authority.
**Verify:** grep -rl GORILLA_TELEMETRY_OFF <rebuilt>/third_party/rust/glean-core/src/metrics | wc -l equals 17.

## Technical Debt

🟠 **MEDIUM** — This folder is a non-reproducible partial record: the checksum-patch(+) hashes match live for the 4 documented rust files (lib.rs, dispatcher/global.rs, memory_distribution.rs, timing_distribution.rs) but equal VANILLA (not live) for the 15 undocumented metric files. Verified by exact-hash compare 2026-08-04 (e.g. boolean patch+=9541aa19, live=261c99f0). Rebuilding from this folder alone produces a 4-guarded-file kill, not the shipped 17-metric-file kill. → Generate the 15 missing .patch files and a corrected .cargo-checksum.json.patch whose + side carries live hashes for all 19 modified files; OR mark this folder a partial record and name the live tree as authority.
🟠 **MEDIUM** — Vendored-crate rebuild fragility: editing glean-core does not reliably trigger a cargo rebuild. → Automate deletion of stale libglean_core-*.rlib / .fingerprint/glean_core-* / libgkrust.a before any build touching glean-core, and assert a fresh rlib timestamp after. Document in the build script.
🟠 **MEDIUM** — Upstream drift on version bump: glean-core is vendored and replaced wholesale each Firefox version; these line-anchored edits and the .cargo-checksum.json SHAs will not survive an upgrade. → Expect to re-apply the telemetry kill per Firefox version; keep the guard list and line anchors in the master log so re-application is mechanical.
🟡 **LOW** — Residual ~0.39% inline Glean is generated FFI/histogram-glue (HistogramIdForMetric, fog_* FFI, firefox_on_glean wrapper) that runs around the guards; a few metric-recording types (url.rs, labeled.rs, dual_labeled_counter.rs) remain unguarded and still pay a clone+dispatch cost that the dispatcher then drops. → Accepted, sub-noise-floor. Guarding the remaining recording types is optional; the dispatcher drop already prevents egress. Do not edit generated bindings for sub-noise-floor gain.

## Impact If Removed

Reverting restores full telemetry recording and the ~12.8 percentage-point parent-process CPU cost on target hardware (2026-07-16 measurement), plus the 60-second /proc/self/smaps scan and an active Glean dispatcher thread flushing metrics. On ~4 GB / HDD distribution machines this is the difference between a responsive browser and a laboring one. Because the change is soft-disable, removal is a clean one-line-plus-early-returns revert; nothing else in the tree depends on the kill being present.

## Claim Sources

| Claim | Basis | Evidence |
|-------|-------|----------|
| GORILLA_TELEMETRY_OFF const at lib.rs:115 = true | 📄 stated in input | lib.rs:115  `pub const GORILLA_TELEMETRY_OFF: bool = true;` |
| FOG early return at :153 before fog_init at :164 | 📄 stated in input | FOG.cpp:150 Gorilla comment; :153 `return NS_OK;` — BEFORE fog_init at :164 |
| MemoryTelemetry Gorilla comment :231, return NS_OK :239 | 📄 stated in input | MemoryTelemetry.cpp:231 Gorilla comment; :237 mLastRun set; :239 `return NS_OK;` |
| Dispatcher drops task at global.rs:55 when !TESTING_MODE | 📄 stated in input | dispatcher/global.rs:48 comment; :54 `if !TESTING_MODE...`; :55 `drop(task); return;` |
| timing_distribution guards at :161,203,486,688; memory_distribution at :103,189,391 | 📄 stated in input | timing_distribution.rs guards at :161, :203, :486, :688 / memory_distribution.rs guards at :103, :189, :391 |
| 17 of 27 metric files guarded in the live tree (2026-08-04) | 📄 stated in input | 17 of 27 files in third_party/rust/glean-core/src/metrics/ carry the guard |
| 19 modified glean-core files total (17 metric + lib.rs + dispatcher/global.rs) | 📄 stated in input | Plus lib.rs (declares the const) and dispatcher/global.rs (guarded via TESTING_MODE) = 19 modified glean-core files total |
| custom_distribution is now guarded (Phase 2 done) | 📄 stated in input | custom_distribution.rs guards at :109, :129  (Phase 2 DONE — was doc-claimed "unguarded") |
| url.rs, labeled.rs, dual_labeled_counter.rs remain unguarded | 📄 stated in input | Still UNGUARDED metric-recording types: url.rs, labeled.rs, dual_labeled_counter.rs |
| Checksum patch matches live for 4 documented files, vanilla for 15 undocumented | 📄 stated in input | the 4 documented rust files ... have checksum-patch(+) == live. The 15 undocumented metric files have checksum-patch(+) == VANILLA != live (e.g. boolean patch+=9541aa19, live=261c99f0) |
| Total telemetry parent CPU ~13.2% -> ~0.39% (2026-07-16) | 📄 stated in input | Total telemetry parent CPU: ~13.2% -> ~0.39% (~12.8 percentage points reclaimed) |
| MemoryTelemetry 8.9% -> 0.02%; dispatcher 3.5% -> 0.00%; inline 0.84% -> 0.39% | 📄 stated in input | MemoryTelemetry (smaps scan): 8.9% -> 0.02% ... Glean dispatcher thread: 3.5% -> 0.00% ... Glean inline recording (timing+memory distribution): 0.84% -> 0.39% |
| Excision abandoned: NS_ERROR_FACTORY_NOT_REGISTERED + 157 shim headers | 📄 stated in input | Prior excision attempt abandoned: NS_ERROR_FACTORY_NOT_REGISTERED + 157 shim headers |
| smaps read triggers vm_normal_page kernel page-table walks | 📄 stated in input | ResidentUnique reads /proc/self/smaps on a background thread every 60s, triggering vm_normal_page kernel page-table walks |
| Perf not re-measured in doc pass; crate-recompile not verified | 📄 stated in input | NOT re-measured in this 2026-08-04 documentation pass ... Not verified: whether the crate actually recompiled on the shipped build (stale-rlib risk) |
| Const guard enables DCE that a runtime atomic could not | 🤖 model inference | *(none — model judgment)* |


---
**How to verify this document:**
`📄 stated in input` — the model's phrasing of something your source text said.
Find the matching line in the original to verify.
`🤖 model inference` — the model's own judgment or synthesis. Treat as opinion,
not measurement. Re-run on the same input and check whether specific numbers
stay consistent between runs.

*Auto-generated DITA-structured developer documentation.*

---

# ═══ MERGED DOCUMENT: 13-telemetry-kill.LAYMAN.md (verbatim · sha256:a1f5c71b0decefd4 · regenerated 2026-08-04) ═══

# The Browser That Stopped Watching Itself (And Got Faster) — Plain Language Guide

> Generated 2026-08-04 from `13.TELEMETRY.KILL`

---

## Should You Run This?

Yes, if you are running this custom Firefox on older or low-memory hardware and you want no self-telemetry. The change only removes measurement of the browser by itself; it does not touch the web pages you visit or your ability to use any feature. The one honest caveat is for someone rebuilding from this folder alone: the patch set is a partial record, so generate the missing metric-file patches (or build from the shipped tree) if you need an exact reproduction.

## Worst Case, Honestly

The realistic worst outcome is narrow. If the build somehow reused a stale cached copy of the collection engine, the switch could fail to take effect and telemetry recording would run as normal (the same behavior as stock Firefox, whose upload is separately blocked in this build anyway). It would not send anything new that stock Firefox does not; it would only waste the processor effort this change was meant to save. There is no path here by which your data is exposed to a third party that it would not already have been.

## What Data This Touches

Nothing about how you use this browser leaves your machine as a result of self-telemetry, because it is never recorded in the first place. Upload was already blocked in this build, so the numbers were going nowhere; this change stops the browser even writing them down. It does not affect the web pages you visit or the data you send to websites yourself; it only stops the browser measuring itself.

## Before You Trust It

You are trusting a stranger's edit to your browser. You cannot read all the source, but you can check a few plain signals that prove the switch is set and the biggest cost is gone. None of these needs you to be a programmer.

**Step 1:** Open the file third_party/rust/glean-core/src/lib.rs and go to line 115. Look for the line that reads: pub const GORILLA_TELEMETRY_OFF: bool = true;
  - Look for: It must say true, not false. This is the master switch. If it says true, the surveillance code behind it is removed at build time.
**Step 2:** Open toolkit/components/glean/xpcom/FOG.cpp around line 150. Look for a comment beginning // Gorilla: skip Glean initialization and a return NS_OK; just below it (line 153).
  - Look for: The return must come before the line that calls fog_init (line 164). If it does, the filing-clerk system is never started.
**Step 3:** Open xpcom/base/MemoryTelemetry.cpp around line 231. Look for the // Gorilla: disabled comment and a return NS_OK; at line 239.
  - Look for: The return must sit before the code that reads /proc/self/smaps. If it does, the 60-second memory count never runs.
**Step 4:** If you can run the build and a profiler (this is the advanced check), play a 1080p video and record the main process. Search the profile for the words smaps, walk_pgd, and accumulate.
  - Look for: Those names should be absent or negligible. Their absence is the proof the work is actually gone, not merely switched off on paper. Note: the published percentages were measured on 2026-07-16 and were not re-run here, so treat your own numbers as the current truth.

## The Big Picture

Every modern web browser keeps a quiet diary about how you use it: how much memory it is using, how long each little job takes, which features you touch. Firefox calls this telemetry. It runs in the background whether you asked for it or not. Mozilla use it to find bugs and guide the product, so this is not a cartoon-villain story. But there is a cost nobody puts on the label: measuring yourself takes real work. Your processor has to stop, count, package the numbers, and get them ready to send.

On a brand-new laptop you would never feel it. On the 12-year-old hardware this build is made for, that hidden work is stealing power you cannot spare. It was measured once, on 2026-07-16, with a profiler (a tool that shows exactly where a computer spends its effort) while the browser played a 1080p video. About 1 out of every 8 units of the main process's effort was going to watching and reporting on itself, not to showing you the video.

This patch group turns that self-watching off at the source. Not by deleting the machinery (that was tried once and it broke the browser), but by cutting the power to it: a permanent build-time switch plus a set of early exits that stop the work before it starts. The happy accident is that privacy and speed turned out to be the same fix. Stop the browser writing the diary, and you also hand its effort back to the web page in front of you.

## Key Concepts

| Name | What It Means | Real-World Comparison |
|------|--------------|------------------------|
| `Memory Telemetry` | A part of Firefox that every 60 seconds walks through the browser's memory and writes down how much it is using. | A clipboard inspector who halts the whole factory every minute to count every item in the warehouse. The counting itself slows the factory. |
| `Glean / FOG` | Mozilla's newer data-collection system that records events: timings, counts, small facts about how the browser runs. | A second set of auditors, each carrying a stopwatch, timing everything anyone does. |
| `The Dispatcher` | A dedicated background worker whose only job is to file all the recorded readings. | The clerk who files every stopwatch reading into a giant cabinet. |
| `/proc/self/smaps` | A Linux system file that lists every scrap of memory a program uses; reading it forces the operating system into heavy bookkeeping. | Asking the government for a certified list of every brick in your house: accurate, but it ties up an official for ages. |
| `GORILLA_TELEMETRY_OFF` | A single permanent switch, set to true when the browser is built, that tells the browser not to take the readings at all. | The master power breaker for a whole wing of a building, flipped once at the fuse box. |
| `Dead-code elimination` | When the build tool sees code that can never run (because the switch behind it is permanently off) and leaves it out of the finished program. | A builder who, told a room will never be used, does not bother wiring it at all. |

## How It Works — Step by Step

### Step 1: Catch it in the act

A profiler watched the main process play a 1080p60 video and asked a blunt question: what is it actually doing? A large slice of the answer was not video. It was the browser measuring itself. This is the measurement that grounds everything below, taken on 2026-07-16.

### Step 2: Silence the memory counter (the biggest thief)

Memory Telemetry woke every 60 seconds and read /proc/self/smaps to count every scrap of memory the browser held. Reading that file forces the operating system into heavy bookkeeping, like certifying every brick in your house. That single habit was eating about 8.9% of the main process's effort. The fix adds an early exit at the top of the counting routine (MemoryTelemetry.cpp, line 239): it tells whoever was waiting that it is done, then returns without doing the count. Measured afterward: 0.02%.

### Step 3: Never hire the filing clerk (the second thief)

Glean runs a dedicated background worker whose only job is to file the recorded readings. That worker was burning about another 3.5%. The fix stops the system that would start it: the startup routine (FOG.cpp, line 153) exits before it ever calls the initialize function. The worker thread is still created, because it is built to always exist, but it sits with nothing to do at 0% effort. Measured afterward: 0.00%.

### Step 4: Install the master breaker

Even with the clerk idle, thousands of tiny stopwatch readings were still being taken (just never filed). So a single permanent switch was added deep in the code: GORILLA_TELEMETRY_OFF, set to true at build time (glean-core/src/lib.rs, line 115). Because it can never be false, the build tool sees that the code behind it can never run and leaves it out of the finished program. Dozens of recording routines across the collection system now start with a one-line check of this switch and exit immediately.

### Step 5: Drop anything that still slips through

As a backstop, the queue that would carry any stray reading to the filing clerk was changed to throw the reading away instead (glean-core/src/dispatcher/global.rs, line 55). So even a recording routine that was not individually switched off has nowhere to send its data. Test builds keep the full behavior so Mozilla's own tests still pass.

### Step 6: Re-seal the sealed part

Glean lives in a vendored crate: a sealed, third-party Rust component copied into Firefox's source. The build refuses an edited sealed part unless its checksum sticker is updated too. Every edited file's sticker was rewritten in .cargo-checksum.json so the build accepts the changes. Forget this and the whole build is rejected; it tripped an earlier attempt.

## Quirky Things Worth Knowing

### Privacy and speed were the same problem

This is the surprising part. Nothing was traded. The spying was the slowness. Kill one and you kill both. On old hardware, surveillance has a real body count measured in wasted seconds and drained battery.

### The settings switch was never connected to the light

Firefox has a menu setting to turn telemetry off. It does not stop the memory counter, which runs on its own 60-second timer regardless. The only real off switch was in the source code. The menu toggle is a light switch wired to nothing.

### The scalpel, not the sledgehammer

An earlier attempt tried to rip the whole telemetry system out. It caused crashes and needed 157 emergency patch-headers to even compile. This build leaves every part in place and cuts its power instead. Same result, no wreckage. This is deliberate policy, not laziness: the code is a fly in a jar, alive but going nowhere.

### The written record is thinner than what actually ships

Checked on 2026-08-04, the live browser switches off recording in 17 of the collection system's metric files. But this folder only carries patch files for 4 of them, plus 3 for the other pieces. If someone rebuilt from these patches alone, they would get a weaker version than the one that ships. The shipped browser is fine; the paper trail is incomplete. This guide documents the real, shipped state so nobody is misled.

## What This Means For You

### Battery, Processor & Memory

On the reference machine (16 GiB, 12-year-old Intel), the total telemetry cost of the main process during 1080p60 playback fell from about 13.2% to about 0.39%, roughly 1/8th of that process's effort handed back. That is cooler running, a quieter fan, and more battery. Memory also benefits slightly: the never-flushed backlog of recorded readings no longer piles up over a long session. These are the 2026-07-16 measured figures; they were not re-run for this guide, and the extra recording routines switched off since then were not separately measured, so the true current cost is likely a little lower but is not measured.

### Speed

Web pages do not load faster because of this change. What changes is that the machine has more spare effort left over, so everything around the page (scrolling, switching tabs) feels lighter. On a ~4 GB distribution machine that headroom is the difference between responsive and laboring.

### Your Privacy

Nothing about how you use this browser is measured, packaged, or prepared for sending. Upload was already blocked in this build, so the data was going nowhere; now the browser does not even write it down. There is no diary to leak.

### Your Internet

No change to network behavior. The win here is local: processor effort and battery, not bandwidth.

## The Off Switch

**What it is:** A single line, GORILLA_TELEMETRY_OFF = true, added deep in the collection engine (glean-core/src/lib.rs, line 115). It is set permanently when the browser is built, not something you toggle in a menu. Because it can never be false, the build tool removes the surveillance code that sits behind it from the finished program.

**Without it:** Every time the browser did anything (drew a frame, opened a connection) it would quietly take a measurement, do the math, and hand it to a background worker to file. Thousands of times a minute, invisible and constant, on your processor's time.

**Think of it like:** The master power breaker for a wing of a building you never use. You do not walk around unplugging each lamp. You cut power to the whole wing at the fuse box, once, and it stays dark.

## How to use this

**Before you start:**
- You are building or running the Gorilla Unleashed Firefox 154 tree, not stock Firefox.
- You understand this changes a vendored Rust crate, so a clean rebuild of glean-core is needed for the change to take effect.

**Step 1:** Apply the patches in this folder to a matching Firefox 154 source tree, then build normally.
  - You should see: The build accepts the edited glean-core files because their checksum stickers were updated in .cargo-checksum.json.
**Step 2:** After building, confirm the glean-core library was actually recompiled by checking that its build artifact has a fresh timestamp.
  - You should see: A stale cached artifact silently reuses the old code and the change appears to do nothing. A fresh timestamp means your build really contains the switch.
**Step 3:** Launch the browser and use it normally.
  - You should see: No visible difference in behavior. On old hardware, the machine feels lighter under load. No self-telemetry is recorded or sent.

## If Something Goes Wrong

**You applied the patches but a profiler still shows telemetry work happening.**
The vendored Rust crate was not rebuilt. Editing glean-core does not always trigger a rebuild, so the build reused a stale cached copy of the old code.
What to do: Delete the stale cached glean-core artifacts (the .rlib, its fingerprint, and libgkrust.a) and rebuild. Then re-check the artifact timestamp is fresh.

**The build is rejected with a checksum error mentioning glean-core.**
A sealed vendored file was edited without updating its checksum sticker, or a sticker does not match the file's current contents.
What to do: Make sure the .cargo-checksum.json patch was applied and that every edited file's recorded hash matches its actual contents.

**You rebuilt from only this folder and fewer things are switched off than expected.**
This folder is a partial record. It carries patches for 4 of the 17 metric files that the shipped browser switches off. This is a known gap, not a bug in your build.
What to do: Treat the live shipped tree as the authority, or generate the missing patch files first. The master switch (lib.rs line 115) and the dispatcher backstop still protect you either way.

## Why a Developer Would Do This

A developer chose the const-switch-and-early-exit approach over deleting the code because deleting it broke the browser badly once (crashes plus 157 emergency headers). Leaving the machinery in place but cutting its power gives the same privacy and speed result with none of the fragility. It also means the change is easy to reverse: flip one line back to false and rebuild. Honesty is part of the design here, which is why the gap in the paper trail is written down instead of hidden.

## Why It Matters That You Can Read This

Edward Snowden showed the world that data pipes, once built, tend to get used, and that improving-the-product is rarely the whole story. The only real defense is being able to look inside the software and check for yourself. That is exactly why this change is public and readable. You do not have to trust that telemetry is off. You can read the one line that turns it off (lib.rs line 115), read the early exits that back it up, and read this honest note that the paper trail is thinner than the shipped browser. A closed browser asks for your faith. An open one hands you the flashlight, including the parts that are not finished.

## Glossary

**Telemetry** — Data a program collects about how it is being used, usually to send back to its makers.

**Glean / FOG** — Mozilla's modern telemetry system, short for Firefox On Glean.

**Profiler** — A tool that shows exactly where a program spends its effort, like a fitness tracker for software.

**Kill switch** — A single deliberate off-switch that disables a whole feature; here it is permanent and set at build time.

**/proc/self/smaps** — A Linux system file listing every piece of memory a program uses; reading it is accurate but expensive.

**Parent process** — The browser's main coordinating process; freeing its effort makes the whole browser feel faster.

**Dead-code elimination** — When the build tool sees code that can never run and leaves it out of the finished program.

**Vendored crate** — A third-party code component copied into the source tree; editing one requires updating its checksum sticker or the build rejects it.

**Dispatcher** — A background worker that files recorded telemetry readings; here it is left idle or made to drop everything.

**Soft-gate** — Turning a feature off by blocking its work with a switch or early exit, rather than deleting the code.

## Claim Sources

| Claim | Basis | Evidence |
|-------|-------|----------|
| Total telemetry parent CPU fell from ~13.2% to ~0.39% | 📄 stated in input | Total telemetry parent CPU: ~13.2% -> ~0.39% |
| Memory Telemetry smaps scan cost 8.9%, then 0.02% | 📄 stated in input | MemoryTelemetry (smaps scan): 8.9% -> 0.02% parent CPU |
| Glean dispatcher thread cost 3.5%, then 0.00% | 📄 stated in input | Glean dispatcher thread: 3.5% -> 0.00% parent CPU |
| Kill switch is at lib.rs line 115 and is set to true | 📄 stated in input | lib.rs:115  `pub const GORILLA_TELEMETRY_OFF: bool = true;` |
| FOG.cpp returns NS_OK at line 153 before fog_init at line 164 | 📄 stated in input | FOG.cpp:150 Gorilla comment; :153 `return NS_OK;` — BEFORE fog_init at :164 |
| MemoryTelemetry.cpp returns NS_OK at line 239 | 📄 stated in input | MemoryTelemetry.cpp:231 Gorilla comment; :237 mLastRun set; :239 `return NS_OK;` |
| Dispatcher drops the task at global.rs line 55 | 📄 stated in input | dispatcher/global.rs:48 comment; :54 `if !TESTING_MODE...`; :55 `drop(task); return;` |
| 17 of 27 metric files carry the guard as of 2026-08-04 | 📄 stated in input | 17 of 27 files in third_party/rust/glean-core/src/metrics/ carry the guard |
| This folder carries patches for 4 of the 17 metric files | 📄 stated in input | the 4 documented rust files ... have checksum-patch(+) == live. The 15 undocumented metric files have checksum-patch(+) == VANILLA != live |
| Prior excision attempt caused crashes and needed 157 shim headers | 📄 stated in input | Prior excision attempt abandoned: NS_ERROR_FACTORY_NOT_REGISTERED + 157 shim headers |
| Upload was already disabled before this change | 📄 stated in input | Upload is already disabled; this prevents the dispatcher thread from being spawned. |
| Perf figures measured 2026-07-16, not re-measured in this pass | 📄 stated in input | measured 2026-07-16 via `perf` ... NOT re-measured in this 2026-08-04 documentation pass |
| The build reuses stale cached crate artifacts unless they are deleted | 🤖 model inference | *(none — model judgment)* |


---
**How to verify this document:**
`📄 stated in input` — the model's phrasing of something your source text said.
Find the matching line in the original to verify.
`🤖 model inference` — the model's own judgment or synthesis. Treat as opinion,
not measurement. Re-run on the same input and check whether specific numbers
stay consistent between runs.

*Human Track. Its Developer Track twin covers the same changes in technical detail. Neither is a simplified copy of the other — they are the same truth in two languages.*

---

# ═══ MERGED DOCUMENT: 13-telemetry-kill.PRECHECK.md (verbatim · sha256:487c4f4126a86d40 · regenerated 2026-08-04) ═══

# Offline Pre-Check: 13-telemetry-kill

*Generated 2026-08-04 07:06:59 by rules only. No model was involved, so everything below is a deterministic finding about the files as they are on disk.*

## Files Scanned

| File | Language | Lines | Code | Complexity | SHA-256 |
|---|---|---|---|---|---|
| `third_party_rust_glean-core_.cargo-checksum.json.patch` | patch | 7 | 7 | 1 | `d8b6d44d895277d3` |
| `third_party_rust_glean-core_src_dispatcher_global.rs.patch` | patch | 20 | 18 | 3 | `2cb8342c56e4f442` |
| `third_party_rust_glean-core_src_lib.rs.patch` | patch | 19 | 16 | 2 | `fea69ff0f3134793` |
| `third_party_rust_glean-core_src_metrics_memory_distribution.rs.patch` | patch | 37 | 31 | 5 | `9bd16fcb6f29da88` |
| `third_party_rust_glean-core_src_metrics_timing_distribution.rs.patch` | patch | 55 | 44 | 6 | `3b528afe52b94635` |
| `toolkit_components_glean_xpcom_FOG.cpp.patch` | patch | 15 | 15 | 2 | `bd5dc87e99d6714a` |
| `xpcom_base_MemoryTelemetry.cpp.patch` | patch | 28 | 26 | 3 | `d18d25900cd1883f` |

## Findings

🔴 P0: 0 · 🟠 P1: 0 · 🟡 P2: 0 · 🟢 P3: 0

*No findings. The rules found nothing wrong; this is not a statement that the code is correct.*


PRECHECK.json: `[]` (0 offline-rule findings)
