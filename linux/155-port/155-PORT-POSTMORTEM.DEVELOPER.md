<!-- Version: 1.0.0 · updated 26-08-27-12-44 -->
# Firefox 155 port: measured state, defects found, and the audit method that produced them

Version: 1.0.0 · updated 26-08-27-13-00
Tree: `~/gorilla-recreate/firefox-src` (155.0b4)
Patch set: `~/gorilla-recreate/kit/patches` (430 patches)
Package: `release/gorilla-unleashed_155.0-2_amd64.deb`, 102,576,532 bytes, built 12:38

Every number below is `measured` unless marked `inference`. Commands are given so
each line can be re-derived rather than trusted.

---

## 1. The triage false-negative, and the corrected inventory

`triage-155.txt` reported: 365 applied clean, 2 already-present, **63 FAILED**.
A status document read the FAILED bucket as "content absent from the built
binary" and reported 63 missing changes.

`patch --dry-run` fails in BOTH directions on a hand-ported file, so a completed
manual port lands in FAILED permanently. The bucket conflates three states:
never applied / already upstream / hand-ported.

Re-triage by content coverage rather than patch applicability
(`scratchpad/content_triage.py`: for each patch, count added lines of >=12 chars
present verbatim in the target file):

| verdict | count | meaning |
|---|---|---|
| DONE (>=90% of added lines present) | 37 | hand-ported, complete |
| PARTIAL (40-89%) | 10 | mostly upstream drift, checked individually |
| TRACE (1-39%) | 7 | almost all CSS, see §4 |
| OPEN (0%) | 3 | genuine |
| FILEGONE | 1 | upstream deleted the target |
| NOADDS | 5 | deletion-only, needs the inverse test |

Deletion-only patches are invisible to an additions-coverage test. Second pass
(`scratchpad/deletion_check.py`) asserts the REMOVED lines are ABSENT: 4 of 5
DONE, 1 (`SpecialMessageActions`) confirmed DONE by marker grep, its 2 residual
matches being generic comments matching elsewhere in the file.

**Corrected: 41 already done, 13 obsolete, 7 genuinely open, 2 skipped by
decision.** `measured`. Error factor on the original headline: 2.9x.

Also falsified by direct grep:

```sh
grep -c Gorilla <install>/browser/localization/en-US/browser/appmenu.ftl   # 47
grep -c 'PHYSICAL LOCK' remote/components/{Marionette,RemoteAgent}.sys.mjs # 3, 3
grep -c 'GORILLA excised' browser/components/DesktopActorRegistry.sys.mjs  # 4
grep -c 'AIChatContent' browser/components/DesktopActorRegistry.sys.mjs    # 0
```

`AudioStream.h` was also listed as unported; it carries the psychoacoustic
enhancer at lines 35, 376-377, 379. It failed triage on one line
(`std::atomic<float> mVolume`) that 155 declares differently.

## 2. The localization port is complete. Proven twice.

Two audits against pristine 155 extracted from the tarball
(`scratchpad/ftl_id_audit.py`, `scratchpad/ftl_attr_audit.py`, using the tree's
own vendored `third_party/python/fluent.syntax`):

- **Source tree**, 199 files: 0 missing message IDs, 0 missing attributes,
  0 Junk entries. `measured`
- **Installed build** (`/usr/lib/gorilla-unleashed/browser/localization/en-US`),
  107 files compared: 0 defects, 0 junk. `measured`

Branding sweep: of **948** Gorilla-branded strings across the FTL patches, 947
were present. The single gap, `update-setting-write-failure-message2`, was
applied by substituting "the file below" -> "the Gorilla file below" while
keeping 155's grammar over the patch's "may be able resolve" typo.

22 further branded strings were classified OBSOLETE: their message IDs do not
exist in pristine 155 either (upstream removed `-focus-brand-name`,
`customize-mode-lwthemes-link`, `delete-profile-header` and 19 others). Nothing
references them, so there is nothing to port.

**This matters because it rules out l10n as the cause of FAULT-01 before any
CSS was read.**

## 3. FAULT-01: the empirical probe

Symptom: `#appMenu-popup` opens; icons, chevrons, separators and the zoom
percentage render; every menu label is blank.

Static analysis was inconclusive and consumed hours. Established but useless:
the panel IS `type="arrow"` (`panelUI.inc.xhtml:277`), it DOES receive
`color: #00FFFF !important` from `master-redirect.css:283-292`, `.subviewbutton`
(`panelUI-shared.css:1575`) sets no `color`, and nothing in the shipped theme
hides `.toolbarbutton-text`.

The probe, a `userChrome.css` in the profile, resolved three hypotheses in one
observation:

```css
#appMenu-popup .toolbarbutton-text, panel[type="arrow"] .toolbarbutton-text {
  color: #FF0000 !important;  background-color: #FFFF00 !important;
  display: block !important;  visibility: visible !important;
  opacity: 1 !important;      min-width: 60px !important;
}
```

Result: **yellow boxes, no red text**, except "100%" which rendered. `measured`

Reading: the rule matched (background applied), so it is not a selector miss.
Colour was forced, so it is not black-on-black, killing the status document's
proposed fix. "100%" is set imperatively by zoom code, not by Fluent. Therefore
the `label` attribute is never applied to l10n-driven rows.

Elapsed: about two minutes, against several hours of CSS reading that produced
nothing.

## 4. What the runtime log gave up in 30 seconds

`ff154-diag` (in `~/.local/bin`) flushes `$PROFILE/startupCache`, relaunches, and
captures stderr. 70 lines. Every error reduces to `formatMessages` returning
null:

```
L10nCache.mjs:140   TypeError: can't access property "value", messages[0] is null   x11
browser-places.js:2027  TypeError: can't access property "attributes", l10n[0] is null  x4
ReportBrokenSite.sys.mjs:577  TypeError: ... result[0] is null
DefaultBrowserCheck.sys.mjs:64  TypeError: (destructured parameter) is null
globalOverlay.js:107  uncaught exception: undefined   x17
console.warn: "Key element" <key id="key_newNavigatorTab" ...> "is missing key and keycode"   x12
Missing chrome or resource URL: chrome://global/content/ml/ModelHub.sys.mjs
```

The requested IDs exist. `menu-edit-bookmark` and `menu-bookmark-tab` are in
`menubar.ftl` in both pristine and installed builds, and `browser.xhtml` does
link `menubar.ftl`. The bundle itself is failing.

`browser.xhtml` links 46 FTL resources. Three belong to the excised AI stack:
`browser/aiWindow.ftl`, `browser/genai.ftl`, `preview/genai.ftl`. In the
installed build, `preview/genai.ftl` and `preview/aiWindowContent.ftl` were
**dangling symlinks** into the deleted `~/firefox-source/`.

`inference`, not yet confirmed: an unreadable resource in the link set degrades
bundle generation for the whole document, so unrelated IDs resolve to null. The
test is the 155.0-2 package, in which those four `<link rel="localization">`
declarations are commented out (§6). Confirm by opening the menu after install.

## 5. DEFECT: excision spliced into the middle of an expression

`toolkit/components/places/PlacesSemanticHistoryManager.sys.mjs`, as shipped in
155.0-1:

```js
    this.qualifiedForSemanticSearch =
      this.embedder.isEnoughPhysicalMemoryAvailable() &&
    // GORILLA OVERRIDE: ml stack excised ...
    this.#finalized = true;
    this.qualifiedForSemanticSearch = false;
    this.semanticDB = null;
    if (true) { return; }
      this.embedder.isEnoughCpuCoresAvailable();
```

The `&&` has no right operand, so the parser consumes the next statement as one,
yielding `(a = b && this.#finalized) = true`:

```
SyntaxError: invalid assignment left-hand side
  resource://gre/modules/PlacesSemanticHistoryManager.sys.mjs:234
```

A SyntaxError is a parse-time failure, so the module never loads. Consumers see
it as ABSENT, not broken. The only surface symptom was
`console.error: URLBar - Controller: "Error getting the semantic manager"`.

`patch` applied it, the 149-minute C++ build succeeded, `mach build faster`
succeeded, and it greps clean for its own GORILLA marker, so a content-coverage
audit scores it DONE.

Fix: whole-statement replacement as an early return, hoisted ABOVE
`lazy.embeddingsGeneratorFactory.forPlaces()`, which would now throw in its own
right. Verified `node --input-type=module --check` (`measured`).

**Proposed gate:** syntax-check every JS/MJS file an excision touches. Neither
`patch`, nor the compiler, nor a marker grep will catch this class.

## 6. Changes applied, with verification

| change | file | verification |
|---|---|---|
| Find bar theme, 13 edits | `toolkit/themes/shared/findbar.css` | 13x `00FFFF` in the deb `measured` |
| about:addons lobotomy | `toolkit/mozapps/extensions/content/aboutaddons.css` | appended, upstream nova block intact (3 refs) |
| Font-size ramp + visited link | `design-system/dist/tokens-platform.css` | 6 additions; the patch's 173 removals NOT replayed |
| Consolidated CSS intent | `browser/themes/shared/master-redirect.css` | +73 lines, page-scoped |
| Search reduced to Google | `services/settings/dumps/main/search-config-v2.json` | specificDefaults 10->0, orders 2->0, 154 engines intact |
| One branded string | `preferences.ftl` | fluent revalidated, 0 junk |
| AI l10n excision, 12 refs | browser.xhtml, preferences.xhtml, macWindow.inc.xhtml, sanitize_v2.xhtml, browser-shared.css, 2x jar.mn | dist/bin AI paths **6 -> 0** `measured` |
| SyntaxError repair | `PlacesSemanticHistoryManager.sys.mjs` | parses clean, in the deb `measured` |

Pre-excision safety check: 0 live `data-l10n-id` in any of the four documents
resolved to the removed bundles, so no element lost text.

**Deliberately not applied**, recorded so the next port does not "fix" them:

- `tokens-shared.css`: +103 / -226, **zero** Gorilla-flavoured values. Generated-file drift.
- `tokens-platform.css` removals: -173, no Gorilla content. Would delete live 155 tokens.
- `browser-shared.css`: no Gorilla values; its content is AI-window styling for an excised feature.
- newtab JSX x2: intent already achieved by **locked prefs** (`firefox.js:1997-2018`, `feeds.topsites`, `showSponsored`, `topstories`, `discoverystream.enabled` all `false, locked`). Duplicating it needs a separate webpack build.
- `cookieBannerHandling.ftl`: upstream deleted the target file.

## 7. Install hygiene

`/usr/lib/gorilla-unleashed` held 33 AI-named paths. Classified:

- **6 real files**, dpkg-owned, shipped by 155.0-1: 5 AI `.ftl` + `aiWindowSidebar.css`. Fixed at source (§6).
- **10 dangling symlinks + 6 symlink trees** into the deleted `~/firefox-source/`. `test -e` false on every one. No AI code was executing.

Two audits reported these as "GenAI ships in the browser". Neither ran `ls -L`,
`test -e`, or `find -type f`. Quarantined to
`Agents.Work.Trash/gorilla-unleashed-install-orphans-26-08-27-14-00`.

Script bug worth recording: `while read -r f; ... done < <(find ...)` with an
unguarded `sudo` in the body silently consumed the input stream and processed
6 of 16 entries while reporting success. Fix: `sudo ... </dev/null`, or
materialise the list first.

## 8. Confirmed good, contra the status document

- `libxul.so` 2026-08-26 22:44. No C++ newer than it, so **no full rebuild needed**.
- The WhatsApp AudioContext fix IS in the shipped binary: `AudioContext.cpp` 16:36 -> `Unified_cpp_dom_media_webaudio*.o` 19:34 -> link 22:44. `measured`
- `mach build faster` is 4-17s. The 149-minute figure applies only to C++.

## 9. Brain lessons filed 2026-08-27

1. `A patch-triage FAILED bucket is a statement about the tool, not the artifact`
2. `A dangling symlink has a name and no content: find prints it anyway`
3. `An excision spliced into the middle of an expression is a SyntaxError, and the module simply vanishes`

All three are the same class: evidence that resembles proof. All filed with
`--no-chroma` and verified retrievable by querying in the MISTAKEN vocabulary.

## 10. Open

- **FAULT-01 unconfirmed.** Candidate fix is in 155.0-2. Install, open the menu, look.
- WhatsApp call field test on the new build.
- `ModelHub.sys.mjs` is still referenced by `ModelHubProvider.sys.mjs` after the ml excision. Logs one load failure per start. Cosmetic, but it is the same excision-left-a-caller class as §5.
- 7 genuinely open patches, listed in §1.
