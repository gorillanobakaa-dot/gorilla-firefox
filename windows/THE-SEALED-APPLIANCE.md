# ⛔ This browser cannot install add-ons

**Not uBlock Origin. Not a password manager. Not themes. Nothing.**

It is deliberate, it applies to **both the Linux and the Windows build**, and
there is no setting to turn it back on — the extension-installing code is
removed from the browser itself. The reasoning, in one line:

> *A browser you can't extend is a browser strangers can't quietly extend
> either.*

**Right now the browser does not tell you.** Clicking **Add to Firefox** makes
the button go pale and then nothing happens, with no error message. That is the
block working, silently.

Blocking is built in instead — tracking protection, cryptominers,
fingerprinters, cookie banners and HTTPS-only are all on in the shipped build.
**Honestly: that is less thorough than uBlock Origin.** uBO blocks more, hides
the empty space where an ad was, and lets you write your own rules. If uBO is
essential to you, this is the wrong browser, and that is a fair conclusion to
reach.

---

## 📄 The full explanation lives at the repository root

Because this is **not a Windows-specific behaviour** — it is a property of the
whole project — the full document sits one level up:

# **➡ [THE-SEALED-APPLIANCE.md](../THE-SEALED-APPLIANCE.md)**

It covers what an "API lobotomy" is, why an extension is uniquely powerful,
why the threat model is other people rather than you, exactly what you give up,
what protection you get instead, and an honest argument for *and against* the
trade-off.

Related:

- **[../WHAT-WE-CHANGED-AND-WHY.md](../WHAT-WE-CHANGED-AND-WHY.md)** — all 441
  patches across 16 groups, plain language and technical, each with its cost
- **[INSTALLING-UBLOCK-ORIGIN.md](INSTALLING-UBLOCK-ORIGIN.md)** — what happens
  when you try, and how this was mis-documented at first

*(This page is kept here so links to the old location still work, and so anyone
browsing the `windows/` folder sees the warning without having to go looking.)*
