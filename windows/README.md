# 🦍 Gorilla Firefox — Windows

**A faster, quieter Firefox for Windows laptops, including old ones.**
No telemetry. No AI chatbots. No sponsored tiles. It wakes up the video
hardware your machine already has, so video plays on the graphics chip
instead of cooking the CPU.

Windows 10 and 11, 64-bit.

---

## Just give me the browser

### ⚠ The trap that catches everybody

Near the top of this page there is a big green **`< > Code`** button.

> ## 🚫 DO NOT CLICK THE GREEN BUTTON
> It gives you the **recipe**, not the **cake**. It downloads a folder of
> instructions for programmers. It will not install a browser.

The browser lives in **Releases**, on the right-hand side of the repository
front page. Download the file ending in **`-win64-setup.exe`**.

### Installing

Double-click it. Say yes to the Windows permission prompt. Done.

You get a Desktop shortcut and a Start Menu entry, both with the gorilla icon.

**Windows may warn you** that it does not recognise the publisher. That is
because this installer is not code-signed — a certificate costs a few hundred
a year, and this project is free. Click **More info → Run anyway** if you trust
the download. Check the SHA-256 against the one on the release page if you want
to be sure the file arrived intact.

### Installing without the permission prompt

If you cannot or would rather not use an administrator account, install it just
for yourself:

```
GorillaUnleashed-155.0.1-win64-setup.exe -ms /InstallDirectoryPath="%LOCALAPPDATA%\Gorilla Unleashed"
```

Shortcuts are still created. Nothing is written outside your own user folder.

---

## Video: getting the most out of your machine

**Most people can skip this.** The browser works out of the box.

The build plays video using **H.264** only, and lets the graphics chip do the
decoding. That is the one format every machine — right back to 2012 laptops —
can decode in hardware. It runs cool and quiet everywhere.

The trade-off: **YouTube tops out at 1080p**, because 1440p and 4K are only
offered in newer formats (VP9 and AV1).

If your machine is newer than roughly 2016, it can probably decode those newer
formats in hardware too, and you are leaving that on the table. To check and
switch it on:

```
python make_decode_profile.py --detect --apply
python make_decode_profile.py --verify
```

It looks at your graphics chip, works out what it can genuinely decode in
hardware, and writes a small settings file into the install folder. That
applies to every profile on the machine.

To undo it, delete `defaults\pref\gorilla-decode.js` from the install folder.

### Which machines gain what

| graphics chip | gains |
|---|---|
| Intel Iris Xe / Arc, NVIDIA RTX 30-series or newer, AMD RDNA2+ | VP9 + HEVC + AV1 — full 4K |
| Intel HD/UHD 5xx–6xx, NVIDIA GTX 9xx–20xx / Quadro P-series | VP9 + HEVC — 4K, no AV1 |
| AMD Polaris (RX 4xx/5xx, Radeon Pro WX) | HEVC only |
| Intel HD 4000 and older, NVIDIA Quadro M-series, AMD TeraScale | nothing — H.264 is already the best it can do |

**Two GPUs?** Many laptops and all mobile workstations have both an Intel chip
and a separate NVIDIA/AMD one. Which one does the decoding depends on your
switchable-graphics setting, which no script can see — so the tool takes the
**weaker** of the two. That is deliberate: switching on a format your chip
cannot decode pushes the work onto the CPU, which is the opposite of what you
want.

If it does not recognise a chip, it **refuses to guess** rather than picking
something plausible.

### If it changes nothing

Two honest possibilities:

- Your machine really is H.264-only, and it was already set correctly.
- You have no proper graphics driver. On very old hardware, Windows 11 may fall
  back to a basic display driver with no video decoding at all. Nothing in the
  browser can fix that — it needs a real driver, and for some chips none exists
  for Windows 11.

---

## For people building it themselves

`mozconfig.win64` is the build configuration, with the reasoning for each
option written next to it — including why the object directory has to live at
`C:\gfobj` rather than inside the source tree. (Short answer: Windows MAX_PATH,
and a failure message that points at a file which visibly exists.)

The Windows-specific source changes are in
[`../patches/17.WINDOWS.FIXES.2026-09-09/`](../patches/17.WINDOWS.FIXES.2026-09-09/).
That group's README explains each one.

`BUILD-PLAYBOOK.md` catalogues every build and runtime failure hit while
porting this to Windows, with the cause and the fix for each. It is generated
from the build harness's check registry. The harness itself is not published
here; the playbook is included because the failures and their causes are
useful on their own — most of them are not Gorilla-specific, they are what
happens when you build Firefox on Windows.

`test_decode_detection.py` is the test suite for the GPU detection. Run it
after changing any detection pattern. It exists because the first version got
two machines wrong, silently, and a wrong answer there is worse than no answer.

---

## What is different from stock Firefox

The short version: telemetry and data collection removed, the AI features
removed, sponsored content removed, and hardware video decoding forced on
rather than left to a blocklist.

The full list is the patch set in [`../patches/`](../patches/), one directory
per topic, each with its own notes.
