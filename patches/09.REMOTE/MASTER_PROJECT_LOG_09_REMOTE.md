# 09.REMOTE — Master Project Log

*One canonical log per folder. The dual-track LAYMAN + DEVELOPER docs and the
IBM-style AUDIT for this topic are merged VERBATIM below; the standalone
`09-remote_*.md` / `*.filled.json` / `*.prep.json` render artifacts are deleted
after merge (recoverable from git history).*

---

## ═══ REGENERATION 2026-08-04 — dual-track docs rebuilt (gen-2), poison autopsy recorded ═══

**Why this regeneration exists.** The RemoteAgent patch was regenerated on
2026-08-04 after the loopback-address poison (documented below) was reverted in
the live tree on 2026-08-03. This log's gen-1 documentation set (dated
2026-08-02, retained at the bottom under a SUPERSEDED banner) reported
"No defects / Audit Status: PASS / 96% ready" and a precheck of "Rule Findings
(0)". That was FALSE: it missed the poison. These gen-2 docs replace it.

**Verification performed 2026-08-04 (against the tree, not the doc):**

- Both patches reproduce the live tree byte-exact: staged vanilla
  (`SafetyVault.Firefox/firefox-main`) + `patch -p1` + `cmp` against
  `the source tree` → `REMOTEAGENT: BYTE-EXACT MATCH`,
  `MARIONETTE: BYTE-EXACT MATCH`.
- Live loopback list is vanilla `["127.0.0.1", "[::1]"]` at
  `remote/components/RemoteAgent.sys.mjs:81` (vanilla comment at `:79`);
  `grep -rn '0.0.0.0'` across both files returns **no matches**.
- Patch SHA-256(16): Marionette `809097a96e171e19` (unchanged since gen-1) ·
  RemoteAgent `22173d4177e0874f` (regenerated; gen-1 record was `db4b74fb87a23476`,
  71 lines → now 59 lines, and the regenerated patch carries **no loopback
  hunk**).

**Poison autopsy — the project's FIRST (ingested to chroma_fx154).** An unmarked,
security-relevant edit had changed `RemoteAgent.sys.mjs` `loopbackAddresses`
from `["127.0.0.1", "[::1]"]` to `["0.0.0.0", "[::1]"]`, with the neighbouring
comment falsified to match. Proven poison across three axes:
(1) **tree diff** — vanilla is `127.0.0.1`; the edit carried **no**
`// 🦍 GORILLA … PHYSICAL LOCK` provenance marker, unlike every one of the
intentional lockdown edits, which is the signature of injected slop rather than
an intentional Gorilla edit;
(2) **scope** — the project's outbound host-blackhole ("kill-categories") is
OUTBOUND-only and is therefore N/A to this INBOUND `allowHosts` whitelist check,
so it offered no compensating control;
(3) **authority** — RFC 5735 classifies `127.0.0.0/8` as Loopback and
`0.0.0.0/8` as "this host on this network" (**not** loopback), consistent with
the in-source Bug 1220810 comment at `RemoteAgent.sys.mjs:78-80`.
It was **disarmed in this build** (dead code: the `allowHosts` loopback branch
is reached only when `#server` is truthy, and `#server` stays null because
`#enabled` is force-disabled), and it was **reverted to vanilla on 2026-08-03**.
Full read-only forensic pass: `POR_DRAFT_2026-08-03.md`.

**One open precheck item, dispositioned.** Gen-2 precheck raises **P1-001**
("patch will not apply"). It is a **false positive**: the regenerated RemoteAgent
patch's git header carries a tab+timestamp
(`RemoteAgent.sys.mjs\t2026-08-03 12:43:46…`) that the rule mis-parses as the
target path; `patch -p1` applies it byte-exact (verified). Tracked as review
defect **P3-101** (normalise the header). Not a release blocker.

**Intentional lockdown (do NOT flag).** The three `GORILLA UNLEASHED - PHYSICAL
LOCK` edits per file are the deliberate lockdown (dead-end setters + inert CLI
branch + construction default false). RemoteAgent is hard-disabled; the
`allowHosts` getter is unreachable today (dead), latent only if the lockdown is
reverted.

**Gate scores (≥85 required):** LAYMAN 89 · DEVELOPER 90 · AUDIT 96 — all PASS.

---


---

# ═══ MERGED DOCUMENT: 09-remote_audit.md (verbatim · sha256:139d128f47bb1068 · merged 2026-08-04) ═══

# IBM-Style Audit Report: 09.REMOTE

## SECTION A: DOCUMENT CONTROL

| Attribute | Value |
|---|---|
| **Target** | 09.REMOTE |
| **Files scanned** | see payload |
| **Date / time** | 2026-08-04 07:18:17 |
| **Audit status** | PASS |

## SECTION B: EXECUTIVE SUMMARY (Plain Language)

Both of Firefox's remote-control hatches are welded shut at the source, in three places each, and both patch files exactly reproduce the code in the build (checked byte-for-byte). A booby-trapped safety value that had been quietly slipped into one file — swapping 'this computer only' (127.0.0.1) for 'the whole network' (0.0.0.0) — was caught, proven wrong, and put back on 2026-08-03. It never did harm because it sat behind a welded-shut door. The one warning the automatic checker raised is a false alarm about the patch's date-stamp, not a real defect. This is safe to ship. The only cost is deliberate: no browser-automation tools work on this build.

## SECTION C: TECHNICAL SUMMARY (Developer)

Three-site dead-coding per channel (constructor default, setter body, command-line-startup branch) disables Marionette and the WebDriver BiDi Remote Agent; env vars, --marionette and --remote-debugging-port are inert. Verified 2026-08-04: (vanilla + patch) == live byte-exact for both files; no 0.0.0.0 remains in either; loopbackAddresses is vanilla ["127.0.0.1", "[::1]"] at RemoteAgent.sys.mjs:81. The RemoteAgent patch was regenerated 2026-08-04 (59 lines, sha 22173d41...) from the prior 71-line poisoned-era patch (sha db4b74fb..., per the merged PRECHECK record) and no longer carries any loopback hunk. The auto-merged P1-001 ('patch will not apply') is a false positive: the regenerated patch's git header carries a tab+timestamp the rule mis-parses as the target path; patch(1) applies it byte-exact. Residual work is a rebase self-test, a runtime preflight, and header normalisation; none blocks release.

## SECTION D: DETECTED DEFECTS

1 found by rules, 3 by review. Rule findings are deterministic; review findings are judgement.

### 🟠 P1-001 — P1 *(found by rule)*

- **Plain English:** A repair instruction points at a room that does not exist in the current building (remote/components/RemoteAgent.sys.mjs	2026-08-03 12:43:46.381629057 +0100). Upstream moved or renamed it, so the repair cannot be carried out.
- **Technical:** remote_components_RemoteAgent.sys.mjs.patch: target path remote/components/RemoteAgent.sys.mjs	2026-08-03 12:43:46.381629057 +0100 is missing under the source tree. The patch will not apply.
- **Fix:** Re-locate the code in the new tree and regenerate the patch against it.
- **Effort:** 1h

### 🟢 P3-101 — P3 *(found by review)*

- **Plain English:** The RemoteAgent patch's header line carries a date-stamp the sibling patch does not; it confuses the automatic checker into a false alarm but does not affect the fix itself.
- **Technical:** remote_components_RemoteAgent.sys.mjs.patch ---/+++ lines carry '\t2026-08-03 12:43:46...'; the PRECHECK path-parser reads it as the filename, producing the P1-001 false positive. patch(1) applies byte-exact.
- **Fix:** Regenerate/normalise the header without the tab+timestamp to match remote_components_Marionette.sys.mjs.patch.
- **Effort:** 10min

### 🟢 P3-102 — P3 *(found by review)*

- **Plain English:** One safety value inside the Remote Agent stays correct only because the door it sits behind is welded shut; if someone unwelds that door later and the value has drifted, it becomes a real hole.
- **Technical:** RemoteAgent.sys.mjs:81 loopbackAddresses is dead code under lockdown (#allowHosts forced null :437; #server null because #enabled false :440 gates #listen :468->:279). Correct today (["127.0.0.1", "[::1]"]) but its correctness is only latent-guarded.
- **Fix:** Add a rebase / self-test asserting loopbackAddresses === ["127.0.0.1", "[::1]"] and that both channels report disabled.
- **Effort:** 1h

### 🟡 P2-103 — P2 *(found by review)*

- **Plain English:** There is no automatic test that proves, on a real launch, that the two hatches stay shut; today it is proven by reading the code, not by running it.
- **Technical:** No runtime assertion of Services.marionette.enabled === false or of no 2828/9222 listener; the ss / --marionette runtime checks were not executed this pass.
- **Fix:** Add the runtime preflight from 00_REMOTE_HISTORY_AND_ROADMAP.md:414.
- **Effort:** 2h

## SECTION E: PRODUCTION READINESS

**Overall readiness: 🟢 90%**

**Done:**
- [x] Marionette three-site lockdown present and marked (Marionette.sys.mjs:58, :78, :124)
- [x] Remote Agent three-site lockdown present and marked (RemoteAgent.sys.mjs:51, :102, :430)
- [x] Both patches reproduce the live tree byte-exact (verified 2026-08-04)
- [x] RemoteAgent loopback poison reverted to vanilla and absent (RemoteAgent.sys.mjs:81; no 0.0.0.0 in either file)
- [x] Poison autopsy filed (POR_DRAFT_2026-08-03.md) — the project's first, ingested to chroma_fx154
- [x] Trade-off (no Selenium/WebDriver) documented

**To do:**
- [ ] Normalise the RemoteAgent patch header to clear P1-001 (P3-101)
- [ ] Add a rebase self-test for the loopback value and disabled states (P3-102)
- [ ] Add a runtime preflight asserting disabled state and no open sockets (P2-103)
- [ ] Confirm no other remote entry points remain (legacy CDP, DevTools remote server, devtools.debugger.remote-enabled) — roadmap High Priority

**Not verified:**
- Runtime socket behaviour: the ss / --marionette checks were NOT executed this pass (no build was run); 'no socket binds' is inferred from static control flow
- The prior 71-line poisoned patch content is not preserved for a line-level diff; that the dropped 12 lines were the loopback hunk is inferred from the line-count delta and the current absence of any loopback hunk
- Values were not re-validated against Mozilla upstream docs for optimality (contamination-screened only)
- The outbound blackhole's non-applicability is an architectural read; the blackhole code was not re-inspected this pass

## SECTION F: PHASED PLAN

### Phase 0 — `RemoteAgent patch header`
- **Change:** strip tab+timestamp from ---/+++ lines
- **Expected impact:** precheck clean; sibling-consistent

### Phase 1 — `rebase guard`
- **Change:** assert loopbackAddresses and enabled==false
- **Expected impact:** catches a silent upstream restore of defaults or poison

### Phase 1 — `runtime preflight`
- **Change:** assert no 2828/9222 listener at startup
- **Expected impact:** dynamic proof of the lockdown

### Phase 2 — `remote-entry audit`
- **Change:** enumerate CDP / DevTools remote server / pref
- **Expected impact:** closes the 'no other path' gap

## POSITIVE OBSERVATIONS

- Three independent activation surfaces are dead-coded per channel — no single-point revert re-enables either
- Dead-coding over deletion preserves class shape; the diff stays small and auditable
- Every intentional edit carries a PHYSICAL LOCK provenance marker; the poison's ABSENCE of one is exactly what exposed it
- Patches verified byte-exact against the live tree, not merely against the doc
- Poison caught, proven across three axes (tree diff; inbound-vs-outbound scope; RFC 5735 / in-source Bug 1220810 loopback definition), and reverted — a working autopsy, not a claim

## VERIFICATION COMMANDS

Run these to check the claims above rather than trusting them.

```bash
patch -p1 --dry-run < remote_components_RemoteAgent.sys.mjs.patch   # applies (P1-001 is a parser false positive)
grep -n loopbackAddresses remote/components/RemoteAgent.sys.mjs   # ["127.0.0.1", "[::1]"] at :81
grep -rn '0.0.0.0' remote/components/RemoteAgent.sys.mjs remote/components/Marionette.sys.mjs   # no matches
grep -n 'PHYSICAL LOCK' remote_components_Marionette.sys.mjs.patch remote_components_RemoteAgent.sys.mjs.patch   # three per file
ss -tlnp | grep -E ':2828|:9222'   # expect no output (run on a build; not executed this pass)
```

## Claim Sources

| Claim | Basis | Evidence |
|-------|-------|----------|
| three-site lockdown per channel | 📄 stated in input | GORILLA UNLEASHED - PHYSICAL LOCK |
| --marionette read and discarded | 📄 stated in input | The command line flag --marionette is now ignored and discarded. |
| RemoteAgent startup forces #enabled false | 📄 stated in input | this.#enabled = false; |
| RemoteAgent patch is 59 lines, sha 22173d41 | 📄 stated in input | sha256:22173d4177e0874f |
| Marionette patch is sha 809097a9 | 📄 stated in input | sha256:809097a96e171e19 |
| RemoteAgent patch header carries a tab+timestamp | 📄 stated in input | --- a/remote/components/RemoteAgent.sys.mjs	2026-08-03 12:43:46.379563830 +0100 |
| prior patch was 71 lines, sha db4b74fb | 🤖 model inference | *(none — model judgment)* |
| both patches reproduce the live tree byte-exact | 🤖 model inference | *(none — model judgment)* |
| loopback reverted to vanilla 127.0.0.1 at :81; no 0.0.0.0 remains | 🤖 model inference | *(none — model judgment)* |
| loopback branch dead under lockdown | 🤖 model inference | *(none — model judgment)* |
| runtime socket checks not executed this pass | 🤖 model inference | *(none — model judgment)* |


---
**How to verify this document:**
`📄 stated in input` — the model's phrasing of something your source text said.
Find the matching line in the original to verify.
`🤖 model inference` — the model's own judgment or synthesis. Treat as opinion,
not measurement. Re-run on the same input and check whether specific numbers
stay consistent between runs.


---

# ═══ MERGED DOCUMENT: 09-remote_developer.md (verbatim · sha256:9acbad54386d659f · merged 2026-08-04) ═══

# 09.REMOTE — Remote Automation Lockdown (Marionette + WebDriver BiDi Remote Agent), with the RemoteAgent loopback-poison autopsy

> Generated 2026-08-04 | Source: `09.REMOTE`

---

## Purpose

This topic hard-disables both of Firefox's browser-automation entry points — Marionette and the WebDriver BiDi Remote Agent — at the source level, so neither can be enabled by preference, environment variable, or command-line flag. It also records the project's first poison autopsy: an unmarked, security-relevant edit to the RemoteAgent loopback allow-list (127.0.0.1 -> 0.0.0.0, with a matching falsified comment) that was caught, proven to be poison, and reverted on 2026-08-03. Trust level: these files run in the privileged parent process; the entire aim is to deny any untrusted caller a lever to switch the automation channels on.

## Design Rationale

A single off-switch is defeatable: a pref can be flipped, a constructor default can be flipped, a CLI flag can be passed. The design therefore dead-codes three independent activation surfaces per channel — the construction default, the setter body, and the command-line-startup branch — so defeating the lockdown requires editing source and rebuilding, not changing any runtime state. Dead-coding is chosen over deletion so the class shape (getters, setters, observer) still satisfies callers and the diff stays small and auditable. Provenance markers (GORILLA UNLEASHED - PHYSICAL LOCK) are mandatory on every edit; the loopback poison's ABSENCE of a marker is precisely what flagged it as injected rather than intentional.

## Architecture

- **Pattern:** Two XPCOM singleton services (Marionette, RemoteAgent) driven by nsIObserver 'command-line-startup' notifications; lockdown is source-level dead-coding at three sites per service.
- **Trust boundary:** The code must trust no external activation input — env vars ENV_ENABLED / ENV_ALLOW_SYSTEM_ACCESS, the --marionette and --remote-debugging-port flags, or any caller of the setters. Post-patch it trusts none of them: each is read-and-discarded or dead-ended.
- **Attack surface:** Stock Firefox exposes two listening TCP sockets (Marionette default 2828; Remote Agent CDP/BiDi default 9222) plus the setters and the env/flag activation path. Post-patch the sockets are never bound because the enable path never runs, and the activation inputs are inert. Residual surface: source edit + rebuild only.
- **Dependencies:** `Services.env`, `Services.obs`, `lazy.Deferred (remote/shared/Sync.sys.mjs)`, `nsICommandLine (subject.handleFlag)`, `lazy.HttpServer (httpd.sys.mjs) — reached only via the disabled #listen() path`

## Flags & Configuration

| Name | Type | Default | Effect | Notes |
|------|------|---------|--------|-------|
| `--marionette` | `bool` | `ignored (forced off)` | Stock: enables Marionette. Here read via subject.handleFlag("marionette", false) then discarded; this.enabled forced false. | Flag still parses, so downstream option handling is unaffected. |
| `--remote-debugging-port` | `int` | `ignored (forced off)` | Stock: enables the Remote Agent on the given port. Here #handleRemoteDebuggingPortFlag runs but its result is discarded; #enabled forced false. | No socket bound. |
| `ENV_ENABLED (MOZ_MARIONETTE)` | `env` | `ignored` | Stock: seeds this.enabled at construction. Here replaced by this.enabled = false. | env read removed from the constructor. |
| `ENV_ALLOW_SYSTEM_ACCESS` | `env` | `ignored` | Stock: seeds #allowSystemAccess and the setter writes it back. Here replaced by #allowSystemAccess = false; the setter's Services.env.set(...) is removed. | Build no longer writes the system-access env marker. |

## API Surface

| Symbol | Description | Side Effects |
|--------|-------------|--------------|
| `Marionette set enabled(value)` | dead-ended; ignores value, forces _enabled=false | none (formerly logged and set _enabled) |
| `RemoteAgent set allowSystemAccess(value)` | dead-ended; forces #allowSystemAccess=false | none (formerly Services.env.set(ENV_ALLOW_SYSTEM_ACCESS, "1")) |
| `RemoteAgent get allowHosts()` | unchanged from vanilla; returns #allowHosts, or ["localhost"] iff bound to a loopback address, else [] | reads #server and #host; DEAD under lockdown (#allowHosts forced null, #server null) |
| `RemoteAgent #listen(port)` | binds lazy.HttpServer and assigns #server | opens a TCP socket — never called under lockdown (#enabled forced false gates it) |

## Kill Switches

### `Marionette.sys.mjs:58 (constructor)`
- **Condition:** every startup
- **Effect:** this.enabled = false at construction
- reversible
- marker :54; replaces this.enabled = Services.env.exists(ENV_ENABLED)

### `Marionette.sys.mjs:78-80 (set enabled)`
- **Condition:** any write to Marionette.enabled
- **Effect:** forces this._enabled = false
- reversible
- marker :78; removes early-return + logger.info

### `Marionette.sys.mjs:124-127 (command-line-startup)`
- **Condition:** startup flag parse
- **Effect:** reads --marionette then forces this.enabled = false
- reversible
- marker :124

### `RemoteAgent.sys.mjs:51 (constructor)`
- **Condition:** every startup
- **Effect:** #allowSystemAccess = false
- reversible
- marker :47; replaces Services.env.exists(ENV_ALLOW_SYSTEM_ACCESS). #enabled = false at :54 is the upstream default, preserved

### `RemoteAgent.sys.mjs:102-105 (set allowSystemAccess)`
- **Condition:** any write
- **Effect:** forces #allowSystemAccess = false; removes Services.env.set
- reversible
- marker :103

### `RemoteAgent.sys.mjs:430-440 (command-line-startup)`
- **Condition:** startup
- **Effect:** runs the flag handlers for side effects but discards results; forces #allowHosts=null, #allowOrigins=null, allowSystemAccess=false, #enabled=false
- reversible
- marker :430

## Dead Code

- **`RemoteAgent.sys.mjs:65-92 get allowHosts() loopback branch (loopbackAddresses at :81)`** — reached only when #server is truthy (:70); #server is assigned only inside #listen() (:279), called only from the enable path (:468) gated by #enabled (:442), which is forced false (:440). #allowHosts is also forced null (:437), so the early return at :66 never fires either. (risk: if the lockdown is ever reverted this getter becomes live again; keeping the list vanilla-correct (127.0.0.1) matters at that point. This is exactly where the poison sat.)
- **`RemoteAgent.sys.mjs:233-298 #listen() / HttpServer bind`** — never invoked under lockdown (risk: removing it would break vanilla shape and any future re-enable path; keep.)

## Performance

- **CPU:** Not measured; both services skip their enable path at startup.
- **MEMORY:** Not measured.
- **IO:** Two TCP listeners (2828, 9222) are never bound; no runtime measurement was taken.
- **NOTES:** No before/after profiling was performed for this topic.

## Security

- **Remote execution:** Removes both browser-automation channels. WebDriver BiDi / Marionette can drive navigation, evaluate script, and (with system access) perform privileged operations; all are denied because the channels never enable.
- **Data handling:** No data is collected, logged, or transmitted by these changes. Removing Services.env.set(ENV_ALLOW_SYSTEM_ACCESS, "1") means the build no longer writes that env marker.
- **Attack surface:** Two fewer reachable listening sockets at runtime; env/flag/setter activation inputs inert. The reverted loopback poison would, IF the lockdown were removed, have inverted the loopback check: whitelisting a 0.0.0.0 (all-interfaces, world-reachable) bind as 'localhost' while failing to recognise a genuine 127.0.0.1 bind. Reverted 2026-08-03; no 0.0.0.0 remains in either file (verified 2026-08-04).
- **Notes:** allowHosts governs INBOUND host whitelisting for the Remote Agent server. The project's outbound host-blackhole ('kill-categories') is OUTBOUND-only and is therefore not a compensating control here — it would not have mitigated the poison. (Basis: architectural read; blackhole code not re-inspected this pass.) Loopback definition authority: in-source Bug 1220810 comment at RemoteAgent.sys.mjs:78-80 ('localhost is guaranteed to resolve to a loopback address (127.0.0.1 or ::1)'), consistent with RFC 5735, which classifies 127.0.0.0/8 as Loopback and 0.0.0.0/8 as 'this host on this network' (not loopback).

## Error Conditions

| Error | Cause | Remedy |
|-------|-------|--------|
| `Selenium/WebDriver 'connection refused'` | no Marionette/BiDi socket bound | expected; use stock Firefox for automation |
| `PRECHECK P1-001 'target path is missing / patch will not apply'` | FALSE POSITIVE — the RemoteAgent patch's git header carries a tab+timestamp ('RemoteAgent.sys.mjs\t2026-08-03 12:43:46...'), which the precheck path-parser mis-reads as part of the filename | none required for correctness; patch(1) applies it byte-exact (verified 2026-08-04). Optionally strip the tab+timestamp to match the sibling Marionette patch header |

## Tasks

### Verify both patches reproduce the live tree byte-exact

Confirm the .patch files are true records of the tree and nothing has drifted. Stage the vanilla files, apply both patches, then compare against the live tree (this is the exact check run 2026-08-04, which returned BYTE-EXACT MATCH for both):

```bash
VAULT=<vault>
LIVE=the source tree
ROOM=patches/new.patches/09.REMOTE
mkdir -p /tmp/rt/remote/components
cp "$VAULT"/remote/components/{Marionette,RemoteAgent}.sys.mjs /tmp/rt/remote/components/
( cd /tmp/rt && patch -p1 < "$OLDPWD/$ROOM/remote_components_RemoteAgent.sys.mjs.patch" \
               && patch -p1 < "$OLDPWD/$ROOM/remote_components_Marionette.sys.mjs.patch" )
cmp /tmp/rt/remote/components/RemoteAgent.sys.mjs "$LIVE"/remote/components/RemoteAgent.sys.mjs
cmp /tmp/rt/remote/components/Marionette.sys.mjs "$LIVE"/remote/components/Marionette.sys.mjs
```

**Prerequisites:**
- vanilla vault tree (SafetyVault.Firefox/firefox-main)
- live tree the source tree
- patch(1), cmp

**Step 1:** Stage the vanilla remote/components/{Marionette,RemoteAgent}.sys.mjs into a work dir, then: patch -p1 < remote_components_RemoteAgent.sys.mjs.patch (and the Marionette patch)
  - Expected: both apply with no .rej
**Step 2:** cmp work/remote/components/RemoteAgent.sys.mjs remote/components/RemoteAgent.sys.mjs (and Marionette)
  - Expected: BYTE-EXACT MATCH for both (verified 2026-08-04)

**After this task:** (vanilla + patch) == live for both files.

### Confirm the loopback poison is reverted and absent

The RemoteAgent loopback list was poisoned 127.0.0.1 -> 0.0.0.0 and reverted 2026-08-03.

**Prerequisites:**
- live tree

**Step 1:** grep -n loopbackAddresses remote/components/RemoteAgent.sys.mjs
  - Expected: ["127.0.0.1", "[::1]"] at line 81; vanilla comment at :79
**Step 2:** grep -rn '0.0.0.0' remote/components/RemoteAgent.sys.mjs remote/components/Marionette.sys.mjs
  - Expected: no matches

**After this task:** No 0.0.0.0 remains; loopback list is vanilla.

### Prove no automation socket binds at runtime

Static analysis says #listen() never runs; confirm dynamically on a build.

**Prerequisites:**
- a built binary

**Step 1:** ss -tlnp | grep -E ':2828|:9222' on a running build
  - Expected: no output
**Step 2:** relaunch with --marionette --remote-debugging-port=9222, re-run the ss command
  - Expected: still no output

**After this task:** No Marionette/BiDi socket. NOTE: not executed in this documentation pass (no build was run).

## Troubleshooting

**Symptom:** precheck reports P1 'patch will not apply'
**Cause:** the timestamped git header on the RemoteAgent patch is mis-parsed by the rule
**Remedy:** ignore (the patch applies), or strip the tab+timestamp from the ---/+++ lines
**Verify:** patch -p1 --dry-run < remote_components_RemoteAgent.sys.mjs.patch succeeds

**Symptom:** loopbackAddresses shows 0.0.0.0 after a rebase
**Cause:** an upstream rebase overwrote the 2026-08-03 revert
**Remedy:** restore ["127.0.0.1", "[::1]"] and the comment
**Verify:** grep shows 127.0.0.1; no 0.0.0.0 in either file

**Symptom:** about:support shows Remote Agent / Marionette enabled
**Cause:** a lockdown site was lost in a rebase
**Remedy:** reapply the three sites per file
**Verify:** grep confirms three PHYSICAL LOCK markers per file

## Technical Debt

🟡 **LOW** — RemoteAgent patch header carries a tab+timestamp, unlike the sibling Marionette patch; it trips the precheck path-parser (P1-001, a false positive) → regenerate/normalise the header to '--- a/... / +++ b/...' with no timestamp so precheck is clean and the two sibling patches are consistent
🟡 **LOW** — allowHosts loopback correctness is guaranteed only by the lockdown staying in place (dead today, live if reverted) → keep the value vanilla-correct and add a rebase guard / self-test asserting loopbackAddresses === ["127.0.0.1", "[::1]"] and enabled states false
🟠 **MEDIUM** — No runtime self-test asserts the disabled state → add the preflight described at 00_REMOTE_HISTORY_AND_ROADMAP.md:414 (assert both report disabled; no 2828/9222 socket)
🟡 **LOW** — Automated-testing capability removed (accepted trade-off) → document it; run CI automation on stock Firefox elsewhere

## Impact If Removed

Reverting these edits restores Firefox's stock behaviour: --marionette / --remote-debugging-port (or the env vars) would re-enable the automation channels and bind listening sockets, and the setters would again allow a runtime enable. If the lockdown were reverted while the loopback poison were also reintroduced, the Remote Agent's allowHosts check would misclassify a 0.0.0.0 (all-interfaces) bind as loopback. Any dependent tooling (Selenium/WebDriver) would start working again — as would any local attacker able to reach the socket.

## Claim Sources

| Claim | Basis | Evidence |
|-------|-------|----------|
| Marionette enabled forced false at construction | 📄 stated in input | this.enabled = false; |
| Marionette setter dead-ended | 📄 stated in input | This setter is now a dead end. Nothing can enable Marionette. |
| --marionette read and discarded | 📄 stated in input | The command line flag --marionette is now ignored and discarded. |
| RemoteAgent #allowSystemAccess forced false at construction | 📄 stated in input | this.#allowSystemAccess = false; |
| RemoteAgent setter removes Services.env.set | 📄 stated in input | This setter is now a dead end. Nothing can grant system access. |
| command-line-startup forces #allowHosts=null, allowSystemAccess=false, #enabled=false | 📄 stated in input | this.#enabled = false; |
| RemoteAgent patch header carries a tab+timestamp | 📄 stated in input | --- a/remote/components/RemoteAgent.sys.mjs	2026-08-03 12:43:46.379563830 +0100 |
| loopback list is vanilla 127.0.0.1 at RemoteAgent.sys.mjs:81 in the live tree | 🤖 model inference | *(none — model judgment)* |
| both patches reproduce the live tree byte-exact | 🤖 model inference | *(none — model judgment)* |
| loopback branch is dead under lockdown | 🤖 model inference | *(none — model judgment)* |
| RFC 5735: 127.0.0.0/8 loopback, 0.0.0.0/8 not loopback | 🤖 model inference | *(none — model judgment)* |
| outbound blackhole is not a compensating control for inbound allowHosts | 🤖 model inference | *(none — model judgment)* |
| no performance measurements taken | 🤖 model inference | *(none — model judgment)* |


---
**How to verify this document:**
`📄 stated in input` — the model's phrasing of something your source text said.
Find the matching line in the original to verify.
`🤖 model inference` — the model's own judgment or synthesis. Treat as opinion,
not measurement. Re-run on the same input and check whether specific numbers
stay consistent between runs.

*Auto-generated DITA-structured developer documentation.*


---

# ═══ MERGED DOCUMENT: 09-remote_layman.md (verbatim · sha256:d846d3064c5c6004 · merged 2026-08-04) ═══

# Bolting Firefox's Two Remote-Control Hatches Shut — and the Booby-Trap We Found Wired to One of Them — Plain Language Guide

> Generated 2026-08-04 from `09.REMOTE`

---

## Should You Run This?

Run it — if you do not need browser-automation tools. This change only ever removes a remote-control capability and closes an attack surface; it never adds data collection. If you rely on Selenium, WebDriver, or remote debugging, this specific build is not for you, and that is by design.

## Worst Case, Honestly

The realistic worst case is a limitation, not a leak: you cannot use Selenium, WebDriver, or remote-debugging tools on this build, because the machinery they connect to never turns on. The booby-trap's worst case only existed IF someone later removed the lockdown; on that day it could have let a browser opened to the whole network be mislabelled as 'only this computer.' That door is welded shut today and the booby-trap has been reverted, so the standing risk from it is none.

## What Data This Touches

Nothing here sends any of your data anywhere. These changes REMOVE two ways an outside program could reach in and drive your browser; they add no new data collection, no phone-home, no logging. The build even stops writing one system marker it used to write (the 'system access allowed' environment flag). If anything, this closes two channels that could have been used to watch or control what you do.

## Before You Trust It

You are trusting a stranger's build with your machine. These checks take a minute and need only a terminal and the files.

**Step 1:** In the folder patches/new.patches/09.REMOTE run: grep -n "PHYSICAL LOCK" remote_components_Marionette.sys.mjs.patch remote_components_RemoteAgent.sys.mjs.patch
  - Look for: Three 'GORILLA UNLEASHED - PHYSICAL LOCK' comments in each file — the labelled locks.
**Step 2:** In the Firefox source tree run: grep -n loopbackAddresses remote/components/RemoteAgent.sys.mjs
  - Look for: The list must read ["127.0.0.1", "[::1]"]. If it says 0.0.0.0, the booby-trap is back and something is wrong.
**Step 3:** If you have the build, launch it and run: ss -tlnp | grep -E ':2828|:9222'
  - Look for: No output. Those are the Marionette and Remote Agent ports; nothing should be listening.
**Step 4:** Try to defeat it: launch firefox --marionette --remote-debugging-port=9222, wait a few seconds, run the ss command again
  - Look for: Still no output — the flags were heard and ignored.

## The Big Picture

Firefox ships with two built-in "service hatches" that let another program drive the browser from outside — open links, read pages, take screenshots, change settings — with no person at the keyboard. They are called Marionette and the Remote Agent (also known as WebDriver BiDi). They exist for good reasons: automated testing and developer tools such as Selenium use them. But a hatch that lets a program drive your browser is exactly what an attacker wants too.

This build welds both hatches shut. Not "off by default" (a setting could flip that back). Not "off unless you pass a flag" (a launcher shortcut could pass the flag). Off at the source, in three separate places per hatch, so no setting, no command-line flag, and no environment variable can wake either one.

There is a second half to this story. While clearing this room we found a booby-trap wired next to one hatch: someone had quietly changed a safety list so the address 0.0.0.0 — which means "every network card on the machine, reachable from the whole network" — was being treated as if it meant "only this computer." It did no harm, because the hatch it sat behind is welded shut, but it was wrong, it was unlabelled, and it was put back to the correct value on 2026-08-03. This is the first booby-trap this project caught, dissected, and filed as a case study.

## Key Concepts

| Name | What It Means | Real-World Comparison |
|------|--------------|------------------------|
| `Marionette` | Firefox's older remote-control system, the one Selenium talks to | the staff door at the back of a shop |
| `Remote Agent (WebDriver BiDi)` | Firefox's newer, standardised remote-control and remote-debugging system | a second staff door — newer design, same kind of access |
| `Command-line flag` | a word you add when launching a program to switch a feature on, like --marionette | a password shouted at the door; this build hears it and ignores it |
| `loopback address (127.0.0.1)` | an address that means 'this same computer, nothing outside' | posting a letter to yourself in your own mailbox — it never leaves the house |
| `0.0.0.0` | the 'all network cards' address; a server on it answers anyone who can reach the machine | leaving your front door open to the whole street, not only your own hallway |

## How It Works — Step by Step

### Step 1: Two hatches, both built in

Each time Firefox starts it creates one Marionette object and one Remote Agent object. Each keeps its own on/off switch. In stock Firefox those switches read an environment variable or a command-line flag at startup to decide whether to turn on.

### Step 2: Lock one — hard-wire the switch to OFF

At the moment each object is built, its switch is set to false and the line that used to read the environment variable is gone. It is like a light switch screwed permanently to 'off'.

### Step 3: Lock two — dead-end the switch

Each object has a 'setter', the piece of code other code calls to flip the switch on. Its insides were replaced: whatever you pass it, it sets the switch to false. It is like a switch you can still flick, but the wire behind it goes nowhere.

### Step 4: Lock three — hear the flag, throw it away

At startup the browser still reads --marionette and --remote-debugging-port, but the code that used to act on them now discards them and forces the switch to false again. The door hears 'open sesame' and stays shut.

### Step 5: Why no socket ever opens

The Remote Agent only opens a listening network socket inside a function that runs only when its switch is on. Because the switch is welded off, that function never runs and no socket is ever opened. Nothing is listening for a connection.

### Step 6: The booby-trap, and why it was harmless — then removed anyway

One safety list inside the Remote Agent decides which addresses count as 'only this computer.' Someone had changed 127.0.0.1 (correct) to 0.0.0.0 (wrong) and edited the nearby comment to hide it. That list is only ever read after the server opens — and the server never opens — so it was dead code that never ran. We still set it back to 127.0.0.1 on 2026-08-03, because leaving a wrong, unlabelled safety value in the code is how the next person gets hurt.

## Quirky Things Worth Knowing

### The tools connect to nothing and don't complain

Point Selenium at this build and it fails to connect. The browser does not warn you; from its side everything is normal. That is expected, not a bug.

### Three locks sounds like overkill — it isn't

Any one lock alone could be undone: a setting could re-enable it, the constructor could start it on, the flag could switch it. Only all three together actually keep it shut.

### A harmless bug is still a bug worth fixing

The 0.0.0.0 booby-trap could not fire while the hatch is welded shut. We reverted it anyway. A wrong value that is 'safe for now' becomes dangerous the moment someone changes the thing that was keeping it safe.

### Nothing was deleted — it was dead-ended

The code still looks almost the same shape as Mozilla's. That is deliberate: deleting parts could crash other code that expects them to exist. Dead-ending keeps the shape and removes the effect.

## What This Means For You

### Battery, Processor & Memory

Not measured. In principle two background services never start and never sit waiting for connections, which is a tiny saving; no before/after numbers were taken, so treat the effect as too small to have been measured.

### Speed

Not measured. Startup skips setting up two remote-control channels, but no timing was recorded, so no speed claim is made.

### Your Privacy

This is the real win. Two channels that could let an outside program drive or inspect your browser are closed at the source. A remote-control hatch on an internet-facing browser is exactly the kind of thing a targeted attack looks for.

### Your Internet

One fewer thing your browser could be made to listen for on the network. No change to your normal browsing traffic.

## The Off Switch

**What it is:** The 'off' here is the whole point — the switch is welded off in three places per hatch, across two source files (Marionette.sys.mjs and RemoteAgent.sys.mjs). There is no user-facing button; reversing it means editing the source and rebuilding.

**Without it:** Without these locks, launching Firefox with --marionette or --remote-debugging-port=9222 would open a listening socket that any program able to reach it could use to drive the browser.

**Think of it like:** Not one lock but three: a bolt, a chain, and welding the hinge — plus we found and peeled off a fake 'this is fine' sticker someone had stuck over a gap beside the door.

## Use this build knowing remote control is off

**Before you start:**
- The Gorilla Unleashed Firefox 154 build installed
- No dependency on Selenium / WebDriver / remote-debugging tools

**Step 1:** Use Firefox normally.
  - You should see: Everything a person does by hand works as usual.
**Step 2:** If you need browser automation, use a separate, stock Firefox for that task.
  - You should see: You keep this hardened build for daily use and do automation elsewhere.

## If Something Goes Wrong

**Selenium or WebDriver cannot connect to this build**
That is the lockdown working — the machinery it connects to never starts
What to do: Use a separate stock Firefox for automation; do not re-enable it here.

**grep shows 0.0.0.0 in loopbackAddresses**
The reverted booby-trap has come back, most likely because an upstream rebase overwrote the fix
What to do: Restore the list to ["127.0.0.1", "[::1]"] and the nearby comment, and check why the revert was lost.

**A port shows up under ss after launching**
Either a different remote feature (such as the DevTools remote server) or a broken lockdown
What to do: Confirm the three locks are present in both files, rebuild clean, and check devtools.debugger.remote-enabled is false.

## Why a Developer Would Do This

A hardened, single-user browser should not answer to remote puppet-strings. A developer disables these two hatches — rather than trusting a preference to stay off — because settings and flags are exactly the levers an attacker or a careless script would pull. Reverting the 0.0.0.0 booby-trap matters for the same reason: safe-for-now is not safe.

## Why It Matters That You Can Read This

You do not have to take any of this on faith. You can open the two files yourself and see the switch set to false, see the dead-ended setter, and see the flag being thrown away. You can also see that the safety list now reads 127.0.0.1, not 0.0.0.0. In a closed browser, 'we disabled remote control' is a marketing line you cannot check. Here it is a handful of lines you can read — and a booby-trap someone already found, proved wrong, and wrote up for you.

## Glossary

**Marionette** — Firefox's older automation backend, the one Selenium's Firefox driver talks to.

**Remote Agent / WebDriver BiDi** — Firefox's newer, standardised remote-control and remote-debugging system.

**loopback address** — An address meaning 'this same computer only'; its usual number is 127.0.0.1.

**0.0.0.0** — The 'all network interfaces' address; a server bound to it can be reached from the whole network, not only this machine.

**Dead-coded / dead-ended** — Code that still exists but can never reach the state where it would take effect.

**Setter** — The piece of code other code calls to change a value; here changed so it always forces 'off'.

## Claim Sources

| Claim | Basis | Evidence |
|-------|-------|----------|
| Marionette switch hard-set false at construction | 📄 stated in input | this.enabled = false; |
| Marionette setter dead-ended | 📄 stated in input | This setter is now a dead end. Nothing can enable Marionette. |
| --marionette flag read and discarded | 📄 stated in input | The command line flag --marionette is now ignored and discarded. |
| Remote Agent system access hard-set false | 📄 stated in input | this.#allowSystemAccess = false; |
| Remote Agent startup forces #enabled false | 📄 stated in input | this.#enabled = false; |
| Three PHYSICAL LOCK markers per file | 📄 stated in input | GORILLA UNLEASHED - PHYSICAL LOCK |
| loopback list is vanilla 127.0.0.1 in the live tree | 🤖 model inference | *(none — model judgment)* |
| 0.0.0.0 is all-interfaces; 127.0.0.1 is loopback | 🤖 model inference | *(none — model judgment)* |
| loopback poison reverted 2026-08-03 | 🤖 model inference | *(none — model judgment)* |
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

# ═══ MERGED DOCUMENT: PRECHECK.md (verbatim · sha256:fe65becc93a603ec · merged 2026-08-04) ═══

# Offline Pre-Check: 09-remote

*Generated 2026-08-04 07:05:01 by rules only. No model was involved, so everything below is a deterministic finding about the files as they are on disk.*

## Files Scanned

| File | Language | Lines | Code | Complexity | SHA-256 |
|---|---|---|---|---|---|
| `remote_components_Marionette.sys.mjs.patch` | patch | 46 | 39 | 4 | `809097a96e171e19` |
| `remote_components_RemoteAgent.sys.mjs.patch` | patch | 59 | 53 | 4 | `22173d4177e0874f` |

## Findings

🔴 P0: 0 · 🟠 P1: 1 · 🟡 P2: 0 · 🟢 P3: 0

### 🟠 P1-001 — P1

- **Plain English:** A repair instruction points at a room that does not exist in the current building (remote/components/RemoteAgent.sys.mjs	2026-08-03 12:43:46.381629057 +0100). Upstream moved or renamed it, so the repair cannot be carried out.
- **Technical:** remote_components_RemoteAgent.sys.mjs.patch: target path remote/components/RemoteAgent.sys.mjs	2026-08-03 12:43:46.381629057 +0100 is missing under the source tree. The patch will not apply.
- **Fix:** Re-locate the code in the new tree and regenerate the patch against it.
- **Effort:** 1h


---

# ═══ SUPERSEDED 2026-08-04 — gen-1 documentation set (retained as autopsy exhibit) ═══

> The block below is the **previous** master log (merged 2026-08-02). It is kept **verbatim**
> and unedited for the record. Its merged `09-remote.AUDIT.md` reported **"No defects" /
> "Audit Status: PASS" / 96% ready**, and its merged `09-remote.PRECHECK.md` reported
> **"Rule Findings (0)"**. Both were **FALSE**: the loopback-address poison (see the
> regeneration banner at the top, and `POR_DRAFT_2026-08-03.md`) was already present at that
> precheck time — the recorded gen-1 sha256(16) `db4b74fb87a23476` for the RemoteAgent patch
> proves the poison predated the "PASS". Retained deliberately as the autopsy's exhibit of a
> false-VERIFIED report. **Do not treat anything below as current status.**

<details>
<summary>gen-1 master log (2026-08-02) — SUPERSEDED, click to expand</summary>

# 09.REMOTE — Master Project Log

*Created 2026-08-02 by consolidating this folder's documentation set (merged verbatim below). Policy: one master project log per folder.*


---

# ═══ CONSOLIDATION 2026-08-02 — side documents merged VERBATIM below; originals deleted (recoverable: merged-docs-backup-2026-08-02.tar.gz + git history) ═══


---

# ═══ MERGED DOCUMENT: 09-remote.AUDIT.md (verbatim · sha256:345f52a54dba631d · merged 2026-08-02) ═══

# IBM-Style Audit Report: 09-remote

## SECTION A: DOCUMENT CONTROL

| Attribute | Value |
|---|---|
| **Target Category** | 09-remote |
| **Files Scanned** | see payload |
| **Baseline** | Firefox 154 (mozilla-central) |
| **Date / Time** | 2026-07-16 22:42:15 |
| **Audit Status** | PASS |

## SECTION B: EXECUTIVE SUMMARY (Track A — Layman)

Two of Firefox's built-in remote-control backdoors (Marionette and Remote Agent / WebDriver BiDi) are permanently disabled — at three layers each — so nothing can drive or inspect the browser from outside. Trade-off: no browser-automation tooling on this build.

## SECTION C: TECHNICAL SUMMARY (Track B — Developer)

Three-site dead-coding per channel: instance `enabled` init false, setter dead-ended, CLI flag branch inert. Applied to Marionette.sys.mjs and RemoteAgent.sys.mjs. Two listening sockets removed. Automation-attack surface eliminated.

## SECTION D: DETECTED DEFECTS

*No defects detected by rules or model.*

## SECTION E: PRODUCTION READINESS ASSESSMENT

- **Overall readiness:** 🟢 96%
- **Done:**
  - [x] Marionette three-layer lockdown
  - [x] Remote Agent (WebDriver BiDi) three-layer lockdown
  - [x] --marionette and --remote-debugging-port CLI flags dead-coded
  - [x] Trade-off documented
- **To Do:**
  - [ ] P3: automated integration test that `firefox --marionette` binds no socket

## POSITIVE OBSERVATIONS

- ✅ Three-layer redundancy per channel — any single layer would be defeatable in isolation.
- ✅ Deliberate dead-coding rather than deletion — preserves the shape of the API so dependent code does not crash.
- ✅ Same architectural pattern as 12.MOZAMBIQUE.DRILL — coherent, not ad-hoc.

## VERIFICATION COMMANDS

```bash
ss -tlnp | grep -E ':2828|:9222'   # expect no output
firefox --marionette --remote-debugging-port=9222 & sleep 3; ss -tlnp | grep -E ':2828|:9222'   # still no output
grep -n 'enabled' remote/components/Marionette.sys.mjs
```



---

# ═══ MERGED DOCUMENT: 09-remote.DEVELOPER.md (verbatim · sha256:d8e51947c010e000 · merged 2026-08-02) ═══

# Remote Automation Lockdown — Marionette + Remote Agent Hard Disable — Developer Track

> **Topic:** `09-remote` · **Files:** `remote/components/Marionette.sys.mjs`, `remote/components/RemoteAgent.sys.mjs`
> **Generated:** 2026-07-16

---

## Module Summary

Three-layer dead-code lockdown of both browser-automation channels. Marionette: instance `enabled = false` at construction, `set enabled(value)` setter body removed, `--marionette` CLI flag branch dead-coded. Remote Agent (WebDriver BiDi): identical treatment with `#enabled = false`, `#allowSystemAccess = false`, setters dead-ended, `--remote-debugging-port` branch dead-coded. Trade-off explicit: browser is unusable with Selenium/WebDriver by design.

## Architecture

- **Pattern:** Belt-and-suspenders dead-coding at three independent activation surfaces per channel.
- **Trust Boundary:** Removes a browser-automation channel that would otherwise be a listening socket. Substantial attack-surface reduction for targeted-attack scenarios.
- **Attack Surface:** Two fewer listening TCP sockets in the browser process.

## Kill Switches

### `Marionette.sys.mjs — `enabled` init + setter + CLI parser branch` — HARD ⚠️

- **Condition:** compile-time (source-level dead-coding)
- **Effect:** Marionette cannot be turned on by any means short of source edit + rebuild.
- **Reversibility:** reversible
- **Notes:** Rebuild required.

### `RemoteAgent.sys.mjs — `#enabled` init + `#allowSystemAccess = false` + setters + CLI parser branch` — HARD ⚠️

- **Condition:** compile-time
- **Effect:** WebDriver BiDi Remote Agent cannot be turned on. Same three-layer redundancy.
- **Reversibility:** reversible
- **Notes:** Rebuild required.

## Performance Profile

- **CPU:** Marginal.
- **Memory:** Marginal.
- **I/O:** One or two fewer TCP listeners.
- **Timer Interval:** N/A

## Security Analysis

### User Profiling

N/A

### Targeting

Removes a class of remote-attack surface. If an attacker reaches localhost (via XSS-in-browser, malicious-extension escape) they cannot enable a browser-automation socket.

### Trust Chain

N/A

### Abuse Potential

Substantial reduction: browser-automation-socket abuse is a documented attack pattern for targeted browser exploitation.

## Implementation Flow

1. **`Marionette constructor`** — Sets `this.enabled = false`.
   *Side effects:* Instance starts disabled.
2. **`Marionette setter`** — Setter body dead-ended.
   *Side effects:* External code calling `Marionette.enabled = true` has no effect.
3. **`startup CLI parse for --marionette`** — Flag parses but branch does nothing.
   *Side effects:* No socket bound.
4. **`RemoteAgent equivalent (three sites)`** — Same pattern for WebDriver BiDi.
   *Side effects:* No listening socket.

## Technical Debt

🟢 **ACCEPTED** — Automated-testing capability gone — cannot self-verify with Selenium
  - *Recommendation:* Documented trade-off. Testing lives elsewhere (headless CI on stock Firefox).

## Impact If Removed / Disabled

Selenium/WebDriver/BiDi tooling would work — and so would any attacker who could poke localhost.

## Testing Notes

`ss -tlnp | grep -E ':2828|:9222'` — expect no output. Try `firefox --marionette --remote-debugging-port=9222` — flags accepted, no sockets bound.

## Changelog Notes

Locked down 2026-07-06. Cross-references 12.MOZAMBIQUE.DRILL for parallel Normandy/Nimbus lockdown pattern.

---
*Developer Track. Human Track twin: `09-remote.LAYMAN.md`.*


---

# ═══ MERGED DOCUMENT: 09-remote.LAYMAN.md (verbatim · sha256:e187874301343383 · merged 2026-08-02) ═══

# 🧍 Remote Control Lockdown — Bolting Marionette and Remote Agent Shut — Plain English Guide

> *Topic `09-remote` of the Gorilla Unleashed Firefox 154 build · Written for everyone · 2026-07-16*

---

## 🌍 The Big Picture

Firefox ships with two hidden 'service hatches' called **Marionette** and the **Remote Agent** (WebDriver BiDi). These exist so automated testing tools like Selenium can drive the browser from outside — click things, read pages, take screenshots. They are legitimate developer tools. They are also, from the outside, exactly the kind of hatch an attacker would want to walk through: something that can drive the browser without a person at the keyboard.

This patch group **bolts both hatches shut and throws away the key.** Not disabled by a preference (could be flipped back on) and not disabled by a command-line flag (could be re-enabled by launching differently). Physically dead-coded at three points per channel: the internal `enabled` flag is initialised `false`; the setter that would flip it back is dead-ended; the command-line flags (`--marionette`, `--remote-debugging-port`) are silently discarded.

**Trade-off worth being honest about:** you cannot use Selenium, WebDriver, or any browser-automation tool with this build. If you need those tools, this build is not for you.

## 🎭 The Main Characters

| Name | What It Is | Real-World Comparison |
|---|---|---|
| **Marionette** | Firefox's older browser-automation backend used by Selenium and internal Mozilla tooling | The service door in the back — for staff, not for customers |
| **Remote Agent / WebDriver BiDi** | The newer W3C-standardised remote-debugging + automation protocol | The other service door — different design, same access |
| **--marionette / --remote-debugging-port** | The command-line switches that would normally wake either hatch up | The words 'open sesame' — this build hears them and ignores them |

## 🔢 How It Works — Step by Step

### Step 1: Internal `enabled` field set to false at construction

Both Marionette and Remote Agent are singleton services that store their own on/off state. That state is now hardcoded false at instantiation.

### Step 2: The setter is dead-ended

Both classes have a setter method that could flip the flag on. The setter body is now empty. Even if code paths call it, the flag stays false.

### Step 3: The command-line flags are silently discarded

The parsers still exist (removing them ripples through option-parsing), but the branches that would act on the flags are dead-coded. The flags parse successfully; they just do nothing.

## 🤔 Quirky Things Worth Knowing

### ⚠️ Three shots to be sure

Just setting a pref would not be enough (prefs get reset). Just dead-coding the setter would not be enough (the constructor could initialise to true). Just discarding the flag would not be enough (the pref could still turn it on). All three together = actually dead.

### ⚠️ The tooling still 'appears' to work — it just does nothing

Selenium tools that try to connect get a connection failure. But the browser does not error out or warn; from its own perspective, everything is normal.

## 💻 What Does This Mean For YOU?

### 🔋 Battery, Speed & Memory

One less background service listening on a socket. Tiny.

### ⚡ Speed

Marginal — startup does not initialise the WebDriver protocol.

### 🕵️ Your Privacy

This is the topic where a real attack surface is closed. A remote-control hatch on the internet-facing browser is exactly the kind of thing a targeted attack looks for.

### 🌐 Your Internet

One fewer listening socket.

## 🔴 The Kill Switch — Explained

**What it is:** The lock is at the source level, in three redundant places per channel. To reverse: rebuild with all three restored.

**Without it:** Firefox starts a listening socket for Marionette / Remote Agent on any invocation with the flags set, exposing browser-automation to anything that can connect.

**Think of it like:** Not one lock — a bolt, a chain, and welding the hinge. Belt, suspenders, and gluing the trousers to the belt.

## 🌐 Open Source & Why It Matters To You

You can verify the lock. Grep for `enabled` in the two files. See the constant. See the dead setter. See the discarded flag. In a closed browser this is a marketing claim; here it is arithmetic.

## 📖 Glossary (Plain English Dictionary)

**Marionette** — Firefox's older browser-automation backend. Underlies Selenium's Firefox driver.

**WebDriver BiDi** — The newer W3C standard for bidirectional browser automation. Implemented in Firefox as the Remote Agent.

**Dead-coded** — Code that still exists in source but cannot reach a state where its effect would happen. Distinguished from deleted: removing might break callers; dead-coding preserves the shape.

---
*Human Track. Its Developer Track twin (`09-remote.DEVELOPER.md`) covers the same changes in technical detail. Neither is a simplified copy of the other — they are the same truth in two languages.*


---

# ═══ MERGED DOCUMENT: 09-remote.PRECHECK.json (verbatim · sha256:4f53cda18c2baa0c · merged 2026-08-02) ═══

```json
[]
```


---

# ═══ MERGED DOCUMENT: 09-remote.PRECHECK.md (verbatim · sha256:42d1785cd6e742d2 · merged 2026-08-02) ═══

# Offline Pre-Check: 09-remote

*Generated 2026-07-16 22:42:15 by doc_audit.py (rule-based, no model involved).*

## File Inventory

| File | Lang | Lines | Complexity | SHA256 (16) |
|---|---|---|---|---|
| remote_components_Marionette.sys.mjs.patch | patch | 46 | 4 | `809097a96e171e19` |
| remote_components_RemoteAgent.sys.mjs.patch | patch | 71 | 4 | `db4b74fb87a23476` |

## Rule Findings (0)

*All offline rules passed.*

</details>
