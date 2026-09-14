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

### ⚠ Windows will try very hard to stop you

You will hit **two** roadblocks, and both are built so that giving up is the
easiest option:

1. **Downloading** — the file gets "blocked". The **Delete** button is big and
   obvious; **Keep** is hidden behind a tiny `…` or `⌄`.
2. **Running it** — a blue box says *"Windows protected your PC"* and offers
   **one** button: **Don't run**. The **Run anyway** button exists, but is not
   drawn until you click the small grey words **More info**.

Nothing is wrong with the file. This happens to every program whose author has
not paid for a yearly code-signing certificate (£200–£600, forever). This
browser is free and intends to stay that way.

**➡ Full walkthrough with the exact clicks for Edge, Chrome and Firefox:
[WINDOWS-WILL-TRY-TO-STOP-YOU.md](WINDOWS-WILL-TRY-TO-STOP-YOU.md)**

Don't just take our word for it either — that page also shows you how to check
the file's SHA-256 fingerprint in ten seconds, which proves the file is exactly
what we built. That is a better guarantee than a certificate, because it checks
the actual file rather than who paid a licence fee.

### Installing without the permission prompt

If you cannot or would rather not use an administrator account, install it just
for yourself:

```
GorillaUnleashed-155.0.1.4-win64-setup.exe -ms /InstallDirectoryPath="%LOCALAPPDATA%\Gorilla Unleashed"
```

Shortcuts are still created. Nothing is written outside your own user folder.

---

## 📞 WhatsApp Web calls

**Voice and video calls on web.whatsapp.com work from v155.0.1-win64.4.** Every
earlier Windows release has broken calls: you hear ringing, the other phone
never rings and shows "Connecting…", and the call drops. If you have an older
build, update.

Two separate faults were behind it — Meta's call relays dropping DTLS 1.3
traffic, and a limit of 8 background workers per website that left WhatsApp's
call engine waiting in a queue. The release notes for .3 said calls worked when
they had not been tested; that page now carries a correction.

**[The full account, and how it was found →](WHATSAPP-CALLS-ON-WINDOWS.md)**

---

## 🛡 uBlock Origin is built in — but you cannot add anything else

**uBlock Origin ships inside this browser.** On the toolbar from first launch,
already blocking, nothing to set up.
**[How to use it →](USING-UBLOCK-ORIGIN.md)**

### ⛔ Other add-ons CANNOT be installed

**Extension installation is deliberately blocked in this build** by a patch in
`patches/07.TOOLKIT` ("API LOBOTOMY", a zero-trust extension policy). Every
route is closed — the add-ons site, dragging an `.xpi`, and Install Add-on
From File. There is no error message: one of the 14 rejection points cancels
the install silently, so the site's button simply spins forever.

**[Why — the reasoning, in plain language](../THE-SEALED-APPLIANCE.md)** ·
[How this came to be mis-documented](INSTALLING-UBLOCK-ORIGIN.md)

The short version: *a browser you can't extend is a browser strangers can't
quietly extend either.* Tracking protection, cryptominer and fingerprinter
blocking, cookie-banner dismissal and HTTPS-only are built in instead — but
they are not as thorough as uBlock Origin, and that is a real cost.


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

---

## What it does not send

Verified against the shipped package and on the wire, not just claimed:

- **33 preferences** checked inside the installed `omni.ja` — telemetry,
  experiments, crash reporting, sponsored content and AI all `false` and
  **locked**, so a policy or an add-on cannot flip them back.
- The **ML engine, AI Window and Link Preview modules are not in the package
  at all.** A preference says what code is told to do; absence says it cannot
  be told anything.
- **Glean** — Mozilla's newer telemetry system — is stopped in C++, not by a
  preference. `FOG.cpp` returns before it initialises, so its dispatcher
  thread never starts.
- A **60-second socket capture** on a brand new profile, touching nothing,
  reached no telemetry, Normandy, Glean, Shield, Contile, Pocket, Merino or
  crash-reporting endpoint.

Re-run either check yourself:

```
python audit_privacy_claims.py     # reads the installed package
python verify_no_phone_home.py     # watches the network on a clean profile
```

### What it does send

Not nothing, and pretending otherwise would be the dishonest version. On a
clean start it contacts Mozilla for:

| host | what for |
|---|---|
| `services.addons.mozilla.org` | the malicious add-on blocklist |
| `content-signature-2.cdn.mozilla.net` | verifying that list is genuine |
| `mozilla.map.fastly.net` | CDN for the above |

None of these reports anything about you — they are downloads, not uploads.
They are kept deliberately: a privacy build that breaks captive-portal wifi or
lets a malicious extension through is not a privacy build, it is an abandoned
one. Every kept door is listed with its reason in
[`../patches/14.EGRESS.LOCKDOWN/`](../patches/14.EGRESS.LOCKDOWN/).
