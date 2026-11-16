# 22.EGRESS.LOCKDOWN.160

Every network caller, identifier and helper executable cut from Firefox 160 at the source. Each cut returns before the code that would send, with a `GORILLA UNLEASHED - PHYSICAL LOCK` comment, so no preference can turn it back on. Verified on the built browser by its own HTTP log, a decrypting proxy, the socket table and the packaged archives. Apply in order, after the snapshot groups.

- `001-pref-conflict-browser-ai-control-boolean-false-lines-removed.patch`: Pref conflict: browser.ai.control.* boolean false lines removed; the blocking string 'blocked' (locked) is the one definition, as in the 158 tree
- `002-d-157-35-t-157-35-b-no-small-gorilla-icon-drawn-by-the-brows.patch`: D-157-35 / T-157-35-B: no small Gorilla icon drawn by the browser; the about:studies favicon link (branding icon32.png) removed, nothing else names it
- `005-excision-creep-in-160-upstream-160-added-toolkit-components-.patch`: Excision creep in 160: upstream 160 added toolkit/components/ml/textgeneration (TextGenerator, an on-device LLM API) built on the llama.cpp backend Gorilla already excised; configure stopped on LOCAL_INCLUDES /third_party/llama.cpp/include. Cut the textgeneration dir, the chrome-only TextGenerator.webidl and the NewTextGeneration message of PHWInference with its child/parent glue
