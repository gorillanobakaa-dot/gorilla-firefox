# Fonts — Gorilla Unleashed Firefox 154

*Dual-track, per the Gorilla Open Source Philosophy. Same facts, two languages.*

---

## 🧍 Human Track — for everyone

**What's going on:** This browser bundles a handful of fonts so it starts fast
and shows text in every language correctly, even on an old computer with a
slow disk. Bundling them means the browser doesn't have to go hunting through
your whole system for fonts every time it opens — that alone took stock Firefox
from ~40 seconds to start down to ~2–4 seconds on this hardware.

**Which fonts:**
- **Segoe UI** — the clean Windows-style text font. Covers Latin, Greek,
  Cyrillic, Arabic, Hebrew, Thai — most of the world's writing.
- **Yu Gothic** — Japanese characters.
- **Consolas** — the fixed-width font for code and developer tools.
- **Twemoji** — colour emoji (this one ships with Firefox already).

**Why they aren't just sitting in this folder:** Segoe UI, Yu Gothic and
Consolas are made by Microsoft. Microsoft lets you *use* them for free, but
does **not** allow anyone to hand out copies of the font files. So instead of
copies, this folder gives you a little program — `get-microsoft-fonts.sh` —
that downloads them **from Microsoft themselves**, legally, onto your own
machine. You end up with the exact same fonts, gotten the honest way.

**How to get them:** open a terminal in this folder and run:

```
bash get-microsoft-fonts.sh
```

It tells you exactly what to do (there's one step where you download
Microsoft's free trial file). That's it.

---

## 👩‍💻 Developer Track — for builders

**Bundled set** (installed to `browser/fonts/`, wired via
`FINAL_TARGET_FILES.fonts` in `browser/fonts/moz.build`):

| File | Family | Coverage |
|---|---|---|
| `segoeui.ttf`, `segoeuib.ttf`, `seguisb.ttf`, `SegUIVar.ttf` | Segoe UI (+Variable) | Latin/Greek/Cyrillic/Arabic/Hebrew/Thai |
| `YuGothR.ttc`, `YuGothB.ttc` | Yu Gothic | Japanese CJK |
| `consola.ttf` | Consolas | monospace |
| `TwemojiMozilla.ttf` | Twemoji | emoji (CC-BY, already in-tree) |

**Acquisition:** `get-microsoft-fonts.sh` implements the Arch
`ttf-ms-win11-auto` method — fetch the Windows 11 Enterprise 90-day evaluation
ISO from Microsoft's eval center, extract `sources/install.wim`, pull
`Windows/Fonts/<needed>` with 7-Zip, verify, install. No Windows required.
Full font tables and background are kept with the project's own notes.

**Why a script, not the binaries — the honest accounting:**
- Microsoft's EULA licenses **use**, not **redistribution**. Committing the
  `.ttf/.ttc` to a public repo (or shipping them inside a distributed browser
  binary) is redistribution. So the repo ships the *method*, and `.gitignore`
  blocks the binaries (`*.ttf`, `*.ttc`, except CC-BY `TwemojiMozilla.ttf`).

**⚠️ Binary-distribution caveat (important for redistribution):**
- A compiled Gorilla browser with these fonts baked into `omni.ja` **contains**
  the Microsoft fonts. Publicly distributing that binary is redistribution too.
- If you distribute the compiled browser to others, the clean options are:
  1. have recipients run `get-microsoft-fonts.sh` and rebuild, or
  2. build a "handout" binary with **open fonts** (Noto, SIL OFL) which cover
     the same scripts and are legal to redistribute in binary form.
- This is documented openly rather than hidden — if you ship binaries with
  Microsoft fonts inside, do so knowing the licensing line you're on.

**The scanning-patch companion (performance):** the 10× cold-boot win also
relied on font-scan short-circuits in `gfxFcPlatformFontList.cpp`,
`gfxFT2FontList.cpp`, `gfxDWriteFontList.cpp`, `gfxPlatformFontList.cpp`
(see the `.patch` files in this folder). Bundling without those still helps;
with them, system font enumeration is skipped when the bundle covers all
requested glyphs.
