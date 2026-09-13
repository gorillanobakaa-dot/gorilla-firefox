# 🔒 Why you can't install add-ons — the "API Lobotomy"

You went to install uBlock Origin and nothing happened. This page explains
why, what the reasoning was, and what you get instead. It is not an apology —
it was done on purpose — but you deserve to know it was done, because the
browser does not currently tell you.

---

## The one-sentence version

> **A browser you can't extend is a browser strangers can't quietly extend
> either.**

That is the project's own stated philosophy, quoted from its notes. Everything
below follows from it.

---

## What "API Lobotomy" means

A *lobotomy* is the deliberate removal of part of something so it can no longer
perform a particular function. That is exactly what this is, and the name is
the patch author's own.

Firefox has an internal system — an **API** — for installing add-ons. Roughly:

```
you click "Add to Firefox"
   ↓
the website asks the browser to install something
   ↓
the browser downloads it, checks the signature, asks your permission
   ↓
the browser writes it into your profile
   ↓
the add-on runs
```

The lobotomy cuts that chain. Not by hiding the button, not by setting a
preference someone could switch back — by **deleting the ability from the
browser's own code**. There are **14 separate cut points** across three files,
so that every route ends in the same place:

| how you might try | what happens |
|---|---|
| **Add to Firefox** on the add-ons site | cancelled |
| Drag an `.xpi` file onto the window | blocked |
| Menu → **Install Add-on From File…** | blocked |
| `Ctrl+O` on an `.xpi` | blocked |
| Installing a theme | blocked |

The browser is described in its own notes as a **"sealed appliance"** — closer
to a kitchen appliance than a computer program. A toaster does not have a
plug-in system, and that is not considered a defect.

---

## The reasoning

Here is the actual argument, put fairly.

### An extension is not a small thing

When you install an add-on, you typically grant it **"Access your data for all
websites."** Read that again. It means the extension can see every page you
open, every form you fill in, everything you type, your banking session, your
email. Extensions are the single most powerful thing you can add to a browser.

uBlock Origin uses that power well. Not everything does.

### The threat is not you — it is everyone else

You know what you are installing. The concern is what gets installed **when
you are not the one doing it**:

- Malware whose entire purpose is to add a browser extension that watches you
- Bundled installers that quietly add a "search helper"
- Someone with five minutes at your unlocked keyboard
- An employer, a family member, a repair shop, a "helpful" relative
- A copycat extension with a familiar name and a stolen icon

A browser with the install path removed cannot be extended by *any* of them.
Not by malware, not by a person, not by you. The protection is
indiscriminate — that is precisely what makes it hard to defeat.

### It cannot be switched back on

There is no preference for this. No `about:config` entry, no command-line flag,
no hidden menu. It is compiled into the browser. Anything that wants to add an
extension to this build would have to **rebuild the browser from source**.

That is the difference between a setting and a property. Settings get changed.

### The machine it was built for

This layer was written for a 2012 Sony VAIO — a laptop with limited memory
where every extension costs real performance, running for a user who wanted
the browsing surface fixed and quiet rather than configurable.

In that context, "sealed" is not a compromise. It is the product.

---

## What you give up — stated plainly

This is a genuine cost and it should not be dressed up:

- **No uBlock Origin**, no other ad blocker
- **No password manager extension** (Bitwarden, 1Password, KeePass)
- **No Dark Reader**, no custom themes
- **No container tabs extension**, no Tampermonkey, no anything
- **No translation** — the built-in translator is disabled too
- **No automatic updates** — updates come from you, not the browser

If any of those is essential to you, this build is the wrong browser, and that
is a reasonable conclusion to reach.

---

## What you get instead

The important thing: **you are not left unprotected because you cannot install
uBlock Origin.** Protection is built into the browser rather than bolted on
afterwards. Verified in the shipped build:

| protection | state |
|---|---|
| Tracking protection | **on** |
| Social-media trackers blocked | **on** |
| Cryptominers blocked | **on** |
| Fingerprinting blocked | **on** |
| Cookie banners auto-dismissed | **on** |
| Third-party cookies partitioned | **on** |
| HTTPS-only mode | **on** |
| Telemetry | **removed** (33 settings off and locked) |
| Sponsored tiles and content | **removed** |
| AI features | **removed from the code entirely** |

An ad blocker you cannot uninstall, roughly — because it was never an add-on.

**The honest gap:** built-in tracking protection is not as thorough as uBlock
Origin. uBO blocks more, blocks cosmetically (hiding the empty space where an
ad was), and lets you write your own rules. Firefox's built-in protection uses
a broad list and does not do cosmetic filtering. You will see more ads than a
uBlock user does. You will see far fewer than a stock-browser user does.

---

## Is this the right trade-off?

Honestly: **it depends who the browser is for, and that is a real question, not
a rhetorical one.**

**It is a good trade** for a machine you set up for someone else — a parent, a
child, a shared family laptop, a public terminal, a machine you maintain but do
not sit at. Nothing can be added to it. Not by them, not by anything that
reaches them.

**It is a bad trade** for your own daily-driver, if you are the sort of person
who reads this far into a technical document. You can judge an extension. The
lock protects you from a threat you were already handling, and costs you tools
you would use well.

The build cannot tell which of those you are. It picked one.

---

## Can it be changed?

Yes — but only by rebuilding the browser.

The change lives in `patches/07.TOOLKIT`. Removing those 14 rejection points
and rebuilding produces a browser where extensions install normally and every
other privacy protection stays exactly as it is. The two are independent: the
telemetry removal, the tracker blocking and the AI excision have nothing to do
with the extension lock.

Whoever gave you this browser can make that call. It is a deliberate policy,
not a bug — but it is a policy, and policies can be revisited.

---

## What the browser should do about this

Right now the failure is silent. You click, the button greys out, nothing
happens, and there is no message. That is the genuinely indefensible part —
not the policy, but the fact that the browser does not say so.

A sealed appliance should say it is sealed.
