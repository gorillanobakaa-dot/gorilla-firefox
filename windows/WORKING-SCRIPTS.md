# working scripts

## What this is (Layman Track)

When we are working on the build, questions come up that need a quick answer —
"how many of these patches actually still fit?", "which of these are for Linux
only?". Answering them means writing a small throwaway program.

The problem with throwaway programs is that they get thrown away. The next
person to ask the same question writes the same program again from scratch.

So they live here instead. Anything written on the fly during a session gets
saved into this folder with a note explaining what it answers, so it can be
run again or adapted rather than rebuilt.

## Technical Definition (Developer Track)

Ad-hoc analysis tooling produced during build and port work, retained and
parameterised rather than discarded. Each script carries a docstring stating
the question it answers, the input it expects, and the date and context it was
written in. All take `--root` so they are not tied to one checkout.

These are **analysis** tools. They read and report; they do not modify the
source tree. Anything that mutates state belongs in `harness/stages/`.

### Inventory

| Script | Answers |
|---|---|
| `triage_patch_groups.py` | Is a patch group Linux/Windows/macOS/neutral, does it overlap another group, and how much of it still applies? |
| `tally_failed_hunks.py` | Given N "failed" patches, how many HUNKS actually failed? Converts patch counts into real rebase cost. |
| `extract_failing_hunks.py` | For each failing hunk: what did it expect, and what does the tree actually say? Anchors by content and ranks by hunk size. |
| `apply_partial_for_rebase.py` | Half-applies failing patches on purpose to generate `.rej` files. Mutates `src/` — deliberately not a harness flag. |
| `repair_fluent_attrs.py` | Finds and repairs Fluent attributes mangled into multiline values. Classifies BREAKING / COSMETIC / LEGITIMATE first. |
| `ftl_rebase_helper.py` | Re-applies "Gorilla" brand injections to strings upstream has since reworded. Derives the insertion point; never guesses. |
| `check_deleted_file_refs.py` | Does any *reachable* build file, or any live JS module URI, still name a deleted source? Exit 1 if so. Run before every build. |
| `css_override_from_rejects.py` | Converts rejected CSS hunks into appended override blocks, so the cascade does the work instead of a diff. Refuses to write structurally invalid CSS. |
| `find_split_clusters.py` | Are any patches split across enabled and disabled groups, leaving a declaration without its implementation? |
| `generate_playbook.py` | Renders BUILD-PLAYBOOK.md from the live check registry, so the docs cannot drift. |
| `triage_build_failure.py` | Classifies a build failure against every signature seen so far; drafts a new Check when it is genuinely novel. |

### Usage

```
python "working scripts\triage_patch_groups.py"                          # all groups
python "working scripts\triage_patch_groups.py" 02.GPU 03.NETWORKING     # specific
python "working scripts\tally_failed_hunks.py" --top 20
```

`tally_failed_hunks.py` reads `state/patch_report_check.json`, so run
`python harness\gorilla_build.py patches --check` first.

### Why these two exist

Both came out of a specific mistake worth not repeating.

`triage_patch_groups.py` classifies by the `+++ b/<path>` targets inside each
patch, **not** by the group's directory name. Triaging `02.GPU` from its name
produced "Mesa/i915 tuning, Linux-only" — wrong. It is Gecko's cross-platform
graphics blocklist, and three of its four patches port to Windows directly.
The same error hit `03.NETWORKING`, which is four C++ patches in `netwerk/`,
not pref tuning.

`tally_failed_hunks.py` exists because GNU patch returns non-zero if *any*
hunk fails, so "39 patches failed" hid the fact that 80% of the hunks in those
patches landed, and 23 of 38 had exactly one bad hunk. Patch counts overstate
the work; hunk counts are the truth.

`extract_failing_hunks.py` anchors by content because hunk headers go stale:
one hunk recorded line 3998 while its content had moved to line 346. It ranks
by hunk *size* because "one failing hunk" hid a `@@ -2,438 +2,16 @@` that gutted
a file — hunk counts overstate cheapness the way patch counts overstate cost.

`repair_fluent_attrs.py` classifies before repairing because 91 of the ~1,070
candidates were legitimate multiline values containing `PLATFORM()` selectors.
A blind regex would have destroyed every one of them.

`ftl_rebase_helper.py` learned three lessons the hard way, all caught by
inspecting output before writing: bare `.label` keys must be qualified by
their parent message or they match the wrong string; insertions must be
positional rather than a `split()`/`join()` round-trip, which silently strips
the leading indent and turns an attribute into a top-level message; and a
`+` line carrying a bare value is a leftover of the Fluent corruption whose
real target is the parent's `.label`.

`check_deleted_file_refs.py` went through three versions before it was worth
trusting, and each wrong version is instructive. Matching deleted *basenames*
as substrings gave 610 hits, essentially all noise — `moz.build` and `jar.mn`
are themselves deleted basenames, so every `JAR_MANIFESTS += ["jar.mn"]` in
the tree matched. Matching quoted paths scoped to the build file's directory
cut that to 7. But those 7 were in build files nothing reaches any more, and
a one-level reachability check still called them live, because the orphaned
file itself contained the reference. Only a transitive walk of the `DIRS`
graph from the root gives the real answer: **0 live, 7 orphaned**.

It earned its keep: it found that the AI excision deleted `third_party/
llama.cpp`'s sources while leaving `toolkit/components/ml/backends/llama`
building against them — a guaranteed failure roughly an hour into a build.

### The recurring lesson

Every one of these scripts encodes a wrong answer that looked right. Run the
`--check` mode and read the output before letting anything write.

---

## Audit tools, added 2026-09-09

Three questions about the harness itself that turned out to have different
answers, after the question *"have all the fixes been turned into scripts so
they can be used later?"* could not be answered without measuring.

### `audit_fix_coverage.py`

For every defect fixed in a session, asks three things that are easy to
conflate:

- **DETECT** — is there a preflight check that catches it coming back?
- **TOOL** — is there a script that performs the fix?
- **RECORD** — is the reasoning written down?

It also answers the harder one: are the source fixes in `gorilla-patchset`?
`src/` is a DERIVED tree — upstream plus the patchset — so a hand edit there
survives only until someone rebuilds it. When first run: detect 18/18,
record 18/18, re-apply **5/18**, and four hand-fixed files were in no patch
group at all.

Note the bug this audit had itself: it looked for files in the patchset **by
filename**, which misses everything exported as `<path_with_underscores>.patch`.
It reported two fixes as missing that were present. An adjacent-property test,
in the tool written to find adjacent-property tests.

### `audit_harness_wiring.py`

Separates *present* from *wired* from *gating*:

- does the build stage actually refuse to start on a failing BLOCKER (yes)
- which tools are invoked by a check, and which are manual
- how many checks are BLOCKER vs WARN
- whether every check carries a `why` and a remedy

Most tools are deliberately **not** invoked by a check: checks DETECT, tools
REPAIR, and the repair tool is named in the check's remedy. The audit also
verifies every tool is named *somewhere* a future session would find it —
a repair tool nobody knows about is no better than a missing one.

### `verify_patches_apply.py`

Applies each exported patch to a **pristine** upstream copy and compares the
result byte-for-byte against `src/`. "The patches exist" is not "the patches
work".

First run: 8 of 9. The failure was an em-dash — `export_session_fixes.py` had
decoded git's UTF-8 output through the Windows locale codepage and re-encoded
it, corrupting the only non-ASCII character in the whole set. Nothing else
would have caught that.

---

## Runtime verification tools, added 2026-09-09

These test the built browser rather than the source tree. Three defects this
session looked perfect in a screenshot and were broken in use, so "it renders"
stopped counting as evidence.

### `type_test.ps1`

Focuses the window, presses Ctrl+L, **types a URL**, screenshots before Enter
and again after. This is what caught the address bar accepting text while
Enter did nothing — a broken urlbar provider. No amount of looking at the
toolbar would have shown it.

### `click_and_shoot.ps1`

Clicks the app-menu button **and** screenshots in ONE PowerShell process.

`capture_chrome.py` originally clicked in one process and screenshotted in
another; launching the second moves focus, and a XUL panel closes the moment
it loses focus. Two rounds of theme debugging were spent reasoning about CSS
from photographs of a menu that had already shut.

### `verify_installer.py`

Confirms the packaged `.installer.exe` still contains a valid 7-Zip payload
after the SFX stub is patched, and that the branding icon really is embedded.
Patching a self-extractor is exactly the kind of edit that produces a
well-formed executable which extracts nothing.

### `dump_icons.py`, `check_embedded_icon.py`, `shell_icon.py`

Earlier, weaker attempts at reading icons out of a PE, kept because their
failure modes are instructive:

- `dump_icons.py` used `EnumResourceNamesW` through ctypes, which **crashed
  the interpreter** (`_PyThreadState_Attach: non-NULL old thread state`).
- `check_embedded_icon.py` byte-matched a 512-byte slice and reported every
  gorilla icon as embedded when none were — the slice was not distinctive, so
  it matched the blue-globe data that genuinely was there. This false pass was
  then used to *dismiss* a correct signal for several hours.
- `shell_icon.py` asks the shell what it would draw, via `SHDefExtractIconW`.
  Incomplete: it hits a ctypes overflow on the HBITMAP handle.

**Use `dump_pe_icons.py` instead.** It parses the PE resource directory by
hand — no callbacks, no `LoadLibrary` — and reports which icon group Explorer
will actually use (the lowest-numbered one).

### `verify_icon_check.py`, `verify_import_check.py`

Prove a check fires on the real defect and stays quiet once fixed, by running
it against both the broken and the repaired input. Worth copying whenever you
add a check: **a check is not finished until you have watched it fail.**

## `one-shot-patches-2026-09-09/`

39 scripts that each made one permanent edit to the harness or the source.
Already applied — do not re-run. Kept for the anchors and reasoning they
record. See the README in that folder.

## Verifying the INSTALLED browser (added 2026-09-11)

`verify_installed_build.py` — the only tool here that looks at what is
actually installed on the machine rather than at `src/` or the objdir.

It tests three links that can each break alone:

1. **install vs build output** — `firefox.exe`, `xul.dll` and both `omni.ja`
   compared byte-for-byte against `dist/firefox`.
2. **source edited after the build** — 13 watched files; any one of them
   newer than the install means the running browser predates a fix.
3. **fixes inside the installed package** — 7 markers searched inside the
   extracted archives.

Wired into preflight as `installed-build` (WARN — a stale install does not
make the next *build* wrong, it makes the next *test session* wrong).

Two things it encodes, both learned by getting them wrong:

- **Firefox ships two archives.** `browser/omni.ja` holds chrome content,
  themes and `.ftl`; the core `omni.ja` holds `moz-src/`, including the urlbar
  providers. A probe that searched only the first declared a present fix
  missing. Markers are matched by filename suffix across BOTH, never by a
  guessed path.
- **Audit the thing you are auditing.** The staleness section originally took
  its timestamp from the objdir, so a rebuilt objdir masked a stale install —
  precisely the case it existed to catch.

Run the failure test before trusting a change to it: build a copy of the
install, corrupt a binary / strip a file from `omni.ja` / backdate it, and
confirm all three cases exit non-zero.

## Prefs portability and hardware decode (added 2026-09-11)

Three tools that came out of one question — "how many of the Linux tweaks
transfer to Windows?"

`analyze_prefs_portability.py` — separates three things that get conflated:
prefs **baked into the build** (277, all verified present in the installed
package), the profile **user.js** (11, of which 0 need to transfer), and the
ones that are **inert or harmful** on Windows.

`guard_linux_prefs.py` — wraps Linux-only prefs in `#ifndef XP_WIN`. Ten were
shipping unguarded; four inverted upstream's deliberate Windows defaults and
disabled hardware video decode. Idempotent, and it tracks preprocessor depth so
a line already inside an `#if` is never double-guarded.

`make_decode_profile.py` — detects the GPU and writes
`<install>/defaults/pref/gorilla-decode.js`, enabling exactly the codecs that
machine can decode in hardware. `--list` prints the fleet matrix, `--verify`
proves the file is actually read.

`test_decode_detection.py` — 14 real adapter strings. **Run it after any change
to the detection patterns.** It exists because the first detector got two of
five fleet machines wrong, silently.

Three things these encode, each learned by getting it wrong:

- **WMI puts trademark noise inside product names.** "Intel(R) Iris(R) Xe
  Graphics" — a pattern of `iris\s*xe` never matches it. Normalise first.
- **"UHD" is a brand, not a generation.** UHD 620 is Gen9.5 with no AV1
  decoder; UHD 770 is Gen12.2 and has one. Only the number tells you. A
  generic pattern for Arc 130V/140V happily swallowed "620".
- **A wrong tier is worse than no tier.** Enabling a codec the GPU cannot
  decode forces software decode — the exact thing the thermal cap exists to
  prevent. Both tools refuse to guess rather than assigning a tier.

The decode profile is verified by exploiting how Firefox persists prefs: force
`media.av1.enabled=false` in a throwaway profile and see whether it lands in
`prefs.js`. Written means the running default was `true`, so the file was read.
Absent means it was not. No screenshot, no assumption — and `about:support` in
headless mode renders its value cells empty, so a screenshot would have proved
nothing anyway.

## Privacy verification (added 2026-09-11)

`audit_privacy_claims.py` — reads the prefs out of the **installed package**,
not the source, and checks them against the claims made in the release notes.
33 prefs across telemetry, sponsored content and AI, plus a list of the doors
deliberately left open with the reason for each.

`verify_no_phone_home.py` — starts the browser on a throwaway profile, touches
nothing, and records every host it contacts. A pref says what code is
*configured* to do; only the socket table says what it *did*.

`close_privacy_gap.py` — lands the Column A close-list prefs that existed only
in a profile `user.js` no installer deploys. Idempotent.

Three bugs these encode, all of which produced confident wrong answers:

- **Firefox pref files take the LAST definition.** The Gorilla block is
  appended, so its values sit below upstream's. Reading the first match
  reported `app.shield.optoutstudies.enabled` and `extensions.ml.enabled` as
  enabled when both are false and locked 400+ lines further down — it inverts
  the answer for every pref the patchset overrides, i.e. all the interesting
  ones.
- **`^(...|127\.|::1|::)$` cannot match `127.0.0.1`.** The `$` after `127\.`
  made the localhost filter a no-op, so Firefox's own IPC sockets were
  reported as unidentified external endpoints — the scariest possible wrong
  result in a privacy audit.
- **Reverse DNS is useless for CDN-hosted services.** Mozilla sits behind
  Fastly and Google Cloud; the addresses resolve to nothing or to a generic
  cloud PTR. "Four unidentified IPs" cannot support a privacy claim, so the
  DNS client cache is read for the names actually looked up.

And one about scope: the audit found *four* missing prefs when there were
**five**. It checked the four already known about rather than the whole
close-list file. A check is bounded by what it thought to look at.

## Bundling an extension into the browser (added 2026-09-13)

`add_builtin_extension.py` — puts a WebExtension *inside* the browser, so it
ships with it. `--amo ublock-origin` or `--xpi <file>`. Writes all five pieces:
the unpacked extension, its `jar.mn` and `moz.build`, the `DIRS` entry, the
registration module, and the `BrowserGlue` hook.

`verify_builtin_extension.py` — checks source, build output and a **running
browser**, and reports the *location* rather than mere presence.

This needs **no change to the add-on lock** (07.TOOLKIT). A bundled extension
never travels the install path — `maybeInstallBuiltinAddon()` reaches
`loadManifest()` and `_activateAddon()` directly, and `BuiltInLocation`'s
installer is a no-op rather than the throwing one.

Full mechanism, Linux and Windows: `../gorilla-patchset/docs/HOWTO-BUNDLE-AN-EXTENSION.md`.

Three things these encode, each learned the hard way:

- **Firefox has two built-in locations and one is permanently invisible.**
  `built_in_addons.json` feeds `app-builtin-addons`, whose class hard-codes
  `hidden() -> true`. Worse, `gen_built_in_addons.py` globs
  `builtin-addons/*/manifest.json` into that file, so packaging beside
  Mozilla's own built-ins *forces* the invisible location. uBlock Origin
  loaded, ran, downloaded 181,551 filters and blocked ads with a toolbar
  badge — and was absent from about:addons. Package under your own resource
  root instead.
- **`browser/modules/` maps to `resource:///modules/`,** not
  `moz-src:///browser/modules/`. The wrong scheme makes the lazy getter point
  at nothing; `install()` throws inside `_onFirstWindowLoaded`; and with the
  add-on correctly absent from `built_in_addons.json` there is no fallback, so
  it vanishes entirely with nothing in the log.
- **`-headless -screenshot` does not run `_onFirstWindowLoaded`.** The
  registration never fires and the extension looks absent when the build is
  perfect. Verify with a real window. This is the second time headless has
  produced a wrong diagnosis in this project.

And one that is about method rather than Firefox: the fix was known to risk
removing a *working* extension, so it was tested against a **copy** of the
install. It did break it — and the real browser was never touched.

### Keeping a bundled extension current

Pinned by SHA-256 in `state/builtin_extensions.json`, like every other input.
`preflight` (`builtin-ext-updates`, WARN) checks the add-ons site each run and
reports when a newer version exists; `--check-updates` asks on demand;
`--update` takes it deliberately. Re-running without `--update` **refuses** if
the pin no longer matches what is served, rather than substituting silently.

Not automatic on purpose: auto-fetch would make the extension the only
unpinned input in an otherwise reproducible build, and it is the component
with access to every page the user visits.

---

## Complete index (added 2026-09-13)

Every tool in this folder, with the preflight check it backs. Tools described
in detail above are listed here only for completeness. `python <tool> --help`
works on all of them; each carries its own docstring explaining the bug it
exists to catch.

### Branding and artwork

| tool | what it does | check |
|---|---|---|
| `generate_branding_icons.py` | builds the Windows `.ico` files from the gorilla PNG artwork | `branding-icons` |
| `generate_windows_branding_assets.py` | generates the Windows-only branding assets (installer bitmaps, wizard images) | `win-branding-assets` |
| `regen_branding_pngs.py` | regenerates the branding PNG ladder from the canonical master | `png-sharpness` |
| `rebuild_about_logo.py` | rebuilds `about-logo.svg` from the canonical master, per the Crisp Icon Doctrine | `logo-provenance` |
| `check_logo_provenance.py` | is the internal-pages logo crisp, and can we even tell? | `logo-provenance` |
| `brand_installer_stub.py` | puts the build's icon on the installer's outer self-extractor | `sfx-stub-icon` |

### Source-tree correctness

| tool | what it does | check |
|---|---|---|
| `check_dropped_imports.py` | finds upstream `@import` rules a patch REPLACED instead of adding to | `css-dropped-imports` |
| `check_lazy_getters.py` | finds `lazy.Foo` used in a module that never declares a getter for it | `lazy-getters` |
| `check_l10n_resources.py` | every `<link rel=localization>` must resolve to a packaged `.ftl` | `l10n-resources` |
| `validate_package_manifest.py` | every file `package-manifest.in` demands must exist | `package-manifest` |
| `diff_mozconfig.py` | diffs the ported mozconfig against the original it came from | `mozconfig-drift` |

Each of these was written after the corresponding defect shipped once. The
reasoning, including the wrong hypotheses, is in `BUILD-PLAYBOOK.md` under the
check id in the right-hand column.

---

## Call verification (added 2026-09-14)

The v155.0.1-win64.3 notes said WhatsApp calls worked because one pref was
found inside `omni.ja`. No call had been made, and calls did not work. These
tools exist so that a claim about calls needs a call behind it.

| tool | what it does | check / gate |
|---|---|---|
| `webrtc_selftest.py` | hidden browser, throwaway profile, fake camera and mic, no network: ICE, DTLS with the 1.2 cap proven live, data channel, RTP | publish gate 8, preflight `call-proof` |
| `capture_call_log.py` | starts the real browser with call logging, including the page's own console and `PageMessages`; reads the log when it closes | publish gate 9, preflight `call-proof` |
| `analyze_call_log.py` | names the first failing layer, judging the call by whether data flowed | used by both above |
| `test_analyze_call_log.py` | 14 fixtures from the real log strings, one per rung | run after any analyzer change |
| `compare_browsers_media.py` | the same test page in Gorilla and Edge; `--gorilla-pref` tests a fix in a throwaway profile before a rebuild | — |
| `supersede_releases.py` | puts an accurate SUPERSEDED banner on older release pages, UTF-8-safe | — |
| `call_forensics.py` | read-only evidence in 10 seconds: installed build, profile, call prefs in the installed package vs the profile, site and Windows camera/mic access, IPv6, crashes | first step when calls fail |
| `profile_prefs.py` | stops Firefox, backs up prefs.js, sets/removes prefs, lists real overrides (ignores Firefox's bookkeeping) | used by the recorder |
| `verify_published_release.py` | GitHub's installer digest vs local vs a fresh download, and the installer unpacked and compared byte-for-byte with the installed browser | after every upload |

What they encode, each learned by getting it wrong:

- **A pref in a file is evidence about a file.** Only a call proves a call.
- **The page's warnings were the answer.** Every transport log was clean; the
  cause (`dom.workers.maxPerDomain = 8`, WhatsApp's call worker queued) showed
  up only in `PageMessages`.
- **One leg up is not a working call, and one leg down is not a failed one.**
  WhatsApp opens many connections; IPv6-only relay legs fail on an IPv4-only
  network in working calls too. Judge by whether data flowed.
- **Two handover instructions do not hold for Firefox 155:** capture
  `mtransport:5`, and the DTLS 1.3 line means something only on the client
  side.
- **Marionette is locked out of this build**, so the self-test reports over
  localhost instead of being driven.

Full account: [WHATSAPP-CALLS-ON-WINDOWS.md](WHATSAPP-CALLS-ON-WINDOWS.md).
