# 06.QUOTA - Master Project Log

*Regenerated 2026-08-04 by the doc-audit toolkit (`dual-track`). Policy: one master project log per folder - the LAYMAN, DEVELOPER, AUDIT and PRECHECK tracks are merged VERBATIM below and their standalone files are deleted (recoverable via git history).*

## Regeneration note (supersedes the 2026-07-16 generation-1 content)

This log replaces the earlier merged docs, which contained a **phantom function name**. Corrections applied and tree-verified this pass (2026-08-04, live tree `the source tree`):

- The whitelist predicate is **`QuotaManager::IsOriginInternal`** (ActorsParent.cpp:7774; declared QuotaManager.h:744), **not** the phantom `IsFirstOriginQuotaPromptRequired`, which exists nowhere in the tree.
- The `NIGHTLY_BUILD -> EARLY_BETA_OR_EARLIER` gate swap (:4297) is a **no-op on this build**: milestone `154.0a1` (config/milestone.txt) defines both macros, and `--disable-debug` leaves the gate on the channel macro alone. The swap only widens the diagnostic's reach to early-Beta milestones. (The old docs implied it newly enabled the diagnostic here.)
- The deleted shutdown block is **8 lines** (old docs said 6); the two private-browsing maps are still used at :8699/:8724/:8738 and no `.Clear()` remains anywhere.
- The single patch **reproduces the live tree byte-for-byte** from vanilla (sha256(16)=`2814f13dbeb54536`, 42 lines). Pre-check: 0 P0/P1/P2/P3.
- Quality gate (MASTER_TEMPLATE >=85): LAYMAN **88**, DEVELOPER **90**, AUDIT **96** - all PASS. Audit readiness: **92%** (only open item: provenance/authorship of the three hunks - project edit vs upstream drift - not resolvable without mozilla-central network access).
- Companion forensic record kept alongside this log: `POR_DRAFT_2026-08-03.md`.


---

# === MERGED DOCUMENT: PRECHECK.md (verbatim - sha256:6fd8931bd587c9dd - merged 2026-08-04) ===
*Track: 06-quota PRECHECK (rule-based offline pre-check)*

# Offline Pre-Check: 06-quota

*Generated 2026-08-04 07:04:07 by rules only. No model was involved, so everything below is a deterministic finding about the files as they are on disk.*

## Files Scanned

| File | Language | Lines | Code | Complexity | SHA-256 |
|---|---|---|---|---|---|
| `dom_quota_ActorsParent.cpp.patch` | patch | 42 | 36 | 7 | `2814f13dbeb54536` |

## Findings

🔴 P0: 0 · 🟠 P1: 0 · 🟡 P2: 0 · 🟢 P3: 0

*No findings. The rules found nothing wrong; this is not a statement that the code is correct.*


---

# === MERGED DOCUMENT: 06-quota_audit.md (verbatim - sha256:9a7cc844e450e808 - merged 2026-08-04) ===
*Track: 06-quota AUDIT (IBM Sections A-F)*

# IBM-Style Audit Report: 06.QUOTA

## SECTION A: DOCUMENT CONTROL

| Attribute | Value |
|---|---|
| **Target** | 06.QUOTA |
| **Files scanned** | see payload |
| **Date / time** | 2026-08-04 07:11:17 |
| **Audit status** | PASS |

## SECTION B: EXECUTIVE SUMMARY (Plain Language)

This is one small, safe change to the part of Firefox that decides how much disk space each website may use. It does three tidy things: it tells Firefox not to ask for a storage permission on its own home page, it adjusts which internal test builds carry one warning message, and it deletes a clean-up step that was no longer needed. Nothing here sends your data anywhere. The change has been checked line-by-line against the actual Firefox source and rebuilds the tree exactly, like a spare key that has been tested in the lock. It is safe to ship. The only open question is a paperwork one - whether these three edits are this project's own work or ordinary Firefox updates that came along with a source refresh - which does not affect whether the code is correct.

## SECTION C: TECHNICAL SUMMARY (Developer)

Three independent point fixes to dom/quota/ActorsParent.cpp, the parent-process Quota Manager. (1) Adds kAboutHomeOriginPrefix = "moz-safe-about:home" (:268) and whitelists it via StringBeginsWith in QuotaManager::IsOriginInternal (:7779; def :7774; decl QuotaManager.h:744), skipping the first persistent-storage prompt for Firefox's own home page - consistent with the existing chrome://, indexeddb://, resource:// entries. (2) Widens a negative-usage console diagnostic (Firefox bug 1683863) from NIGHTLY_BUILD to EARLY_BETA_OR_EARLIER at :4297; on this build's milestone (154.0a1) both macros are defined, so the swap is a no-op here and only changes reachability on early-Beta milestones. (3) Deletes an 8-line MutexAutoLock(mQuotaMutex) + dual .Clear() block from temporary-storage shutdown; the two maps remain populated/queried at :8699/:8724/:8738 and no .Clear() remains anywhere. The patch reproduces the live tree byte-for-byte from vanilla (verified 2026-08-04). No code defects. Non-blocking: authorship of the three hunks (project vs upstream drift) is unresolved, and no GORILLA OVERRIDE markers are present.

## SECTION D: DETECTED DEFECTS

0 found by rules, 2 by review. Rule findings are deterministic; review findings are judgement.

### 🟢 P3-001 — P3 *(found by review)*

- **Plain English:** Housekeeping, not a code fault: these three edits to Firefox's source carry no project 'who changed this and why' tag, which the project's own rules ask for. It is unclear whether they are the project's own work or ordinary Firefox updates. Like a repair with no signature on the work order - the repair is fine, the paperwork is missing.
- **Technical:** grep 'GORILLA' dom/quota/ActorsParent.cpp -> none. the project rules file mandates // GORILLA OVERRIDE: markers on project edits to Mozilla source. None of the three hunks (:268/:7779, :4297, deleted shutdown block) carry one. None is a resource optimization; all read as upstream correctness fixes; vanilla vs live trees are ~3 days apart.
- **Fix:** Diff the three hunks against mozilla-central at the pull revision. If project-authored, add provenance markers; if upstream, annotate 06.QUOTA as documenting upstream drift.
- **Effort:** 30min (needs network access to mozilla-central)

### 🟢 P3-002 — P3 *(found by review)*

- **Plain English:** A prior version of this room's documentation named a function that does not exist. The code is right; the old description was wrong. Corrected here.
- **Technical:** Pre-2026-08-04 docs named the whitelist predicate IsFirstOriginQuotaPromptRequired; that symbol exists nowhere in dom/quota/. The real predicate is QuotaManager::IsOriginInternal (:7774). Already flagged in POR_DRAFT_2026-08-03 and the PRECHECK correction; this audit uses the correct name throughout.
- **Fix:** Ensure the integrated MASTER_PROJECT_LOG uses IsOriginInternal only; retire the phantom name.
- **Effort:** done in this pass

## SECTION E: PRODUCTION READINESS

**Overall readiness: 🟢 92%**

**Done:**
- [x] Patch applies clean and reproduces $FF_SRC/dom/quota/ActorsParent.cpp byte-for-byte from vanilla (verified 2026-08-04)
- [x] about:home whitelist present and correctly placed in QuotaManager::IsOriginInternal (:268 constant, :7779 use)
- [x] Console-diagnostic gate correctly swapped to EARLY_BETA_OR_EARLIER (:4297), exactly one occurrence
- [x] Shutdown origin-map clear fully removed; maps still used at :8699/:8724/:8738, no orphaned .Clear()
- [x] Pre-check clean: 0 P0 / 0 P1 / 0 P2 / 0 P3 (rules: .dual-track-rules.py)
- [x] Phantom function name corrected to the real QuotaManager::IsOriginInternal

**To do:**
- [ ] Resolve authorship of the three hunks (project vs upstream drift) and add // GORILLA OVERRIDE: markers if project-authored
- [ ] Merge these rendered docs into MASTER_PROJECT_LOG_06_QUOTA.md and retire the stale generation-1 (2026-07-16) '95%' self-assessment

**Not verified:**
- Whether the three changes are project-authored or upstream mozilla-central drift - no network access to mozilla-central this pass; both readings are plausible and no marker disambiguates them
- OriginOperations.cpp:1681 and :3914 as additional IsOriginInternal callers - listed in POR_DRAFT_2026-08-03, not re-grepped this pass (the :9587 caller in ActorsParent.cpp WAS verified)
- Correctness/optimality against Mozilla's own quota documentation - not performed; this pass verified existence, placement, and byte-exact reproduction, not design-review against upstream intent
- Runtime behaviour of the about:home prompt bypass on a live profile - not exercised; asserted from the in-code comment at :7778 and the predicate's callers

## SECTION F: PHASED PLAN

### Phase 1 — `dom/quota/ActorsParent.cpp (three hunks)`
- **Change:** Establish provenance vs mozilla-central; add GORILLA OVERRIDE markers if project-authored
- **Expected impact:** Closes the only open item; makes the room auditable by name-and-marker

### Phase 0 — `MASTER_PROJECT_LOG_06_QUOTA.md`
- **Change:** Replace merged generation-1 docs with these tree-verified renders; drop the phantom name and the stale 95% score
- **Expected impact:** Single canonical doc, drift-free

### Phase 2 — `QuotaManager::IsOriginInternal callers`
- **Change:** Re-verify OriginOperations.cpp caller lines when next in the tree
- **Expected impact:** Completes the call-graph claim

## POSITIVE OBSERVATIONS

- The patch is byte-exact against the live tree - a faithful record, not an approximation
- The stale shutdown clear-removal is a genuine quiet win: it drops an unnecessary mutex acquisition that only careful review surfaces
- The whitelist reuses the exact StringBeginsWith pattern of the neighbouring internal-origin entries - consistent, low-surprise
- The room's own POR_DRAFT already caught and documented the phantom-function-name error before this audit ran

## VERIFICATION COMMANDS

Run these to check the claims above rather than trusting them.

```bash
grep -n 'kAboutHomeOriginPrefix' $FF_SRC/dom/quota/ActorsParent.cpp   # -> :268 and :7779
grep -n 'IsOriginInternal' $FF_SRC/dom/quota/ActorsParent.cpp $FF_SRC/dom/quota/QuotaManager.h   # -> :7774, :9587, QuotaManager.h:744
grep -rn 'IsFirstOriginQuotaPromptRequired' $FF_SRC/dom/quota/   # -> no matches (phantom)
grep -n 'EARLY_BETA_OR_EARLIER' $FF_SRC/dom/quota/ActorsParent.cpp   # -> exactly :4297
grep -n 'mOriginToStorageOriginMap\|mStorageOriginToOriginMap' $FF_SRC/dom/quota/ActorsParent.cpp   # -> :8699 :8724 :8738, no .Clear()
cat $FF_SRC/config/milestone.txt   # -> 154.0a1 (both NIGHTLY_BUILD and EARLY_BETA_OR_EARLIER defined)
sha256sum patches/new.patches/06.QUOTA/dom_quota_ActorsParent.cpp.patch   # -> 2814f13dbeb54536...
```

## Claim Sources

| Claim | Basis | Evidence |
|-------|-------|----------|
| Patch is 42 lines, sha256(16)=2814f13dbeb54536 | 📄 stated in input | patch, 42 lines, sha256:2814f13dbeb54536 |
| about:home whitelisted via StringBeginsWith in the internal-origin predicate | 📄 stated in input | StringBeginsWith(aOrigin, nsDependentCString(kAboutHomeOriginPrefix)) \|\| |
| Real predicate is QuotaManager::IsOriginInternal at :7774 (decl QuotaManager.h:744); IsFirstOriginQuotaPromptRequired is a phantom | 🤖 model inference | *(none — model judgment)* |
| Gate swapped to EARLY_BETA_OR_EARLIER at :4297 | 📄 stated in input | #if defined(EARLY_BETA_OR_EARLIER) \|\| defined(DEBUG) |
| Milestone 154.0a1 defines both macros, so the swap is a no-op on this build | 🤖 model inference | *(none — model judgment)* |
| 8-line mutex-guarded dual .Clear() removed from shutdown; maps still used at :8699/:8724/:8738 | 📄 stated in input | mOriginToStorageOriginMap.Clear(); |
| Patch reproduces live tree byte-for-byte (verified 2026-08-04) | 🤖 model inference | *(none — model judgment)* |
| No GORILLA OVERRIDE markers on any hunk; authorship unresolved | 🤖 model inference | *(none — model judgment)* |
| Pre-check found 0 P0/P1/P2/P3 | 🤖 model inference | *(none — model judgment)* |


---
**How to verify this document:**
`📄 stated in input` — the model's phrasing of something your source text said.
Find the matching line in the original to verify.
`🤖 model inference` — the model's own judgment or synthesis. Treat as opinion,
not measurement. Re-run on the same input and check whether specific numbers
stay consistent between runs.


---

# === MERGED DOCUMENT: 06-quota_developer.md (verbatim - sha256:6b1dda6206d84626 - merged 2026-08-04) ===
*Track: 06-quota DEVELOPER (audit-grade technical track)*

# Quota Manager Parent Actor: about:home Internal-Origin Whitelist, Console-Diagnostic Channel Gate, and Private-Browsing Origin-Map Cleanup

> Generated 2026-08-04 | Source: `06.QUOTA`

---

## Purpose

This topic patches dom/quota/ActorsParent.cpp, the parent-process implementation of Firefox's storage Quota Manager. The Quota Manager arbitrates how much disk each origin may consume across storage APIs (IndexedDB, Cache API, DOM storage). It runs in the parent process and is trusted: it enforces the per-origin quota policy and mediates the persistent-storage permission flow. The patch makes three independent, small corrections; it does not restructure the module.

## Design Rationale

Each change is a point fix. (1) about:home (moz-safe-about:home) is Firefox's own page, not a web origin, so classifying it as internal keeps it out of the first persistent-storage prompt, matching the treatment already given to chrome://, indexeddb://, and resource://. (2) Widening a diagnostic's build gate from NIGHTLY_BUILD to EARLY_BETA_OR_EARLIER makes the negative-usage warning available on early-Beta milestones as well as Nightly, without shipping it to Release. (3) Deleting the shutdown-time origin-map clear removes work that is redundant at that point and that briefly re-acquired mQuotaMutex. None of the three is a resource optimization in the project's usual sense, and none carries a project provenance marker; see Technical Debt.

## Architecture

- **Pattern:** IPDL parent actor (PBackground). Static predicate helpers plus per-instance shutdown teardown on the QuotaManager singleton.
- **Trust boundary:** QuotaManager::IsOriginInternal classifies an origin string as Firefox-internal. It is consulted by callers that grant internal origins a persistent-storage bypass. The added match uses StringBeginsWith (prefix), not EqualsLiteral (exact) - the same broader match the sibling indexeddb:// and resource:// entries use. moz-safe-about: origins are minted by Firefox, not supplied by remote content, so the prefix match is not a remotely-reachable surface in practice.
- **Attack surface:** None reachable by remote web content through this diff. IsOriginInternal receives already-canonicalised origin strings; the console diagnostic is gated out of Release builds; the deleted block ran only during parent-process temporary-storage shutdown.
- **Dependencies:** `nsIConsoleService (NS_CONSOLESERVICE_CONTRACTID)`, `mozilla::MutexAutoLock / mQuotaMutex`, `StringBeginsWith / nsDependentCString`, `build-time defines NIGHTLY_BUILD, EARLY_BETA_OR_EARLIER, DEBUG from build/moz.configure/init.configure`

## Flags & Configuration

| Name | Type | Default | Effect | Notes |
|------|------|---------|--------|-------|
| `NIGHTLY_BUILD (removed from this gate)` | `compile-define` | `defined when milestone.is_nightly (e.g. 154.0a1)` | Previously gated the negative-usage console warning. Replaced here. | Set in build/moz.configure/init.configure from milestone.is_nightly. |
| `EARLY_BETA_OR_EARLIER (added to this gate)` | `compile-define` | `defined when milestone.is_early_beta_or_earlier (true for 154.0a1)` | Now gates the negative-usage console warning; superset of NIGHTLY_BUILD that also covers early Beta. | Set at build/moz.configure/init.configure:1181-1182. On this tree (milestone 154.0a1, config/milestone.txt) it is defined, as is NIGHTLY_BUILD - so on THIS build the swap is a no-op at runtime; it only changes reachability on early-Beta milestones. |
| `DEBUG` | `compile-define` | `not defined on this build` | Second arm of the gate; would also enable the diagnostic. | The root mozconfig sets --disable-debug, so on the shipped build the gate rests entirely on the channel macro. |

## API Surface

| Symbol | Description | Side Effects |
|--------|-------------|--------------|
| `QuotaManager::IsOriginInternal(const nsACString& aOrigin)` | Returns true if aOrigin is a Firefox-internal origin (chrome://, moz-safe-about:home, indexeddb://, resource://) for which the first persistent-storage prompt is skipped. | None (pure predicate). Declared QuotaManager.h:744; defined ActorsParent.cpp:7774; the in-code comment at :7778 states 'The first prompt is not required for these origins.' Called from ActorsParent.cpp:9587 (verified). POR_DRAFT_2026-08-03 additionally lists OriginOperations.cpp:1681 and :3914 as callers - not re-verified this pass. |

## Kill Switches

### `QuotaManager::IsOriginInternal, ActorsParent.cpp:7779 (constant at :268)`
- **Condition:** compile-time; there is no runtime toggle
- **Effect:** Removing the added StringBeginsWith line makes about:home fall through to the non-internal path and take the first persistent-storage prompt again.
- reversible
- Trivially reversible: delete the one added line plus the constant at :268.

### `console-diagnostic gate, ActorsParent.cpp:4297`
- **Condition:** compile-time
- **Effect:** Reverting to NIGHTLY_BUILD narrows the negative-usage warning back to Nightly-only.
- reversible
- One-token preprocessor change; no runtime effect on a Nightly/alpha milestone build such as 154.0a1.

### `shutdown origin-map clear removal, ActorsParent.cpp (was around old :7484-7491)`
- **Condition:** compile-time (code deleted)
- **Effect:** Restoring the 8-line block reinstates a MutexAutoLock(mQuotaMutex) + two .Clear() calls during temporary-storage shutdown.
- reversible
- Deletion, not a guard. The hunk @@ -7482,14 +7483,6 @@ removes 8 lines (2 comment lines, the brace scope, MutexAutoLock, two .Clear() calls, one blank).

## Dead Code

- **`Deleted shutdown block (old ActorsParent.cpp temporary-storage shutdown path)`** — The block cleared mOriginToStorageOriginMap / mStorageOriginToOriginMap during temporary-storage shutdown. After the patch no .Clear() call exists on either map anywhere in the file; the maps are still populated and queried at ActorsParent.cpp:8699 (TryLookupOrInsertWith), :8724 (WithEntryHandle), and :8738 (MaybeGet). (risk: None observed from the removal. Caveat: 'redundant' here means 'not required at this shutdown point', not 'another .Clear() does the same job' - there is no other .Clear(). If some path depended on these maps being empty after this shutdown, that assumption is now gone; no such dependent path was found in this file.)

## Performance

- **CPU:** One fewer mQuotaMutex acquisition and two fewer hashmap .Clear() calls per temporary-storage shutdown. Not measured; negligible by inspection.
- **MEMORY:** No change. Map capacity is unchanged; only an unconditional clear at shutdown is removed.
- **IO:** No change.
- **NOTES:** No timers, no allocation-path changes.

## Security

- **Remote execution:** None. No code path in this diff executes remote-supplied data.
- **Data handling:** Local only. Governs on-disk quota bookkeeping and an internal-origin classification; nothing is transmitted.
- **Attack surface:** IsOriginInternal takes canonicalised origins; the prefix match is consistent with existing entries. moz-safe-about: is a Firefox-minted scheme, not remotely injectable.
- **Notes:** Whitelisting moz-safe-about:home only skips the FIRST persistent-storage prompt for Firefox's own page; it does not raise the quota ceiling or change eviction policy.

## Error Conditions

| Error | Cause | Remedy |
|-------|-------|--------|
| `"QuotaManager warning: client <leafName> reported negative usage for group <group>, origin <origin>"` | A quota client reports a negative TotalUsage() (Firefox bug 1683863, root cause not yet identified). The value is treated as unset and a warning is logged to the browser console. | Diagnostic only; no action for end users. The message now compiles in under EARLY_BETA_OR_EARLIER || DEBUG (ActorsParent.cpp:4297-4312). |

## Tasks

### Verify the patch reproduces the live tree byte-for-byte

Confirm the single .patch is a faithful record before trusting the docs. Exact sequence (verified 2026-08-04):

```bash
cp vanilla/dom/quota/ActorsParent.cpp tmp/dom/quota/ && cd tmp
patch -p1 < dom_quota_ActorsParent.cpp.patch   # 'checking file dom/quota/ActorsParent.cpp', no fuzz
cmp dom/quota/ActorsParent.cpp "$FF_SRC/dom/quota/ActorsParent.cpp"   # silent == byte-exact
sha256sum dom_quota_ActorsParent.cpp.patch     # 2814f13dbeb54536...  (42 lines)
```

**Prerequisites:**
- A vanilla dom/quota/ActorsParent.cpp baseline
- The patch dom_quota_ActorsParent.cpp.patch

**Step 1:** Stage the vanilla file into a tmp tree, then: patch -p1 < dom_quota_ActorsParent.cpp.patch
  - Expected: Applies clean, no fuzz, no offsets: 'checking file dom/quota/ActorsParent.cpp'.
**Step 2:** cmp the patched file against $FF_SRC/dom/quota/ActorsParent.cpp
  - Expected: Byte-exact match (verified 2026-08-04).

**After this task:** The patch is proven to reproduce the live tree from vanilla; sha256(16)=2814f13dbeb54536, 42 lines.

### Confirm the three edits and their exact locations in the live tree

Validate function name and line placement, not the doc's word.

**Prerequisites:**
- export FF_SRC=the source tree

**Step 1:** grep -n 'kAboutHomeOriginPrefix' $FF_SRC/dom/quota/ActorsParent.cpp
  - Expected: Definition at :268 and use at :7779, inside QuotaManager::IsOriginInternal (:7774).
**Step 2:** grep -n 'IsOriginInternal' $FF_SRC/dom/quota/ActorsParent.cpp $FF_SRC/dom/quota/QuotaManager.h
  - Expected: Definition :7774, caller :9587, declaration QuotaManager.h:744. (The name IsFirstOriginQuotaPromptRequired must NOT appear anywhere - it is a phantom the old docs invented.)
**Step 3:** grep -n 'EARLY_BETA_OR_EARLIER' $FF_SRC/dom/quota/ActorsParent.cpp
  - Expected: Exactly one hit at :4297.
**Step 4:** grep -n 'mOriginToStorageOriginMap\|mStorageOriginToOriginMap' $FF_SRC/dom/quota/ActorsParent.cpp
  - Expected: Only :8699, :8724, :8738 - all insert/lookup, no .Clear().

**After this task:** All three changes confirmed present, correctly located, and named.

## Troubleshooting

**Symptom:** A developer greps for IsFirstOriginQuotaPromptRequired and finds nothing.
**Cause:** That symbol never existed; it was a fabricated name in the pre-2026-08-04 documentation. The real predicate is QuotaManager::IsOriginInternal.
**Remedy:** Use IsOriginInternal (ActorsParent.cpp:7774, QuotaManager.h:744).
**Verify:** grep -rn 'IsFirstOriginQuotaPromptRequired' dom/quota/ returns no matches; grep -n 'IsOriginInternal' returns the real sites.

**Symptom:** You expect the EARLY_BETA_OR_EARLIER swap to enable a diagnostic that was previously off on this build.
**Cause:** On milestone 154.0a1 both NIGHTLY_BUILD and EARLY_BETA_OR_EARLIER are defined, so the diagnostic was already compiled in before the swap.
**Remedy:** Treat the swap as a channel-reach change, not a this-build behaviour change.
**Verify:** cat config/milestone.txt shows 154.0a1; build/moz.configure/init.configure:1181-1182 sets EARLY_BETA_OR_EARLIER from is_early_beta_or_earlier.

## Technical Debt

🟡 **LOW** — No // GORILLA OVERRIDE: provenance marker on any of the three edits, though the project rules file mandates them for project edits to Mozilla source. Either the markers are owed, or these are upstream mozilla-central changes captured as ~3-day drift (none is a resource optimization; all read as ordinary upstream correctness fixes). → Resolve authorship: diff the three hunks against mozilla-central at the pull revision. If project-authored, add provenance markers; if upstream, annotate 06.QUOTA as documenting upstream drift, not customization.
🟡 **LOW** — 06.QUOTA is a single-file catch-all with three unrelated changes. → Acceptable as-is; fold into a broader dom/quota topic only if more quota work lands.
🟡 **LOW** — 'redundant' framing for the deleted clear is only defensible as 'not required at this point', since no other .Clear() exists. → Keep the 'stale-mutex-hold / not required here' framing; do not claim another site clears the maps.

## Impact If Removed

Reverting all three: about:home would take the first persistent-storage prompt on a fresh profile; the negative-usage console warning would narrow to Nightly-only (no effect on a 154.0a1 build); and temporary-storage shutdown would resume a redundant MutexAutoLock(mQuotaMutex) + two .Clear() calls. No functional regression to the quota policy itself; the module continues to operate.

## Claim Sources

| Claim | Basis | Evidence |
|-------|-------|----------|
| Constant kAboutHomeOriginPrefix = "moz-safe-about:home" added at ActorsParent.cpp:268 | 📄 stated in input | const char kAboutHomeOriginPrefix[] = "moz-safe-about:home"; |
| Whitelist added inside QuotaManager::IsOriginInternal (def :7774, use :7779, comment :7778, decl QuotaManager.h:744, caller :9587) | 🤖 model inference | *(none — model judgment)* |
| Phantom name IsFirstOriginQuotaPromptRequired does not exist in dom/quota/ | 🤖 model inference | *(none — model judgment)* |
| Gate swapped NIGHTLY_BUILD -> EARLY_BETA_OR_EARLIER at ActorsParent.cpp:4297 | 📄 stated in input | #if defined(EARLY_BETA_OR_EARLIER) \|\| defined(DEBUG) |
| Milestone 154.0a1 defines both macros; EARLY_BETA_OR_EARLIER set at init.configure:1181-1182; DEBUG off via --disable-debug; swap is a no-op on this build | 🤖 model inference | *(none — model judgment)* |
| 8-line shutdown clear of the two private-browsing maps deleted; maps still used at :8699/:8724/:8738, no .Clear() remains | 📄 stated in input | mOriginToStorageOriginMap.Clear(); |
| The deleted block was commented as dropping the original-origin <-> uuid-based storage-origin mappings for private-browsing origins | 📄 stated in input | Drop the (original-origin <-> uuid-based storage-origin) mappings used |
| The predicate's in-code comment states the first prompt is not required for these origins | 📄 stated in input | The first prompt is not required for these origins. |
| The gated diagnostic obtains the console via NS_CONSOLESERVICE_CONTRACTID | 📄 stated in input | do_GetService(NS_CONSOLESERVICE_CONTRACTID) |
| Patch reproduces the live tree byte-for-byte; sha256(16)=2814f13dbeb54536, 42 lines | 🤖 model inference | *(none — model judgment)* |
| No GORILLA OVERRIDE marker present on any hunk | 🤖 model inference | *(none — model judgment)* |


---
**How to verify this document:**
`📄 stated in input` — the model's phrasing of something your source text said.
Find the matching line in the original to verify.
`🤖 model inference` — the model's own judgment or synthesis. Treat as opinion,
not measurement. Re-run on the same input and check whether specific numbers
stay consistent between runs.

*Auto-generated DITA-structured developer documentation.*


---

# === MERGED DOCUMENT: 06-quota_layman.md (verbatim - sha256:f7fba9ee2e1ae0d2 - merged 2026-08-04) ===
*Track: 06-quota LAYMAN (plain-language track)*

# Firefox's Disk-Space Gatekeeper: Three Small, Boring, Correct Fixes — Plain Language Guide

> Generated 2026-08-04 from `06.QUOTA`

---

## Should You Run This?

Yes. This is a low-risk, local-only, 42-line change to a storage-housekeeping subsystem. It sends nothing, collects nothing, and its worst-case failure is a missing or unexpected permission prompt on an internal page. There is no reason to avoid it.

## Worst Case, Honestly

The realistic worst case is very small. The change that whitelists Firefox's home page uses a 'begins-with' text match, not an exact match, so in theory any origin whose name started with 'moz-safe-about:home' would also skip the first storage prompt. In practice that internal address is generated by Firefox itself and is not something a remote website can hand you, and the two neighbouring rules (indexeddb:// and resource://) already work the same 'begins-with' way. If this change were buggy, the visible symptom would be nothing more than a missing or unexpected storage-permission prompt on an internal page. No data loss, no leak, no charge.

## What Data This Touches

Everything here stays on your own machine. The Quota Manager governs local disk storage only. Not one of these three changes opens a network connection, sends anything to a server, or records anything about you. This is housekeeping for a local subsystem.

## Before You Trust It

You should be able to see that an edit to your browser's storage subsystem is exactly what the documentation says it is, no larger. These commands need only a terminal and the Firefox source folder.

**Step 1:** Run: grep -n 'kAboutHomeOriginPrefix' dom/quota/ActorsParent.cpp
  - Look for: Two lines: the label being defined (around line 268) and it being used in the home-page rule (around line 7779). If you see those two, the home-page change is present.
**Step 2:** Run: grep -n 'EARLY_BETA_OR_EARLIER' dom/quota/ActorsParent.cpp
  - Look for: One line near 4297. That is the build-channel gate on the console warning. Seeing exactly one confirms the swap and confirms it was not sprinkled anywhere else.
**Step 3:** Run: grep -n 'mOriginToStorageOriginMap.Clear\|mStorageOriginToOriginMap.Clear' dom/quota/ActorsParent.cpp
  - Look for: No output. That proves the clear-the-list step really was removed and was not quietly moved somewhere else.

## The Big Picture

Every website you visit can ask to store data on your computer. Firefox has a subsystem, called the Quota Manager, that decides how much disk space each site is allowed to use for things like offline data, caches, and databases. Think of it as the caretaker of a storage building who hands out lockers and keeps track of who has how much room.

This topic changes exactly one file in that subsystem (dom/quota/ActorsParent.cpp) in three small ways. First, it tells the caretaker that Firefox's own home page is part of the building, not an outside tenant, so it does not get treated like a website asking for a locker. Second, it adjusts which internal builds print a specific warning message to the developer console. Third, it deletes a small clean-up step that was no longer needed.

Nothing here is dramatic. None of it sends your data anywhere. It is the kind of change you would never notice, which is exactly what a healthy fix looks like. The whole patch is 42 lines and fits on one screen.

## Key Concepts

| Name | What It Means | Real-World Comparison |
|------|--------------|------------------------|
| `Quota Manager` | The part of Firefox that tracks and limits how much disk space each website may use for stored data. | A building caretaker who assigns storage lockers and stops any one tenant from taking over the basement. |
| `Origin` | A website's identity: its address scheme, host, and port together (for example https://example.com). | A tenant's full name and apartment number on the mailbox. |
| `moz-safe-about:home` | The internal address of Firefox's own home page. It is served by Firefox itself, not downloaded from the internet. | The building's own front lobby, which is not rented to anyone. |
| `Build channel gate` | A compile-time switch that decides whether a chunk of code is included, based on which release track (Nightly, Beta, Release) is being built. | A note in the blueprints that says 'only install this fixture in the show-home units.' |
| `Private-browsing origin map` | An in-memory list Firefox keeps while private browsing, matching a site's real name to a temporary random one so private data stays separated. | A coat-check ticket that pairs your coat with a number for one visit only. |

## How It Works — Step by Step

### Step 1: Firefox's home page is marked as 'one of ours'

A new label, kAboutHomeOriginPrefix = "moz-safe-about:home", is added, and the home page is added to the short list of addresses Firefox treats as internal. When the Quota Manager asks 'is this one of Firefox's own pages?', the home page now answers yes, and so it is not asked to confirm a storage permission on first use. It sits alongside chrome:// (Firefox's own UI), indexeddb://, and resource:// on that list.

### Step 2: A console warning is set to appear on a slightly wider set of builds

One warning message about odd storage-usage numbers used to be compiled in only on Nightly builds. The switch is changed so it is compiled in on 'early Beta or earlier' builds instead. This is only a decision about which internal test builds carry the message. On the actual build this project produces, the message was already being included, so in practice you see no difference. It is a tidy-up, not a new feature.

### Step 3: A no-longer-needed clean-up step is deleted

During shutdown of temporary storage, an eight-line block used to clear two private-browsing lists while holding a lock. That block is removed entirely. The two lists are still created and read in other places, so nothing that depends on them breaks; the removed step was simply not needed here, and it briefly held a lock it did not have to. This is a deletion, not a switch that turns something off.

## Quirky Things Worth Knowing

### The build-channel change does nothing you can see on this build

The switch from NIGHTLY_BUILD to EARLY_BETA_OR_EARLIER only matters on early-Beta builds. This project builds at version 154.0a1, an alpha/nightly milestone where BOTH switches are already on, so the warning message was already included before the change and is still included after it. Do not read this as 'a diagnostic that was off is now on for you' - on this build it was never off.

### 'Removed', not 'disabled'

The third change deletes code outright. After the patch there is no clear-the-list step anywhere for those two private-browsing lists. That is deliberate: the lists are managed where they are used, not wiped here.

### It uses 'begins with', not 'is exactly'

The home-page rule matches any address that STARTS WITH moz-safe-about:home. That is the same style the existing indexeddb:// and resource:// rules use, so it is consistent - but it is broader than an exact match, which is worth knowing when you read it.

### No 'GORILLA OVERRIDE' marker is present

This project normally tags its own edits to Firefox source with a comment. None of these three changes carry that tag. That is a signal these may be ordinary upstream Firefox changes that arrived as the source tree updated, rather than custom project work. This has not been confirmed either way.

## What This Means For You

### Battery, Processor & Memory

Not measured. The only plausible effect is one fewer lock-and-clear during storage shutdown, which is far too small to notice. Memory use is unchanged.

### Speed

No measurable change. Storage shutdown does marginally less work; you will not perceive it.

### Your Privacy

Unchanged. This is local storage housekeeping, not a privacy-policy change. Nothing new is collected, stored, or sent.

### Your Internet

Zero change. No network connection is involved anywhere in this patch.

## The Off Switch

**What it is:** N/A - none. These are three compile-time edits to Firefox's source. There is no runtime preference or toggle to switch them off; changing them back means editing the source and rebuilding.

**Without it:** Without the home-page rule, visiting about:home on a fresh profile could produce a storage-permission prompt for what is really Firefox's own page. Without the deletion, shutdown would keep doing a small, unnecessary locked clean-up. Without the build-gate change, one console warning would be limited to Nightly builds.

**Think of it like:** Not a switch on the wall - more like three worn screws replaced with three fresh ones. You do not toggle them; they are just part of the fixture now.

## How to use this

**Before you start:**
- A build of Gorilla Unleashed Firefox 154 that includes this patch. There is nothing to install or configure separately.

**Step 1:** Open a fresh profile and visit about:home.
  - You should see: No storage-permission prompt appears for the home page.

## If Something Goes Wrong

**You still see a storage-permission prompt on about:home.**
Either your build does not include this patch, or the page you are on is not the moz-safe-about:home origin (for example a customised new-tab page from an add-on).
What to do: Confirm the patch is in your source with step 1 of the verification task. If it is present and rebuilt, the internal home page will not prompt.

**You expected a new console warning to appear and it did not.**
That warning only fires when a storage client reports a negative usage number, which is a rare internal condition (Firefox bug 1683863). It is not something you can trigger on demand.
What to do: Nothing to do. Its absence is normal.

## Why a Developer Would Do This

Developers make these choices to keep the browser's own internal pages out of the permission machinery meant for outside websites, to keep diagnostic messages on the right test builds, and to delete code that no longer earns its place. Small, deliberate corrections like these are how a large codebase stays trustworthy.

## Why It Matters That You Can Read This

You can read every line of this change yourself - all 42 of them. Because it is open, you do not have to take anyone's word that 'it is just housekeeping.' You can run two short search commands (below) and confirm exactly what was added and where. If this code were closed, you would be trusting, unseen, that a stranger's edit to your browser's storage system really is as small and harmless as claimed. Here, you can check.

## Glossary

**Quota Manager** — The Firefox subsystem that tracks and limits how much disk space each website can use for stored data.

**Origin** — A website's identity, made of its scheme, host, and port together.

**moz-safe-about:** — An internal address prefix Firefox uses for its own safe built-in pages, such as the home page.

**Build channel** — Which release track a build belongs to - Nightly, Beta, or Release - which decides what code is compiled in.

**Mutex** — A lock that lets only one part of the program touch a shared piece of data at a time, to prevent conflicts.

## Claim Sources

| Claim | Basis | Evidence |
|-------|-------|----------|
| A new constant kAboutHomeOriginPrefix = "moz-safe-about:home" is added | 📄 stated in input | const char kAboutHomeOriginPrefix[] = "moz-safe-about:home"; |
| about:home is added to the internal-origin whitelist next to chrome://, indexeddb://, resource:// | 📄 stated in input | StringBeginsWith(aOrigin, nsDependentCString(kAboutHomeOriginPrefix)) \|\| |
| The whitelist lives in QuotaManager::IsOriginInternal at ActorsParent.cpp:7774 | 🤖 model inference | *(none — model judgment)* |
| The console-warning gate changed from NIGHTLY_BUILD to EARLY_BETA_OR_EARLIER | 📄 stated in input | #if defined(EARLY_BETA_OR_EARLIER) \|\| defined(DEBUG) |
| The build is milestone 154.0a1, where both NIGHTLY_BUILD and EARLY_BETA_OR_EARLIER are defined, so the gate swap has no observable effect on this build | 🤖 model inference | *(none — model judgment)* |
| An eight-line clear of two private-browsing maps under a mutex is deleted from shutdown | 📄 stated in input | MutexAutoLock lock(mQuotaMutex); |
| After the patch no .Clear() remains on either map; they are still used elsewhere | 🤖 model inference | *(none — model judgment)* |
| No GORILLA OVERRIDE marker is present, suggesting possible upstream drift rather than project work | 🤖 model inference | *(none — model judgment)* |


---
**How to verify this document:**
`📄 stated in input` — the model's phrasing of something your source text said.
Find the matching line in the original to verify.
`🤖 model inference` — the model's own judgment or synthesis. Treat as opinion,
not measurement. Re-run on the same input and check whether specific numbers
stay consistent between runs.

*Human Track. Its Developer Track twin covers the same changes in technical detail. Neither is a simplified copy of the other — they are the same truth in two languages.*

