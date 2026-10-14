# Session handover, 2026-10-14 19:59 (Linux, Sony VAIO)
<!-- Version: 1.0.0 · updated 26-10-14-19-59 -->

From the session "Windows scripts folder survey" to whoever continues. Read this whole file before doing
anything. Then read ~/.claude/CLAUDE.md, ~/.agents/SETTLED.md and the memory index
~/.claude/projects/-home-gorilla/memory/MEMORY.md. The owner is not a developer; he directs AI
tools. Reports to him go in plain words, short sentences; he asked for Romanian when he says so.

## 1. What the day was about, in one paragraph

The Linux side of the Documents reorganisation is finished (scripts merged, 21 tools adopted into
Fieldkit/local/kits, sitrep tool built). The rest of the day went into teaching the Fieldkit build harness to
build Firefox 158 on Linux properly, from the stable release only, with ONE patch set shared with Windows
(settled 2026-10-14, see SETTLED.md). Three things run in parallel: the port of the patch set onto 158, the
decision register shared by both operating systems, and the port of the Windows preflight checks to Linux.

## 2. Where everything stands (checked 19:59)

| Thing | State |
|---|---|
| Port task `firefox-158-linux` | done 66, proposed 4, deferred 4, obsolete 13, pending 35 of about 122 steps. Current step: group 16.SNAPSHOT.DELTA, DesktopActorRegistry.sys.mjs hunk 3. Work tree `~/Documents/FIREFOX.WORK/work/firefox-158.0` (git; root commit = pristine 158.0) |
| Who is porting now | the session "Make the Firefox harness recompute vendored checksums" (it resumed after the checksum step). Do not run the port from two sessions at once |
| Fieldkit main checkout | `~/Documents/Scripts/Fieldkit`, currently on branch `feat/vendored-checksums` (the checksum session switched it). The editable install runs whatever is checked out there |
| Fieldkit PRs merged today | #30 declared `removes:` + span fix + stylesheet obsolete rule; #31 shared decision register, per-check platform, packet citations; #32 first ten Linux preflight checks |
| Fieldkit PRs open | #33 vendored checksums (checksum session's work); #34 two host-dependent tests (fixes main's red Windows CI). Owner merges |
| gorilla-firefox PR open | #3 the shared decision register (decisions/PRODUCT-DECISIONS.yaml + ABOUT-PAGES.yaml). Until merged, Windows cannot pull it |
| Proposals waiting for the owner | 4 adapted hunks. He approves all at once: `~/.local/bin/fieldkit build-harness accept firefox-158-linux --all` |
| Deferred steps | 4 (upstream removed what they change). The build gate stays closed while any step is deferred; list them with `~/.local/bin/fieldkit build-harness status firefox-158-linux` and take them to the owner |

## 3. The decision register (one file, both operating systems)

`~/Documents/FIREFOX.WORK/gorilla-firefox/decisions/PRODUCT-DECISIONS.yaml`, 45 entries: D-157-00..42 copied
from the Windows owner repo (Gorilla.firefox @ 6f2d835, only in the private handover bundle, not on GitHub)
plus D-158-01 (remote control closed: Marionette, Remote Agent, WebDriver BiDi) and D-158-02 (vendored crate
checksums recomputed after our own edits).

- Check it: `~/.local/bin/fieldkit build-harness decisions firefox-158-linux`. Today it reports
  about 19 VIOLATED: that is port progress, not loss. Every marker it looks for was verified present in the
  public patch set; the steps that bring them have not run yet. At the end of the port it is the gate.
- A whole entry may carry `platforms: [linux|windows]`, a single check `platform: ...`. Paths under
  `gorilla-patchset/` resolve to the harness folder on Linux. `covers:` globs say which tree files an entry
  governs; a port packet touching such a file quotes the entry and its `models:` note before any edit.
- A new product decision goes into the register as an entry WITH a check, never only into chat (owner,
  2026-10-14: "decisions like these MUST be logged ... the harness seems like a good place").

## 4. The safety classifier (read this before touching hardening code)

The Claude Code auto-mode classifier refused, as "Security Weaken": the Marionette setter lock (removing an
enterprise-policy check inside a setter that can now only write false), read-only analysis of the glean-core
`.cargo-checksum.json`, and later a response that started writing checksum code. The owner's position: this
is hardening; Marionette, Normandy, Pocket, experiments, WebDriver BiDi are the risk and every door gets closed.

Rules: do not argue with a refusal and never work around it. Stop, quote the register entry id to the owner,
and let him run or allow the action. A fresh session (the checksum one) wrote the checksum code without a
refusal. A permission rule only affects command approval, not the response checker. Narrow rule the owner may
add to `~/.claude/settings.json`: `"Bash(~/.local/bin/fieldkit build-harness:*)"`.

## 5. How to port a hunk (what the harness taught today)

1. `~/.local/bin/fieldkit build-harness next firefox-158-linux` gives the packet.
2. Literal hunks that only differ in context: apply with trimmed context, require ONE match, then DRY-RUN the
   check before submitting. The dry run, in Python from the Fieldkit folder:
   `task._call(s["check"], t, s, **s["args"])` with `t = task.load(...)`, `s = task.current(t)`.
3. Submit only when the dry run says ok, gated on its exit status, never chained with `;` and never through a
   pipe (one attempt of three was lost that way today).
4. Upstream changed the removed lines: use `--adapted '<reason>'` with `removes: <line>` / `keeps: <line>`
   declarations. It becomes a proposal for the owner's one-go accept, costs no attempt.
5. Log every command a person or model would repeat through
   `~/.agents/teach.sh ~/Documents/FIREFOX.WORK/HARNESS-TEACHING-LOGS/firefox-linux-build-26-10-14.md -- "<command>"`.
6. A whole block gone from the 158 tree (search it first) is OBSOLETE: the harness now detects that for
   stylesheets itself; for other files, report it, do not invent code.

## 6. Fieldkit working rules learned the hard way

- The pre-commit hook runs the FULL suite (about 10 minutes) plus a privacy scan, and refuses on any failure.
  Run commits in the background. Never edit the tree while the hook runs (`pgrep -f hooks/pre-commit`).
- Never put a `/home/...` path in source, tests or public files (privacy scan). Use `~`, `Path.home()`, tmp_path.
- A worktree has no venv: commit with
  `PATH=~/Documents/Scripts/Fieldkit/.venv/bin:$PATH PYTHONPATH=<worktree> git commit ...` so the hook tests
  the worktree's own code.
- Tests must not depend on the host: no exact POSIX modes on Windows, no relative fake paths (lesson filed).
- Every command handed to a person carries the program's full path (directives 12b).
- Brain lessons: `python3 ~/Documents/Scripts/Fieldkit/local/kits/brain-management/brain_scribe.py lesson
  --payload FILE` with keys title, category, layman, problem, solution, developer, keywords, paths. Read it
  back with `brain_reader.py`. Four lessons were filed today, all verified.

## 7. The preflight port (owner: "whatever windows has taught the harness ... imported, adapted, improved")

Source: the Windows owner repo, read-only clone at
`<read-only clone of Gorilla.firefox>/harness/lib/preflight.py`
(scratchpad: may vanish; the git bundle it came from is
`~/Documents/Handover.to.Linux.Claude/Linux-Catchup-Handover-261012/unpushed-work/Documents_Gorilla.firefox/Gorilla.firefox.bundle`).
64 checks; 16 Windows-only; 48 to port.

Done (PR #32, `fieldkit/build/firefox_preflight.py`, stage `preflight` before `bootstrap` in
`fieldkit/build/pipelines/firefox-linux.yaml`): source, mozconfig, branding, bundled-files, clobber,
stale-objdir, base-tools, agent-env, disk, temp-source. It found a real gap (the build stripped only one of the
four agent markers; fixed).

Next batch, portable straight onto the Linux mozconfig: capability-guards, staged-options, sccache,
app-identity. After that the checks that call Windows helper scripts (`working scripts/*.py`: split clusters,
package manifest, mozconfig diff, lazy getters, l10n resources, deleted-file refs, fluent attrs, logo
provenance...). Those scripts exist only in the Windows repo: port each into Fieldkit as a tested function,
keep the Windows id, severity and incident text, state the Linux adaptation.

## 8. What is left, in order

1. The port, to the end (the checksum session is on it). Then: owner accepts proposals; deferred steps to the
   owner; final checks; the register with `--strict`.
2. Preflight batches (section 7), one at a time, each proved against the 158 tree, each its own PR.
3. The `patches-check` pipeline stage still dry-runs patches one by one; it must apply into a scratch copy
   (stacked groups gave 27 false failures).
4. Windows side: pull Fieldkit main, merge the shared register (#3), point the Windows harness at the Linux
   preflight module so there is one copy.
5. Dual-track docs for the build group.

## 9. Files to read for the full story

- Audit and measurements: `~/Documents/Scripts/Fieldkit/local/firefox-and-kernel-build-harness-audit-26-10-14-14-30.md`
- Teaching log: `~/Documents/FIREFOX.WORK/HARNESS-TEACHING-LOGS/firefox-linux-build-26-10-14.md`
- Scripts survey and execution record: `~/Documents/Scripts/Fieldkit/local/scripts-folder-survey-26-10-14-10-30.md`
- Memories written today: firefox-decision-register-both-os, firefox-stable-only-one-patch-set,
  commands-to-people-carry-full-paths, terminal-opener-for-people, firefox-154-folder-rescue-done.
