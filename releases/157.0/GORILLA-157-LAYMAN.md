# Gorilla Unleashed 157.0 for Windows: a browser that only talks to the sites you open — Plain Language Guide

> Written 2026-10-03 and 2026-10-04 for the 157.0 release, build 27 (BuildID `20261004224302`). The full release leak test last ran on build 26, not on this build; the release notes say what it found and what build 27 changed.

---

## Should You Run This?

**Yes**, if you want a web browser that does not report on you, does not phone its maker, and does not run AI features in the background, and you can live with English only, one look, no add-ons except the built-in ad blocker, and updating by hand.

**Only if** you are ready to download each new version yourself. This browser never updates itself. If you forget, you keep running an old browser with old security holes.

**No**, if any of these are true:

- You need another language for the browser's menus, or you rely on page translation.
- You need an add-on such as a password manager extension.
- Your workplace or your antivirus inspects secure web traffic. You will get certificate errors on every secure site.
- You depend on the browser warning you about phishing and malware pages. Gorilla does not have those warnings.
- You need the browser to find your location, or to sync with other devices.
- You are not on 64-bit Windows 10 or 11. This release is for Windows only.

## Worst Case, Honestly

The most harmful thing that can realistically happen comes from a choice, not from a bug: **this browser never updates itself.** Picture this. You install 157.0 and forget about it. Months later Mozilla fixes a serious security hole in Firefox. Gorilla does not tell you, and does not download the fix. You keep browsing with the hole open until you notice a new release and install it yourself. That is the price of a browser that never contacts an update server.

The second risk is the missing phishing and malware warnings (decision D-157-25). Example: a convincing fake bank page arrives by email. Ordinary Firefox might show a red warning page. Gorilla does not. The built-in uBlock Origin blocks many known bad sites, but not all of them, and it is not a warning system.

Third, ordinary website certificates are not checked for revocation. If a site's certificate was stolen and then revoked, Gorilla does not find out. Revoked certificate authorities are still refused from the list built into this version.

Last, no measurement proves the absence of every bug. The release proofs for this exact build are listed at the top of the release notes. A leak that waits longer than the tests watch, or that uses a route none of the test witnesses sees, would not be caught.

## What Data This Touches

**On your computer.** The program folder is wherever you extract the zip. Your bookmarks, history, saved logins, cookies and settings live in a profile folder inside your Windows user folder, not in the program folder. You can see its exact place in `about:support`, on the line called Profile Folder. Cookies and logins are kept when you close the browser (decision D-157-28), so you stay logged in. The browser keeps recently loaded pages in memory. It keeps no pages on disk unless you switch on Gorilla.Satellite mode, which keeps up to 256 MB of pages on disk, also after you close the browser.

**On the internet, on its own initiative.** Only three kinds of contact, and nothing else:

- The sites you open, and whatever those pages load.
- The built-in uBlock Origin fetching its filter lists from its own list hosts (such as `ublockorigin.github.io`, `cdn.jsdelivr.net`, `pgl.yoyo.org` and `publicsuffix.org`). Those are the ad blocker's hosts, not Mozilla's.
- Only when a page asks for protected video or a video call needs it: Google's Widevine plug-in or Cisco's OpenH264 plug-in, downloaded straight from their makers and checked against fingerprints built into the browser (decision D-157-12).

**What is never sent.** No telemetry, no crash reports, no usage pings, no update checks, no experiments, no search suggestions, no location lookups, no Mozilla accounts, no sync. Names of websites are looked up through your computer's normal internet settings, so your internet provider can see which sites you visit, as with every other program on your computer (decision D-157-18). Nothing in this browser sends anything to the maintainer.

## Before You Trust It

You can check the main promises yourself without reading any code. Each step says what passing and failing look like.

**Step 1:** Check the fingerprint of the file you downloaded, using the PowerShell steps in "How to install and first run" below.
  - Look for: Pass: the long code PowerShell prints is exactly the SHA-256 code on the release page (installer: `02A7A403C314ACDAF55D7C70449CE06C520D45DC30A845D6D6F1C67B0670DBA5`; zip: `1E9CB307A2CC50194C006552FA534F19641D8665B53D0345E97682B4235A474A`). Fail: any character differs. Delete the file and download it again. If it still differs, do not run it.

**Step 2:** Start the browser, type `about:support` in the address bar and press Enter. Find the line called Build ID.
  - Look for: Pass: the Build ID matches the one on the release page (`20261004224302`). Fail: it differs. You are running a different build from the one the release proofs were made on.

**Step 3:** Type `about:config` in the address bar and press Enter. Click the button that accepts the risk and continues. In the search box, type `toolkit.telemetry.enabled`.
  - Look for: Pass: the value is `false` and the row shows a padlock, which means it is locked and cannot be changed. Try the same with `geo.enabled` (no location) and `browser.search.suggest.enabled` (no suggestions while typing). Fail: a value is `true`, or there is no padlock.

**Step 4:** Type `about:policies` in the address bar and press Enter.
  - Look for: Pass: the page says the policy engine is active and lists policies. This is the second lock layer that 155.0.1 was missing (decision D-157-26). Fail: the page says no policies are active. In this build the two active policies are "Disable Firefox Studies" and "Disable Telemetry"; one visible sign is that `about:telemetry` says it is blocked by your organisation.

**Step 5:** Visit any add-ons website and click an "Add to Firefox" button.
  - Look for: Pass: a message says that Gorilla does not install add-ons or themes and that uBlock Origin is built in. Nothing is installed. Fail: an add-on installs, or nothing at all happens (that was the old, silent behaviour). This message is in the build but no automated test clicks an install button yet, so this check is yours.

**Step 6:** Type `about:addons` in the address bar and press Enter.
  - Look for: Pass: uBlock Origin is listed and switched on, and it is the only extension. Fail: any other extension appears.

## The Big Picture

A web browser is the program you use to read web pages. Most browsers also do many things you never asked for. They send reports about how you use them. They check with their maker for updates, news and experiments. They suggest searches by sending what you type before you press Enter. Firefox 157 also ships artificial-intelligence features that can download models and send text away.

Gorilla Unleashed is Firefox 157 with all of that cut out of its source code. The maintainer's rule is short: **this browser never calls home.** It talks to the sites you open. It does not talk to Mozilla, Google, Microsoft, Cloudflare or any certificate authority on its own. The only exceptions are written down as trade-offs, and the biggest is the video plug-ins that films and video calls need.

Every choice in this browser is a recorded decision with a reason and a cost. You lose things: automatic updates, other languages, other themes, other add-ons, search suggestions, location, sync, and the phishing warnings. In exchange, the browser does what you tell it and nothing else. Each decision is checked against the finished browser every time it is built, not only written in a document.

This release also adds Gorilla.Satellite mode for slow, far-away or expensive internet links. It has a button right of the address bar and a switch in Settings, and it is off by default.

## Key Concepts

| Name | What It Means | Real-World Comparison |
|------|--------------|------------------------|
| `call home` | A program contacting its maker's servers on its own, without you asking. | A hired car that reports every journey back to the rental company. |
| `telemetry` | Reports a program sends about how you use it. | A shop assistant following you round the store writing down what you pick up. |
| `locked setting` | A setting fixed by the browser itself, shown with a padlock in `about:config`. Nothing can change it, not even an add-on. | A thermostat in an office with a locked plastic cover over it. |
| `uBlock Origin` | The ad and tracker blocker built into this browser. It is the only add-on allowed. | A doorman who turns away known pushy salespeople before they reach your door. |
| `BuildID` | A date-and-time stamp that names one exact build of the browser. | The batch number printed on a medicine box. |
| `SHA-256 fingerprint` | A long code calculated from a file's contents. If one byte of the file changes, the code changes completely. | A wax seal on a letter: a broken or different seal means someone opened it. |
| `certificate` | A digital proof that a website is who it says it is, issued by a certificate authority. | A passport issued by a government office. |
| `revocation` | Cancelling a certificate before it expires, because it was stolen or misused. | A bank cancelling a lost card before its expiry date. |
| `profile` | The folder where the browser keeps your bookmarks, history, logins and settings. | Your personal drawer in a shared office desk. |
| `Gorilla.Satellite mode` | A switch, on the toolbar and in Settings, that makes the browser download less, keep what it already has, and wait longer on slow or distant internet links. | Packing a lighter rucksack and walking slower for a long mountain trail. |
| `Save-Data` | A short note the browser adds to every request in the Very slow link level, asking sites for lighter pages. Sites may ignore it. | Asking a restaurant for a half portion: some kitchens do it, some do not. |
| `trade-off` | A choice the maintainer recorded that costs some privacy or convenience on purpose, with the reason. | Leaving the back gate unlocked on bin day, and writing down that you did. |

## How It Works — Step by Step

### Step 1: You download one zip file

The release page offers one zip file with the whole browser inside. There is no installer that writes into Windows. Think of it as a boxed board game: everything is in the box, and nothing is glued to your table.

### Step 2: You check the fingerprint

PowerShell calculates the SHA-256 code of the zip. You compare it with the code on the release page. If they match, the file is byte for byte the one that passed the release proofs. This is like checking the seal number on a parcel against the delivery note before you open it.

### Step 3: You extract it and start it

You extract the zip into a folder you choose and double-click `firefox.exe`. Windows SmartScreen may warn you because the program is not signed with a paid certificate. The fingerprint check in step 2 is a stronger proof than a certificate, because it checks the actual file rather than who paid a fee. It is like a sealed envelope from a friend: you trust the seal you checked, not the brand of envelope.

### Step 4: The browser starts with its locks already on

At start-up the browser reads its built-in settings. Many of them are locked. A policy file inside the program folder locks the most important ones a second time. The parts that would contact Mozilla are not merely switched off: their code returns before it can send anything, so no setting can switch them back on. This is like a door that is bricked up, not only locked: there is no key to lose.

The browser you install is also the browser you keep. Ordinary Firefox can be changed after you install it: Mozilla can switch features on or off for groups of users, run experiments, and even replace the whole new-tab page with a newer version it downloads by itself. In Gorilla all of that is cut out at the source (decision D-157-31). Your new tab page is the one inside the program you downloaded, and it changes only when you install a new Gorilla. Think of a printed book rather than a web page: nobody can edit it after it reaches your shelf.

### Step 5: You browse

When you open a site, the browser connects to that site and loads what the page asks for. The built-in uBlock Origin blocks known ad and tracker addresses on the way. The browser does not connect to links you only hover over, and it does not guess what you will type. It is like a taxi that goes only where you say, without detours.

### Step 6: Your ad blocker keeps its lists fresh

uBlock Origin downloads its filter lists from its own list hosts, by itself, on its own schedule. This is the only regular background traffic, and it belongs to the ad blocker, not to Mozilla. Think of a security guard who collects the updated list of banned visitors each morning from the security company, not from the building's landlord.

### Step 7: A page asks for protected video or a video call

Films on some streaming sites need Google's Widevine plug-in. Some video calls need Cisco's OpenH264 plug-in. The licences forbid shipping them inside the browser. So, only at that moment, the browser downloads the plug-in straight from Google or Cisco and checks it against a fingerprint built into the browser. It never does this at start-up or in the background. It is like ordering a part from the manufacturer only when the repair actually needs it.

### Step 8: You meet a certificate error

If a site's certificate is not trusted, you see an error page. Ordinary Firefox would ask a Mozilla server whether something is intercepting your connection; Gorilla does not. Certificates added to Windows by antivirus programs or employers are not trusted (decision D-157-17), so their inspection shows up as an error. It is like a border guard who accepts only passports from real governments, not cards printed by a travel agency.

### Step 9: You want an add-on

When you try to install an add-on or theme, the browser refuses and shows a message saying so. Older versions refused silently. It is like a shop sign that says "card only" instead of a till that quietly ignores your cash.

### Step 10: You switch on Gorilla.Satellite mode (optional)

On a slow or distant link, click the **Gorilla.Satellite mode** button right of the address bar (it says which level is on), or open Settings, General, and look under Network. Hover over any choice for its full explanation. "Satellite" asks sites for their mobile version, stops videos starting by themselves or downloading in advance, waits longer before giving up on a connection, remembers website addresses for 10 minutes, and keeps up to 256 MB of pages on disk so a restart does not download everything again. "Very slow link" adds: no JavaScript, no pictures, no web fonts, a Save-Data note on every request, and 6 connections per site; a page you already have opens from the disk without asking the site, and Reload fetches a fresh copy. The same menu has "This site: show the normal (desktop) version" and "This site: allow JavaScript", remembered per site. "Off" restores the normal values. Anything you changed by hand yourself always wins. It is like a car's eco mode: the same car, driven more gently to make the fuel last.

### Step 11: A new version comes out

Nothing happens by itself. When you notice a new release, you download it, check its fingerprint, extract it into a fresh folder and start it. Your profile carries over, because it lives in your user folder, not in the program folder. It is like changing a car's engine while keeping the driver's seat and mirrors as you set them.

## Quirky Things Worth Knowing

### The program says "Firefox" in a few places

The window is Gorilla-branded, but a few dialogs still use Mozilla's wording. Firefox 157 renamed some of its messages, and not every Gorilla rewording was carried to the new names. A few built-in texts that Gorilla never reworded, such as a statement about Mozilla's list of trusted certificate authorities, still name Mozilla on purpose.

### Your logins survive a restart

Many privacy browsers clear cookies when you close them. Gorilla keeps them, by decision, because logging in again after every restart drew complaints. You can clear your data yourself at any time in Settings.

### Some sites show more captchas

Privacy protections make some sites, Google among them, ask you to prove you are human more often. This is a recorded trade-off: no protection is removed to avoid captchas.

### Hotel and airport Wi-Fi login pages do not pop up

Ordinary Firefox detects these "captive portals" by contacting a Mozilla server. Gorilla does not. Open any plain web page by hand and the Wi-Fi login page usually appears.

### Your antivirus may break secure sites

If your antivirus has a feature called HTTPS scanning, web inspection or similar, secure sites show certificate errors. That is Gorilla refusing a certificate your antivirus added. Switch that antivirus feature off, or use another browser for that computer.

### The built-in password manager is still on

Older Gorilla documents said "no password manager". They meant no password-manager add-ons. Firefox's own password manager remains.

### Gorilla.Satellite mode makes the browser look like a phone

In Satellite and Very slow link, sites are asked for their mobile version. A phone on a large screen is a rare mix that a website could notice, and a site you switch back to its desktop version can still see the Android name from JavaScript. Pages you visited stay on disk after you close the browser (history, form data and downloads are still wiped), and a page kept on disk can be out of date until you press Reload. These costs are recorded in decision D-157-33.

### The address bar speaks Gorilla

The empty address bar says "Search with Gorilla or enter address you Apple Moron", whichever search engine is set.

### What this cannot do

- It cannot update itself, and it does not tell you when a new version exists.
- It does not warn you about phishing or malware pages.
- It does not check ordinary website certificates for revocation.
- It does not stop your internet provider seeing which sites you visit.
- It does not make you anonymous. The strong anti-fingerprinting mode is off by default; a determined site can still tell browsers apart.
- It cannot install add-ons other than the built-in uBlock Origin, or other themes, or other languages.
- It does not translate pages, find your location, sync, or suggest searches.
- Gorilla.Satellite mode cannot make your link faster. It was measured on six real sites over an ordinary link and on a test bench that imitates slow and satellite links, not on a real satellite link.
- Some Mozilla code is still compiled in, switched off with its network calls cut: experiments, sync, accounts and telemetry. Removing it is planned, not done.
- Its judgement should not be trusted beyond what the release proofs measured. Battery use, and the speed of the network fixes on real links, are not measured.

## What This Means For You

### Battery, Processor & Memory

Not measured on your kind of computer. On the maintainer's test bench, the browser's peak private memory during a fixed set of pages was 717 MB on an emulated broadband link before this release's network fixes; after them it was 729 MB, within the normal variation between runs (on an emulated Starlink-like link it fell from 906 to 770 MB; on the 5 KB/s link it rose from 553 to 586 MB). The browser keeps up to 1 GiB of recently loaded pages in memory by default. Battery use is not measured.

### Speed

On the local test bench, before this release's fixes, a set of article pages loaded in 0.75 seconds on emulated broadband and 3.92 seconds on an emulated GEO satellite link. On a 5 KB/s link it took 95.6 seconds, and the same again after a restart because nothing was kept on disk. After the fixes: 0.39 seconds on broadband, 0.37 seconds on a Starlink-like link and 3.21 seconds on GEO; the 5 KB/s link is full, so it still takes 95.6 seconds. With Gorilla.Satellite mode on Very slow link, the 5 KB/s link took 41.0 seconds the first time and 23.7 seconds after a restart; on the GEO link after a restart, Satellite took 2.51 seconds instead of 3.78. Opening the same page again on Very slow link asks the site nothing at all. Not connecting to links you only hover over may make a first click a few milliseconds slower. Real-world times are not measured; the real-site sizes are in "Your Internet" below.

### Your Privacy

Nothing is sent about you by the browser itself. What sites can learn about your computer is reduced by the light fingerprinting protection, which still keeps your local time and page dark mode. Your internet provider still sees the names of the sites you visit.

A website also cannot quietly feel its way round your home network. A page you visit could otherwise try to reach your router or printer and time the answers, like someone trying door handles along a corridor to learn which rooms exist. Firefox 157 stops the request only after the knock has already been made; Gorilla stops it before (decision D-157-16), and a site must ask you first. Your own router page, opened by you, still works.

### Your Internet

The browser's own background traffic is the ad blocker's filter lists and, only when a page needs them, the video plug-ins. Gorilla.Satellite mode on Very slow link downloads far less. Measured on six real sites with an empty cache (the times at 5 KB/s are worked out from the bytes):

| Site | As shipped | Very slow link | At 5 KB/s |
|---|---|---|---|
| BBC News | 1,636 KB | 101 KB | about 21 s |
| The Guardian | 1,121 KB | 148 KB | about 30 s |
| DuckDuckGo search | 2,504 KB | 207 KB | about 42 s |
| Reuters | 2,230 KB | 315 KB | about 65 s |
| Wikipedia (Starlink article) | 744 KB | 322 KB | about 66 s |
| CNN | 14,057 KB | 608 KB | about 2 minutes |

Most of the saving comes from leaving JavaScript out. The text of all six pages stays readable.

## The Off Switch

**What it is:** Close the browser and delete its program folder. That removes the program. Your profile stays in your Windows user folder until you delete it too; you can find it from `about:support` before you remove the program. Gorilla.Satellite mode has its own off switch: click its button right of the address bar and choose Off, or choose Off in Settings, General, under Network. Off restores every value the browser shipped with. The strong fingerprinting mode, if you switched it on, is switched off the same way with `privacy.resistFingerprinting`.

**Without it:** Without a clean way out, you would be stuck with a program you cannot remove. Because Gorilla writes nothing into Windows' list of installed programs when you use the zip, there is no uninstaller: deleting the folder is the whole job.

**Think of it like:** A camping stove: when you are done, you pack it back in its box and nothing stays bolted to the kitchen.

## How to install and first run

**Before you start:**
- A 64-bit Windows 10 or 11 computer.
- The installer or the zip, and its SHA-256 code from the release page. Installer: `GorillaUnleashed-157.0-win64-setup.exe`, SHA-256 `02A7A403C314ACDAF55D7C70449CE06C520D45DC30A845D6D6F1C67B0670DBA5` (double-click it and follow the steps). Zip: `Gorilla-Unleashed-157.0-win64.zip`, SHA-256 `1E9CB307A2CC50194C006552FA534F19641D8665B53D0345E97682B4235A474A` (the steps below).
- Free disk space for the extracted program. The zip is 133 MB and the installer 92 MB; the unpacked folder is larger.
- Close any other copy of Gorilla that is running.

**Step 1:** Open PowerShell. Press the Windows key, type `PowerShell`, and press Enter. A window with a blinking cursor opens.
  - You should see: A blue or black window with a line ending in `>`. **Pass:** you can type in it. **Fail:** nothing opens; try again, or right-click the Start button and choose Terminal.

**Step 2:** Go to your Downloads folder. Type this and press Enter:

```powershell
cd "$HOME\Downloads"
```

  - You should see: The line now ends in `Downloads>`. **Pass:** that word is there. **Fail:** an error says the path does not exist; your downloads are somewhere else, so use the folder where your browser saved the zip.

**Step 3:** Calculate the fingerprint of the zip. Type this, with the real file name in place of the angle brackets, and press Enter:

```powershell
Get-FileHash "<the zip file name>" -Algorithm SHA256
```

  - You should see: A table with `Algorithm`, `Hash` and `Path`, and a long code under `Hash`. **Pass:** the code matches the release page exactly. **Fail:** any difference. Delete the zip, download it again and repeat. Do not continue with a file that does not match.

**Step 4:** Extract the browser. Type this and press Enter (it creates a folder called `Gorilla Unleashed` in your Documents):

```powershell
Expand-Archive "<the zip file name>" -DestinationPath "$HOME\Documents\Gorilla Unleashed"
```

  - You should see: A progress bar, then the cursor comes back. **Pass:** the folder `Documents\Gorilla Unleashed` exists and contains a `firefox.exe`, possibly inside one more folder. **Fail:** an error about space or access; free some disk space or pick another folder after `-DestinationPath`.

**Step 5:** Start the browser. In File Explorer, open the new folder and double-click `firefox.exe`. If Windows shows "Windows protected your PC", click **More info**, then **Run anyway**.
  - You should see: The Gorilla browser window with its dark frame. **Pass:** it opens. **Fail:** Windows refuses with no Run anyway button; your organisation blocks unsigned programs, and you cannot use this browser on that computer.

**Step 6:** Check which build you are running. In the address bar type `about:support` and press Enter, then find Build ID.
  - You should see: A long number. **Pass:** it matches the BuildID on the release page. **Fail:** it differs; you opened an older copy.

**Step 7 (optional): switch on Gorilla.Satellite mode.** Click the **Gorilla.Satellite mode** button right of the address bar. A black menu with cyan text opens. Choose **Satellite** or **Very slow link**. Hover over a choice to read what it does.
  - You should see: The button now names the level you chose. **Pass:** that is all; it applies at once. **Fail:** there is no such button; you are running an older build, so check the Build ID (Step 6). To switch it off, choose **Off** in the same menu.

## If Something Goes Wrong

**"Windows protected your PC" with only a Don't run button**
Windows SmartScreen blocks programs that are not signed with a paid certificate.
What to do: Click the small words **More info**. A **Run anyway** button appears. Check the fingerprint first (Step 3) so you know the file is the right one.

**Every secure website shows a certificate error**
Your antivirus, or your employer's network, is inspecting secure traffic with a certificate it added to Windows. Gorilla does not trust those certificates, on purpose.
What to do: Switch off "HTTPS scanning" or "web shield" style features in your antivirus. On a company network, use the browser the company provides.

**The hotel or airport Wi-Fi login page never appears**
Gorilla does not use Mozilla's server to detect these login pages.
What to do: Type any plain address such as `example.com` in the address bar and press Enter. The login page usually appears.

**A film will not play, or a video call has no picture**
The video plug-in is downloaded only when a page asks for it. It may still be downloading, or the download may have been blocked by your network.
What to do: Wait a minute and reload the page. Check that your network allows connections to Google or Cisco.

**I clicked "Add to Firefox" and got a message instead**
Gorilla does not install add-ons or themes. uBlock Origin is already built in.
What to do: Nothing; this is working as designed. If you need that add-on, use another browser for that task.

**The menus are in English but I need another language**
Gorilla is English only, by decision, so there is no translation engine and no language packs.
What to do: Websites still show their own languages. For the browser's menus, use another browser.

**Pages download again after every restart on my slow link**
Gorilla.Satellite mode is Off, so the browser keeps no pages on disk.
What to do: Click the Gorilla.Satellite mode button and choose Satellite or Very slow link (Step 7 above).

**A site does not work in Very slow link (webmail, maps, a shop, a login)**
Very slow link leaves JavaScript out, and these sites need it.
What to do: On that site, open the Gorilla.Satellite mode menu and tick **This site: allow JavaScript**. It is remembered for that site.

**A site's mobile version is poor**
Satellite and Very slow link ask sites for their mobile version.
What to do: On that site, tick **This site: show the normal (desktop) version** in the Gorilla.Satellite mode menu.

**A page looks out of date in Very slow link**
A page you already have opens from the disk without asking the site.
What to do: Press Reload. Reload always fetches a fresh copy.

**The Gorilla icon looks blurry after you put a new version in place.**

**What it is:** Windows keeps a picture of every program icon. When a new Gorilla replaces the old one in the same folder, Windows can keep showing the old, stretched picture.

**What to do:** download **Fix-blurry-icons.cmd** from the release page and double-click it. It asks Windows to draw its icons again; it changes nothing else and needs no administrator rights. If the icon is still blurry, sign out of Windows and sign back in.

## Why a Developer Would Do This

Most privacy browsers switch features off with settings. Settings can be switched back on, by a later update, an add-on, or a mistake. Gorilla cuts the code that would send, so there is nothing to switch back on, and then checks the finished browser with its own network log, not with a promise. The port from Firefox 155 to 157 showed why that matters: the previous release was quietly asking eight Mozilla servers for things, and an earlier check had passed it. Every lesson from that port is now a check that runs on every build.

## Why It Matters That You Can Read This

You are trusting this browser with everything you do on the web. Because the source, the patches, the decisions and their costs are published, anyone can check the claims in this guide: that the calls home are cut, which servers the browser still contacts and why, and what each decision costs you. Because the release proofs measure the actual build, an "ok" means something was measured. If this were a closed browser, "we do not track you" would only mean "we say so".

## Glossary

**Browser** — The program you use to open and read web pages.

**Zip file** — One file that holds many files packed together, which Windows can unpack.

**PowerShell** — A Windows window where you type commands instead of clicking.

**Address bar** — The long box at the top of the browser where you type a web address.

**about:config** — A built-in page that lists every browser setting and lets you change the unlocked ones.

**Phishing** — A fake website made to look like a real one so that you type your password into it.

**Captcha** — A small puzzle a website shows to check you are a person.

**Internet provider** — The company that connects you to the internet, such as a broadband or mobile phone company.

**Plug-in** — An extra piece of software a browser downloads to play certain kinds of video.

**Release** — One published version of the browser, with its files and notes.

## Claim Sources

| Claim | Basis | Evidence |
|-------|-------|----------|
| the browser never calls home | 📄 stated in input | THE RULE: this browser never calls home |
| no automatic updates; updates are manual | 📄 stated in input | Cost: updates are manual. |
| phishing and malware lists are off | 📄 stated in input | Cost: no built-in phishing/malware lists (uBlock still blocks known bad hosts) |
| revocation of ordinary site certificates is not checked | 📄 stated in input | revocation of ordinary site certificates is not checked |
| antivirus HTTPS scanning causes certificate errors | 📄 stated in input | antivirus "HTTPS scanning" and corporate inspection proxies produce certificate errors |
| video plug-ins only on demand from Google and Cisco | 📄 stated in input | fetched only when a page needs them |
| cookies are kept on shutdown | 📄 stated in input | Users stay logged in after a restart. |
| captchas are an accepted cost | 📄 stated in input | Captchas are accepted as a cost |
| 155.0.1 asked eight Mozilla hosts on its own | 📄 stated in input | 155.0.1, still asked eight Mozilla hosts on its own |
| a refused add-on install now shows a message | 📄 stated in input | a refused add-on or theme install now shows a doorhanger |
| satellite mode values and levels | 📄 stated in input | One pref, gorilla.linkmode: 0 = off |
| bench numbers before the network fixes | 📄 stated in input | cold.load_s: 95.6174 |
| Gorilla.Satellite mode has a toolbar button and a Settings switch | 📄 stated in input | RELEASE-NOTES-157.0.md section 6 (D-157-32, D-157-33) |
| Gorilla.Satellite mode measurements on real sites and on the bench | 📄 stated in input | RELEASE-NOTES-157.0.md section 6 |
| the browser keeps up to 1 GiB of pages in memory | 📄 stated in input | browser.cache.memory.capacity |
| profile carries over between versions because it is outside the program folder | 🤖 model inference | *(none — model judgment)* |
| deleting the program folder removes a zip install | 🤖 model inference | *(none — model judgment)* |
| about:policies shows the policy engine active once policies.json ships | 🤖 model inference | *(none — model judgment)* |
| the unpacked folder is larger than the zip | 🤖 model inference | *(none — model judgment; not measured)* |
