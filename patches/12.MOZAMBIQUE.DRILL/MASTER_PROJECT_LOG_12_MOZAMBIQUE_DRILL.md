# 12.MOZAMBIQUE.DRILL — Master Project Log

*Canonical single document for this topic. Regenerated 2026-08-04 via `dual-track`
(precheck → code prep → fill → render `--validate`). This supersedes the
2026-08-02 consolidation, whose merged docs carried a 2026-07-17 audit and an
empty PRECHECK. Policy: one master project log per folder — the side documents
below are merged VERBATIM, then their standalone copies and the `.prep.json` /
`.filled.json` build intermediates are deleted. They are recoverable from git
history and reproducible by re-running `dual-track code render` on the
`.filled.json` inputs.*

## Regeneration summary (2026-08-04)

| Track | Merged file | sha256 (16) | Quality gate (≥85) |
|---|---|---|---|
| Layman | `12-mozambique-drill_layman.md` | `4a7f01b794d5afce` | 87/100 — PASS |
| Developer | `12-mozambique-drill_developer.md` | `15a7f7229e166610` | 89/100 — PASS |
| Audit | `12-mozambique-drill_audit.md` | `e364579ee234bb18` | 94/100 — PASS |
| Pre-check | `PRECHECK.md` | `e5cef98179828ad0` | P0–P3: 0 / 0 / 0 / 0 |

**Topic patch files** (both verified applied in the live tree
`the source tree` on 2026-08-04 by grep):

- `toolkit/components/normandy/lib/RecipeRunner.sys.mjs:289` — fallback default
  `21600` → `1893456000  // 60y (Mozambique Drill)`
- `toolkit/components/nimbus/lib/RemoteSettingsExperimentLoader.sys.mjs:256` —
  getter default `21600` → `1893456000  // 60y (Mozambique Drill)`

Both files read the same pref `app.normandy.run_interval_seconds`
(`RUN_INTERVAL_PREF`; RecipeRunner.sys.mjs:41, RSEL:52). The changed number is the
**in-code fallback**, used when the pref is absent.

**Cross-topic layers** (documented here for coherence; the files live elsewhere,
not in this folder):

- `05.PREFS/browser_app_profile_firefox.js` — sets and `locked`s
  `app.normandy.enabled=false`, `app.normandy.api_url=""`, and
  `app.normandy.run_interval_seconds=1893456000` (live firefox.js:2921/2923/2926).
- `NEW_FILES/distribution/policies.json` — runtime `locked` re-lock of the same
  three prefs (enterprise policy engine).

**Doctrine note (authoritative):** Normandy/Nimbus are remote-control /
experiment surfaces; this is a **doctrine kill (soft-gate / neutralise)**, part of
the egress-lockdown family — **not** a removal. The `1893456000`-second
(≈ 60.0 Julian-year) timers are **intentional**; the `// 60y (Mozambique Drill)`
comment is factually correct and must not be documented as a bug. Structural
excision of ExperimentAPI/Normandy was **attempted and abandoned** (README origin
story) because ~145 dependent components crash on delete; `ExperimentAPI.sys.mjs`
remains present in the tree (`toolkit/components/nimbus/`) with no override marker,
so the launching brief's phrasing "ExperimentAPI getters forced false" is **not
observable in this tree** and is recorded under the audit's Not-Verified list.


---
# ═══ MERGED DOCUMENT: PRECHECK.md (verbatim · sha256:e5cef98179828ad0 · merged 2026-08-04) ═══

# Offline Pre-Check: 12-mozambique-drill

*Generated 2026-08-04 07:04:30 by rules only. No model was involved, so everything below is a deterministic finding about the files as they are on disk.*

## Files Scanned

| File | Language | Lines | Code | Complexity | SHA-256 |
|---|---|---|---|---|---|
| `toolkit_components_nimbus_lib_RemoteSettingsExperimentLoader.sys.mjs.patch` | patch | 11 | 10 | 1 | `4256dd5d6de3f1b9` |
| `toolkit_components_normandy_lib_RecipeRunner.sys.mjs.patch` | patch | 11 | 7 | 2 | `f8ce051dfb3f949c` |

## Findings

🔴 P0: 0 · 🟠 P1: 0 · 🟡 P2: 0 · 🟢 P3: 0

*No findings. The rules found nothing wrong; this is not a statement that the code is correct.*


---
# ═══ MERGED DOCUMENT: 12-mozambique-drill_layman.md (verbatim · sha256:4a7f01b794d5afce · merged 2026-08-04) ═══

# Putting Firefox's remote-experiment radios to sleep for 60 years — Plain Language Guide

> Generated 2026-08-04 from `12.MOZAMBIQUE.DRILL`

---

## Should You Run This?

Run it, if your goal is a Firefox that does not participate in Mozilla's remote experiment and remote-config systems. The change only makes the browser do less, and it keeps the dependent machinery intact so nothing breaks. If you actively want to receive Mozilla studies, this is not the build for you.

## Worst Case, Honestly

The realistic worst case for the change itself is close to nothing. A timer set 60 years out simply never fires, so the code that would contact Mozilla never runs. It cannot crash the browser and it cannot leak data, because it does less than before, not more. The only thing you lose is participation in Mozilla's remote experiments, which is the whole point.

## What Data This Touches

These two patches send nothing and store nothing. They change one number in each of two code files. The direct effect is the opposite of a privacy risk: they stop a background job that used to reach out to Mozilla's servers on a schedule. No personal data is read, written, or transmitted by the change itself.

## Before You Trust It

Before you trust that these systems are neutralised, confirm the number in the code with your own eyes. You do not need to understand the code, only to find the value.

**Step 1:** Open a terminal in the Firefox source tree and run: grep -n 1893456000 toolkit/components/normandy/lib/RecipeRunner.sys.mjs toolkit/components/nimbus/lib/RemoteSettingsExperimentLoader.sys.mjs
  - Look for: You should see one match in each file, each ending with the comment 60y (Mozambique Drill). Two matches total means both timers are dilated.
**Step 2:** In the running browser, open about:studies from the address bar.
  - Look for: The list of active studies should be empty. An empty list means no experiments are running on your browser.
**Step 3:** Open about:config, search for app.normandy.run_interval_seconds, and try to change it.
  - Look for: The value should read 1893456000 and the edit should be refused, because a policy locks it. A refused edit confirms the lock is active.

## The Big Picture

Firefox ships with two systems, Normandy and Nimbus, that let Mozilla reach into your browser from a distance. They can quietly turn features on or off, run A/B experiments on you, and measure what you do. You never asked for this and it is on by default.

Each system has a background timer. Every so often it wakes up, phones a Mozilla server, and asks: any new instructions for me? Stock Firefox sets that timer to fire every 6 hours. This patch topic changes the built-in default for that timer to fire once every 60 years instead. The radios are still bolted to the wall and still powered on, but they will not make their next call until the year 2085.

Why leave them bolted to the wall at all? Because pulling them out breaks the browser. When this project tried to delete the systems outright, roughly 145 other parts of Firefox that expect them to exist crashed on startup. So the fix keeps the machinery physically present and structurally intact, and simply makes sure it never actually does anything. Structurally perfect, biologically dead.

## Key Concepts

| Name | What It Means | Real-World Comparison |
|------|--------------|------------------------|
| `Normandy` | Firefox's older remote-control and experiment system. It fetches 'recipes' (small bundles of instructions) from a Mozilla server and runs them in your browser. | A supervisor with a two-way radio, listening for orders from head office. |
| `Nimbus` | Normandy's newer replacement. Same job, delivered through Firefox's Remote Settings service. | The same supervisor with a shinier radio. |
| `RecipeRunner` | The Normandy part that runs on a timer and calls out to check for new recipes. | The scheduled 'anything for me?' phone call. |
| `RemoteSettingsExperimentLoader` | The Nimbus equivalent. It runs on a timer and pulls new experiment definitions from Remote Settings. | The Nimbus version of the same phone call. |
| `The 60-year timer (1893456000 seconds)` | The new built-in default gap between calls. 1,893,456,000 seconds is exactly 60 years. | Setting an alarm clock so far in the future that it will never ring in the life of the machine. |

## How It Works — Step by Step

### Step 1: Find the two alarm clocks

Two files each hold a background timer. Normandy's timer lives in RecipeRunner.sys.mjs. Nimbus's timer lives in RemoteSettingsExperimentLoader.sys.mjs. Both read the same setting, called app.normandy.run_interval_seconds, to decide how long to wait between calls.

### Step 2: Read the fallback number

Each timer asks Firefox for that setting, and passes along a fallback number to use if the setting is somehow missing. In stock Firefox that fallback is 21600, which is 6 hours in seconds. This is the number both patches change.

### Step 3: Swap 6 hours for 60 years

Each patch replaces 21600 with 1893456000, and labels it in the code with the comment '60y (Mozambique Drill)'. 1,893,456,000 seconds is exactly 60 years (60 x 365.25 x 24 x 3600). So if either timer ever falls back to its built-in default, that default now means 'wait 60 years', not 'wait 6 hours'.

### Step 4: The timer still registers, it just never rings

The timer object is still created and handed to Firefox's scheduler, exactly as before. Nothing is deleted. The scheduler simply will not fire it for 60 years. The roughly 145 other parts of Firefox that expect these objects to exist still find them, so the browser starts normally.

### Step 5: Belt and braces from the pref layer

In practice the fallback is a second line of defence. A separate topic (05.PREFS) already sets app.normandy.run_interval_seconds to the same 60-year value and locks it, and a distribution policies.json file locks it again at runtime. So the value in these two files is the safety net for the case where the setting is ever stripped or reset. Even then, the built-in default is still 60 years.

## Quirky Things Worth Knowing

### The systems are not deleted, and that is deliberate

It would feel cleaner to just remove Normandy and Nimbus. That was tried and it failed: about 145 other components crash on startup without them. So the machinery is kept intact and made inert instead. If you go looking, you will still find all the code present.

### The 60-year comment is correct, not a joke

The inline note '// 60y (Mozambique Drill)' is factually accurate. 1893456000 really is 60 years in seconds. It is not a placeholder or a bug to be cleaned up.

### 60 years was chosen to still fit in a 32-bit integer

A signed 32-bit number tops out around 68 years in seconds. 60 years fits comfortably under that ceiling, so no computer or runtime rejects the value. Picking, say, 500 years could overflow and behave unpredictably.

### This is a pattern, not a one-off

The same 'keep the corpse standing so nothing crashes, but make sure it never acts' approach is used for other systems the project cannot safely delete. It is a repeatable technique for tangled code.

## What This Means For You

### Battery, Processor & Memory

Not measured. In principle one recurring background job that used to run roughly every 6 hours no longer runs, which removes a small, repeated wake-up. The timer objects still exist in memory, so the memory saving is negligible. No before/after numbers were captured.

### Speed

Not measured. Any change is expected to be small: one fewer scheduled background task waking up and reaching the network. No startup or steady-state timing was recorded.

### Your Privacy

This closes the 'targeting' channel: the route by which Mozilla could reach into your specific browser to switch features or run experiments on you. It pairs with the telemetry work (topic 13), which closes the 'reporting' channel that sends data out.

### Your Internet

One fewer repeating background connection to Mozilla infrastructure. Stock Firefox would poll roughly every 6 hours; with the change it does not poll on any human timescale.

## The Off Switch

**What it is:** The off switch is the timer interval itself. In RecipeRunner.sys.mjs (line 289) and RemoteSettingsExperimentLoader.sys.mjs (line 256), the built-in default wait is set to 1893456000 seconds. That number is the switch: it decides how long the system sleeps before its next network call.

**Without it:** Without it, each timer falls back to 6 hours (21600 seconds), so Firefox would call out to Mozilla's experiment servers roughly four times a day to fetch and run whatever recipes or experiments are waiting.

**Think of it like:** It is like resetting the delay on an automatic sprinkler from 'every 6 hours' to 'once every 60 years'. The sprinkler is still installed and still plumbed in, it simply never turns on again in any timeframe that matters.

## Use this build with remote experiments already asleep

**Before you start:**
- A Firefox 154 build made from this patched source tree
- No action on your part: the change is baked into the build

**Step 1:** Install and launch the build as normal.
  - You should see: Firefox starts normally. The roughly 145 dependent components find the Normandy and Nimbus objects they expect, so nothing crashes.
**Step 2:** Use the browser as you would any other day.
  - You should see: You will not see studies appear and you will not receive pushed experiments, because the timers that fetch them are set 60 years out.

## If Something Goes Wrong

**You expected these systems to be gone, but you can still find Normandy and Nimbus code in the tree.**
They are intentionally kept in place. Deleting them crashes about 145 dependent components on startup. The fix disables their behaviour, it does not remove their code.
What to do: This is expected. Confirm the neutralisation by checking the timer value (1893456000) rather than by looking for missing files.

**about:studies briefly shows something, or you worry the timer could still fire.**
The master switch (app.normandy.enabled=false) and the empty endpoint from topic 05 already stop the pipeline; the 60-year timer is the backstop.
What to do: Confirm app.normandy.enabled is false and app.normandy.api_url is empty in about:config. With those set, no fetch happens regardless of the timer.

## Why a Developer Would Do This

A developer chose to dilate a timer rather than delete the code because deletion was tried and caused a cascade of startup crashes across roughly 145 dependent components. Changing one number in each of two files is a small, reversible, auditable edit that reaches the same practical outcome: the remote-control channel never opens.

## Why It Matters That You Can Read This

You do not have to take any of this on faith. Every claim here is one line you can grep for: the number 1893456000 in two named files, the locked preference in topic 05, and the locked entry in policies.json. In a closed-source browser, 'we turned off remote experiments' would be a marketing promise you could not check. Here it is arithmetic in a handful of files you can open yourself. If you could not read it, you would be trusting the vendor's word that the radios are off, with no way to confirm they are not still calling home.

## Glossary

**Normandy** — Firefox's older system for fetching and running remote 'recipes' from a Mozilla server.

**Nimbus** — Normandy's newer replacement, which delivers experiments through Firefox's Remote Settings service.

**Recipe** — A small bundle of instructions Mozilla can send for your browser to run.

**Timer interval** — How long a background job waits between runs. Here it is stretched from 6 hours to 60 years.

**1893456000** — Sixty years measured in seconds, the new wait between timer firings.

**policies.json** — A Firefox enterprise file that locks preferences so they cannot be changed at runtime, even from about:config.

## Claim Sources

| Claim | Basis | Evidence |
|-------|-------|----------|
| Both timers' fallback default changed from 21600 to 1893456000 | 📄 stated in input | -      21600, +      1893456000, // 60y (Mozambique Drill) |
| The change is labelled '60y (Mozambique Drill)' in the code | 📄 stated in input | 1893456000, // 60y (Mozambique Drill) |
| Both files read the same pref app.normandy.run_interval_seconds | 📄 stated in input | getIntPref(RUN_INTERVAL_PREF, 1893456000) |
| Stock default is 6 hours | 📄 stated in input | getIntPref(RUN_INTERVAL_PREF, 21600); // 6h |
| RecipeRunner change lives at line 289 of the live tree | 🤖 model inference | firefox-main RecipeRunner.sys.mjs:289 grep-confirmed 1893456000 |
| RSEL change lives at line 256 of the live tree | 🤖 model inference | firefox-main RemoteSettingsExperimentLoader.sys.mjs:256 grep-confirmed 1893456000 |
| 1893456000 seconds equals 60 years (60*365.25*24*3600) | 🤖 model inference | arithmetic: 365.25*24*3600=31557600; *60=1893456000 |
| Topic 05 sets and locks the same pref plus enabled=false and empty api_url | 🤖 model inference | firefox.js:2921/2923/2926 pref(...,locked) Chest Shot 1/2/Headshot |
| A distribution policies.json locks the three prefs at runtime | 🤖 model inference | NEW_FILES/distribution/policies.json app.normandy.* Status locked |
| Deleting the systems crashed ~145 dependent components | 🤖 model inference | README.md: 'These systems have 145+ dependencies'; not independently reproduced here |
| The systems are kept in place, not removed | 🤖 model inference | ExperimentAPI.sys.mjs present in tree with no override marker; timer objects still registered |
| No performance numbers were captured | 🤖 model inference | no benchmark artifact supplied with the topic |


---
**How to verify this document:**
`📄 stated in input` — the model's phrasing of something your source text said.
Find the matching line in the original to verify.
`🤖 model inference` — the model's own judgment or synthesis. Treat as opinion,
not measurement. Re-run on the same input and check whether specific numbers
stay consistent between runs.

*Human Track. Its Developer Track twin covers the same changes in technical detail. Neither is a simplified copy of the other — they are the same truth in two languages.*


---
# ═══ MERGED DOCUMENT: 12-mozambique-drill_developer.md (verbatim · sha256:15a7f7229e166610 · merged 2026-08-04) ═══

# Mozambique Drill — 60-year timer dilation for Normandy RecipeRunner and Nimbus RemoteSettingsExperimentLoader

> Generated 2026-08-04 | Source: `12.MOZAMBIQUE.DRILL`

---

## Purpose

This topic neutralises the two poll timers that drive Firefox's remote-experiment and remote-config channels: Normandy's RecipeRunner and Nimbus's RemoteSettingsExperimentLoader. Each timer reads app.normandy.run_interval_seconds to decide how often to fetch and apply remote recipes/experiments. Both patches change the in-code fallback default for that pref from 21600 seconds (6 hours) to 1893456000 seconds (60 years). The timers still register with Firefox's nsIUpdateTimerManager, so all dependent objects keep their shape; they simply never fire within the machine's lifetime. This is a doctrine kill (soft-gate/neutralise), not a removal.

## Design Rationale

Structural excision was attempted first (hollowing ExperimentAPI, deleting Normandy) and abandoned because roughly 145 components across the tree depend on these modules and their data shapes; returning null cascaded into TypeError/ModuleNotFoundError at boot. Dilating the fallback interval is a two-line, reversible edit that preserves every module, import, and object while guaranteeing the network callout never happens. The value 1893456000 is chosen to stay under the signed 32-bit ceiling (2147483647 ≈ 68 years) so no runtime rejects it.

## Architecture

- **Pattern:** Shape-preserving neutralisation via timer-interval dilation. Both modules use Firefox's nsIUpdateTimerManager registration pattern; the patch only alters the numeric default fed into that registration.
- **Trust boundary:** Closes the inbound targeting boundary: Mozilla-controlled Normandy/Nimbus endpoints can no longer schedule work inside this browser, because the scheduler that would invoke the fetch is set 60 years out. It does not by itself alter the outbound reporting boundary (that is topic 13's telemetry work).
- **Attack surface:** Removes a supply-chain-style vector: a compromised or coerced RemoteSettings/Normandy endpoint pushing a malicious 'experiment' or 'recipe'. With the fetch timer dilated (and, from topic 05, the master switch off and endpoint emptied), that push has no scheduled retrieval path.
- **Dependencies:** `toolkit/components/normandy/lib/RecipeRunner.sys.mjs`, `toolkit/components/nimbus/lib/RemoteSettingsExperimentLoader.sys.mjs`, `app.normandy.run_interval_seconds (RUN_INTERVAL_PREF, shared by both files)`, `Services.prefs / XPCOMUtils.defineLazyPreferenceGetter`, `lazy.timerManager (nsIUpdateTimerManager)`, `Cross-topic: 05.PREFS firefox.js locked prefs; NEW_FILES/distribution/policies.json runtime lock`

## Flags & Configuration

| Name | Type | Default | Effect | Notes |
|------|------|---------|--------|-------|
| `app.normandy.run_interval_seconds` | `int` | `1893456000 (in-code fallback; was 21600)` | Wall-clock seconds between Normandy/Nimbus poll firings. Both modules read this single pref. | Shared by RecipeRunner.sys.mjs:41 and RemoteSettingsExperimentLoader.sys.mjs:52 as RUN_INTERVAL_PREF. Topic 05 sets the pref itself to 1893456000 and locks it, so the in-code fallback is the backstop for a stripped/reset pref. |

## API Surface

| Symbol | Description | Side Effects |
|--------|-------------|--------------|
| `RecipeRunner.updateRunInterval()` | Registers the Normandy poll timer using the (now 60-year) fallback interval. | Calls lazy.timerManager.registerTimer; no network at registration time. |
| `RemoteSettingsExperimentLoader.intervalInSeconds` | Supplies the Nimbus poll interval; change callback re-runs setTimer(). | Getter resolution triggers setTimer() via the defineLazyPreferenceGetter callback. |
| `RemoteSettingsExperimentLoader.setTimer()` | Registers or unregisters the Nimbus update timer based on _enabled and intervalInSeconds. | registerTimer with updateRecipes('timer') callback; unregisters if intervalInSeconds===0. |

## Kill Switches

### `RecipeRunner.sys.mjs:289 (updateRunInterval / registerTimer path)`
- **Condition:** Every scheduler (re)registration when the pref is absent
- **Effect:** runInterval fallback = 1893456000 s; registerTimer(TIMER_NAME, () => this.run(), runInterval) schedules the next Normandy run 60 years out.
- reversible
- Reverse by restoring 21600 and rebuilding. Comment '// 60y (Mozambique Drill)' is factually correct and intentional; do not treat as debt to strip.

### `RemoteSettingsExperimentLoader.sys.mjs:256 (defineLazyPreferenceGetter for intervalInSeconds)`
- **Condition:** Lazy getter resolution when the pref is absent
- **Effect:** intervalInSeconds fallback = 1893456000 s; setTimer() (line ~868) feeds it to registerTimer(TIMER_NAME, () => this.updateRecipes('timer'), this.intervalInSeconds).
- reversible
- setTimer() has an intervalInSeconds===0 branch that unregisters the timer (test hook); 1893456000 does not hit that branch, so the timer registers but never fires within any human timescale.

## Dead Code

- **`N/A — none introduced by these two patches`** — The timers are not dead code: they still register and hold their objects; only the firing interval is dilated. The abandoned structural-excision path is not present in these files. (risk: N/A)

## Performance

- **CPU:** Not measured. One recurring background poll (nominally every 6 hours) no longer fires; the per-fire cost avoided was not benchmarked.
- **MEMORY:** Not measured. Negligible by inspection: the timer objects and their stacks still exist, so no allocation is freed by the change.
- **IO:** Not measured by number. One fewer recurring outbound fetch to Mozilla Normandy/RemoteSettings endpoints on the poll cadence.
- **NOTES:** No before/after profiling artifact was supplied with this topic. Do not state a figure; the effect is directional, not quantified.

## Security

- **Remote execution:** Reduces exposure to remotely delivered 'recipes'/experiments: the retrieval timer that would fetch them is dilated to 60 years, and topic 05 additionally sets app.normandy.enabled=false with an emptied api_url.
- **Data handling:** These two patches read one pref and touch no user data; they transmit nothing. The net effect is fewer outbound connections.
- **Attack surface:** Closes a scheduled inbound path a compromised RemoteSettings/Normandy endpoint could use.
- **Notes:** This is defence in depth: fallback default (these files) + locked pref (topic 05 firefox.js) + runtime lock (policies.json). Any single layer being bypassed still leaves the other two.

## Error Conditions

| Error | Cause | Remedy |
|-------|-------|--------|
| `TypeError: ExperimentAPI is undefined (and similar ModuleNotFoundError) at boot` | Observed by the project when Normandy/Nimbus were structurally deleted rather than neutralised; ~145 dependents lose their expected objects/shapes. | Do not delete the modules. This topic's approach (interval dilation with objects preserved) avoids the cascade by design. |

## Tasks

### Verify both timer dilations are present in the tree

Confirm the patches applied and the values match before shipping. Each site changes exactly one line, from the 6-hour default to the 60-year default:

```diff
-    const runInterval = Services.prefs.getIntPref(RUN_INTERVAL_PREF, 21600); // 6h
+    const runInterval = Services.prefs.getIntPref(RUN_INTERVAL_PREF, 1893456000); // 60y (Mozambique Drill)
```


**Prerequisites:**
- FF_SRC pointed at the patched tree (the source tree)

**Step 1:** grep -n 1893456000 $FF_SRC/toolkit/components/normandy/lib/RecipeRunner.sys.mjs $FF_SRC/toolkit/components/nimbus/lib/RemoteSettingsExperimentLoader.sys.mjs
  - Expected: One match per file: RecipeRunner.sys.mjs:289 and RemoteSettingsExperimentLoader.sys.mjs:256, each with '// 60y (Mozambique Drill)'.
**Step 2:** grep -n 'RUN_INTERVAL_PREF =' on both files
  - Expected: Both define RUN_INTERVAL_PREF = "app.normandy.run_interval_seconds" (RecipeRunner:41, RSEL:52), confirming the shared pref.

**After this task:** Both fallback intervals are 1893456000; the shared pref name is confirmed.

### Confirm the pref-lock and policy layers back the fallback

The in-code fallback is a backstop; the primary control is the locked pref plus policies.json. Verify both.

**Prerequisites:**
- Access to 05.PREFS/browser_app_profile_firefox.js.patch and NEW_FILES/distribution/policies.json

**Step 1:** grep -n 'app.normandy' $FF_SRC/browser/app/profile/firefox.js
  - Expected: enabled=false locked (line ~2923), api_url="" locked (~2921), run_interval_seconds=1893456000 locked (~2926).
**Step 2:** jq '.policies.Preferences' NEW_FILES/distribution/policies.json
  - Expected: app.normandy.enabled, api_url, and run_interval_seconds each present with Status: locked.

**After this task:** All three layers (fallback, locked pref, runtime policy lock) are confirmed consistent at 1893456000 / false / empty.

### Runtime smoke test

Confirm neutralisation is live and the browser still boots.

**Prerequisites:**
- A build from the patched tree

**Step 1:** Launch the build; open about:studies.
  - Expected: Empty studies list; browser boots without ExperimentAPI-related errors.
**Step 2:** In about:config, attempt to set app.normandy.run_interval_seconds; check about:policies.
  - Expected: Edit rejected (locked); about:policies shows the Normandy prefs hard-locked.

**After this task:** No experiments run; the pref cannot be flipped at runtime; startup is clean.

## Troubleshooting

**Symptom:** Nimbus timer appears to unregister entirely rather than sleep.
**Cause:** setTimer() unregisters when intervalInSeconds===0 (a test hook). That is not this value.
**Remedy:** Confirm intervalInSeconds resolves to 1893456000, not 0. A dilated timer registers and holds; it does not unregister.
**Verify:** grep the getter default (RSEL:256) and inspect setTimer() at ~868.

**Symptom:** Someone flags 1893456000 as a magic number to remove.
**Cause:** The value has an inline comment but is not a named constant.
**Remedy:** Keep the value and comment; the 60y comment is correct and intentional. Optionally extract to a named constant, but do not 'clean up' the comment.
**Verify:** Confirm the comment reads '// 60y (Mozambique Drill)' at both sites.

**Symptom:** Boot cascade of TypeError: ExperimentAPI is undefined.
**Cause:** That failure belongs to the abandoned structural-excision approach, not to this topic.
**Remedy:** Ensure the modules are present and only the interval is dilated; do not delete Normandy/Nimbus code.
**Verify:** ExperimentAPI.sys.mjs exists in toolkit/components/nimbus/ and boots normally.

## Technical Debt

🟡 **LOW** — 1893456000 carries an inline '// 60y (Mozambique Drill)' comment at both sites but is not extracted to a named constant. → Optionally define a shared named constant (e.g. SIXTY_YEARS_IN_SECONDS = 1893456000) for readability. The correct inline comment already prevents misreading it as a bug; do not remove the comment.
🟡 **LOW** — The policy-lock layer relies on the enterprise policy engine (policies.json) being present and MOZ_HAS_ENTERPRISE_POLICIES defined. → Add a build-time or startup assertion that the enterprise policy engine is active, so a silent degradation of the runtime lock is detected. The in-code fallback still holds if it degrades.

## Impact If Removed

Reverting either fallback to 21600 restores a 6-hour poll cadence for that channel. On its own this would not re-open the channel while topic 05 keeps app.normandy.enabled=false and api_url empty and locked; both layers would have to be reverted for Mozilla to regain scheduled Normandy/Nimbus remote-control of this browser. Removing the modules entirely (rather than reverting the interval) reintroduces the ~145-dependent boot cascade the project already documented.

## Claim Sources

| Claim | Basis | Evidence |
|-------|-------|----------|
| Fallback default changed 21600 -> 1893456000 in both files | 📄 stated in input | -      21600, +      1893456000, // 60y (Mozambique Drill) |
| Both files read RUN_INTERVAL_PREF via getIntPref/defineLazyPreferenceGetter | 📄 stated in input | getIntPref(RUN_INTERVAL_PREF, 1893456000) |
| Stock Normandy fallback was 21600 s (6h) | 📄 stated in input | getIntPref(RUN_INTERVAL_PREF, 21600); // 6h |
| Nimbus getter 'intervalInSeconds' default set to 1893456000 | 📄 stated in input | "intervalInSeconds", RUN_INTERVAL_PREF, ... 1893456000, // 60y (Mozambique Drill) |
| RecipeRunner registers the timer via lazy.timerManager.registerTimer | 📄 stated in input | lazy.timerManager.registerTimer(TIMER_NAME, () => this.run(), runInterval); |
| Change sits at RecipeRunner.sys.mjs:289 and RSEL:256 in the live tree | 🤖 model inference | grep on firefox-main: RecipeRunner.sys.mjs:289, RemoteSettingsExperimentLoader.sys.mjs:256 |
| RUN_INTERVAL_PREF = app.normandy.run_interval_seconds in both files | 🤖 model inference | RecipeRunner.sys.mjs:41 and RemoteSettingsExperimentLoader.sys.mjs:52 |
| RSEL setTimer() unregisters when intervalInSeconds===0, else registers with updateRecipes('timer') | 🤖 model inference | RemoteSettingsExperimentLoader.sys.mjs:868-885 |
| 1893456000 s = 60 years and fits under signed 32-bit max (~68y) | 🤖 model inference | 60*365.25*24*3600=1893456000 < 2147483647 |
| Topic 05 sets enabled=false, api_url empty, run_interval_seconds=1893456000, all locked | 🤖 model inference | firefox.js:2921/2923/2926 pref(...,locked); 05.PREFS patch lines 773/776/780 |
| policies.json locks the three prefs at runtime | 🤖 model inference | NEW_FILES/distribution/policies.json Preferences block, Status: locked |
| Structural excision was attempted and abandoned due to ~145 dependents | 🤖 model inference | README.md '145+ dependencies'; ExperimentAPI.sys.mjs still present with no override marker |
| No performance figures were captured | 🤖 model inference | no benchmark artifact accompanies the topic |


---
**How to verify this document:**
`📄 stated in input` — the model's phrasing of something your source text said.
Find the matching line in the original to verify.
`🤖 model inference` — the model's own judgment or synthesis. Treat as opinion,
not measurement. Re-run on the same input and check whether specific numbers
stay consistent between runs.

*Auto-generated DITA-structured developer documentation.*


---
# ═══ MERGED DOCUMENT: 12-mozambique-drill_audit.md (verbatim · sha256:e364579ee234bb18 · merged 2026-08-04) ═══

# IBM-Style Audit Report: 12.MOZAMBIQUE.DRILL

## SECTION A: DOCUMENT CONTROL

| Attribute | Value |
|---|---|
| **Target** | 12.MOZAMBIQUE.DRILL |
| **Files scanned** | see payload |
| **Date / time** | 2026-08-04 07:11:07 |
| **Audit status** | PASS |

## SECTION B: EXECUTIVE SUMMARY (Plain Language)

This topic puts Firefox's two remote-experiment radios to sleep for 60 years instead of ripping them out of the wall. Each of two code files had a background timer that woke every 6 hours to phone Mozilla for new instructions; both are changed to wake once every 60 years. The machinery is left physically in place because removing it crashes about 145 other parts of the browser on startup. Both changes are present and correct in the source tree, and two further layers (a locked preference and an enterprise policy file) hold the same values. It is safe to ship. What was not independently re-tested here is the live browser behaviour and the exact 145-dependent crash claim, which comes from the project's own notes rather than a reproduction in this audit.

## SECTION C: TECHNICAL SUMMARY (Developer)

Two-line-per-file neutralisation: the in-code fallback default for app.normandy.run_interval_seconds is changed from 21600 s to 1893456000 s (60 years, under the signed 32-bit ceiling) in RecipeRunner.sys.mjs:289 and RemoteSettingsExperimentLoader.sys.mjs:256. Both modules read the same RUN_INTERVAL_PREF and still register their timers via nsIUpdateTimerManager, so all dependent object shapes are preserved and boot does not cascade. This is a doctrine kill (soft-gate/neutralise), not a removal. Defence in depth: topic 05 sets enabled=false, api_url empty, and run_interval_seconds=1893456000, all locked; policies.json re-locks the three prefs at runtime. Both diffs were verified against the patched tree by grep. Precheck rules returned 0 findings. Deductions are for behaviour not exercised in this audit and for the 145-dependency figure being documentary rather than reproduced.

## SECTION D: DETECTED DEFECTS

*No defects found by rules or review. This is not a statement that the material is correct — only that nothing was detected.*

## SECTION E: PRODUCTION READINESS

**Overall readiness: 🟢 90%**

**Done:**
- [x] RecipeRunner.sys.mjs:289 fallback = 1893456000 with '// 60y (Mozambique Drill)' — grep-confirmed in the live tree
- [x] RemoteSettingsExperimentLoader.sys.mjs:256 fallback = 1893456000 with the same comment — grep-confirmed
- [x] Both files confirmed to read the shared pref app.normandy.run_interval_seconds (RecipeRunner:41, RSEL:52)
- [x] Cross-layer: topic 05 firefox.js sets enabled=false, api_url='', run_interval_seconds=1893456000, all locked (firefox.js:2921/2923/2926)
- [x] Cross-layer: NEW_FILES/distribution/policies.json locks the three prefs at runtime (Status: locked)
- [x] Object shapes preserved: timers still register; ExperimentAPI.sys.mjs present in tree, so no structural-excision cascade
- [x] Precheck rules: 0 findings (P0-P3 all 0)

**To do:**
- [ ] P3: extract 1893456000 to a shared named constant (comment already prevents misreading it as a bug)
- [ ] P3: add a startup/build assertion that the enterprise policy engine (MOZ_HAS_ENTERPRISE_POLICIES) is active, to catch silent degradation of the runtime lock
- [ ] P2 (optional): add an integration test asserting no outbound request to Normandy/RemoteSettings endpoints on boot

**Not verified:**
- Live runtime behaviour (about:studies empty; about:config edit rejected; clean boot) was reasoned from code, not executed in this audit
- The '~145 dependent components crash on delete' figure is from the project's README/history, not independently reproduced here
- Performance impact (CPU/memory/IO, startup timing) was not measured; no benchmark artifact was supplied — recorded as 'not measured', not estimated
- The launching brief's phrasing 'ExperimentAPI getters forced false with init shape preserved' is NOT observable in this tree: ExperimentAPI.sys.mjs exists at toolkit/components/nimbus/ExperimentAPI.sys.mjs with no override marker. The actual kill in this topic is timer dilation plus pref/policy locking, and the structural-excision approach is documented as attempted and abandoned

## SECTION F: PHASED PLAN

### Phase 1 — `toolkit/components/normandy + nimbus`
- **Change:** Add an integration test: on boot, assert no network request to Mozilla Normandy/RemoteSettings endpoints.
- **Expected impact:** Regression protection against a future revert of the interval or the locked prefs.

### Phase 2 — `both .sys.mjs sites`
- **Change:** Introduce a shared named constant for 1893456000 with a one-line doc comment.
- **Expected impact:** Readability; removes the 'magic number' objection without altering behaviour.

### Phase 2 — `enterprise policy engine wiring`
- **Change:** Startup assertion that policies.json prefs are actually locked.
- **Expected impact:** Detects silent degradation of the runtime-lock layer early.

## POSITIVE OBSERVATIONS

- Three independent layers (in-code fallback, locked build-time pref, runtime policy lock) all agree on the same values — a single bypass leaves the other two intact
- Shape-preserving approach is honest and documented: the delete-first attempt and its boot cascade are recorded rather than hidden
- The 1893456000 value is bounded deliberately to fit signed 32-bit, avoiding overflow-driven surprises
- The inline '// 60y (Mozambique Drill)' comment is factually correct, so the value cannot be misread as an accidental magic number
- Both diffs were verified against the actual patched tree, not just the doc — grep confirmed line and value at both sites
- Coherent with the project's egress-lockdown family (topics 05, 09, 13): same neutralise-don't-remove doctrine

## VERIFICATION COMMANDS

Run these to check the claims above rather than trusting them.

```bash
grep -n 1893456000 $FF_SRC/toolkit/components/normandy/lib/RecipeRunner.sys.mjs $FF_SRC/toolkit/components/nimbus/lib/RemoteSettingsExperimentLoader.sys.mjs
grep -n 'RUN_INTERVAL_PREF =' $FF_SRC/toolkit/components/normandy/lib/RecipeRunner.sys.mjs $FF_SRC/toolkit/components/nimbus/lib/RemoteSettingsExperimentLoader.sys.mjs
grep -n 'app.normandy' $FF_SRC/browser/app/profile/firefox.js
jq '.policies.Preferences | keys' patches/new.patches/12.MOZAMBIQUE.DRILL/NEW_FILES/distribution/policies.json
# runtime: about:studies (empty), about:policies (Normandy prefs locked), about:config set app.normandy.run_interval_seconds (rejected)
```

## Claim Sources

| Claim | Basis | Evidence |
|-------|-------|----------|
| Both fallback intervals changed 21600 -> 1893456000 | 📄 stated in input | -      21600, +      1893456000, // 60y (Mozambique Drill) |
| Both files use the shared RUN_INTERVAL_PREF | 📄 stated in input | getIntPref(RUN_INTERVAL_PREF, 1893456000) |
| Live-tree lines are RecipeRunner:289 and RSEL:256 | 🤖 model inference | grep on firefox-main confirmed both |
| Shared pref name is app.normandy.run_interval_seconds | 🤖 model inference | RecipeRunner.sys.mjs:41; RemoteSettingsExperimentLoader.sys.mjs:52 |
| 1893456000 s = 60y and < signed 32-bit max | 🤖 model inference | 60*365.25*24*3600=1893456000 < 2147483647 |
| Topic 05 locks enabled/api_url/run_interval_seconds | 🤖 model inference | firefox.js:2921/2923/2926 pref(...,locked) |
| policies.json locks the three prefs at runtime | 🤖 model inference | NEW_FILES/distribution/policies.json Status: locked |
| Precheck returned 0 findings | 📄 stated in input | PRECHECK.md: P0:0 P1:0 P2:0 P3:0 |
| ExperimentAPI structural excision was abandoned; module still present | 🤖 model inference | ExperimentAPI.sys.mjs present at toolkit/components/nimbus/ with no override marker; README '145+ dependencies' |
| Performance not measured | 🤖 model inference | no benchmark artifact supplied |


---
**How to verify this document:**
`📄 stated in input` — the model's phrasing of something your source text said.
Find the matching line in the original to verify.
`🤖 model inference` — the model's own judgment or synthesis. Treat as opinion,
not measurement. Re-run on the same input and check whether specific numbers
stay consistent between runs.
