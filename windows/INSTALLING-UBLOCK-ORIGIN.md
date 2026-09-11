# 🛡 Installing uBlock Origin

**Short version: it just works. Use the normal way.** This page exists because
there is also a manual way, and because you might reasonably wonder whether a
"hardened" browser breaks add-ons. It does not — this was tested.

---

## The normal way (30 seconds)

1. Open Gorilla Firefox.
2. Go to **https://addons.mozilla.org/firefox/addon/ublock-origin/**
3. Click the big blue **Add to Firefox** button.
4. A small box asks for permission. Click **Add**.
5. Done. A little shield icon appears near the address bar.

That is it. No warnings, no tricks, no hoops. The add-ons site works normally
in this browser.

**From inside the menus instead:** ☰ menu → **Add-ons and themes**
(or press **Ctrl+Shift+A**) → type `uBlock Origin` in the search box → click it
→ **Add to Firefox**.

---

## The manual way (from GitHub)

Some people prefer to get it straight from the author, Raymond Hill, at
**https://github.com/gorhill/uBlock**. That works too.

### First, something worth knowing

We downloaded both versions and compared them byte for byte:

| | |
|---|---|
| From the add-ons site | `4617614` bytes |
| From gorhill's GitHub | `4617614` bytes |
| SHA-256 | **identical** |

**They are the same file.** The GitHub one is signed by Mozilla too — Raymond
Hill uploads the same signed package to both places. So there is no security
difference. Pick whichever you prefer.

### Step 1 — get the file

1. Go to **https://github.com/gorhill/uBlock/releases**
2. The newest release is at the top. Under it, click **Assets** to expand the
   list if it is collapsed.
3. Download the one ending **`.firefox.signed.xpi`**

   > It will look like `uBlock0_1.74.0.firefox.signed.xpi`. The numbers change
   > with each version — that is fine.
   >
   > ⚠ **Take the one that says `.signed.xpi`.** The others are for Chrome, or
   > are unsigned developer builds that Firefox will refuse to install.

4. Windows may fuss about the download. It is not an `.exe`, so usually it
   does not — but if it does, it is the same nonsense described in
   [WINDOWS-WILL-TRY-TO-STOP-YOU.md](WINDOWS-WILL-TRY-TO-STOP-YOU.md).

### Step 2 — install it

**The easy way:** just **drag the `.xpi` file onto the Gorilla Firefox
window**. Drop it anywhere on a page. The permission box appears. Click
**Add**.

**The menu way**, if dragging is awkward:

1. Press **Ctrl+Shift+A** (or ☰ → **Add-ons and themes**).
2. Find the **gear icon ⚙** near the top right of that page.
3. Click it → **Install Add-on From File…**
4. Find your downloaded `.xpi` and click **Open**.
5. Click **Add** when it asks.

**The very lazy way:** press **Ctrl+O**, pick the `.xpi` file, done.

### Step 3 — check it is switched on

Press **Ctrl+Shift+A** and look at **Extensions**. uBlock Origin should be
there with its toggle **blue / on**.

If it is greyed out or says **Enable**, click that. Firefox sometimes puts
manually-installed add-ons in a "waiting for you to say yes" state — this is a
standard Firefox safety feature against programs that try to sneak extensions
in behind your back, not anything to do with this browser.

---

## "Is it actually working?"

The shield icon near the address bar shows a **number** — how many things it
blocked on the page you are looking at. Visit a news site; the number will not
be zero.

Click the shield → a panel opens with a big power button. That panel is uBlock
Origin. If you see it, it is running.

---

## Does the hardening break add-ons? No. Here is what was checked.

A fair question for a browser that advertises stripped-out telemetry. Tested
on the actual shipped build, not assumed:

| check | result |
|---|---|
| Does the add-ons site load? | Yes — page and **Add to Firefox** button render normally |
| Does the `.xpi` download? | Yes, from both the add-ons site and GitHub |
| Is Mozilla's signature accepted? | **Yes** — Firefox reports `signedState: 2`, "properly signed" |
| Does the blocklist wrongly flag it? | No — `blocklistState: 0`, not blocked |
| Does the browser itself reject it? | No — `appDisabled: false` |
| Does it actually load and run? | **Yes** — it was given a runtime ID and its storage was initialised, which only happens when its code executes |

Nothing in the privacy work touches add-on installation, signature checking or
the extension system. Those were deliberately left alone.

### One thing that *is* switched off

**Recommendations.** Stock Firefox shows "Recommended for you" suggestions in
the add-ons manager. That feature works by sending your browsing behaviour to
Mozilla to pick suggestions — so it is disabled here, along with the rest of
the telemetry.

You can still search for and install anything you like. You simply do not get
suggested things based on what you have been doing.

---

## Add-ons worth having alongside it

uBlock Origin on its own covers most of what people install three or four
add-ons for. It blocks ads, trackers, pop-ups and coin miners out of the box,
with no configuration.

If you want more, the usual companions are a password manager and possibly a
container extension. You do not need another ad blocker — running two makes
things slower and occasionally breaks pages, without blocking anything extra.
