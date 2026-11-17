## Linux and Windows: what changed in 160, in plain words

**1. Firefox 160 underneath.** The browser is now built on Firefox 160.0. All the security fixes Mozilla made since 158 are in.

**2. Firefox 160's new AI parts are cut out.** Firefox 160 added more AI: an on-device text generator and an "AI control" switch. In Gorilla, the AI switch is locked to "blocked", and the text-generation code is taken out of the browser completely, so nothing is left to switch back on.

**3. The new tab page works.** A Firefox 160 module that guesses what kind of page you are on (shopping, news) was removed from Gorilla. One leftover line still asked for it, and the new tab page stayed blank. That line is fixed.

**4. Two settings removed.** Firefox 160's "Link preview" and "Highlight to search" settings are gone from Settings: the features behind them are not in Gorilla.

**Still the Gorilla you know:** it never calls home, uBlock Origin is built in and nothing else can be installed, Gorilla.Satellite mode is there for slow and expensive connections, and studies and telemetry are refused.

### Install on Linux

```bash
sudo apt install ./Gorilla-Unleashed-160.0-linux-x86_64.deb
```

Check the download first, in the folder where you saved both files:

```bash
sha256sum -c SHA256SUMS
```

### Install on Windows

Unzip `Gorilla-Unleashed-160.0-win64.zip` anywhere (for example `C:\Gorilla`) and start `firefox\firefox.exe`. Nothing is installed into Windows.

Check the download first, in PowerShell, in the folder where you saved it:

```powershell
(Get-FileHash .\Gorilla-Unleashed-160.0-win64.zip -Algorithm SHA256).Hash
```

It must print `B54F67E5076BE7A0D04288DAB377DBBD4182ABA6803EC1849013F3F1337090F1`.

## Old Macs (macOS 10.13): what changed, in plain words

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
