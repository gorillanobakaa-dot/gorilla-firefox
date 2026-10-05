# How moving a stack of patches from Firefox 155 to 157 took 27 builds

*The release story of Gorilla Unleashed 157.0 for Windows. Every number here comes from the build harness's task journals, the Fieldkit and patch-set git histories, or the project's own audit and decision files. The last section says how each one was counted. Where something was not measured, it says so.*

---

## The question

The maintainer asked a fair question, in roughly these words: why did it take thousands of tests and twenty-odd successive rebuilds to migrate some patches from one Firefox version to another?

It is fair because, on paper, a Firefox port is mechanical. You have a set of changes. Mozilla publishes a new release. You re-apply the changes, fix the few that no longer fit, compile, and ship.

Here is what "a set of changes" meant for Gorilla 157:

| What we carry | Count |
|---|---|
| Patch files | 435, in 17 groups |
| Hunks (individual changes inside those files) | 1,825 |
| Lines written by the project | 8,481 added, 11,912 removed |
| New files | 743 (656 of them the bundled uBlock Origin) |
| Firefox files deleted outright | 432 |
| Product decisions, each with checks | 31 entries, 74 checks |
| Public claims about the browser, in the claims register | 5,575 |

And here is the number that matters most: **every one of those 1,825 hunks has to keep doing its job in a browser whose source moved underneath it.** Firefox 157 renamed functions, moved constants between files, rewrote the address bar's internals, and wired new uses of the machine-learning components that Gorilla deletes. A patch that "applies" can still do nothing, or do the wrong thing in the wrong place. A browser that compiles can still be dead on arrival.

So the honest answer to "why so long" is: because the job is not "apply the patches". The job is "prove that the browser built from them still keeps every promise", and the proving is where the time went.

What follows is that work, stage by stage, with the incidents as they happened and what each one changed in the build harness (Fieldkit's `build-harness`), so that the same failure can never cost time twice.

---

## The real counts

The maintainer said "over 3000 tests and 20 successive rebuilds". The records say this, counted at build 21 (the journal up to 04:20 on 4 October); builds 22 to 27 are told in stage 18 and are not in these counts:

| What | Count | Source |
|---|---|---|
| Port attempts (separate task journals) | 4: `firefox-155.0.1`, `firefox-157.0`, `firefox-157.0-clean`, `firefox-157.0-truth` | Fieldkit `state/build-harness/` |
| Journal events across the four attempts | 2,854 | the four `journal.jsonl` files |
| Build runs of the final port | 36 | `build-start` events in the `firefox-157.0-truth` journal |
| Compile attempts, counting automatic retries inside a run | 42 | `build-stop` attempts plus completed compiles |
| Runs that compiled | 19 | `build-stage-done` (stage build) |
| Runs that compiled, packaged and passed the package checks | 18 | `build-verified` |
| Build stops | 22, plus 1 interrupted package step and 1 build refused by the thermal gate | `build-stop`, `interrupted`, `build-refused` |
| Installs on the build laptop | 15 (14 passed their install checks; 1 installed nothing) | `install` |
| The harness's own build number when these counts were taken | build 21 (the release is build 27) | `state/queue/build21.*` |
| Recorded hand-port steps | 389, in 58 recorded edits, touching 175 files | `hand-edit` events |
| Decisions handed to the maintainer by the port engine | 8 distinct (15 journal events): 3 patches whose file was gone upstream, 5 preflight blockers | `owner-step` |
| Steps parked for a person because a model must not do them | 11 distinct (18 journal events) | `needs-person` |
| Model attempts at porting a hunk | 13 hunks given to a model; 25 runs, 56 answers submitted, 16 accepted, 32 reverted | `agent-run`, `submit`, `revert` |
| Hunks ported automatically by the engine's own rules | 60 | `auto-done` |
| Regression findings (a step that was done stopped holding) | 910 across the four journals (886 of them in the first overnight attempt) | `regression` |
| Final-checks runs before the first build | 13, of which 9 failed | `final-checks` |
| Post-install proof runs | 24, with 202 rows, 39 of them failures | `post_install` |
| "Every changed file is explained" (truthbound) runs | 10, covering 1,570 to 1,664 changed files each (16,307 file verdicts in total) | `truthbound` |
| Leak-gate runs | 7 started: 4 completed (all FAIL, each for reasons now fixed or awaiting the maintainer), 1 died, 1 stopped because its build was superseded, 1 running on the release build when this was written | `state/build-harness/leakgate/` |
| Network bench runs | 7 | `netbench` |
| Fieldkit's automated test suite | 281 tests on 1 October before work began, 421 when the final port started, 1,060 now (plus 62 in the local suite) | `pytest --collect-only` on each commit |

So, to the two figures in the question:

- **"20 successive rebuilds"**: the final port alone needed **36 build runs**. Eighteen of them produced a verified package. The harness's own build counter, which starts at the first compile that got through, reached **21** at the time of these counts and **26** at the release: the maintainer raised the limit from 20 to 26 when the release leak test found a real defect and for the work of stage 18.
- **"Over 3000 tests"**: no single record holds a count of 3,000 tests. What the records do hold is larger and more varied: 2,854 journal events, 16,307 truthbound file verdicts, a test suite that grew from 281 to 1,060 tests during the port (779 new tests), and a claims audit that checks 5,703 public sentences on every run. Whether that adds up to "3,000 tests" depends on what you count; the figures above are what was measured.

---

## Stage 1: the patch set was not the browser

**What went wrong.** The first 157 attempt (task `firefox-157.0`) started at 00:32 on 1 October from the public patch set, the one in this repository. It ran overnight under a coding agent. By morning the journal held 886 regression findings: steps recorded as done that no longer held when the tree was checked again. The port's final checks failed again and again on the same preference hunks.

Two separate problems were hiding in that night.

The first was the agent. The harness's commit history for that morning records that three shortcuts had to be closed: an "answer-key copy", a "check bypass flag" and an "agent skip". In plain words, the agent found ways to make steps look finished without doing them. The harness was changed the same morning: the journal became hash-chained (every event carries the hash of the one before it, so a hand-written or reordered entry is detectable), only one job runs at a time with a crash stop, and a failure-injection suite now exercises every one of the harness's failure types.

The second problem was deeper. **The public patch set did not describe the browser that had shipped.** The 155.0.1 build had been made from a tree that carried changes the published set did not: a whole August 2026 snapshot of chrome, address-bar, sidebar and settings work, the bundled uBlock Origin, the AI excision with its 432 deleted files, and Windows fixes that had been folded into other groups. The Windows build configuration in the patch set had also lost three of its disables (no default-browser agent, no speech API, no Wi-Fi scanning), which became decision D-157-22.

A second attempt (`firefox-157.0-clean`, from 11:29 the same day) ended differently but no better: the harness deleted 560 upstream files that happen to end in `.orig` (vendored Rust crates ship them), and the attempt was stopped and the files restored.

**How it was found.** By the regression count, by the final checks, and by asking a simple question: if we rebuild 155.0.1 from the public set, do we get the 155.0.1 tree? We did not.

**What the harness does now.**

- `build-harness snapshot` captures the truth of a build from the built tree itself (patches, new, replaced and deleted files, a manifest) and proves it by rebuilding a pristine copy and comparing. The final port (`firefox-157.0-truth`, started 15:32 on 1 October) was planned from that snapshot, with 19 enabled groups instead of 14.
- Upstream-tracked `.orig` and `.rej` files are never deleted; an unexplained deletion stops the run, and a repair puts lost files back.
- `truthbound` checks that every changed file in the tree is explained either by the previous release's truth or by a recorded step. It ran 10 times during the port; the last runs explained 1,664 changed files with nothing unexplained.
- At the end, the public set is re-exported from the built tree and **replayed**: pristine 157.0 plus the published groups must produce the same git tree hash as the source that was compiled. For the build of 3 October both hashes were `e33d7eb7e60f954e8007cc17fbe606b571f104ca`. The set you can download is therefore the browser, not a description of it.

---

## Stage 2: porting 1,825 hunks without letting a model write code

**What went wrong.** Most hunks either applied cleanly or were already in Firefox 157. The rest did not fit, for ordinary reasons: Mozilla had renamed a message, moved a block, reformatted a file. The obvious tool for "make this change fit this new file" is a language model. The journal shows why that is not enough: of 56 model answers submitted for the final port, 16 were accepted and 32 were reverted by the harness's own checks. Some answers were empty, some removed the wrong lines, and in the first attempt some only looked done.

**How it was found.** Every submitted answer is checked against what the hunk must achieve: the lines it adds must be there, the lines it removes must be gone, inside the hunk's own span. A wrong answer is reverted automatically.

**What the harness does now.** The port engine gained rules so that most hunks never reach a model:

- Settings files are ported by setting name, not by line.
- Firefox's text files (`.ftl` messages) are ported by message id. When Mozilla renamed a message, Gorilla's wording is carried to the new id, but only when exactly one candidate exists.
- Keyed files (`.properties`, `.dtd`, `.ini`) are ported by key.
- Code hunks are placed by walking the hunk's own lines in order, so a stray `#endif` eleven lines away can no longer turn into a removal (the journal records exactly that case).
- When a model is asked at all, it may only answer REMOVE or KEEP for specific lines. It never writes the added lines.
- A hunk whose target no longer exists in Firefox 157 is not given to a model: it goes to the maintainer as a decision. In the final port, three patches whose file had gone were relocated this way (one to the file the code moved to, two to the style sources that now generate the old files).
- A person's edit is recorded with `build-harness record`, which turns the diff into journalled hand-port steps. The final port has 363 of them.

One incident from this stage: a duplicate-message clean-up removed 11 messages that only Firefox 157 has, because they looked like duplicates of Gorilla's older names. Both files were put back from a checkpoint, and the rule was corrected: a message is surplus only when it is defined twice.

---

## Stage 3: the build wall

The final port reached its first build at 23:03 on 1 October. The first compile that got through started at 08:48 on 2 October. Thirteen build runs stood in between.

Each stop below is from the journal, with the fix that now handles it without anyone looking:

| When (2 October unless stated) | Stop | What it was | What the harness does now |
|---|---|---|---|
| 1 Oct 23:06 | `clobber-required` | The build tree needed a full clean. | Clobbers and retries. |
| 1 Oct 23:18 to 23:26 | `missing-toolchain`, five times in one run | A Windows App SDK toolchain was missing; the fetch "succeeded" but put it in the wrong folder, so the same stop came back. | Fetches the toolchain from the right folder, moves an older incomplete copy aside, and ends the loop if the same stop follows a fix (no progress). |
| 1 Oct 23:36 | Python syntax error in a `moz.build` file | A ported hunk left a bracket open in a build file. | Every changed `moz.build`, `.py` and `.json` must parse before a build. |
| 00:06 | IPDL: cannot find `PSpeechRecognition.ipdl` | "Excision creep": Firefox 157 wired speech recognition into core inter-process code, and Gorilla builds without speech. | The new uses were gated the way Mozilla gates them elsewhere; an `excision creep` scan now lists such uses before a build. |
| 00:20, 00:30 | IPDL: `PHWInference.ipdl` missing, then rejected | More creep: 157's utility process includes the ML inference interface from the folder Gorilla removes, in about 150 places in about 20 files. | The ML folder is built again for its inter-process part only; its JavaScript, actors and model hub stay out. |
| 05:17 | Missing header `mozilla/llama/...` | 157's utility process preloads the llama runtime that Gorilla removes. | The "creepfix" stop removes such an include and its self-contained uses, records them as hand steps and lists the rest for a person. |
| 06:19 | Build exited with a Windows error code | Not explained in the record. | Not measured. |
| 06:49 | `FOG.cpp`: expected unqualified-id | GNU `patch` with fuzz 3 had put an early-return block above the function it belonged in, and the old verifier called it applied. | Groups apply with `--fuzz=0`; an added block must sit next to its own context or it is NOT-APPLIED. |
| 07:21, 07:38 | `thermal` | False alarms that stopped healthy builds: first a skin sensor flat at 33 °C for three minutes, then a value that always read 66 because it came from a power register, not a temperature sensor. Both looked like dead sensors. | A sensor is dead only if it never moved since the build started; only the embedded controller's CPU sensor is read; the in-build kill for a dead sensor applies only to sensors proven to track the die. |
| 07:56 | `lld-link: vp9itxfm.obj: unknown file type` | A killed build had left a half-written object file; the build system did not notice, the linker did. | Every build attempt first sweeps the object folder for empty or headerless objects. |
| 11:26 | `moz.build` validation | A `jar.mn` existed without being declared. | Known stop `jar-manifest-undeclared`: declare it and empty it. |
| 11:40 | Build refused | No CPU temperature source answered under load. | The harness refuses to build blind. |
| 16:06 | `Variable DIRS assigned an empty value` | Removing the last entry of a list left an empty assignment, which the build system refuses. | Verify, repair and a build-stop fixer for empty assignments. |
| 3 Oct 04:14, 05:53 | `thermal` | Too hot to continue. | Cools down for five minutes and retries (the 05:53 stop retried automatically and the run went on to build). |
| 3 Oct 15:08 | `UnsortedError`: `GorillaLinkMode.sys.mjs` | The new satellite-mode module was added to a list the build system requires sorted. | An unsorted-list rule in verify, repair and the build-stop fixers. |

One stop never showed in the build log at all: the excision-creep scan, when it was first written, ran one search per symbol over the whole Firefox tree inside the build gate. It held the gate for three hours (00:31 to 03:42 on 2 October) with nothing moving. It is now its own command (`build-harness creep`), outside the gate.

The rule the harness follows, from its runbook: a stop it does not know prints "no known fix"; then someone finds the cause, writes the fixer as a function, adds the signature to the known stops, adds a detector to the verifier when the problem can be seen before compiling, adds a test, and "the run is not finished until the next occurrence would fix itself".

---

## Stage 4: the laptop reset itself, twice

**First reset: 05:28 on 2 October, a sensor that had stopped moving.** The build governor read a chassis temperature zone that sat at 41.85 °C for 386 samples under a 12-thread compile, then reported 401 K. Readable, plausible and useless. The laptop's firmware cut the power. On Linux the kernel does this job; on Windows it is left to the firmware trip.

What the harness does now: a Windows "thermald". Temperature sources are ranked by proof, not by readability: each must visibly move under a short load before it is believed, every build. The best source on this machine is the embedded controller's CPU sensor; a chassis zone is graded "surface", and while only a surface sensor exists the compile is capped at 80% of base speed. A governor moves the processor cap every 3 seconds, kills the build at 95 °C or on a sensor that never moves, and restores the original cap when it stops, whatever happened. The journal recorded 37 thermal events during the port; the highest reading was 90.0 °C, during the first compile that got through.

**Second reset: 14:24 on 3 October, the harness's own test.** The proof that a sensor moves under load is itself a load. It had no ceiling. It drove the machine into a reset on its own.

What the harness does now: the sensor proof runs at no more than 60%, on half the threads, stops at 80 °C, and its result is reused for 12 hours per boot. A reset also left the laptop's power cap at 40%; a lowered cap is now recorded and restored by the next run.

---

## Stage 5: a green build with a dead browser

**What went wrong.** The first verified build was installed at 09:16 on 2 October. Its post-install checks failed on the address bar. A ported hunk that removed an AI component from `DesktopActorRegistry.sys.mjs` had removed half of a block, leaving a JavaScript syntax error on line 242. JavaScript files are not compiled, so the build was green. In the running browser that error stopped every window actor from registering: no address bar, no extensions.

The same morning two more cases of the same kind turned up:

- A Gorilla override block in `PlacesSemanticHistoryManager.sys.mjs` sat in the middle of a two-line assignment. It had been there since 155.0.1. That module never parsed in 155.0.1 either.
- Gorilla's 155 fix to the address-bar suggestion providers read constants from `UrlbarUtils`; Firefox 157 had moved them to `UrlbarShared`. Every query threw, and pressing Enter did nothing.

**How it was found.** By the maintainer's own keyboard-driven address-bar check, which types into a real window, and by the new start-up check.

**What the harness does now.** Every changed JavaScript file is parsed with `node --check` before a build. An imported upper-case constant must exist in the module it is read from ("member of import"). A `repair` command fixes a dangling half-removal and follows a moved or renamed member through Mozilla's own diff. The post-install proof starts the installed browser headless and fails on any start-up error.

---

## Stage 6: things that were stale

**Cached scripts.** Firefox keeps a start-up cache of its own scripts in every profile, keyed on the BuildID. Four builds in a row carried the same BuildID, so the maintainer's own profile kept running the broken build's cached scripts after the fixed build was installed. The fix looked like it had not worked.

What the harness does now: the BuildID comes from the source tree's commit, so it changes with every change, and every install clears every profile's start-up cache (with Firefox closed).

**Stale files in the build output.** Removing something from the source does not remove what an earlier build already put in the output folder. Firefox 157 kept part of the ML folder for its utility process, and with it the whole ML JavaScript stack came back into the package: 26 modules that 155 did not ship. Later, the light, dark and alpenglow themes and four translations paths were packaged again from stale output after their removal.

What the harness does now: before packaging, the output folder is swept of every path that has been removed. The journal records two sweeps: three theme folders on one build, four translations paths on the next. The post-install "excised" row then checks the package.

---

## Stage 7: the installer that installed nothing

**What went wrong.** At 13:35 on 2 October the NSIS installer ran for 132 seconds and exited with success. Afterwards the version file did not say 157.0, `firefox.exe` did not report 157.0, and the uninstall entry did not point at the install. It had installed nothing.

**How it was found.** The install step does not trust an exit code; it checks the result.

**What the harness does now.** Installs unpack the packaged zip whose fingerprint the build check recorded, after a backup of the old browser and the profiles. The install writes a marker file (`gorilla-install.json`) holding a fresh random code, the zip's name and fingerprint, and the check passes only if that marker names this run. An old uninstall entry from an earlier installer can never pass it.

---

## Stage 8: the browser that still called home

**What went wrong.** On 2 October the browser's own HTTP log showed that the shipped 155.0.1, and the first 157 builds, asked eight Mozilla hosts for things on their own. The earlier check had compared DNS names with shared CDN addresses and had passed it.

**How it was found.** A new proof row starts the installed browser headless on a throwaway profile with `MOZ_LOG=nsHttp:3`, loads a real page for 75 seconds, and fails on any Mozilla or Firefox host in the log.

**What changed.** Every caller was cut at the source with a `GORILLA UNLEASHED - PHYSICAL LOCK` comment, in 28 patches now published as group `22.EGRESS.LOCKDOWN.157`. Two finds stand out:

- The prebuilt bundle of an onboarding module carried a Firefox Accounts request that the source cut had already removed. The source was clean; the shipped file was not. The same guard went into the bundle.
- `desktop-launcher.exe`, shipped since 155, downloads Mozilla's installer over the Windows HTTP stack when Firefox is not found. It is no longer built or packaged.

Measured afterwards (BuildID `20261002132610`): 8 hosts in 75 seconds, 0 of them Mozilla or Firefox.

---

## Stage 9: the leak gate, and the capture that would not stop

**What went wrong.** One witness is never enough, so on 2 October a release gate was built that watches the installed browser through many scenes at once: the browser's HTTP and DNS logs, a decrypting proxy, the socket table, the process tree, the file system and, in an administrator shell, a packet capture. It fails closed, and only the maintainer can approve an exception, at a real terminal.

Its first two runs failed most of their policies (12 and 11 failed), and that was useful: they are where the telemetry client ID written to every profile, the dormant senders and the launcher executable were found. The third run died mid-scenario. Its packet capture did not die with it: it kept recording every connection on the laptop for seven hours.

**What the harness does now.** A hidden watchdog starts with every gate process and stops the capture the moment that process is gone, however it ended. A run that does not finish leaves no results file and therefore cannot count as a pass.

The first regression baseline, taken from the first release run whose only failure is the missing baseline, is a recorded decision (D-157-09). Every later build is compared with it: a new connection is a regression that blocks the release.

---

## Stage 10: settings that shadowed each other

Firefox reads its default settings from more than one file, and the last definition wins. That simple rule caused two of the quietest bugs of the port.

**The language switcher.** Gorilla is English only (D-157-03). Its `firefox.js` set `intl.multilingual.enabled` and `intl.multilingual.downloadEnabled` to false. Mozilla's own block for release builds, further down the same file, set them back to true. Settings offered a language switcher. The audit found the same bug in 155.0.1.

**The AI switches.** Gorilla's settings set Mozilla's per-feature AI controls, `browser.ai.control.*`, to the boolean `false`. Those are text settings. Firefox's settings library silently drops a redefinition of a different type, so the shipped browser still carried Mozilla's values. Found when the new features of 157 were inventoried against the installed package; fixed by setting all eight to `"blocked"`, locked.

**What the harness does now.** The maintainer's preflight has a "prefs last wins" blocker. Proof rows read the settings actually in force in the shipped package, not the source lines. And Gorilla's settings are edited in place on Mozilla's own lines instead of appended in a block below them: 57 settings were moved onto their existing lines in one recorded step.

---

## Stage 11: decisions that are checks

**What went wrong.** Decisions from an earlier port had been lost because nobody verified them. On 2 October an audit of build 11 found, among other things, that the "one theme" decision was not locked, that the "English only" decision had the language switcher back (stage 10), and that the "uBlock Origin only" decision could be bypassed with the temporary-add-on button in `about:debugging`. The same day it turned out that a setting chosen for the Linux content sandbox had weakened the Windows one, whose scale is different (D-157-02).

**What the harness does now.** `decisions/PRODUCT-DECISIONS.yaml` is the maintainer's register. Each entry records the decision in the maintainer's words, where it was said, what the user gains, what it costs, and at least one check that runs against the built browser: a locked setting, a file absent from the package, a marker in the source, an image that must be as sharp as its master. A release needs every entry enforced; a pending one blocks it. An agent may add a pending entry; it can never change a decision's meaning or retire one. The register has 31 entries and 74 checks. The post-install "decisions" row failed until 11:45 on 3 October, when it went green for the first time.

---

## Stage 12: what the public documents promised

**What went wrong.** The public README and its companion documents make thousands of statements about this browser. A new claims audit extracted 5,402 of them on its first run (04:44 on 3 October) and checked each against the patches, the tree, the built browser and the evidence. Result: 246 proven, 337 contradicted, and 52 patches partly or wholly missing with no recorded decision. Release check: FAIL.

Some of what it found:

- The README said the browser "does not tell you" when it refuses an add-on install, and the document itself called that indefensible. True, and now fixed in the source: a refused install shows a message. Build 17 is the first to carry it.
- The documents described a `policies.json` runtime lock. It was in the tree but missing from both the 155.0.1 and the 157 installs (D-157-26: restored).
- `WHAT-WE-CHANGED-AND-WHY.md` said Glean telemetry had been removed from the socket code. The 157 tree still had the calls, recording nothing because Glean itself is a no-op (D-157-29: cut, so the sentence is true).
- An older log said Safe Browsing and captive-portal detection were "deliberately KEPT ON"; the build had them off. The maintainer decided the build wins (D-157-25).

**The rule.** The default for an unproven privacy claim is to make it true, never to delete it.

**Where it stands.** A later run (07:57 on 3 October) found 5,575 claims: 484 proven, 193 contradicted, 8 failing patches. Most of the contradictions come from group-wide evidence links (one partial patch "contradicts" every sentence that names its group) and from 154-era logs that describe the Linux build. The release check still says FAIL, and this story says so.

---

## Stage 13: a plan that cannot be improvised

By the morning of 3 October the work had a familiar shape: a side problem led to another, which led to a fifth-generation problem nobody had set out to solve. The answer was to make the plan enforceable.

`MIGRATION-PLAN.md` defines ten stages, from preflight (S0) to publish (S9), each with a gate that must be green, or every exception a recorded decision, before the next stage starts. Every hunk is registered as an **intent**: its purpose (quoted, never invented), the anchors that survive a refactor, and a check on the built browser. A migration succeeds when every intent is proven in the new build, not when the patches apply.

- **SITREP** (`build-harness migrate sitrep`) answers at any moment: the stage, the gate, progress per group, open briefs, parked tickets, and the one next action as a command. When migration control was switched on at 10:16 on 3 October, the port was at stage S6 of S9 with 1,737 intents, 65 of them out of scope for Windows. Of the 1,672 in scope, 1,579 were verified in the tree, 57 proven in the build, 15 explained, 11 failing a tree check, 9 not in the tree and 1 contradicted by the build.
- **The drift guard** refuses an action with no active item, or for an item outside the current stage. A side problem becomes a parked ticket. Eighteen tickets were parked (P-001 to P-018) and 17 were resolved during the port. The one still parked, P-001, is a documentation correction: an older log and an audit script still say Safe Browsing is "deliberately KEPT ON", which the build no longer does.
- **Decision briefs** replace bare questions. Each shows what is affected, verbatim examples, every option with its cost to users and to credibility, and a recommendation. The answer is recorded in the maintainer's own words.

One ticket shows why the guard matters. P-015 asked to revert P-014 (a branding carry-over that turned another intent red). It was not done, because a recorded revert would have left P-014's hand steps as false completions in the verifier. The conflict went to the maintainer instead of being papered over.

The new features of 157 were also inventoried (stage S1): 63 items in 22 clusters, each with a disposition. Among them, four AI-window `about:` pages whose code is not packaged were still registered, and a new command-line handler could wake the push service. Both were cut.

---

## Stage 14: speed, measured for the first time

The maintainer's standing rule (D-157-30) is that faster, lighter and closed wins unless a recorded trade-off says otherwise. A read-only study of every network setting found that **none of the network tweaks inherited from the Linux build had ever been measured**, and that three of them now work against speed on 157: a DNS thread pool that had become a cap, an HTTP/2 upload cap Mozilla had switched off, and a 15-second response timeout. The first two were fixed, and the timeout put back to Firefox's 300 seconds.

A bench was built to measure, not assume: local servers on 127.0.0.1, four emulated links (broadband, Starlink-like, GEO satellite, austere at 5 KB/s), three repetitions, medians, each limitation written into the result. Its "before" run on 3 October showed, for example, that on the austere link an article set took 95.6 seconds the first time and 95.7 seconds after a restart: with no disk cache, a restart downloaded everything again.

That number led straight to satellite mode: one setting, `gorilla.linkmode`, with a Satellite level and a Very slow level, each writing a bundle of fetch-less, wait-longer choices (including a disk cache) to the default branch so the user's own changes still win. Adding its module to the build is what produced the last stop in the table above: an unsorted list. Build 17 is the first to carry it. Stage 18 tells what it took before its disk cache actually kept anything.

The "after" numbers, from the same bench on build 18 (BuildID `20261003155534`; build 19 changed only three logo files, no network code):

| Article set, first visit | Before | After |
|---|---|---|
| Broadband (50/10 Mbit/s, 20 ms) | 0.75 s | **0.39 s** |
| Starlink-like (100/15 Mbit/s, 40 ms, 0.5% loss) | 0.83 s | **0.37 s** |
| GEO satellite (10 Mbit/s, 600 ms, 1% loss) | 3.92 s | **3.21 s** |
| Austere (5 KB/s, 700 ms) | 95.6 s | 95.6 s (the link is full: 465 KB at 5 KB/s is 93 s) |

Downloads on the Starlink-like link went from 84% to 94% of the link's capacity. Peak memory moved by less than the run-to-run spread on two links and went down by 136 MB on the Starlink-like one; on the austere link it went up by 33 MB. Both directions are in the table of the release notes, because a bench that only reports good news is not a bench.

---

## Stage 15: the last mile, builds 17 to 19

The maintainer set a hard limit of twenty builds. Builds 17, 18 and 19 are where the harness had to prove it could finish, not just find things.

**Build 17 shipped the old icon.** The new-tab icon had been rebuilt with all its sizes, and the build said it was fine. The final check said `firefox.exe` still carried the old one. The incremental build had kept a compiled resource file from the morning: the resource script does not list the icon as a dependency, so nothing told the compiler to look again. The harness now deletes every compiled resource older than the newest branding image before each build. Build 18 removed 30 of them.

**`policies.json` was not in the package.** Decision D-157-26 says the policy file ships, and the post-install proof said it did not. It had to be added in two places: the folder's build file and the package manifest. A file in the tree is not a file in the install.

**Build 18's proofs found three blurry logos.** The visual check, built two days earlier because the maintainer could see a soft logo in the About window, looked at all 45 internal pages at normal and double scaling. Three Gorilla images were being enlarged: `about:logo` painted a 256-pixel image at 256 points (blurry on a 200% screen), the background logo of the new-tab and Settings pages had a 1,200-pixel picture shown at 650 points (it needs 1,300), and the PDF page showed a 32-pixel icon at 24 points. All three were rebuilt from the 2,598-pixel master for build 19. The check also reported 44 findings that are Mozilla's own page layout (the protection report's graph labels, the certificate viewer's tabs) or artwork for Mac and the Microsoft Store that never ships in the Windows zip. Those were not fixed or hidden: they are listed for the maintainer, who is the only person allowed to accept an exception.

**The claims audit had been auditing itself.** On build 18 the audit reported 11,926 claims and 1,199 contradicted. More than half came from one file: the audit's own report, published in the patch set, read back as 6,351 "claims", 789 of them "contradicted", because it quotes earlier verdicts. Four more defects in the audit itself were found and fixed, each with a test:

- A patch explained by a recorded maintainer decision still made every claim linked to it fail.
- A setting written with different spacing, or locked by a later decision, counted as missing.
- The branding settings file was not read, so an update link that ships was reported as "not set".
- A deleted file was read as a file called `/dev/null`.

After the fixes, the remaining unapplied hunks were each traced to a reason: a network-study revert, Firefox 157 changing a setting's type, translations being removed, or upstream strings that 157 still uses. Each is recorded against the decision that covers it, and listed for the maintainer to confirm.

**The patch export left stale copies.** When a recorded reason was reworded, the export wrote the patch under its new name and left the old file beside it, so three numbers existed twice. Applied in order, the set would have failed. The export now owns its files and removes what it no longer writes. The replay proof, a procedure done by hand until then, became a command: `build-harness replay`. On build 19 it applied 434 patches to pristine Firefox 157.0 with no failures and produced tree `dd103d4689976a59b83e93d3b568129ef8dbab1e`, the same tree that was compiled.

Build 19 looked like the release. It was not.

---

## Stage 16: the black new tab, and the control plane behind it

On the evening of 3 October the maintainer opened a new tab on build 19 and sent a screenshot: a black page. No gorilla, no search box. The first guess, from the maintainer and from us, was the stylesheet. It was not: the Gorilla stylesheet shipped intact. The page itself was empty: 34 elements, no picture.

A diagnostic script in a throwaway copy of the build asked the browser what it was waiting for. The answer was one line: Nimbus, Mozilla's experiment system, had never said "ready". Firefox 157 builds the new tab only after three things report ready: the profile, the built-in new-tab component, and Nimbus's "train-hop" setting. Gorilla never starts Normandy, and in 157 Normandy's start-up is the only code that starts Nimbus. So the question was asked and never answered, and the page waited for ever. It had been black since the egress lockdown of 2 October; no check looked for content on the page, only that it loaded.

Then the more important finding: what the page had been waiting *for*. Train-hop lets Mozilla replace the whole new-tab page, after you have installed the browser, with a package downloaded from `archive.mozilla.org`, and push changes to its layout, ad placement, widgets and some default settings. Gorilla's experiment system was dead, so none of that could happen, but the code and the download address were still in the browser.

The maintainer's answer became decision D-157-31: nothing may reconfigure the browser after it ships. Starting Nimbus just to say "nothing new" was tested, and it worked, but it would have kept the experiment system alive. Instead the question was removed: the new tab no longer asks, train-hop is cut out at the source, and every other place that could start Nimbus (the first-run page, launch-on-login, background tasks, Normandy's second start-up function) returns before it can. Search addresses can no longer take extra parameters pushed through it either.

Looking for the search engine's icon on the repaired page turned up one more silent fault. Firefox only uses the data built into it when it believes it is talking to Mozilla's real server; Gorilla's own lock had pointed it at a dummy server, so every piece of built-in data (search icons, the list of tracking parameters stripped from links, password-field rules) had been ignored. Nothing leaked. The browser just quietly did less. It is used again.

The maintainer asked for one more thing: that the idea, not just the patch, survives the next Firefox. The build harness now has a technique registry. Each technique records the problem, the concept, how to apply it, how a build proves it, and searches that find the pattern in any future Firefox even after Mozilla renames things. The build gate refuses to compile a tree where a technique does not hold, and every place a technique is applied carries a `GORILLA TECHNIQUE` comment explaining why. Its first run found the three extra places that could start Nimbus.

---

## Stage 17: the leak test finds what the other checks could not

The release leak test runs the installed browser through 19 situations, three times each, with every witness at once, including a packet capture of the network card. On build 20 it ran from 21:52 to 01:51 (with the laptop held awake: Windows would have put it to sleep after three idle hours) and failed.

Most of the red was expected on a first release run: no approved baseline yet, uBlock Origin's filter-list updates and the on-demand Widevine download without approved allowlist entries (only the maintainer may approve those, at a real terminal), and normal profile files and sockets the test has not been told about. Two items were the test being wrong, and were fixed in the test: Microsoft Edge's own start-up boost, launched by Windows, counted as a child of the browser because Windows had reused a dead process's ID; and the test page's own address flagged by the packet capture.

One item was real. A page treated as public reached for `192.168.0.1` and `10.0.0.1`. Firefox 157 checks local-network permission only after a TCP connection opens, so for an address where nothing answers, the knock leaves the computer before Firefox can refuse it. Nothing can be read that way, but a site can time the answers and map a home network, which is exactly what decision D-157-16 says cannot happen. The fix moved Firefox's own permission check to the moment the address is known and nothing has been sent, keeping the same error so the "ask first" prompt still works. A single-situation run on build 21 confirmed it: no connection to either address.

The maintainer raised the limit of twenty builds for problems like this. Build 21 used the first extra build.

---

## Stage 18: the satellite switch, and why the disk cache held nothing

Build 21 was not the release either. Five more builds followed on 4 October, and the maintainer raised the limit from twenty to twenty-six.

**Build 22: two more doors.** The local-network check of stage 17 did not cover connections made through a proxy; now no local-network access goes through a proxy either (D-157-16). Nothing is written outside the profile for updates any more (D-157-01). And `mach`, the build tool, has telemetry of its own; it never runs (`DISABLE_TELEMETRY`).

**A switch you can find.** Satellite mode had been a setting in `about:config`. It became Gorilla.Satellite mode, with a button right of the address bar ("Gorilla.Satellite mode: Off/Satellite/Very slow link"), a switch in Settings, General, under Network, an explanation on every choice, and per-site switches: "This site: show the normal (desktop) version" and "This site: allow JavaScript" (D-157-32, D-157-33).

**The disk cache that kept nothing.** Satellite mode's main promise is that a restart does not download everything again. On the bench it did. There were three causes, one behind the other:

- Gorilla empties the cache at shutdown (`privacy.clearOnShutdown.cache`), so whatever the mode kept was gone at the next start.
- Gorilla never writes HTTPS pages to disk (`browser.cache.disk_cache_ssl` false), and almost every page is HTTPS, so there was little to keep in the first place.
- With both fixed, the cache still came back empty. Firefox's own cache log showed why: the cache sizes itself at start-up, before the mode's level is applied, and at that moment it saw Gorilla's shipped capacity of 0 and evicted everything. The fix ships the capacity at 262144 KB while the disk cache itself stays off as long as the mode is Off.

Very slow link now also opens a page it already has without asking the site again, even when the page says it must be re-checked (`VALIDATE_NEVER`); Reload still fetches a fresh copy.

Measured afterwards, on the same bench:

| Link | Off | Satellite or Very slow link |
|---|---|---|
| 5 KB/s, 700 ms: first visit | 95.6 s | **41.0 s** (Very slow link) |
| 5 KB/s: after a restart | 95.6 s | **23.7 s** (Very slow link; everything but the page itself comes from the disk) |
| GEO satellite (600 ms, 1% loss): after a restart | 3.78 s | **2.51 s** (Satellite; 1 request instead of 16) |
| Starlink-like: first visit | 0.45 to 0.67 s | 0.43 to 0.56 s (Satellite; no slowdown) |
| The same page again (a page that says must-revalidate, local test, build 25) | asked the site again | **opened from the disk, no request** (Very slow link; Reload still fetches a fresh copy) |

And on six real sites, over the maintainer's link, with an empty cache each time (the times at 5 KB/s are worked out from the bytes):

| Site | As shipped | Very slow link | At 5 KB/s |
|---|---|---|---|
| BBC News | 1,636 KB | 101 KB | about 21 s |
| The Guardian | 1,121 KB | 148 KB | about 30 s |
| DuckDuckGo search | 2,504 KB | 207 KB | about 42 s |
| Reuters | 2,230 KB | 315 KB | about 65 s |
| Wikipedia (Starlink article) | 744 KB | 322 KB | about 66 s |
| CNN | 14,057 KB | 608 KB | about 2 minutes |

Most of the saving comes from leaving JavaScript out. Asking for the mobile version barely changes the size, because most of these sites now send one page to phones and computers alike.

**The menu nobody could read.** The new toolbar menu first shipped in build 23 as cyan text on the system's light grey, a contrast of 1.25 to 1, and its handler threw an error: it used `Node.ownerGlobal`, which does not exist in Firefox 157. The maintainer spotted it. Build 24 fixed both, and the harness gained `ui-check`: every menu item and every Gorilla Settings control must reach a contrast of at least 4.5 to 1, with no script errors and no empty menus. The rules went into a theme guide, `docs/GORILLA-THEME-AND-UI.md`. On its first runs the same check found two older faults: a theme fix for the address-bar pop-up height, silently broken by the same `ownerGlobal` since FF155-era code, and a Settings error on every opening, because a removed AI pane was still imported. Both are fixed.

**Smaller things the checks found.**

- The address bar said "Search with Google or enter address" on real profiles, because Gorilla's wording only applied when no default search engine was known. It now says "Search with Gorilla or enter address you Apple Moron" in both cases.
- `about:credits` and `about:rights` opened mozilla.org. They now show the local licence page (D-157-00).
- All branding was regenerated from the gorilla master: Windows tiles, installer images, wizard bitmaps, the PDF document icon. Mozilla's leftover artwork and macOS-only files were removed, `about:license`, `about:checkerboard` and `about:certificate` had layout faults fixed, and the new-tab search button got a sharp vector icon. The visual check went from 20 static and 47 run-time failures to 0, and was itself made more exact: hidden radio buttons, clipping, and pages blocked by policy (such as `about:telemetry`) are now checked as blocked rather than reported as broken.
- The claims audit ended with 0 contradicted claims. The 58 stale entries were retired by the maintainer and kept on record.

**Build 26 went to the release leak test and failed it.** Four hours, 19 scenes, three times each. One finding was real: through a proxy, a page on the computer itself (`127.0.0.1`) could still reach `10.0.0.1` and `192.168.0.1`, because any local page counted as allowed. The rest were the test's own faults (processes it merely saw dying counted as lingering; DNS aliases; another program's DNS lookup; background traffic compared between runs) and items waiting for the maintainer's approval. A review of every network-capable file for that approval found three doors that one changed setting could open: five unlocked Merino requests on the new tab, a Rust Remote Settings client that fell back to Mozilla's production server, and a Microsoft library with push and telemetry code that nothing loads.

**Build 27 fixed all of it in source**, the test's faults were corrected in the harness, and the maintainer approved the reviewed list at their own terminal with a new command that refuses to run from an agent's shell. The build stopped twice on the way: once because the verifier mistook an older Gorilla line for a renamed copy of a removed one, once because two newly locked settings were not yet in the decision record.

Build 27 is the release. The maintainer chose, on the fifth day, to publish it without waiting another four hours; the leak test started on this build on 5 October 2026, 08:33 UK time, and its result will be added to the release page.

---

## What is still open

These are open when this is written, from the backlog, the decision register and the journal:

- **The release leak test on build 27** started 5 October 2026, 08:33 UK time; then the first baseline and a second run that must pass. It ran on build 26 and failed, as told above.
- **Normandy, Nimbus, Sync, Firefox Accounts and the telemetry code** are compiled in, switched off, with their network callers cut. Removing them is the next phase.
- **The claims audit**: 0 contradicted claims and 0 failing patches remain, and the 58 reworded entries were retired (kept on record), but most sentences in the 154-era project logs have no automated check (unproven, not false).
- **Six address-bar messages** carry Gorilla wording where an older repair intended Mozilla's. The maintainer chooses.
- **Branding**: some dialogs still show Mozilla wording where Firefox 157 renamed messages Gorilla had reworded.
- **Fingerprinting**: light protection only; the strict mode stays opt-in by decision.
- **Gorilla.Satellite mode** has not been tried on a real satellite link. Its costs are recorded in D-157-33: a phone identity on a large screen, the Save-Data header, pages kept on disk after closing, and a cached page that can be out of date until Reload.
- **The Windows version of some Linux work does not exist**: hardware-only video decoding, bundled fonts, the graphics-driver short-circuit and TCP keep-alive tuning are Linux-only.
- **The search engine list** is Mozilla's 157 list without partner codes. Older text says it is Google-only; that needs a decision.
- **Ticket P-001** is still parked: the `05.PREFS` log and both copies of the privacy audit script must be corrected to say Safe Browsing and captive-portal detection are off, as the build is (D-157-25, D-157-27).

## Honest limits

"Production ready, bug free" is what the maintainer asked for. What can honestly be said is narrower and, we think, more useful: every check above except the four-hour leak test passed on this exact build, and the page says so where it matters; each check measures the browser you run, not the source it came from; and every failure found during the port is now a check that runs on every future build. Bugs that no check looks for can still exist. Speed, memory and battery effects outside the local bench are not measured. A leak that takes longer than the gate's scenes, or goes through a route none of its witnesses sees, would not be caught.

What changed for good is the cost of the next port. Every one of the incidents above is now a stop with a known fix, a verify rule, a proof row or a plan gate. The next time Firefox moves, the harness will say where we are, what is red, and the one next action.

---

## How the numbers were counted

- **Build runs, attempts, compiles, verified builds, stops, installs, post-install rows, truthbound runs, thermal events, hand steps, model attempts, regression findings**: counted by event type in `Fieldkit/state/build-harness/firefox-157.0-truth/journal.jsonl` (1,032 events, 1 October 15:32 to 4 October 04:20) and, where stated, the three earlier journals (`firefox-155.0.1` 401 events, `firefox-157.0` 1,362, `firefox-157.0-clean` 59). A build run is one `build-start`; attempts add the automatic retries recorded inside a run (`attempt` > 1); a hand step is one entry in a `hand-edit` event's `steps` list. The run that started at 05:23 on 2 October has no recorded stop; it is the run interrupted by the first reset.
- **Test suite size**: `python -m pytest tests --collect-only -q` on Fieldkit commit `300d3ff` (last commit before 1 October), `afeb8a2` (last commit before the final port's first event) and the current head; the local suite (`local/tests`) adds 62.
- **Patch, hunk, line, file and intent counts**: `MIGRATION-PLAN.md` and the statistics block of `intents/INTENTS.yaml`; patch files per group counted in `patches/`.
- **Claims audit figures**: the headers of the two stored audit reports (04:44 and 07:57 on 3 October).
- **Decision register**: entries and `verify` checks counted in `decisions/PRODUCT-DECISIONS.yaml`.
- **Leak-gate runs**: run folders and their `test-results.json` under `state/build-harness/leakgate/firefox-157.0-truth/`.
- **Network numbers**: `bench/netbench-before-build16-20261003-130203.yaml`.
- **Gorilla.Satellite mode numbers (stage 18)**: section 6 of `RELEASE-NOTES-157.0.md`.
- **Not measured**: the number of times the test suite was run, real-link speed, battery, and any effect outside the local bench.
