<!-- Shared copy, 2026-10-14: moved here from the Windows owner repo (Gorilla.firefox @ 260f588, 2026-10-10) so the
     Linux and Windows harnesses read ONE plan. Edit it here; the Windows side reads it from this repository. -->

# Gorilla Firefox: the migration plan

How the Gorilla patch set is carried to every new Firefox release. It is a plan that is followed step by step. It
does not depend on any model's memory, and it is never improvised. The harness enforces it: a stage cannot start
while the one before it is red, and every action names the checklist item it serves.

Written 2026-10-03, after the 157 port taught every lesson in it.

## 1. What we carry (measured on the 157 patch set)

| Unit | Count |
|---|---|
| Patch files | 435 in 17 groups |
| Hunks (individual changes) | 1,825 |
| Authored lines | +8,481 / -11,912 |
| New files | 743 (656 are the bundled uBlock Origin) |
| Deleted upstream files (excisions) | 432 |
| Preference lines | 423 |
| Product decisions (`decisions/PRODUCT-DECISIONS.yaml`) | 24 |
| Public claims (`claims/CLAIMS.yaml`) | 5,575 (about 73 distinct reviewed clusters + history) |

The privacy core is groups 05, 07, 09, 12, 13 and 22 (about 430 hunks). 08.Look holds 1,066 hunks, mostly
branding strings and CSS.

## 2. The principle: we port the idea, not the line

Firefox moves code, renames functions and changes syntax between releases, so a line-by-line diff stops being
proof. Every hunk is therefore registered as an **intent** in `intents/INTENTS.yaml`:

- **purpose**: why it exists, quoted from its patch header, decision or claim (never invented);
- **anchors**: what survives a refactor: pref names, function names, file basenames, endpoint hosts, string ids;
- **behaviour check**: how the built browser proves it, without looking at lines. Examples: the shipped pref value
  and lock, a module absent from omni.ja, an endpoint never contacted (leak gate), a marker or early return in
  the tree, an icon's sharpness against its master.

A migration succeeds when every intent is **proven in the new build**, not when the patches apply.

## 3. Stages and gates

| Stage | What happens | Exit gate (all green, or each exception a recorded decision) |
|---|---|---|
| **S0 Preflight** | Inventory: groups, patches, intents, decisions, claims. Audit of the previous release (claims, decisions, leak-gate baseline). Toolchain, disk, thermal sensor proven. | Previous release audit stored; inventory counts recorded; machine ready. |
| **S1 Upstream intake** | Diff the old Firefox release against the new one: new prefs, new endpoints and hosts, new modules, actors and about: pages, new background tasks, new AI/ML features. Each is an INTAKE item. | Every intake item has a disposition (cut at source, accepted with a decision, or not network-capable). |
| **S2 Mechanical apply** | Patches applied in policy order, zero fuzz; hunks already upstream detected. | Every hunk is APPLIED, ALREADY-UPSTREAM, or queued for S3. |
| **S3 Intent port** | Each intent whose hunks did not apply is located by its anchors in the new tree and re-implemented. Every edit is recorded (`build-harness record`), never committed by hand. | Every intent ported, or obsolete with a recorded reason. |
| **S4 Tree verification** | `verify` (JS parses, imports exist, mozbuild sane), `repair`, `truthbound` (every change explained), intent tree checks, decision tree checks, visual static checks. | All green. |
| **S5 Build** | `build-run`: idle wait, thermal proof, governor, known stops fixed automatically, stale files swept. | BUILD OK; packaging checks green. |
| **S6 Install and proof** | `install` (backup first, fingerprinted zip), `post-install`: prefs, excised, startup, egress, ad blocking, leaks, decisions, intents, visual runtime, the maintainer's scripts. | All rows green; the keyboard tests run with `--drive` after a warning. |
| **S7 Leak gate** | `leakgate --release` in an administrator shell: every scenario, including user actions (address bar, downloads, DRM, calls, certificate errors, LAN probes). | Release PASS; the first release seeds the baseline. |
| **S8 Claims and consistency** | Claims audit `--strict`; every public document and owner tool agrees with the decisions and the shipped build. | No UNPROVEN or CONTRADICTED claim without a recorded decision. |
| **S9 Publish** | `export-hand`; the public patch set replayed onto pristine upstream must equal the built tree hash; privacy scans; push only on the maintainer's recorded yes. | Identical tree hash; scans clean; pushed. |

## 4. How the work is split

- **Order of groups:** privacy core first (13, 12, 09, 07, 05, 22), then build fixes (02, 03, 04, 06, 11, 21), then
  08.Look and 16. A privacy regression is found on day one, not on day six.
- **Batches:** one group at a time through S2 and S3. Inside a group, intents are independent, so analysis can run in
  parallel; **recording into the tree is serial** (one writer), because two writers lose steps.
- **Parallel work that is safe:** intake analysis, intent location by anchors, documentation, test writing, audits.
- **Never in parallel:** recording, building, installing, the leak gate.

## 5. Knowing where we are: SITREP

`fieldkit build-harness migrate sitrep <task>` answers in plain words at any moment:

- the stage and the gate status, with the failing items;
- progress: intents total / applied / ported / verified in the tree / proven in the build, per group;
- open decision briefs by kind, and parked tickets;
- the last events from the journal;
- **the one next action**, as a command.

A SITREP is written into the journal at every stage change, so a new session (or a different model) starts from the
record, not from memory.

## 6. Staying on course: the drift guard

- Work happens on an item: `migrate work <item>`. Recording, repair, build and decisions are journalled against it.
- An action with no active item, or for an item outside the current stage, is refused.
- A side problem that does not block the current stage becomes a **parked ticket** (`--park "<why>"`), shown in the
  SITREP, and is not chased now. This is what stops the spiral of fixing the fifth-generation problem of a
  side-track.
- A problem that blocks the gate is fixed with a deterministic tool, and the tool is added to the harness
  (a STOPS entry, a verify rule, a repair, a check) before the stage continues: the same failure never costs time
  twice.

## 7. Asking the maintainer: decision briefs only

A model never asks a bare question. Every decision is a brief (`build-harness briefs`): what is affected, verbatim
examples and where they are linked from, every option with what it changes and its cost to users and to credibility,
and a recommendation. The answer is recorded in the maintainer's own words. The default for an unproven privacy claim
is to make it true, never to delete it.

## 8. Rules that do not bend

- **This browser never calls home.** The only compromises are recorded trade-offs.
- A build is not done because it compiled; it is done when S6-S8 are green.
- Nothing is claimed publicly that the harness has not proven.
- Pushes and approvals belong to the maintainer.

## Techniques (added 2026-10-03)

At S1 (intake) and before every build: `fieldkit build-harness techniques <task>`. Each technique in Fieldkit `fieldkit/buildh/techniques.py` (problem, concept, signals, apply, verify) is applied to every UNGUARDED place in the new tree, even when its patch no longer applies. The build gate refuses a tree where a technique does not hold.
