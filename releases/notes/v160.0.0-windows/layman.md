

**1. Firefox 160 underneath.** The browser is now built on Firefox 160.0. All the security fixes Mozilla made since 158 are in.

**2. Firefox 160's new AI parts are cut out.** Firefox 160 added more AI: an on-device text generator and an "AI control" switch. In Gorilla, the AI switch is locked to "blocked", and the text-generation code is taken out of the browser completely, so nothing is left to switch back on.

**3. The new tab page works.** A Firefox 160 module that guesses what kind of page you are on (shopping, news) was removed from Gorilla. One leftover line still asked for it, and the new tab page stayed blank. That line is fixed.

**4. Two settings removed.** Firefox 160's "Link preview" and "Highlight to search" settings are gone from Settings: the features behind them are not in Gorilla.

**Still the Gorilla you know:** it never calls home, uBlock Origin is built in and nothing else can be installed, Gorilla.Satellite mode is there for slow and expensive connections, and studies and telemetry are refused.

### Install

Unzip `Gorilla-Unleashed-160.0-win64.zip` anywhere (for example `C:\Gorilla`) and start `firefox\firefox.exe`. Nothing is installed into Windows.

Check the download first, in PowerShell, in the folder where you saved it:

```powershell
(Get-FileHash .\Gorilla-Unleashed-160.0-win64.zip -Algorithm SHA256).Hash
```

It must print `B54F67E5076BE7A0D04288DAB377DBBD4182ABA6803EC1849013F3F1337090F1`.

