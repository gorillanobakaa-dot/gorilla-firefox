# 21.PORT.FIXES.157

Repairs needed to carry Gorilla's patches onto Firefox 157. Apply in order, after the snapshot groups.

- `003-phwinference-ipdl-now-carries-ifdef-moz-webspeech-so-it-must.patch`: PHWInference.ipdl now carries #ifdef MOZ_WEBSPEECH, so it must be a PREPROCESSED_IPDL_SOURCES entry like PContent.ipdl (the IPDL lexer refused the directive)
- `005-misplaced-by-the-group-apply-gnu-patch-fuzz-3-ignored-the-hu.patch`: Misplaced by the group apply (GNU patch --fuzz=3 ignored the hunk's context): the early return NS_OK block moved to its place after gInitializeCalled = true, inside InitializeFOG
- `007-the-gorilla-override-block-sat-in-the-middle-of-a-two-line-a.patch`: The GORILLA OVERRIDE block sat in the middle of a two-line assignment (since 155.0.1), so the module never parsed; moved it above the embedder line. Found by the new node --check on changed JS.
- `021-gorilla-s-decision-security-sandbox-content-level-4-is-the-l.patch`: Gorilla's decision: security.sandbox.content.level 4 is the Linux value; on Windows Mozilla's 9 (its strictest) applies. The all.js line is now under #ifdef XP_LINUX.
- `028-branding-about-window-logo-rebuilt-from-the-1200px-master-wi.patch`: Branding: About window logo rebuilt from the 1200px master with Lanczos (edge energy 12.6 -> 29.3 at 500px, was soft); Nightly wordmark replaced by Gorilla Unleashed; update links point to the Gorilla releases page instead of nightly.mozilla.org

`REPLACE_FILES/` holds the final bytes of the binary files these steps changed (GNU patch cannot apply a git binary diff); they are written after the patches.
