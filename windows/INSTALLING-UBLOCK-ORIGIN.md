# ⛔ Extensions cannot be installed in this build

**An earlier version of this page said uBlock Origin "just works". That was
wrong.** Extension installation is deliberately blocked. This page now explains
what actually happens and why.

---

## What you see

You open the add-ons site, find uBlock Origin, click **Add to Firefox**.

The button goes pale. Nothing else happens. No error, no permission box, no
message — it just sits there.

That is not a glitch. It is the browser working exactly as this build was
written to work.

---

## What is actually happening

The Gorilla patch set contains a change its own comments call the
**"API LOBOTOMY"** — a zero-trust extension policy that rejects every route by
which an add-on could be installed. It lives in `patches/07.TOOLKIT` and
touches three files:

| file | rejection points |
|---|---|
| `toolkit/mozapps/extensions/internal/XPIInstall.sys.mjs` | 9 |
| `toolkit/mozapps/extensions/AddonManager.sys.mjs` | 4 |
| `toolkit/mozapps/extensions/LightweightThemeManager.sys.mjs` | 1 |

Every route is closed:

| route | result |
|---|---|
| **Add to Firefox** on the add-ons site | cancelled |
| Drag an `.xpi` onto the window | blocked |
| **Install Add-on From File…** | blocked |
| `Ctrl+O` on an `.xpi` | blocked |
| Themes | blocked |

### Why there is no error message

Two of the rejection points behave differently, and that difference is the
whole reason the failure is so confusing.

`XPIInstall.install()` **throws**, which at least writes to the browser
console:

```
XPIInstall.sys.mjs:1395: Error: [GORILLA] Installation rejected: uBlock0@raymondhill.net
```

But `AddonManager.installAddonFromWebpage()` — the one the website actually
calls — does this instead:

```js
logger.error(`[GORILLA] AddonManager: Web installation rejected.`);
aInstall.cancel();
```

It **cancels silently**. The add-ons site is left waiting for a reply that
never arrives, so its button stays in the loading state forever. From the
outside it is indistinguishable from a hung page.

---

## Why this page was wrong

The original test dropped the `.xpi` directly into a profile's `extensions/`
folder and confirmed the extension loaded. Every result it reported was true:

- the signature verified (`signedState: 2`)
- the blocklist did not flag it (`blocklistState: 0`)
- the browser did not disable it (`appDisabled: false`)
- it was instantiated and its storage initialised

All correct, and all irrelevant. Dropping a file into `extensions/` is a
**sideload** — it goes nowhere near `AddonInstall.install()`, which is the
exact function containing the block. The test exercised a path no user takes
and declared the path every user takes to be working.

This is the same mistake catalogued a dozen times in `BUILD-PLAYBOOK.md`:
**testing something adjacent to the property that matters.** A green result on
the wrong route is worse than no test, because it gets written into
documentation.

It was found only by clicking the button in a real window and reading the
browser console.

---

## Can it be turned off?

Not with a preference. The block is compiled into the JavaScript that ships
inside `omni.ja` — there is no pref, no `about:config` switch, and no
command-line flag. Removing it means editing `patches/07.TOOLKIT` and
rebuilding.

Whether it should be removed is a policy decision, not a bug fix. The patch
was written deliberately, and a browser that cannot load extensions is
genuinely more locked down. It is also a browser that cannot run uBlock
Origin — which, for an ad-blocking-focused build, is a real cost.

That decision belongs to whoever is deploying it.

**➡ [Why it was done, and what you get instead](../THE-SEALED-APPLIANCE.md)** —
the full reasoning in plain language, the honest cost, and what protection is
built in given that you cannot add an ad blocker.
