# 21.PORT.FIXES.157

Repairs needed to carry Gorilla's patches onto Firefox 157. Apply in order, after the snapshot groups.

- `003-phwinference-ipdl-now-carries-ifdef-moz-webspeech-so-it-must.patch`: PHWInference.ipdl now carries #ifdef MOZ_WEBSPEECH, so it must be a PREPROCESSED_IPDL_SOURCES entry like PContent.ipdl (the IPDL lexer refused the directive)
- `005-misplaced-by-the-group-apply-gnu-patch-fuzz-3-ignored-the-hu.patch`: Misplaced by the group apply (GNU patch --fuzz=3 ignored the hunk's context): the early return NS_OK block moved to its place after gInitializeCalled = true, inside InitializeFOG
- `007-the-gorilla-override-block-sat-in-the-middle-of-a-two-line-a.patch`: The GORILLA OVERRIDE block sat in the middle of a two-line assignment (since 155.0.1), so the module never parsed; moved it above the embedder line. Found by the new node --check on changed JS.
- `021-gorilla-s-decision-2026-10-02-security-sandbox-content-level.patch`: Gorilla's decision 2026-10-02: security.sandbox.content.level 4 is the Linux value; on Windows Mozilla's 9 (its strictest) applies. The all.js line is now under #ifdef XP_LINUX.
- `028-branding-about-window-logo-rebuilt-from-the-1200px-master-wi.patch`: Branding: About window logo rebuilt from the 1200px master with Lanczos (edge energy 12.6 -> 29.3 at 500px, was soft); Nightly wordmark replaced by Gorilla Unleashed; update links point to the Gorilla releases page instead of nightly.mozilla.org
- `038-d-157-24-visual-rasters-rebuilt-from-the-master-full-ico-lad.patch`: D-157-24 visual: rasters rebuilt from the master, full .ico ladders, About logo image-set, clamp, Gorilla wordmark
- `039-d-157-30-network-stage-0-upstream-dns-resolver-thread-pool-r.patch`: D-157-30 network stage 0: upstream DNS resolver thread pool restored
- `042-gorilla-s-decision-2026-10-02-security-sandbox-content-level.patch`: Gorilla's decision 2026-10-02: security.sandbox.content.level 4 is the Linux value; on Windows Mozilla's 9 (its strictest) applies. The all.js line is now under #ifdef XP_LINUX.
- `048-p-014-08-look-i-d10de1e603-157-renamed-the-address-bar-searc.patch`: P-014 08.Look I-d10de1e603: 157 renamed the address-bar search-mode and result-menu messages; the Gorilla wording is carried to the ids 157 uses (D-157-24 branding)
- `066-gorilla-address-bar-wording-search-with-gorilla-or-enter-add.patch`: Gorilla address-bar wording 'Search with Gorilla or enter address you Apple Moron' also when the default engine is known (urlbar-placeholder-with-name), in the new tab search box and in private windows; until now only the no-engine string carried it, so a real profile showed 'Search with Google or enter address' (maintainer's screenshot, 2026-10-04).
