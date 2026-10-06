## 🎭 In plain words: it passes the leak test, so why does a fingerprint test still call me "unique"?

**This build passed the four-hour leak test: 19 of 19 rules.** Nothing leaves your computer that you did not ask for.

Fingerprint test websites (the ones that say "your browser is unique") measure something different: how recognisable your browser looks to a website you are already visiting. Two tricks matter here.

- **Canvas fingerprinting.** A website secretly asks your browser to draw a small hidden picture. Every computer draws it very slightly differently (graphics card, screen settings, fonts), and those differences work like a signature that can follow you from site to site, no cookies needed.
- **Font fingerprinting.** A website quietly checks which fonts your computer has. Everyone's mix is a little different, so the list can identify you too.

A friend asked the maintainer about this, and the answer came as a story from survival training. Picture a prisoner being questioned. The one who refuses to say a word is the one who gets marked as "hiding something" and gets the worst of it. Survival courses teach a smarter way: have a few cover stories ready, each plausible, none of them the truth. Every story sends the questioners off to check it, and by the time they have, it is worthless.

**Gorilla is the prisoner with the cover stories, and it goes one better: the truth never comes out.**

- **Canvas:** Gorilla never hands over your real drawing. It adds a tiny, invisible amount of random "noise" to it. Each website gets a different cover story, and every website gets a new one each time you restart the browser. A fingerprint test sees a result nobody else has and calls it "unique", but that "unique" signature belongs to nobody and changes before anyone can use it to follow you.
- **Fonts:** websites only see the standard fonts that come with Windows for your language, not the extra ones you installed.
- **Graphics card:** websites see a generic name, not your graphics card's model.

Refusing to answer at all would be the hero who stands out: a browser that blocks the drawing outright is rare, so it is easy to recognise. Gorilla answers every question politely, with a different plausible answer each time.

These protections are switched on and locked in this build (Firefox's fingerprinting protection, `privacy.fingerprintingProtection`). The strictest Tor-style mode stays off by default because it breaks more websites; you can switch it on yourself (`privacy.resistFingerprinting`).
