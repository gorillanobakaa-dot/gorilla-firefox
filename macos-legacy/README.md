<!-- Version: 1.2.0 · updated 26-10-23-22-30 -->
# Gorilla Unleashed for old Macs (MacBook Air 2011, macOS 10.13 High Sierra)

Apple stopped updating these Macs years ago, and Firefox stopped supporting macOS 10.13. This is the Gorilla browser
rebuilt for them: the same privacy and speed decisions as the Linux and Windows versions, with a layout and fonts
made for an 11-inch, 1366x768 screen.

## Will it run on my Mac?

| Your Mac | Runs? |
|---|---|
| MacBook Air 2011 (the machine it is built and tested on), macOS 10.13.6 | Yes, tested |
| Any Intel Mac from 2011 or newer, macOS 10.13 or newer | Should, not tested yet |
| Apple Silicon (M1 and newer) | Only through Rosetta (slower, warmer); a native build is not made yet |
| macOS 10.12 or older | No |

## Install (about 130 MB)

1. Download `gorilla-air-<date>.zip` and its `.sha256` from the release.
2. Double-click the zip. Drag **Gorilla Unleashed.app** into **Applications**.
3. First start: the app is not signed by Apple. Right-click it, choose **Open**, then **Open** again. On newer
   macOS: System Settings > Privacy & Security > **Open Anyway**.

## Screenshots (click for full size)

The browser's own pages in Segoe UI with thin, greyscale text, on the MacBook Air's 1366x768 screen:

[![about:about on the MacBook Air in Segoe UI, thin greyscale text, no coloured fringes](https://raw.githubusercontent.com/gorillanobakaa-dot/gorilla-firefox/macbook-air/macos-legacy/screenshots/air-about-about-segoe-ui.png)](https://raw.githubusercontent.com/gorillanobakaa-dot/gorilla-firefox/macbook-air/macos-legacy/screenshots/air-about-about-segoe-ui.png)

The add-ons page: the Gorilla picture fits the 11-inch screen (before, it ran off the bottom corner):

[![about:addons on the MacBook Air with the Gorilla picture fully on screen](https://raw.githubusercontent.com/gorillanobakaa-dot/gorilla-firefox/macbook-air/macos-legacy/screenshots/air-addons-logo-fits.png)](https://raw.githubusercontent.com/gorillanobakaa-dot/gorilla-firefox/macbook-air/macos-legacy/screenshots/air-addons-logo-fits.png)

The same sentence, enlarged 3x without smoothing: Linux on top, the MacBook Air below. Strokes 2.12 px and 2.13 px:

[![The same about:about sentence on Linux (top) and the MacBook Air (bottom), 3x, equal stroke width](https://raw.githubusercontent.com/gorillanobakaa-dot/gorilla-firefox/macbook-air/macos-legacy/screenshots/linux-vs-air-same-sentence-3x.png)](https://raw.githubusercontent.com/gorillanobakaa-dot/gorilla-firefox/macbook-air/macos-legacy/screenshots/linux-vs-air-same-sentence-3x.png)

## What is different from the Linux and Windows versions

- **Built on Momiji 157**, a Firefox kept alive for old macOS by its own maintainer, not on Firefox 158. The Gorilla
  changes sit on top as a small, separate patch series (`PATCHES.sha256` lists every patch).
- **Built for the 2011 processor by name** (Sandy Bridge), never for the build machine's: code the Air's CPU cannot
  run would crash it.
- **Readability on 11 inches:** the browser's own pages and menus use Segoe UI (like the rest of the Gorilla
  browser), monospace text uses Consolas, and text is smoothed in greyscale, which keeps strokes as thin as on Linux.
  Measured on the Air: 2.13 px stroke on the browser's own pages, the same as Linux (2.12 px), against 2.97 px
  with macOS's own font and smoothing.
- **Fits the screen:** the About window and the large Gorilla pictures are sized from the Air's usable screen
  (768 px minus the menu bar and the Dock), not from a desktop monitor.

## Build it yourself (one command, no Mac needed)

A modern browser cannot be compiled on a 2011 Mac, so it is built on a Linux PC and copied over.

```bash
bash macos-legacy/recreate-mac.sh
```

It checks your machine first (64-bit Linux, about 45 GB free, 12 GB of memory or more), then downloads Momiji, our
patch series (checked against `patches-mac.sha256`), Apple's macOS SDK (the version Mozilla pins), and Mozilla's
build tools, builds (2 h 15 to 2 h 35 min the first time on a 2012 laptop; a rebuild of the same configuration reuses its own
compiler cache, one per configuration, so code from another configuration can never be mixed in), and checks that every program file runs on macOS 10.13. It
ends with one line: `VERDICT READY: <zip>`.

- **The Microsoft fonts** (Segoe UI, Consolas, Yu Gothic) are not ours to hand out. The script fetches them from
  Microsoft's own free Windows 11 evaluation download, with one manual step it explains. If you already have them:
  `FONTS_FROM=/folder/with/the/fonts bash macos-legacy/recreate-mac.sh`.
- **Every stage can run alone** (`preflight`, `source`, `fonts`, `sdk`, `configure`, `build`, `package`, `check`),
  and a stage that is already done says so.
- **The hard way** (`--route b`): plain Momiji plus the whole Gorilla patch set, as the project started. Expect to
  resolve conflicts by hand.

## Known limits (measured on the Air, 4 GB of memory)

- Memory (all browser processes, Macs Fan Control off, 2026-10-23): 499 MB for a blank page two minutes after start,
  about 1.0 GB playing a 1080p60 H.264 video. The home page and new-tab page are blank and no spare content process
  is started ahead of need; together these took 162 MB off the idle total.
- Hardware video decoding works for H.264 (the Intel HD 3000 has no VP9 or AV1 hardware).
- Not yet measured: running temperature over a long session with the latest build.
