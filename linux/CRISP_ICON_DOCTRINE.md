<!-- Version: 1.0.0 · updated 26-09-09-16-39 -->

# Crisp Icon Doctrine, Gorilla Unleashed Firefox

**Handoff report for the Windows build.** Everything below was learned on the
Linux/Debian build between 2026-05-29 and 2026-08-27. The doctrine is
platform-independent; the deployment paths are not, and the split is marked
throughout.

Every claim here is `stated in input` (read out of a file on this machine) unless
tagged `model inference`. Paths are given so you can check any of it.

---

## 0. Read this before you touch an icon

The single most important fact: **for anything about icons, logos or
internal-page branding in this estate, read the project folder first and treat
the brain as a fallback.**

`~/Documents/FIREFOX.WORK/FIrefox.154.Work/Icon.app.grid.Dash/`

There is a recorded lesson (`The_icon_doctrine_lives_in_the_project_folder_not_the_brain`,
measured 2026-08-27) that brain FTS queries on this subject return junk. The
query `icon size position internal pages` returned a page about **Windows
printer drivers**. The query `category-icon illustration size` returned nothing.
A single grep over that one folder returned 7 authoritative documents
immediately.

Key files in it:

| File | What it is |
|---|---|
| `HARVESTED_GOOD.css` | The assembled, proven-good CSS. Sections 2 and 3 are the icon core. Marked "do NOT improve these". |
| `NEW_MASTER_CSS_PLAN.md` | The phased rebuild doctrine |
| `GATHERED_BRAIN_LESSONS/` | About 40 lessons. `SVG_Injection_Lesson.md` and `LESSON_icon_slot_size_fix.md` are the two that matter here |
| `GATHERED_BRAIN_LESSONS/ALL_ICON_LESSONS_CONSOLIDATED.md` | 4669 lines, every icon lesson from all brain tiers concatenated in full |

Change history lives separately, in
`FIrefox.154.Work/patches/FIrefox.154.Look/notes/`:
`THEME_FIX_LOG_2026-07-31.md` (sections 20, 23, 38) and
`THEME_FIX_LOG_2026-08-27.md` (section 40).

---

## 1. The one rule

**Never CSS-upscale a raster.** That is the entire cause of the blur.

`background-size` interpolation on a bitmap smaller than its render box is what
made every blurry gorilla in this project's history. The browser is doing a
cheap runtime resample and it looks like a blown-up mess.

The correct method, from `Lessons_Learned_SVG_Injection` (2026-05-29):

1. Start from the canonical master. On Linux that is
   `canonical_about_logo.png`, 2598x2626, 8 MB.
2. **Lanczos-downsample** it to the exact intrinsic size of the SVG wrapper.
3. Base64-encode the result.
4. Embed it as `<svg><image width="W" height="H" href="data:image/png;base64,..."/></svg>`.
5. CSS then only **places** the logo. It never resamples upward.

The reason for the downsample step rather than just embedding the master: an 8 MB
base64 payload on the UI thread bloats the DOM and slows the browser. The sweet
spot is a script that downsamples the canonical master to exactly the wrapper's
intrinsic boundary size.

### The single-icon rule

One artwork for every internal page:
`chrome://branding/content/about-logo.svg`. Never duplicated on disk, never
raster-upscaled.

This was violated once by file copy. On 2026-07-31 it was found that
`about-logo-private.png` and its `@2x` were **byte-identical duplicates** of
`about-logo.png` and its `@2x`, 346,651 and 1,033,163 bytes respectively, about
1.4 MB duplicated. The doctrine had been "satisfied" by `cp`. The files were left
in place because vanilla references may exist, but our CSS no longer points at
them.

### The current intrinsic size is 1200px

Settled 2026-07-31. Do not change it without reading section 40 of
`THEME_FIX_LOG_2026-08-27.md` first, because it has already been churned once:
an assistant changed it 800 to 1200 on the strength of a stale code comment,
then "corrected" it back to 800 against an older lesson, then back to 1200.
Final answer is **1200**.

---

## 2. The trap that will get you: blur is a PROVENANCE problem, not a size problem

This is the most valuable thing in this report and it cost a full debugging cycle
on 2026-08-27.

`about-logo.svg` carried the correct recorded intrinsic size. Every size check
passed. It still looked blurry.

The raster inside it **had never been Lanczos-downsampled from the canonical
master at all**. Measured high-frequency edge energy: **6.62, against 26.10 for a
true downsample of the same master to the same dimensions.** Roughly 4x softer.

A soft asset passes every dimension check ever written. If you are looking at a
blurry logo and the numbers all look right, **the numbers are not the problem.
Check where the pixels came from.**

The measurement is cheap and now automated, see section 5.

---

## 3. The new tab specifically

This is what the original question was about.

**It lives in `browser/extensions/newtab/css/activity-stream.css`.** It does
**not** live in `master-redirect.css`, and the master-redirect rebuild is
explicitly instructed not to touch that file.

Verbatim from `HARVESTED_GOOD.css` section 2, annotated "WORKS, user: perfect":

```css
.logo-and-wordmark .logo,
.logo-and-wordmark .logo-variation-small,
.logo-and-wordmark .spin-ball-small {
  width: 600px !important;
  height: 600px !important;
  max-width: 95vw !important;
  max-height: 70vh !important;
  background-size: contain !important;
}

/* logo margin, activity-stream.css top override */
.logo-and-wordmark,
.search-wrapper .logo-and-wordmark { margin-block-end: 16px !important; }
```

**Why it is crisp:** a 1200x1200 raster paints into a 600px box. The browser is
downsampling 2:1, which is the good direction.

### The control experiment that proves the rule

On 2026-07-31 the user reported the private-browsing gorilla looked blurry
*compared to the new tab one*. Same artwork, same session, different page. Cause:

- newtab painted `about-logo.svg` (1200px raster) into a 600px box. Downsample, crisp.
- about:privatebrowsing painted a **500px PNG at a hardcoded `background-size: 500px`**. 1:1, and soft under any window scaling.

The fix was to make PB mirror newtab exactly: 600x600 box, `max-width: 95vw`,
`max-height: 70vh`, `background: url("chrome://branding/content/about-logo.svg")
no-repeat center center`, `background-size: contain`. Deployed in the Look
`aboutPrivateBrowsing.css` `.logo` rule. User verdict on the next build: "PB logo
crisp, newtab perfect".

### The 2:1 headroom rule

Formalised later as gate ASSET-002: **a raster must out-resolve the CSS box it is
painted into by at least 2x.** The gate reads the actual `width`/`height` px
values out of the built `activity-stream.css`, finds the matching SVG in
`browser/branding/gorilla/content/`, reads its `<image width="...">`, and fails
if `raster < box * 2`.

---

## 4. The other trap: the 200px explosion (ERR-UI-004)

Recorded 2026-07-10. Recurred 2026-08-27, seven weeks later, in exactly the same
form.

The one-icon rule injects the master artwork via `content: var(--gorilla-master-icon)`
onto illustration classes. **With no size clamp.** The moment the artwork gained
pixels, about:addons rendered a gorilla hanging off the right edge of the page.

`HARVESTED_GOOD.css` section 5 had **already flagged this exact line**, with the
fix written beside it, and it was missed:

> `content: var(--icon)` injection on illustration classes => keep, but pair with
> the crisp SVG and constrain size (200px lesson)

The affected selectors are `.illustration`, `.info-icon`, `.error-icon`,
`.category-icon`, `moz-promo img`, `#extensions-empty-illustration`.

The guard, `HARVESTED_GOOD.css` section 4f:

```css
.ac-site-icon,
panel[type="autocomplete-richlistbox"] image {
  max-width: 16px !important;
  max-height: 16px !important;
  object-fit: contain !important;
}
autocomplete-row-item { --icon-width: 16px !important; --icon-height: 16px !important; }
```

The 2026-07-10 lesson closes with the sentence "A CSS pre-flight validator must be
implemented to catch these anti-patterns before deployment." It never was, which
is why the same bug came back. It exists now, see below.

---

## 5. The scripts were merged into the release pipeline

This is the part the registry does not tell you, and it is why searching for the
tool names fails.

**`generate_crisp_svgs.py`, `brand gen-icons`, `branding_engine.py`,
`gorilla_brand.py`, `crisp_logo_generator.py`, `apply_icon_and_cleanup.sh` and
the `gorilla` dispatcher are all GONE from disk.** Searched across the whole
filesystem on 2026-08-24, not just `$HOME`. None of them exist. They appear in no
registry. A first search looks like the memory is simply wrong; it is not.

The brain has a lesson filed specifically so nobody spends that search again:
`SECOND.BRAIN/Chroma.DB.and.Brain.xml/Brain/brand_gen_icons_and_branding_engine_py_are_GONE_from_disk_the_Lanczos_icon_pipeline_doctrine_survives_the_tool_does_not.xml`

**What replaced them:** the doctrine was rewritten as *executable data* inside

`~/.agents/skills/browser-release-pipeline/scripts/release_pipeline.py`

Its own comment block says why:

> THE DOCTRINE, EMBEDDED AS DATA. This block is the point of the whole script.
> Every value below was tuned by hand, approved on sight, and then very nearly
> lost, because it lived only in documentation. **Documentation is not
> executable. This is.**

That file carries `ICON_SVG_INTRINSIC = 1200`, the full `WATERMARKS` table, and
`LOGO_SIZES_REFERENCE` including the newtab 600px block verbatim. It also states
plainly: DO NOT "IMPROVE" THESE NUMBERS, both obvious alternatives were tried and
rejected on 2026-07-31, with the reasons recorded beside each one.

`gate_desk_001` delegates to `apply_desktop_entry.sh` and its docstring notes it
"replaces apply_icon_and_cleanup.sh, named by the 2026-07-11 lesson but long gone
from disk: the doctrine outlived the tool".

### The gates that now enforce all of the above

| Gate | Phase | Fails when |
|---|---|---|
| `ICON-002` | preflight | An injected raster is not a true Lanczos downsample of the master. Edge-energy proxy, threshold `got < want * 0.75`. This is the 6.62-vs-26.10 measurement, automated. |
| `CSS-004` | preflight | An injected icon selector has no size clamp. This is the validator ERR-UI-004 asked for on 2026-07-10. |
| `MARK-001` | preflight | Any tuned per-page watermark string has gone missing from the tree. |
| `ASSET-002` | postbuild | A raster does not out-resolve its CSS render box by 2x. |
| `ICON-001` | postbuild | A size slot's real pixels do not match its nominal name, OR two size slots are byte-identical (the "copied the big one everywhere" failure). |

`gate_icon_002` in detail, because it is the reusable trick: open the master,
crop to its alpha bounding box, centre it on a square canvas, `Image.LANCZOS`
resize it to the same dimensions as the raster you are testing, then compare
`ImageStat.Stat(im.filter(ImageFilter.FIND_EDGES)).mean[0]` for both. If the
shipped one is under 75% of the reference, it was never a real downsample.

### A working reimplementation of the generator does exist

`Documents/Gorilla.Portable.Network.Hub/packaging/make-icons.py`
(also at `FIREFOX.WORK/firefox.work.scripts/04.theme-icon/make-icons.py`)

Flags `--crop-head`, `--keep-background`. It strips the flattened background,
centre-crops square, then Lanczos-resizes to each of 16/22/24/32/48/64/128/256/512,
asserting each written file really is that many pixels and that the files are all
distinct hashes.

Prove it afterwards, because "copied the big one everywhere" is the failure mode:

```
md5sum OUTDIR/hicolor/*/apps/*.png | awk '{print $1}' | sort -u | wc -l
```

That count must equal the number of sizes.

The minimal doctrine, if you have neither script to hand, is six lines:

```python
from PIL import Image
m = Image.open("master.png"); s = min(m.size); m = m.crop((0,0,s,s))
for px in (16,32,48,64,128,256,512,1024):
    m.resize((px,px), Image.LANCZOS).save(f"icon{px}.png")   # each file = real px, never a copy
```

### Where the registry actually is

Two files, and neither alone is sufficient. This is stated in the header of the
first one, reconciled 2026-08-27:

- `Documents/Scripts.For.Work/SCRIPT_INVENTORY.md` says **why** each tool exists. Curated prose. Of the 81 scripts it names, **22 do not exist on disk**, and separately **54% of the scripts actually on disk appear in no registry at all**.
- `Documents/SECOND.BRAIN/SCRIPT_REGISTRY_GENERATED.md` says **what** exists right now. Built by reading every file, so it cannot drift. 194 distinct scripts.

There is a copy of the inventory at `~/.agents/SCRIPT_INVENTORY.md`. The four
dead icon scripts named above appear in **neither** registry, which is consistent
with them being gone rather than merely moved.

---

## 6. Per-page watermark values, for reference

Pattern:
`background: #000000 url(<ICON>) no-repeat fixed <x> bottom <N>px / <size> !important`

| Page | File | Value |
|---|---|---|
| about:addons | `toolkit/themes/shared/in-content/common-shared.css` | `right calc(10% - 39px) bottom 50px / 450px` |
| about:telemetry | `toolkit/content/aboutTelemetry.css` | `fixed center bottom 10px / 450px` |
| about:studies | `toolkit/components/normandy/content/about-studies/about-studies.css` | `fixed center bottom 10px / 450px` |
| about:robots | `browser/base/content/aboutRobots.css` | `padding-inline-start: 420px` (not a watermark, a 400px title image with the heading beside it) |

Other recorded logo sizes: about:welcome split art `center / min(80%, 500px)`
with `.brand-logo` at 300x300; about:translations `#about-translations-logo` at
200x200; about:robots `.title` at `background-size: 400px`, `background-position:
left center`, `min-height: 400px`.

**Two wrong instincts, both tried and rejected on 2026-07-31:**

1. Grow the `top` offset to push the image down. Works for exactly one window height, breaks on every other.
2. Plain `bottom Npx` with no attachment. On a scrolling page that anchors to the bottom of the **content**, so a long list sinks the image below the fold.

The answer is bottom-anchor **and** `background-attachment: fixed`, which pins it
to the viewport. Low on any window height, always in frame while scrolling.

**On the 450px value:** it was 650px on Firefox 154 and correct there. Firefox 155
narrowed the `#content` column, so an unchanged 650px occupied more of the visible
page. 450px was chosen 2026-08-27 and confirmed on sight, and it matches telemetry
and studies. 800px was judged "way too big". Never delete a value, record the next
one beside it.

---

## 7. Linux-only material, listed so you can skip it

The following is GNOME and Debian specific. It is included because the underlying
reasoning may transfer to the Windows shell icon cache, but the mechanics will
not.

**The GNOME slot-size fix** (`LESSON_icon_slot_size_fix.md`, 2026-07-17). Our icon
looked visually smaller than Chromium and Gemini in the dash and app grid despite
being deployed at 2048x2048. Cause: GNOME picks the **closest declared folder
size** to what it requests. Having `64x64`, `96x96` and `128x128` slots meant
GNOME found exact small matches and rendered small. Gemini only had `256x256`
deployed, so GNOME was forced to use the larger slot and rendered bigger. **The
small exact-match slots were actively making our icon smaller.** Fix: deploy only
to `256x256`, `1024x1024` and `2048x2048`, remove the 64/96/128 slots, and declare
all deployed sizes in `~/.local/share/icons/hicolor/index.theme`.

Note the apparent contradiction with the Lanczos doctrine's advice to pre-render
64/96/128 for GNOME. They are answering different questions and both stand:
*generate* every size properly from the master, but *declare* only the large slots
if you want visual size parity in the dash. `model inference`: the resolution is
that the Lanczos rule governs pixel provenance and the slot rule governs
selection, and neither overrides the other.

**Wayland requires a full logout.** `gtk-update-icon-cache` updates the disk cache
but GNOME Shell on Wayland holds the old icon in RAM from session start.
`Alt+F2 → r` is not available on Wayland. If you change an icon and nothing
happens, this is usually why, and it is not a bug in your pipeline.

**The .deb app-grid icon**, fixed 2026-08-10: `build_deb.sh` had been shipping the
raw 2598x2626 non-square master in the 1024 slot. It now regenerates square 512
and 1024 via fuzz-trim, Lanczos, centre-extent, and `postinst` runs
`gtk-update-icon-cache`.

---

## 8. Checklist for the Windows build

`model inference` throughout this section. It is what the Linux history implies
for your target, not something already verified on Windows.

1. Find your canonical master and confirm its real pixel dimensions. Do not trust a filename or a code comment. On Linux both lied at least once.
2. Confirm `about-logo.svg` in the Windows tree embeds a **1200px** raster, and that the raster is a genuine Lanczos downsample of that master. Run the edge-energy check from `gate_icon_002`; it is about fifteen lines of PIL and it is the only check that catches a soft asset.
3. Confirm `activity-stream.css` in the Windows build still carries the 600px block from section 3 verbatim. A `npm run bundle:css` is recorded as dropping CSS injections, so re-verify after any bundle step.
4. Check every injected illustration selector has a size clamp before you look at a single screenshot. This bug has landed twice.
5. If Windows applies its own DPI scaling to chrome images, the 2:1 headroom rule from ASSET-002 may need to become 2x the **scaled** box, not the CSS box. Unverified. Measure it rather than assuming.
6. Screenshot the new tab, about:addons, about:privatebrowsing and about:welcome at the real window size, full resolution and unscaled. Those four are where every icon regression in this project's history has shown up first.

---

## 9. Source index

Everything above traces to one of these.

```
FIREFOX.WORK/FIrefox.154.Work/Icon.app.grid.Dash/HARVESTED_GOOD.css
FIREFOX.WORK/FIrefox.154.Work/Icon.app.grid.Dash/NEW_MASTER_CSS_PLAN.md
FIREFOX.WORK/FIrefox.154.Work/Icon.app.grid.Dash/GATHERED_BRAIN_LESSONS/
    SVG_Injection_Lesson.md
    LESSON_icon_slot_size_fix.md
    ALL_ICON_LESSONS_CONSOLIDATED.md          (4669 lines, everything, in full)
    Lessons_Learned_SVG_Injection.xml
FIREFOX.WORK/FIrefox.154.Work/patches/FIrefox.154.Look/notes/
    THEME_FIX_LOG_2026-07-31.md               (sections 20, 23, 38)
    THEME_FIX_LOG_2026-08-27.md               (section 40)
FIREFOX.WORK/FIrefox.154.Work/patches/FIrefox.154.Look/activity-stream.css
~/.agents/skills/browser-release-pipeline/scripts/release_pipeline.py
~/.agents/skills/browser-release-pipeline/scripts/apply_desktop_entry.sh
SECOND.BRAIN/Chroma.DB.and.Brain.xml/Firefox.154.Lessons/08.Look.And.Feel.CSS.FTL/
    Lanczos_Downsample_Icon_Pipeline.xml
SECOND.BRAIN/Chroma.DB.and.Brain.xml/Brain/
    brand_gen_icons_and_branding_engine_py_are_GONE_from_disk_...xml
Documents/Gorilla.Portable.Network.Hub/packaging/make-icons.py
Documents/Scripts.For.Work/SCRIPT_INVENTORY.md        (why)
Documents/SECOND.BRAIN/SCRIPT_REGISTRY_GENERATED.md   (what)
```

---

## 10. The meta-lesson, which is the reason this file exists

Three separate times, a value that had been tuned by hand and approved on sight
was nearly lost because it lived only in documentation. The brain came up empty on
the watermark value in 2026-07-31 and again in 2026-08-27; the author's own memory
was the recovery tier both times. That is the third recorded instance.

Documentation is not executable. If you tune something on Windows and it is
approved, put the value in a gate, not only in a note.
