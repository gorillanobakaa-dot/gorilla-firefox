# 14.EGRESS.LOCKDOWN — Telemetry & Remote-Channel Severance (Unifying Topic)

> **Created:** 2026-08-01 · **Status:** Consolidation / index topic
> **Scope decision (author, 2026-08-01):** the coherent super-topic uniting four
> deployed patch clusters that all answer one question — *"can this browser send
> data out, or be driven from outside, without the user's say-so?"* Answer: no.

This folder does **not** hold new patches. It is the **single source of truth**
that unifies four topics whose patches live elsewhere, reconciles a doctrine
contradiction that had crept into the older docs, and points at the authoritative
per-topic documentation. Read this first; then dive into the source topic dirs.

---

## What this unifies (and where the patches actually are)

| Cluster | Patches live in | One-line |
|---|---|---|
| **Necko Glean gate** | `../03.NETWORKING/` | Compile-time `GLEAN_DISABLED 1` preprocessor gate in 4 netwerk `.cpp` files (plus socket tuning, documented there) |
| **Glean / FOG core** | `../13.TELEMETRY.KILL/` | `GORILLA_TELEMETRY_OFF` const-DCE in vendored glean-core + `FOG::InitializeFOG` no-op + `MemoryTelemetry` short-circuit — **measured 13.2% → 0.39% parent CPU** |
| **Normandy / Nimbus** | `../12.MOZAMBIQUE.DRILL/` | Three-shot: `enabled=false` + `api_url=""` + 60-year timer, policy-locked |
| **Remote automation** | `../09.REMOTE/` | Physical-lock hard-disable of Marionette + RemoteAgent (WebDriver BiDi) |

**Explicitly OUT of scope (cross-linked, not folded in):**
- **WebIDL** — not telemetry. It appears only in the **Clang-21 build-fix** work
  (`IsComplete<T>` SFINAE in `Maybe.h`/`MaybeStorageBase.h`,
  `BufferSourceBindingFwd` redefinition, `Codegen.py`). Home: `../07.TOOLKIT/`
  build lessons. Listed here only because the author grouped it in the original
  ask; it is a build-system topic, kept separate on purpose.

---

## THE DOCTRINE RECONCILIATION (read this before touching any of it)

The older docs in `03.NETWORKING` and several DB atoms use the words **"excision,"
"delete," "lobotomy," "scour."** **The deployed reality is the opposite of
deletion.** Every one of these patches is a **soft gate** — a compile-time or
runtime short-circuit that leaves every symbol, factory, `moz.build` entry, and
module *present and compiled*, and only stops the *work* from running.

**Why this matters — it is a landmine for the next agent:**
- Structural excision of the telemetry/experiment machinery was **TRIED and
  ABANDONED**. Deleting Glean symbols caused `NS_ERROR_FACTORY_NOT_REGISTERED`
  and required **157 shim headers** to even compile. Hollowing out
  `ExperimentAPI`/`Normandy` crashed **145+ dependents** (`UrlbarPrefs`,
  `FirstStartup`, boot sequence) with `TypeError`/`ModuleNotFoundError`.
- This is **Prime Directive 0**: *neutralize in place, never excise.* Keep the
  body, stop the heart.
- Residual excision-era artifacts still in the DB — `fog_glean_excision_sop.xml`,
  `excision_targets.xml`, `excision_roadmap.xml` — describe the **abandoned**
  approach. They are history, **not a roadmap**. Do not resurrect them. (This is
  the same "unrecorded verdict resurrects as a bug" failure mode that bit the
  privacy-pane promo and the 1.5MB warning.svg on 2026-08-01.)

**Vocabulary correction, applied going forward:** prefer **gate / short-circuit /
neutralize / dilate / lock**. The word "excision" in older prose means, in
practice, one of these soft techniques — read it as such.

### Gated, not dead — "the fly in the jar" (author's framing, 2026-08-01)

Equally important honesty in the OTHER direction: do not oversell the gates as
"the telemetry is dead." It is **alive and sealed in**, like an annoyed fly
buzzing in a jar — it can't get out, but it still moves. Concretely:

| State | What it means | Examples |
|---|---|---|
| **Physically gone** | optimizer deleted the code from

---

## The egress trust chain — where each topic cuts it

Telemetry data, if it flowed, would travel:

```
 call site ─▶ metric record ─▶ dispatcher queue ─▶ ping assembly ─▶ uploader ─▶ Mozilla endpoint
     │              │                  │                                │
 (13) const     (13) FOG no-op     (13) dispatcher              (03) Necko-internal
  DCE guard      → never flushed     launch() drops              Glean metrics gated
                                                                  at compile time
 (12) Normandy/Nimbus recipe+experiment channel: switched off, endpoint erased, 60-year timer, locked
 (09) Marionette / RemoteAgent inbound control sockets: physically locked, flags discarded
```

The design principle across all four: **sever as early in the chain as possible.**
Cutting at the *recording* stage (13) is strictly stronger than cutting at the
*upload* stage (what `toolkit.telemetry.*` prefs do) — there is no staged data to
leak even if a later stage regressed.

---

## Deliverables of this consolidation (2026-08-01)

- `14-egress-remote-lockdown.LAYMAN.md` — the whole cluster in plain English.
- `14-egress-remote-lockdown.DEVELOPER.md` — the cross-cutting architecture,
  the four mechanisms side by side, the shared invariants and debt.
- `14-egress-remote-lockdown.AUDIT.md` — IBM A–F over the unified topic.
- Distilled findings are kept with the project's own notes
  (the DB's telemetry+remote category), ingested into the `firefox_154` collection.

Authoritative per-topic detail remains in each source dir's own
`.LAYMAN/.DEVELOPER/.AUDIT` set — this topic indexes and unifies them, it does
not replace them.
