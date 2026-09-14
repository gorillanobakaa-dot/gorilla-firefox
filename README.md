# 🦍 Gorilla Firefox

<!-- WHO-THIS-IS-FOR: managed block, do not edit by hand -->

**Firefox with the telemetry stripped out and hardware video decoding forced on, for laptops the web has given up on.**

Tracks current Firefox. Latest build: **155.0.1**, for **Linux and Windows**.

Built for the people every other tool prices out: kids with no credit
card, 15-year-old laptops, data sold by the megabyte. Free forever, by
design, not as a trial.
Why, with the numbers: [PHILOSOPHY.md](https://github.com/gorillanobakaa-dot/Gorilla.Opencode/blob/main/PHILOSOPHY.md)

<!-- /WHO-THIS-IS-FOR -->

**A faster, quieter Firefox for old and cheap laptops.**
No telemetry. No AI chatbots. No "experiments". No sponsored tiles. It wakes up
the hardware your old machine already has, and it runs fine on 2 GB of RAM.
Linux (.deb) and Windows (installer).

---

## 🛡 uBlock Origin is already inside. You cannot add anything else.

Two things are true at once, and both matter:

**1. uBlock Origin ships built in.** Nothing to install, nothing to configure.
It is on the toolbar from first launch and already blocking.

![uBlock Origin blocking ads on YouTube](docs/screenshots/03-blocking-on-youtube.png)

**2. You still cannot install add-ons.** No password manager, no themes,
nothing from the add-ons site. The extension-installing code is removed from
the browser and there is no setting to turn it back on. The reasoning:

> *A browser you can't extend is a browser strangers can't quietly extend
> either.*

uBlock Origin is here because it was **built in**, not installed — the same way
Mullvad Browser ships it and Tor Browser ships NoScript. That is also why
nothing can remove it behind your back.

**Right now the browser does not tell you** when it refuses an install.
Clicking **Add to Firefox** on the add-ons site makes the button go pale and
then nothing happens, with no message. That is the block working, silently.

If you need an extension other than uBlock Origin, this is the wrong browser —
and that is a fair conclusion to reach.

- **[Using uBlock Origin here](windows/USING-UBLOCK-ORIGIN.md)** — where it is, what you can change
- **[Why add-ons are blocked](THE-SEALED-APPLIANCE.md)** — the reasoning and the cost
- **[How to bundle an extension yourself](docs/HOWTO-BUNDLE-AN-EXTENSION.md)** — Linux + Windows, for developers and LLMs
- **[WhatsApp calls on Windows](windows/WHATSAPP-CALLS-ON-WINDOWS.md)** — broken before v155.0.1-win64.4; what was wrong and how it was found

---

# 👉 START HERE — which one are you?

|  | 🐧 Linux — just give me the browser | 🪟 Windows — just give me the browser | 🔧 I want to build it myself |
|---|---|---|---|
| **You get** | A ready-to-install file. ~5 minutes. | A ready-to-install file. ~2 minutes. | A version compiled for *your exact* CPU. |
| **You need** | Debian / Ubuntu / Mint, 64-bit | Windows 10 or 11, 64-bit | ~25 GB free disk + a few hours |
| **Go to** | **[Part 1](#part-1--just-give-me-the-browser)** ⬇ | **[windows/README.md](windows/README.md)** ⬇ | **[Part 2](#part-2--build-it-yourself)** ⬇ |

> 📖 **Want the whole rationale?** Every one of the 441 patches, grouped by
> topic, in plain language *and* in technical detail, with the honest cost of
> each: **[WHAT-WE-CHANGED-AND-WHY.md](WHAT-WE-CHANGED-AND-WHY.md)**

> 🪟 **Windows users:** Windows will block the download and then block the
> install, and hides the "carry on" button both times. Nothing is wrong with
> the file. **[Here is exactly what to click.](windows/WINDOWS-WILL-TRY-TO-STOP-YOU.md)**

---

## Part 1 — "Just give me the browser"

### ⚠ First, the trap that catches everybody

Near the top of this page there is a **big green `< > Code` button**.

> ## 🚫 DO NOT CLICK THE GREEN BUTTON
> It gives you the **recipe**, not the **cake**. It downloads a folder of
> instructions for programmers. It will not install a browser.

The actual browser lives somewhere else, in a section called **Releases**.

### Step 1 — Get the file

**Easiest way — click this direct link:**

### ➡ **[DOWNLOAD THE BROWSER (101 MB)](https://github.com/gorillanobakaa-dot/gorilla-firefox/releases/latest)**

That opens the **Releases** page. On it you'll see a small heading called
**`Assets`** (you may need to click the little ▸ triangle to open it).
Under Assets, click the file ending in **`.deb`**:

```
gorilla-unleashed_<version>_amd64.deb     ← click this one
```

Ignore the files called "Source code (zip)" and "Source code (tar.gz)" — those
are the recipe again, not the browser.

*(Prefer to find it yourself? Look down the right-hand side of this page for the
word **Releases**, and click it.)*

### Step 2 — Check it fits your computer

This file works on **Debian, Ubuntu, Linux Mint, Pop!\_OS, MX Linux** and similar,
on a **64-bit** computer. It does **not** work on macOS, Chromebooks,
Raspberry Pi, or Fedora/Arch.

**On Windows?** There is a separate installer — see
**[windows/README.md](windows/README.md)**.

Not sure? Open a terminal and paste this — if it answers `x86_64`, you're good:

```sh
uname -m
```

### Step 3 — Install it

**The clicking way:** open your **Downloads** folder, double-click the `.deb`
file. Your system's software installer opens — click **Install**, type your
password.

**The terminal way** (more reliable, and it tells you what went wrong):

```sh
cd ~/Downloads
sudo apt install ./gorilla-unleashed_*_amd64.deb
```

When it asks for your password, the screen shows **nothing** as you type — that's
normal, not a broken keyboard. Press Enter, and answer `Y` if it asks.

### Step 4 — Open it

Look in your applications menu for **Gorilla Unleashed** — the big gorilla
icon. That's it. You're done. 🎉

### If something goes wrong

| It said… | Do this |
|---|---|
| `unmet dependencies` / `dependency problems` | `sudo apt --fix-broken install` |
| `not a Debian format archive` | The download was cut short. Download it again. |
| Nothing happens when I double-click | Use the terminal way in Step 3. |
| `Illegal instruction` when it starts | Your CPU is older than the one it was built on → build your own in **Part 2**. |
| Videos won't play on some sites | Expected: this build prefers the codecs your old chip can decode in hardware. See `patches/01.MEDIA`. |

Still stuck? [Open an Issue](https://github.com/gorillanobakaa-dot/gorilla-firefox/issues)
— no question is too basic. That's what it's for.

---

## Part 2 — Build it yourself

The ready-made file above was compiled on **my** laptop (a 2012 Intel machine).
It runs elsewhere, but it's tailored to mine.

Build it yourself and it gets compiled for **your** processor — using every
instruction your CPU actually has, instead of the safe lowest-common-denominator
settings that any shared download is forced to assume. Same browser, fitted to
your machine.

**What it costs:** about **25 GB** of free disk and **1.5 to 12 hours** of
compiling, depending on your computer's speed. The laptop will be busy and warm.
Plug it in.

**How:** open a terminal and paste these three lines:

```sh
git clone https://github.com/gorillanobakaa-dot/gorilla-firefox.git
cd gorilla-firefox
./recreate.sh
```

The script **inspects your computer before it starts** and tells you the truth:
how much disk and memory you have, roughly how long it will take, and exactly
which build tools are missing — with the copy-paste commands to install them. If
your machine can't handle it, it says so plainly and sends you back to Part 1
rather than wasting four hours of your life.

> ⚠ **Build it on the machine you'll actually run it on.** A browser compiled for
> a new laptop may refuse to start on an older one (`Illegal instruction`).

---

## What's actually in here (for the curious)

Every change is a **patch** — a small, readable file showing exactly what was
changed — and beside each group sits a document explaining it **twice**: once in
plain English, once for developers. Nothing is hidden.

| Folder | What it changes |
|---|---|
| `patches/01.MEDIA` | Video & audio — hardware decoding, speaker tuning |
| `patches/02.GPU` | Wakes up old Intel graphics chips |
| `patches/03.NETWORKING` | Network speed tuning |
| `patches/05.PREFS` | The settings baked into the browser |
| `patches/07.TOOLKIT` | Removes the AI features |
| `patches/08.Look` | The black theme and the gorilla |
| `patches/09.REMOTE` | Locks out remote control / automation |
| `patches/13.TELEMETRY.KILL` | Switches off the phone-home |
| *…and 6 more* | 04, 06, 10, 11, 12, 14 |

Open any folder and read the file whose name starts with **`MASTER_PROJECT_LOG`** —
that's the full story of that part, in both plain English and developer detail.

### Two patch sets, two Firefox versions

| Folder | Baseline | Builds |
|---|---|---|
| `patches/` | Firefox 154.0a1 nightly, no pinned changeset | the 154 releases |
| `patchset-155.0b4/` | Firefox 155.0b4, pinned by SHA256 | `155.0-3` and later |

They are cut against different upstream sources and must never be applied to
the same tree. `recreate.sh` uses `patches/` by default; set
`GORILLA_PATCHSET` to build the 155 line:

```bash
GORILLA_PATCHSET="$PWD/patchset-155.0b4" ./recreate.sh ~/firefox-src
```

The 155 set was checked by rebuilding from it: a pristine 155.0b4 tarball plus
that set plus the two fetch steps comes out **byte-identical** to the tree that
compiled the shipped `.deb`. See `patchset-155.0b4/BASELINE.txt`.

`recreate.sh` = the builder · `patches/`, `patchset-155.0b4/` = the changes ·
`scripts/` = helpers · `mozconfig` = build settings

**A note on fonts:** the build can bundle Microsoft fonts (Segoe UI, Yu Gothic,
Consolas) using the established `ttf-ms-win-auto` method — fetched from
Microsoft's own Windows evaluation edition, the same approach mainstream Linux
distributions use. See `scripts/fonts-microsoft.sh`.

---

## Why this exists

Open source gave the world the recipe but forgot to teach people how to cook.
Publishing code isn't real access if only engineers can read it.

This browser is for the person who saved for a year to buy a laptop somebody in a
richer country threw away. Every background service, every "helpful" feature
quietly phoning home, is memory and mobile data taken from that person. So it's
stripped out — and **everything done to it is written down in plain language**, so
the owner of the laptop can read it, understand it, and decide for themselves.

---

*Not affiliated with Mozilla. "Firefox" is a trademark of the Mozilla Foundation;
this is an unofficial modified build. Free and open source.*
