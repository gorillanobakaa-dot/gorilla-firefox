## What changed, in plain words

**1. Gorilla's own name inside the app.** macOS now sees the app as Gorilla Unleashed, made by Gorilla (bundle ID `org.gorilla.unleashed`). The earlier build still named Mozilla there, and listed Mozilla's updater and DMG helper. Those are gone.

**2. Everything else is the earlier MacBook Air build.** Same thin, clear text (Segoe UI with greyscale smoothing), pages sized for an 11-inch screen, the same privacy decisions as the Linux and Windows versions.

**Why it is 157 and not 160:** nobody keeps Firefox 160 alive for macOS 10.13 yet. The newest Momiji is a 158 beta. This build stays on Momiji 157 until a newer stable one exists.

### Will it run on my Mac?

| Your Mac | Runs? |
|---|---|
| MacBook Air 2011, macOS 10.13.6 | The earlier build of the same series was tested there; THIS build is not tested on the Air yet (see below) |
| Intel Mac 2011 or newer, macOS 10.13 or newer | Should, not tested |
| Apple Silicon (M1 and newer) | Only through Rosetta |

### Install

1. Download `Gorilla-Unleashed-157.0-mac-x86_64.zip` and check it: `shasum -a 256 -c SHA256SUMS`.
2. Unzip, drag **Gorilla Unleashed.app** into **Applications**.
3. First start: the app is not signed by Apple. Right-click, **Open**, **Open**. Newer macOS: System Settings > Privacy & Security > **Open Anyway**.

### Not checked yet (honest list)

- This exact build has NOT been installed or started on the MacBook Air: the Air was offline when it was published. The checks below ran on the build machine only.
