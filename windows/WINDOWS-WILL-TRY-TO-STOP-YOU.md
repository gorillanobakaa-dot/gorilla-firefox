# 😤 Windows will try to stop you. Here is exactly what to do.

**Nothing is wrong. Your download is not broken and your computer is not
infected.** Windows does this to *every* program that has not paid for a
certificate. Read this once and you will never be confused by it again.

You will hit **two** roadblocks: one when you **download**, one when you
**run**. Both are designed so that giving up is the easiest thing to do.

---

## Roadblock 1 — downloading

You click the download link. Instead of a file, you get something like:

> **GorillaUnleashed-155.0.1-win64-setup.exe was blocked because it could
> harm your device**

or

> **...isn't commonly downloaded. Make sure you trust it before you open it.**

### Here is the sneaky part

Look at that message. You will see an obvious **Delete** or a **bin icon**.
That is the *only* thing that looks clickable.

The button that keeps your file is **hidden**. It is behind a **tiny arrow
(`⌄`)** or **three little dots (`…`)** at the side of the message. You have to
know it is there.

That is not an accident. The easy, obvious, big-target action is the one that
throws your download away. The action you actually want is small, unlabelled,
and one extra click deeper.

### Edge (the blue "e", Windows' own browser)

1. Find the download message at the top right.
2. **Hover your mouse over the file name.** Little icons appear.
3. Click the **three dots `…`** (not the bin).
4. Choose **Keep**.
5. Another box appears. If you only see *Delete* and *Cancel*, click
   **Show more**.
6. Now click **Keep anyway**.

Yes — **two** rounds of this. That is normal.

### Chrome

1. Look at the download bubble, top right.
2. Click the **little arrow `⌄`** next to the file name — or right-click the
   file name.
3. Choose **Keep**.
4. If asked again, click **Keep anyway** or **Download insecure file**.

### Firefox

1. Open the downloads arrow, top right.
2. **Right-click** the file.
3. Choose **Allow download**.

Firefox is the least obstructive of the three. Make of that what you will.

---

## Roadblock 2 — running it

You double-click the installer. A **big blue full-screen box** appears:

> ### Windows protected your PC
> Microsoft Defender SmartScreen prevented an unrecognised app from starting.
> Running this app might put your PC at risk.
>
> **[ Don't run ]**

**Look at that box. There is only one button, and it says "Don't run".**

There is no visible way to continue. Most people stop here, and that is the
intention.

### What to actually do

1. Find the small grey words **More info**. They are *above* the button, and
   they do not look like a link.
2. **Click "More info".**
3. The box expands and a **second button appears: `Run anyway`**.
4. Click **Run anyway**.

That is it. The installer opens normally and takes about a minute.

> The "Run anyway" button exists the entire time. It is simply not drawn until
> you click a word that does not look clickable.

---

## Why does this happen?

**Because we have not paid Microsoft's toll, and we are not going to.**

To make these warnings disappear, a developer buys a **code-signing
certificate**. It costs roughly **£200–£600 every single year**, forever, and
it has to be renewed. That is the actual mechanism. Not "being trusted" — a
subscription.

Gorilla Firefox is free, has no company behind it, and takes no money from
anyone. Paying a yearly fee to a certificate authority so that Windows stops
frightening people would mean charging you for the browser. That is the whole
thing this project exists not to do.

### It gets worse, honestly

Even developers who *do* pay still get warned about at first. SmartScreen also
scores apps on **reputation**, which is built from *how many people have
already downloaded it*. A brand-new signed app is still "unrecognised" until
enough people push through the warning.

So the system is: pay every year, **and** be popular, or your users get told
you might be malware.

### Is the warning ever real?

**Yes — and this is the important bit.** Criminals really do spread malware as
unsigned `.exe` files. The warning is not pure theatre, and you should not
train yourself to click through it on autopilot.

The honest position is this: **the warning does not mean "this file is
dangerous". It means "Windows does not know who made this."** Those are very
different statements, and Windows deliberately words it as the first one.

So do not just trust us because we say so. **Check the file yourself.** It
takes ten seconds.

---

## ✅ Prove the file is the real one (10 seconds)

Every release has a **SHA-256** — a fingerprint. If one single byte of the file
were different, the fingerprint would be completely different. It cannot be
faked.

**1.** Open the folder with your download. Click the address bar at the top,
type `cmd`, press Enter.

**2.** Paste this and press Enter:

```
certutil -hashfile GorillaUnleashed-155.0.1-win64-setup.exe SHA256
```

**3.** Compare the long string it prints with the one in **`SHA256SUMS.txt`**
on the release page.

**Match → the file is exactly what we built.** Not tampered with, not a
lookalike, not corrupted on the way down.

**Doesn't match → delete it and download again.** If it still doesn't match,
do not run it, and tell us.

*(PowerShell instead of cmd? Use
`Get-FileHash .\GorillaUnleashed-155.0.1-win64-setup.exe -Algorithm SHA256`.
It prints in capitals — that doesn't matter, capitals and lowercase are the
same hash.)*

---

## One more thing Windows may do

Even after installing, Windows remembers that a file "came from the internet"
by attaching a hidden tag to it. If something behaves oddly:

Right-click the file → **Properties** → at the bottom, tick **Unblock** →
**OK**.

---

## The short version

| What you see | What it means | What to click |
|---|---|---|
| "Blocked because it could harm your device" | Windows doesn't recognise the publisher | `…` or `⌄` → **Keep** → **Keep anyway** |
| Blue "Windows protected your PC" | Same thing again | **More info** → **Run anyway** |
| No "Run anyway" button | It's hidden until you click **More info** | **More info** |
| Download vanished | The default action deleted it | Download again, use `…` → **Keep** |

**None of these mean anything is wrong with the file.** They mean nobody paid
the yearly fee. Check the SHA-256 and decide for yourself — that is a better
guarantee than a certificate anyway, because it checks the *actual file* rather
than who bought a licence.
