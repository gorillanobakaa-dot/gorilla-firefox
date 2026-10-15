# Handover: the Linux 158 session, 2026-10-14 to 2026-10-16 (about 40 hours)
<!-- Version: 1.0.0 · updated 26-10-16-02-30 -->

Copy of the Linux session handover for the Windows machine (the Linux original lives in its private teaching logs).
Written for the next model on EITHER machine. Do not start by reading it all: run the three commands, then read the part you need.

```
<fieldkit> build-harness platform-steps firefox-158-linux     # what to do on THIS system, computed from the machine
<fieldkit> build-harness symptom "<what you see>"            # a visible problem -> the tool already built for it
<fieldkit> build-harness decisions firefox-158-linux          # every product decision, on the tree and the install
```
`<fieldkit>` is the full path of the program (the absolute path of fieldkit on that machine).

---

## 1. Message to the Windows model (Fable 5), from the Linux session

You are going to port Gorilla Unleashed 158 on Windows. The Linux side has done the port, and the patch set is now
proven against pristine 158: pristine 158 + the set = the tree Linux built (same git tree hash). You should NOT
redo the port by hand. Do this, in this order, and stop at the first thing that is not green:

1. `git pull` Gorilla.Fieldkit (main) and gorilla-firefox (master). Check `config/patch_policy.json` has
   `23.REBASE.158`. `.gitattributes` keeps patches LF: never re-save a patch on Windows.
2. `fieldkit build-harness platform-steps <task>` and do every DO/BLOCKED line it prints.
3. Apply the set the harness way (the migration flow / `build-harness next`); the policy picks the Windows patches by
   itself (`platforms`, `exclude_on`: 01.MEDIA, the GTK GfxInfo unlock and the Linux font list are left out).
4. Build, install, `post-install`, `decisions`, `probe <task> js=install-surface`.
5. Any Windows-only edit: `build-harness record <task> kind=privacy|port <files> --note '<why>'`, then
   `build-harness check-change <task>`. That exports it, runs `rebase-set` (it writes `23.REBASE.158.windows` by itself)
   and proves the set with replay. Never `git commit` a source change by hand: it reaches no patch.

**One thing you must fix on your side, and it is overdue.** `harness/gorilla_build.py`, the Windows build script
that `build-harness build-run`, the owner preflight and `publish_gate.py` call, is NOT in Gorilla.Fieldkit and NOT on
GitHub. It lives only in the private Gorilla.firefox repository on the Windows machine. That makes the Windows build
undocumented, unreviewable and one disk failure from gone, and it is why the Linux side could not reproduce or
check any of it. Integrate it into Fieldkit as a deterministic tool, the way Linux has `fieldkit pipeline run
firefox-linux` (fieldkit/build/pipelines/firefox-linux.yaml + fieldkit/build/firefox_linux.py): stages with a
verify function each, tests, a privacy scan before commit, and `platform-steps` must then report it as OK. Until it
is, `platform-steps` on Windows says BLOCKED, by design. Also tell the owner whether the Windows harness has the
vault (`fieldkit build-harness vault verify firefox`); the Linux one does.

Do not loosen anything that refuses an install. The add-on, theme, search-engine, policy and PKCS#11 refusals
are product decisions (D-157-05, D-158-13, D-158-17, D-158-18), not bugs: the owner, 2026-10-15, "We are the cause
of the incompatibility. This is a DESIGN security measure ... do NOT mess around with them."

---

## 2. What exists now, as tools (all in Gorilla.Fieldkit, all tested)

| Tool | Command | What it proves | Born from |
|---|---|---|---|
| platform-steps | `build-harness platform-steps <task>` | what this OS needs, from the machine; the session brief prints the open ones | owner: "on Windows you do this, on Linux this" |
| symptom router | `build-harness symptom "<words>"` | what you SEE -> the tool built for it (12 entries, English and Romanian) | owner: "a narrative is not a deterministic tool" |
| clip-check | `build-harness clip-check <task>` | cut dialog text, OURS vs stock, the CSS rule and line behind it (InspectorUtils) | WhatsApp "Leave page?" cut to a strip |
| rebase-set | `build-harness rebase-set <task> write=1` | the set carried onto a new release; replay proves it; SUPERSEDED.md says if each old patch's logic is in; fluent_moves finds wording on renamed ids | 77 patches failed on pristine 158 |
| export (fixed) | `build-harness export-hand <task>` | every change above the pristine root becomes a patch, recorded or committed directly | 23 commits were in no patch |
| check-change | `build-harness check-change <task>` | after each edit: export -> rebase-set -> replay, decisions, techniques | |
| OS policy | `config/patch_policy.json` `platforms`, `exclude_on` | one policy for both systems; `firefox._policy` picks by OS | each machine had its own policy file |
| privacy push-check | `fieldkit privacy push-check <repo> --range A..B` + `privacy install-hook <repo>` | nothing private in a push; browser profile data (bookmarks, history, cookies, passwords, sessions) can never pass | owner: "don't upload my bookmarks and history" |
| release-roundtrip | `build-harness release-roundtrip <task> tag=<tag>` | the PUBLISHED .deb: downloaded, SHA256SUMS, deb_check, old install removed, installed, verified | owner: "delete the old install, download from GitHub" |
| install-surface probe | `build-harness probe <task> js=install-surface` | uBlock active, Google only, engine add refused, policy status | install surface closed |
| vault restore-files | `build-harness vault restore-files firefox <tree> <paths>` | files back to Mozilla's original without git; old ones to Agents.Work.Trash | owner: GitHub glitching, keep a vault |
| pipeline src + preflight | `fieldkit.local.json firefox.src`; preflight `source-is-the-port` | the build never uses the pristine tree by mistake | pipeline pointed at Build.Work |
| packaging checks | firefox_linux prune + stale .deb refusal; deb_install icon shadows + stale shell note | dangling dist links, a .deb older than libxul, personal icons over the package's | rsync code 23; grid said "155" |
| must-keep-set (fixed) | preflight | reads what patches WRITE, per platform | false "no patch for GfxInfo.cpp" |
| lessonrules | `build-harness lessons <task> [--all]` | a lesson leaves the waiting list only when a rule names its tool and test | 12 lessons with no way to close |
| profile-check | `build-harness profile-check <task>` | which profile really starts, does its new tab paint (from the other session) | black new tab: old ff154 profile |

## 3. Product decisions recorded (decisions/PRODUCT-DECISIONS.yaml)

D-158-08 no AI (UI before texts); D-157-05 `not_a_bug` + every lock a verify row; D-158-13 correction (no engine can
be added); D-158-17 only Gorilla's own policies (Linux /etc and Windows GPO); D-158-18 no PKCS#11 modules;
D-158-15 and D-158-16 Linux only (Windows: WhatsApp desktop app; audio fine). T-158-10-A dialogs without
transitions. Register on the installed Linux build: 57 enforced, 0 violated.

## 4. Lessons (brain_scribe, read back)

Filed this session: D-158-08 excision order; dialog cut by a 0.01 ms transition; one-run false conviction (confirm
rule); rsync code 23 / stale .deb; pipeline pristine src; icon shadows / stale GNOME shell; CI silent commit identity;
export missed direct commits + Windows-only owner script; patch set never carried onto 158 (rebase-set); no OS
selection in the policy; add-on refusal is the design (register first). Port-and-teach lessons: 12 recorded lines,
8 distinct (4 were written twice by the porting runs; kept, never deleted; all 8 ruled in lessonrules.py). The
brain lessons of this session were checked for duplicates by query: one entry each.

## 5. State of the repositories

- Gorilla.Fieldkit: PR #68 merged; #69 (rebase-set, export, OS policy, privacy, platform-steps, lessonrules,
  release-roundtrip) and #70 (profile-check) merged once CI is green; the main checkout back on `main`.
- gorilla-firefox: branch `d158-04-two-build-paths` -> PR -> master; tag `v158.0-1`; release with the .deb, SHA256SUMS
  and the notes in releases/158.0/RELEASE-NOTES-158.0.md.
- Not done, for the owner: log out and in (app grid name/icon); the 60 fps gap (834 of 8667 frames dropped at 1080p60).
