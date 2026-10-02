# 21.PORT.FIXES.157

Repairs needed to carry Gorilla's patches onto Firefox 157. Apply in order, after the snapshot groups.

- `003-phwinference-ipdl-now-carries-ifdef-moz-webspeech-so-it-must.patch`: PHWInference.ipdl now carries #ifdef MOZ_WEBSPEECH, so it must be a PREPROCESSED_IPDL_SOURCES entry like PContent.ipdl (the IPDL lexer refused the directive)
- `005-misplaced-by-the-group-apply-gnu-patch-fuzz-3-ignored-the-hu.patch`: Misplaced by the group apply (GNU patch --fuzz=3 ignored the hunk's context): the early return NS_OK block moved to its place after gInitializeCalled = true, inside InitializeFOG
- `007-the-gorilla-override-block-sat-in-the-middle-of-a-two-line-a.patch`: The GORILLA OVERRIDE block sat in the middle of a two-line assignment (since 155.0.1), so the module never parsed; moved it above the embedder line. Found by the new node --check on changed JS.
