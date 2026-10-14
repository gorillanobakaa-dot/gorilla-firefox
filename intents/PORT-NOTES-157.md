# Port notes 157: intents that stay red in the ledger, and why

Written 2026-10-03 by the pass-2 writer (one writer). The harness has no command to record a per-intent reason in the
ledger, so the reasons are kept here. Every row was read in the 157 tree (`Build.Work/firefox/157.0-truth`) with the
harness's own hunk judge (`claims.hunk_status`) and the intent's tree checks. Nothing here edits INTENTS.yaml, the
decision register or the claims register.

Classes:

- **IMPLEMENTED (judge artefact)**: the tree does what the intent wants; the hunk judge or the seeded tree check
  misreads it. The check is left as it is (never weaken a check); this row says why it is red.
- **SUPERSEDED**: a later, recorded change in this port does the same job better, so the old line is gone on purpose.
- **OBSOLETE (snapshot artefact)**: the hunk "removes" a string, token or rule that upstream added after the snapshot
  the patch was cut from. It was never a Gorilla change. 157 code uses it, so removing it would break the UI.
- **OBSOLETE (AI excised)**: the hunk styles or wires a feature that is excised in 157.

| Intent | Group / patch | Class | Why |
|---|---|---|---|
| I-603ca4481b | 03.NETWORKING nsHostResolver.cpp | SUPERSEDED | P-003 (D-157-30, network study F1) restored upstream's limits on purpose: the 154-era "raise to 16 threads / 12 idle" now LOWERS the 157 pool (MaxResolverThreads() = 64). Faster wins. |
| I-192549d1dc | 05.PREFS all.js | SUPERSEDED | P-008: `browser.ai.control.*` are string prefs; the hunk's boolean `false` was dropped by libpref (type mismatch), so they shipped enabled. Now `"blocked"`, locked (all eight). The six `false` lines are gone on purpose; the intent's pref checks still expect `false`. |
| I-f63a56ec9c | 07.TOOLKIT ExperimentAPI.sys.mjs | IMPLEMENTED (judge artefact) | All four getters return `false` and `isInitialized` exists (ExperimentAPI.sys.mjs:469-487); the tree check passes. The judge's renamed-line heuristic pairs `return this.#studiesEnabled;` with the unrelated setter `this.#studiesEnabled =`. |
| I-c6b19ff48b | 07.TOOLKIT TranslationsParent.sys.mjs | OBSOLETE (code gone upstream) | `#getBergamotWasmRecord` does not exist in 157 (the record fetch is inlined in `#getBergamotWasmBlob`). Its only caller, `getTranslationsEnginePayload`, throws first under the 22/014 PHYSICAL LOCK, so no wasm record is ever fetched (backlog AI-04: "record TranslationsParent #9 as covered by 014"). |
| I-5965dea0ea, I-c306879738 | 08.Look backupSettings.ftl | OBSOLETE (snapshot artefact) | `turn-on-scheduled-backups-location-choose-folder` and `-error-default-dir-denied` are used by 157's turn-on-scheduled-backups.mjs. The backup feature is off anyway (D-157-20). |
| I-d10de1e603 | 08.Look browser.ftl | IMPLEMENTED by idea (P-014) | 157 renamed the ids back: SearchModeSwitcher.mjs uses `urlbar-searchmode-popup-search-settings` / `-settings`, not `-panelitem`. The Gorilla wording is now on the ids 157 uses ("Search Gorilla Settings", "Gorilla Settings"), with the siblings 157 also renamed (`-remove-from-history2`, `-bookmarks3`, `-history3`, `-tabs3`). The judge still sees the old ids "not removed". |
| I-1977b622eb | 08.Look browser.ftl (GORILLA REPAIR 2026-07-31 graft) | CONFLICT, maintainer | Red since P-014. The graft adds 157's renamed address-bar messages "verbatim from the vanilla vault"; P-014 carried the Gorilla wording of I-d10de1e603 (and the older Gorilla ids) to six of them. The two intents cannot both be green. P-014 is kept because a recorded revert would leave its hand steps as false completions in verify. The maintainer picks: Gorilla wording on the six ids (now) or vanilla (P-015 brief). |
| I-5f9eb0fc13 | 08.Look browser.ftl | OBSOLETE (snapshot artefact) | `urlbar-result-menu-trending-dont-show2` is used by 157's UrlbarProviderSearchSuggestions.sys.mjs. Trending is off by pref. |
| I-ec65526e4a, I-e0f137ead4 | 08.Look customkeys.ftl | OBSOLETE (snapshot artefact) | 157's customkeys.js / CustomKeysParent.sys.mjs use these ids (key editor, shortcut list). |
| I-f34b37cf5d | 08.Look menubar.ftl | IMPLEMENTED (judge artefact) | All five Tools-menu labels read "Gorilla ..." (menubar.ftl:298-314). The hunk ends inside `menu-settings`' multi-line accesskey selector, so the judge compares a truncated message. |
| I-aa1a4a3d90 | 08.Look newtab.ftl | OBSOLETE (snapshot artefact) | The World Cup survey strings are used by 157's OMCHighlightRegistry.mjs; removing them leaves no network effect, only blank text. |
| I-850f2a5c5c | 08.Look formAutofill.ftl | OBSOLETE (snapshot artefact) | `autofill-card-network` / `-search-term-credit-cards` are used by 157's FormAutofillUtils.sys.mjs and CreditCard.sys.mjs. |
| I-f0798a159c | 08.Look browser-shared.css | OBSOLETE (snapshot artefact) | 157 needs the `tabs-navbar.tokens.css` import; removing it drops the tab and nav-bar design tokens. |
| I-1c4ee80d5d | 08.Look browser-shared.css | OBSOLETE (snapshot artefact) | The toolbox background-image rule is upstream 157 code for theme images. |
| I-c240a88b0f | 08.Look browser-shared.css | OBSOLETE (AI excised) | The missing line is the Smart Window (nova) icon; aiwindow is excised and the Smart Window button is removed (P-011). |
| I-67c4d210da | 16 aboutDialog.css | IMPLEMENTED by idea | The Gorilla logo is there as a crisp 1x/2x `image-set` (D-157-24, aboutDialog.css:25), not the single soft PNG the hunk names. |
| I-e05936ff6b | 16 preferences.css | IMPLEMENTED by idea | Same: the decoration uses the 1x/2x `image-set` (preferences.css:1779, D-157-24). |
| I-7c95861d9f | 16 SessionStore.sys.mjs | GREEN since P-011 | The isAIWindow block was already gone; the tree check text also matched the AI start-page block, which P-011 removed (measured VERIFIED-IN-TREE 13:42). |
| I-e774655952 | 16 PlacesSemanticHistoryManager.sys.mjs | SUPERSEDED by 21/007 | 21.PORT.FIXES.157/007 moved the override above the embedder line (the 155 placement never parsed). The 16 hunk's "next to its context" can no longer hold. |
| I-92e95bf643 | 21 007 PlacesSemanticHistoryManager.sys.mjs | IMPLEMENTED (check to review) | The tree is exactly 007's result: the override and `return` sit above the embedder lines. The seeded `tree_lacks this.embedder = ...` only saw 007's removal half; 007 re-adds the line below the return. |
| I-0faedebda5 | 16 LightweightThemeConsumer.sys.mjs | IMPLEMENTED (check to review) | No `_isAIWindow` or AI-window observer is left. `this._update(this._lastData);` is upstream code in other pref callbacks (lines 237-346), so the `tree_lacks` check cannot pass. |
| I-7c830d7610, I-3f797dffcd | 16 tokens-shared.css | OBSOLETE (snapshot artefact) | `--link-color*`, `--button-border-color-ghost` and `--card-header-border-color` are 157 design tokens used across chrome. Removing them breaks link and button colours. |
| I-038f9c8b50 | 22 010 ml/moz.build | IMPLEMENTED by idea | A later hand edit (checkpoint c49af9eb26) keeps `JAR_MANIFESTS` but EMPTIES ml/jar.mn, because mozbuild refuses an undeclared jar.mn. Nothing under chrome://global/content/ml/ is packaged. The `actors` and MLModelHubService excisions are in place. |

## 08.Look branding sweep (pass 2)

- Of 2,023 Gorilla-branded Fluent messages in the 08.Look patches, 2,022 read in the tree as the patch wants. The one
  that does not is `menu-settings`, the judge artefact above. A line-level check of every added "Gorilla" line in all
  235 08.Look patches finds 0 missing.
- 157 renamed some ids, which left the Gorilla wording on unused ids. Those 157 actually shows were carried over in
  P-014 (address bar). 358 branded ids have no literal reference in the source. Most of them are built dynamically
  (policy descriptions, NSS errors, onboarding/feature-callout message JSON); the rest are 157 rewordings whose
  English changed, so they are not renames to carry.
- The shipped en-US .ftl now contains 5 "Firefox/Mozilla/Nightly" values. None of them was rebranded by Gorilla:
  `identity-description-custom-root2` (a statement about Mozilla's root store), 3 Nightly-only default bookmarks and
  about:translations' blocked message.
