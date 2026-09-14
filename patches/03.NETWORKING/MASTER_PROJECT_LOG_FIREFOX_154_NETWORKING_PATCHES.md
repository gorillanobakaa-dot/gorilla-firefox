# MASTER PROJECT LOG — FIREFOX 154 NETWORKING PATCHES

---

## Part 1: History, Roadmap & Overview
*(Originally from 00_NETWORKING_HISTORY_AND_ROADMAP.md)*

### Document Control
- **Category:** Necko Telemetry Scouring & Socket Tuning
- **Last Updated:** 2026-07-08
- **Status:** Active Development
- **Verification Required:** Yes (see Validation section)
- **Related Documents:**
  - `../DOCUMENTATION_TEMPLATES.md` (IBM format guide)
  - `../01.MEDIA/MASTER_PROJECT_LOG_FIREFOX_154_MEDIA_PATCHES.md` (VA-API buffers - COMPANION)
  - `../02.GPU/MASTER_PROJECT_LOG_FIREFOX_154_GPU_PATCHES.md` (WebRender overrides)
  - `../10.OVERRIDES/user.js` (preference layer)

---

### Executive Summary

**What This Does (Plain Language):**
This folder alters Firefox's networking layer (Necko) to match our custom Linux kernel settings. It:
1. Shuts down backend telemetry connections (Glean metrics) that spy on browser connection events.
2. Expands the internal network buffers to handle high-speed video transfers over UDP.
3. Increases the number of simultaneous DNS resolution tasks from 8 to 16.
4. Keeps active TCP connections alive aggressively to prevent idle timeouts.

**Technical Summary:**
Necko telemetry excision and socket tuning for Sony VAIO SVE14A3AJ (Intel Core i7-3632QM, Debian 13 Wayland + custom Linux 7.x-unleashed.gorilla kernel). Deletes telemetry hooks (`GLEAN_DISABLED 1` and `MOZ_TELEMETRY_REPORTING 0` preprocessors) from Necko modules, scales DNS thread resolver pools to 16, overrides socket send/recv windows up to 64 MB for HTTP/3 UDP channels, and forces aggressive TCP keepalive timings (15s idle, 5s interval, 3 probes).

---

### System Architecture & Logic

```
Necko Socket Thread / DNS Worker Thread Pool / Parent Channel
        |
        +-- nsHostResolver.cpp: SetThreadLimit(16) / SetIdleThreadLimit(12)
        |   Increases DNS worker concurrency for responsive page load
        v
+-----------------------------+
| nsSocketTransport2.cpp      |  Overrides TCP keepalive defaults unconditionally:
| (TCP Socket Layer)          |  - TCP_KEEPIDLE = 15s (forces active keepalive early)
+-----------------------------+  - TCP_KEEPINTVL = 5s (rapid probe intervals)
        |                        - TCP_KEEPCNT = 3 (fast drops for dead routes)
        v
+-----------------------------+
| HttpConnectionUDP.cpp       |  Scales HTTP/3 UDP buffer properties dynamically:
| (UDP / QUIC Socket Layer)   |  - SetRecvBufferSize(64MB)
+-----------------------------+
        |
        v
+-----------------------------+  Glean / Telemetry metrics disabled via compile-time
| HttpChannelParent.cpp       |  preprocessor blocks (#ifndef GLEAN_DISABLED):
| nsHttpConnectionMgr.cpp     |  - Gated: back_pressure_suspension_rate
| Http3Session.cpp            |  - Gated: back_pressure_suspension_delay_time
+-----------------------------+  - Gated: http3_session_version metrics
```

**Kernel Configuration Contract:**
These socket buffer sizes expect cooperating system limits configured in `/etc/sysctl.d/99-gorilla-network.conf`:
```ini
# Maximum socket buffer sizes (64 MB)
net.core.rmem_max = 67108864
net.core.wmem_max = 67108864
# Enable BBR congestion control and FQ-CoDel queueing
net.ipv4.tcp_congestion_control = bbr
net.core.default_qdisc = fq_codel
```

---

### Component Documentation

#### 1. nsHostResolver.cpp — Concurrency Expansion
- **Deploy Path:** `netwerk/dns/nsHostResolver.cpp`
- **Tuning:** Thread pool limit raised to 16, idle thread limit raised to 12.
- **Verification:** Confirm thread limits in constructor output log.

#### 2. nsSocketTransport2.cpp — Keepalive Overrides
- **Deploy Path:** `netwerk/base/nsSocketTransport2.cpp`
- **Tuning:** Hardcodes TCP_KEEPIDLE to 15, TCP_KEEPINTVL to 5, and TCP_KEEPCNT to 3.
- **Verification:** `ss -ie | grep keepalive` on active connections should reflect low timing intervals.

#### 3. HttpConnectionUDP.cpp — Buffer Tuning
- **Deploy Path:** `netwerk/protocol/http/HttpConnectionUDP.cpp`
- **Tuning:** Passes `StaticPrefs::network_http_http3_recvBufferSize()` (typically 64MB) to the socket buffer allocator.
- **Correction:** The UDP send buffer is NOT configured currently; it defaults to system limits.

---

### Chronological History (Recovered)

#### 2026-06-08/09
**Initial Networking Patches Applied:**
DNS thread expansions and socket buffer overrides introduced in Firefox 153. A buggy helper method (`SetIsPrivate`) was mistakenly introduced by a script generator, causing immediate compile failures. It was quickly reverted, restoring Necko build stability.

#### 2026-07-05
**Firefox 154 Rebase:**
Patches migrated and adapted to Firefox 154 codebase.

#### 2026-07-08
**Glean Scouring Phase:**
Scoured Necko files for residual telemetry metrics. Wrapped parent-side backpressure statistics in `HttpChannelParent.cpp` under `#ifndef GLEAN_DISABLED` guards.

---

## Part 2: Audit & Performance Assessment (2026-07-10)

We completed a full verification of the C++ implementations against the claims made in the roadmap.

### 1. Verification Checklist

| Claim / Goal | Status | Details |
| :--- | :--- | :--- |
| **Telemetry Lobotomy** | ✅ VERIFIED | Preprocessor macros (`GLEAN_DISABLED 1` and `MOZ_TELEMETRY_REPORTING 0`) successfully wrap all metrics loops inside `Http3Session.cpp`, `nsHttpConnectionMgr.cpp`, and `nsUDPSocket.cpp`. |
| **64MB UDP Receive Buffers** | ✅ VERIFIED | `mSocket->SetRecvBufferSize` is properly wired to preference metrics in `HttpConnectionUDP.cpp`. |
| **32MB UDP Send Buffers** | ❌ MISSED | **The baseline code lacks UDP send buffer configurations.** Socket send buffers are left to standard kernel defaults. |
| **16 DNS Resolver Threads** | ✅ VERIFIED | Resolvers successfully call `SetThreadLimit(16)` and `SetIdleThreadLimit(12)` in `nsHostResolver.cpp`. |
| **Aggressive TCP Keepalive** | ✅ VERIFIED | `nsSocketTransport2.cpp` sets idle delay to 15s and probe interval to 5s unconditionally. |
| **Parent Backpressure Telemetry** | ✅ VERIFIED | Residual Glean metrics in `HttpChannelParent.cpp` are successfully gated under `#ifndef GLEAN_DISABLED`. |

---

### 2. High-Fidelity Performance Opportunities

The following knobs and changes can be applied to further improve Necko throughput:

#### A. Configure UDP Send Buffer Size
- **Opportunity:** Call `SetSendBufferSize` on UDP sockets in `HttpConnectionUDP.cpp` (inside `InitCommon`) to prevent upload pacing bottlenecks.
- **Tweak:**
  ```cpp
  rv = mSocket->SetSendBufferSize(33554432); // 32MB send window
  ```

#### B. Wire Upload Pacing
- **Opportunity:** Wire the defined constant `kGorillaUploadChunkSize = 256 * 1024` into the upload data stream inside `nsHttpTransaction.cpp::ReadSegments` to pace large uploads against BBR congestion windows.

#### C. Reduce DNS Negative Cache Lifetime
- **Opportunity:** Change `#define NEGATIVE_RECORD_LIFETIME 60` to `15` inside `nsHostResolver.cpp`. This reduces delay when dynamic signaling nodes quickly shift IP configurations.

---

## Part 3: Detailed Breakdown of Flagged Issues & Buffer Asymmetry

Here is a plain-English and technical breakdown of the flagged issues in the networking audit:

### 1. 🟠 HIGH-001: Missing UDP Send Buffer Sizing
- **What it means (Layman):** Imagine widening a highway to 8 lanes for incoming traffic (64MB UDP receive buffers for video playback) but leaving the exit ramps restricted to a single lane (default kernel send buffers for uploads). If you try to upload data or participate in a high-resolution video call, the outgoing data gets bottlenecked, causing packet loss and lag.
- **Technical details (Developer):** In `HttpConnectionUDP.cpp::InitCommon()`, the code calls `mSocket->SetRecvBufferSize(StaticPrefs::network_http_http3_recvBufferSize())` but completely omits setting `SO_SNDBUF` (`mSocket->SetSendBufferSize(...)`).
- **Why it's a defect:** During high-speed HTTP/3 (QUIC) transmissions, asymmetric buffer sizes conflict with our kernel's **BBR congestion control** and **FQ-CoDel** pacing, leading to buffer starvation on upload streams.
- **The Fix:** Add a line to explicitly pin the send buffer size to 32MB:
  ```cpp
  mSocket->SetSendBufferSize(33554432); // 32 MB send window
  ```

### 2. 🟡 MED-001: Unused Upload Pacing Constant
- **What it means (Layman):** You have calculated the perfect size for package shipments to keep traffic moving smoothly (the `kGorillaUploadChunkSize` limit of 256 KB), but you forgot to tell the shipping clerk to actually split the cargo into those package sizes. The cargo is still shipped in massive blocks, which causes immediate shipping lanes congestion (bufferbloat).
- **Technical details (Developer):** `nsHttpTransaction.cpp` defines a constant:
  ```cpp
  const uint32_t kGorillaUploadChunkSize = 256 * 1024; // 256 KB
  ```
  However, inside `nsHttpTransaction::ReadSegments()`, this constant is never referenced. The transaction reads whatever the stream manager provides in one large block.
- **Why it's a defect:** Without pacing these reads, the browser dumps huge bursts of data into the socket queue at once. This degrades **BBR's** RTT (Round Trip Time) estimations.
- **The Fix:** Gate segment reads inside `ReadSegments()` to read a maximum of 256 KB per cycle when dealing with large uploads.

### 3. 🟢 LOW-001: Excessive Negative DNS Lifetime Cache
- **What it means (Layman):** If you try to call a friend and get a busy signal, you wait 60 seconds before trying their number again, even though they might have hung up and become available in 10 seconds. 
- **Technical details (Developer):** In `nsHostResolver.cpp`, the negative cache record duration is defined as:
  ```cpp
  #define NEGATIVE_RECORD_LIFETIME 60 // 60 seconds
  ```
- **Why it's a defect:** For dynamic servers (like WebRTC signaling hosts that change IP addresses quickly or fall back to relays), a failed lookup is cached for a full minute, blocking reconnection attempts.
- **The Fix:** Change the definition to 15 seconds:
  ```cpp
  #define NEGATIVE_RECORD_LIFETIME 15
  ```

---

## Part 4: Technical Analysis of Buffer Asymmetry & Memory Safety

### Why is the upload window set asymmetrically?

#### 1. The "Web-Consumer" Bias (Upstream Defaults)
Historically, web browser engines are designed under the assumption that clients are primarily **consumers** of data (downloading videos, loading images, fetching pages) rather than massive uploaders. 
- Upstream Firefox allocates large receive buffers (`network.http.http3.recvBufferSize` up to 64MB) to prevent incoming packet loss on high-bandwidth streams (like AV1/VP9 video).
- In contrast, outgoing uploads are treated as short, bursty control messages (HTTP GET/POST API payloads), so upstream simply delegates the send buffer size to the operating system's auto-tuning defaults.

#### 2. Safeguarding against RAM Bloat on Socket Creation
Unlike receive buffers which are allocated dynamically per-active-channel, setting a high static `SO_SNDBUF` (like 32MB) on every socket initialization forces the kernel to immediately lock down that memory window for output queues. 
- Since Necko spawns dozens of concurrent connections, statically forcing 32MB buffers on every socket could easily allocate hundreds of megabytes of system memory (RAM) instantly, even if the connection only uploads a 2KB header.
- Leaving it unconfigured was likely an intentional safety choice to prevent memory exhaustion (OOMs) on machines with less RAM.

#### 3. Relying on Linux TCP/UDP Kernel Auto-Tuning
On modern Linux kernels, the socket layer auto-tunes buffer sizes dynamically based on measured RTT (Round Trip Time) and bottleneck bandwidth (especially under TCP). 
- The original author likely assumed the Linux kernel's sysctl properties (`net.ipv4.tcp_wmem` and dynamic socket allocation) would scale the upload window automatically.
- **The Catch:** For UDP (which HTTP/3 / QUIC runs on), Linux kernel auto-tuning is much less aggressive than TCP, meaning the upload buffer remained clamped at the low default baseline (usually 128KB–256KB) while the download buffer scaled up to 64MB.

---

### What's the maximum safety size we can increase to on the UDP side without hogging the memory?

For your VAIO laptop with **16 GB of RAM**, the optimal maximum safety size for the UDP send buffer (`SO_SNDBUF`) is **`4,194,304` bytes (4 MB)**.

#### Why 4 MB is the Sweet Spot:

1. **Prevents Memory Hogging:**
   - In a typical heavy browsing session, Firefox might open up to **16 concurrent UDP/QUIC streams** (for media networks, WebRTC, and HTTP/3).
   - Statically setting **32 MB** per socket could lock up **512 MB** of memory immediately.
   - Statically setting **4 MB** per socket clamps the maximum active UDP upload pool to a highly safe **64 MB** total, which is negligible on a 16 GB machine.

2. **Perfect Pacing for Upstream BBR:**
   - At **4 MB**, the socket buffer is large enough to saturate a **1 Gbps upload link** at **32ms of latency** (Bandwidth-Delay Product: 1000 Mbps * 0.032 s = 4 MB).
   - This provides BBR congestion loops with enough room to pace packets smoothly without buffer starvation, while preventing bufferbloat.

3. **Aligns with FQ-CoDel:**
   - FQ-CoDel handles buffer congestion best when queues are not overly saturated. A 4MB send buffer matches the dynamic queue size of high-speed household uploads perfectly.

#### Recommended Value:

```cpp
mSocket->SetSendBufferSize(4194304); // 4 MB upload window
```

---

## Part 5: Outbound Security & Background Connection Audit

To guarantee Firefox is not leaking data or connecting to background telemetry, dictionaries, translators, AI assistants, PDF telemetry, or dynamic experiments, the following security measures are locked into the build:

### 1. The Mozambique Drill — Dynamic Studies Exclusion
Firefox's Normandy and Nimbus C2 experiment engines are neutralized at the compilation and xpcom layer:
- **`app.normandy.enabled`** is locked to `false` via system policies.
- **`app.normandy.api_url`** is wiped to `""`, triggering initialization aborts.
- **RecipeRunner & RemoteSettingsLoader** fallback loops are dilated to 60 years (`1893456000` seconds). The loader threads are functionally inert and will make no network requests for 60 years.

### 2. Local-Only Translator & Extension Locks
- **`browser.translations.enable`** is set to `false`.
- **`browser.translations.select.enable`** is set to `false`.
- **`extensions.translations.disabled`** is set to `true` to block translations extensions.

### 3. PDF.js & AI Chatbot Shielding
- **`browser.ai.control.pdfjsAltText`** is overridden to `false` in `all.js`, preventing the browser from attempting local or remote AI models to transcribe or parse PDF content.
- Telemetry modules inside PDF.js (`pdfjs.enableTelemetry`) are scoured.

All outbound connections remain locked down, and the browser cannot connect to unauthorized background services.


---

# ═══ CONSOLIDATION 2026-08-02 — side documents merged VERBATIM below; originals deleted (recoverable: merged-docs-backup-2026-08-02.tar.gz + git history) ═══


---

# ═══ REGENERATION 2026-08-04 — dual-track docs + audit regenerated from the live tree; supersedes the 2026-08-02 merge below-the-fold, which carried the since-reverted Necko telemetry-fencing claims ═══

> The three merged documents that follow were regenerated on 2026-08-04 by the doc-audit toolkit
> (`dual-track code prep`/`render`, quality gate PASS: audit 98, developer 90, layman 91) against the
> patched live tree at `the source tree`, and re-verified byte-for-byte. They REPLACE the
> 2026-08-02 verbatim merges of the same three files. The correction is substantive: the prior merges
> asserted Necko-layer Glean/telemetry fencing (`GLEAN_DISABLED` / `MOZ_TELEMETRY_REPORTING 0`) in
> HttpChannelParent / nsHttpConnectionMgr / Http3Session / nsUDPSocket. That fencing was REVERTED in the
> 2026-08-01/02 reconciliation (those four files are byte-identical to vanilla; their .patch files were
> deleted; `grep GLEAN_DISABLED` returns nothing, re-confirmed 2026-08-04). This room is four
> kernel-matched tuning patches only; telemetry containment lives in the locked prefs (05.PREFS) and
> topic 13.TELEMETRY.KILL. Two further stale claims from the old merges were also corrected: the HTTP/3
> receive buffer is HARD-CODED to 64 MB (`SetRecvBufferSize(67108864)`), not read from
> `network_http_http3_recvBufferSize`; and the buffer path GRACEFULLY DEGRADES (log + continue) rather
> than “failing visibly” — vanilla's abort (Close + return) was removed. The append-only forensic trail
> (VERIFICATION / RESOLUTION 2026-08-02, AUDIT CORRECTION 2026-08-03) is preserved unchanged below.

---

# ═══ MERGED DOCUMENT: 03-networking.AUDIT.md (verbatim · sha256:117317526161ad34 · regenerated 2026-08-04) ═══

# IBM-Style Audit Report: 03.NETWORKING

## SECTION A: DOCUMENT CONTROL

| Attribute | Value |
|---|---|
| **Target** | 03.NETWORKING |
| **Files scanned** | see payload |
| **Date / time** | 2026-08-04 07:12:32 |
| **Audit status** | PASS |

## SECTION B: EXECUTIVE SUMMARY (Plain Language)

This room re-tunes four spots in Firefox's networking code so the browser cooperates with the computer's custom Linux kernel instead of fighting it. It sets bigger data buffers for video and uploads, keeps connections from silently dying on cheap routers, lets Firefox look up many web addresses at once, and retries failed lookups in 3 seconds instead of 60. Think of it as a car service that matches the engine to the road it actually drives on. None of it touches your private data. All three problems flagged in the older audit are fixed in the current code, and the code is written to keep working even on a machine whose kernel was never tuned. It is safe to ship, with one thing to keep an eye on: on a very low-memory machine, many big transfers at once use more RAM. One correction from the last review: earlier notes said this room blocks tracking — it does not, and that false claim has been removed.

## SECTION C: TECHNICAL SUMMARY (Developer)

Four numeric/behavioural Necko patches, all verified byte-consistent with the live tree on 2026-08-04 and previously via POR_2026-08-03. HTTP/3 UDP recv hardcoded to 64 MB (67108864) and send to 4 MB (4194304) with graceful degradation (log + continue) replacing vanilla's abort-on-failure; the recv size no longer reads network_http_http3_recvBufferSize. TCP keepalive forced 15/5/3 unconditionally per socket. DNS pool hardcoded 16 threads / 12 idle (was MaxResolverThreads()/8); NEGATIVE_RECORD_LIFETIME 60 -> 3 s. Upload pacing via kGorillaUploadChunkSize (256 KB) gated on mRequestSize > 10 MB in ReadSegments — the constant is live, closing the old MED-001 'unused constant' finding. All three 2026-07-10 defects (HIGH-001 send buffer, MED-001 pacing, LOW-001 negative cache) are closed in code. The 64 MB recv figure traces to the kernel BDP derivation (06-MATHEMATICAL-DERIVATIONS.md 6.2); the 4 MB send figure to master-log Part 4; keepalive/DNS/chunk values are operationally justified in-comment but have no located formal derivation. Telemetry fencing that prior docs claimed for HttpChannelParent/nsHttpConnectionMgr/Http3Session/nsUDPSocket was reverted (files vanilla, patches deleted, grep clean) — containment lives in locked prefs + topic 13, not here.

## SECTION D: DETECTED DEFECTS

0 found by rules, 3 by review. Rule findings are deterministic; review findings are judgement.

### 🟡 P2-301 — P2 *(found by review)*

- **Plain English:** The browser asks the operating system for large buffers, but nothing checks that the operating system was set up to grant them. On a fresh machine where the companion kernel file was never installed, the request is quietly trimmed and the user just gets less speed with no warning.
- **Technical:** No build/preflight assertion that /etc/sysctl.d/99-gorilla-network.conf is active. HttpConnectionUDP.cpp:301/311 requests 64 MB/4 MB; if net.core.rmem_max/wmem_max are low, the request clamps silently (only a MOZ_LOG line records it).
- **Fix:** Add a preflight check that /proc/sys/net/core/rmem_max >= 67108864 and warns loudly otherwise.
- **Effort:** 1h

### 🟢 P3-302 — P3 *(found by review)*

- **Plain English:** The project's own kernel-contract note lists a setting (fq_codel) as shipped in the config file, but that line is not actually in the file — the setting comes from the kernel build instead. Harmless, but a reader verifying the contract would look for a line that is not there.
- **Technical:** Master log 'Kernel Configuration Contract' lists net.core.default_qdisc = fq_codel as present in /etc/sysctl.d/99-gorilla-network.conf; the on-disk .conf has no default_qdisc line (verified 2026-08-04). fq_codel is the custom kernel's compiled-in default.
- **Fix:** Correct the master-log contract block to attribute fq_codel to the kernel build, not the sysctl file.
- **Effort:** 15min

### 🟢 P3-303 — P3 *(found by review)*

- **Plain English:** The size that decides when to pace a big upload (10 MB) is typed straight into the code as a bare number, with no label. It works, but it is easy to miss when reading.
- **Technical:** nsHttpTransaction.cpp:847 uses the literal 10 * 1024 * 1024 inline; unlike kGorillaUploadChunkSize it is not a named constant.
- **Fix:** Extract to a named constexpr next to kGorillaUploadChunkSize with a rationale comment.
- **Effort:** 15min

## SECTION E: PRODUCTION READINESS

**Overall readiness: 🟢 90%**

**Done:**
- [x] All 4 patches verified byte-consistent with the live tree (2026-08-04) and byte-exact vanilla+patch==live (POR 2026-08-03).
- [x] HIGH-001 closed: explicit 4 MB UDP send buffer at HttpConnectionUDP.cpp:311.
- [x] MED-001 closed: kGorillaUploadChunkSize is defined (:79) AND used (:847-851) — no longer dead.
- [x] LOW-001 closed and exceeded: NEGATIVE_RECORD_LIFETIME 60 -> 3 s (:69), past the audit's recommended 15 s.
- [x] TCP keepalive 15/5/3 forced unconditionally (nsSocketTransport2.cpp:1527-1541).
- [x] DNS pool 16/12 (nsHostResolver.cpp:190-191).
- [x] Graceful-degradation rewrite verified: recv/send failures log and continue instead of aborting (:306/:316) — correct for untuned distribution kernels.
- [x] Telemetry-fencing revert confirmed still in effect: zero GLEAN_DISABLED matches in the four ex-telemetry files (2026-08-04).
- [x] 64 MB recv figure cross-referenced to the kernel BDP derivation (06-MATHEMATICAL-DERIVATIONS.md 6.2); 4 MB send to master-log Part 4.
- [x] Kernel-contract .conf present on the reference machine with rmem_max/wmem_max=64 MB and bbr.

**To do:**
- [ ] P2-301: preflight assertion for the sysctl contract (silent-clamp risk on fresh installs).
- [ ] P3-302: fix the master-log contract block's fq_codel attribution.
- [ ] P3-303: name the 10 MB pacing threshold as a constexpr.
- [ ] Optional: extract DNS/negative-TTL/keepalive literals behind a network.gorilla.* pref if runtime A/B is ever wanted.

**Not verified:**
- Runtime sysctl values could not be re-measured this pass — `sysctl` is not on PATH in the doc-agent shell. The on-disk .conf is verified; the POR's live-kernel figures (128 MB, bbr, fq_codel) are carried from POR 2026-08-03, not re-measured today.
- No performance was measured for this topic: no throughput, CPU %, RAM, or page-load before/after numbers exist. All 'faster/less stutter' statements are design intent, not measurement.
- Only the 64 MB receive buffer and 4 MB send buffer have located derivations (kernel report 6.2 and master-log Part 4). Keepalive 15/5/3, DNS 16/12, NEGATIVE_RECORD_LIFETIME=3 and the 256 KB chunk have NO located formal kernel-side derivation — their rationale is the in-source comments only.
- Exact vanilla effective TCP keepalive idle value not traced (in-source comment cites 300 s; Linux kernel default is 7200 s; upstream Firefox keepalive is per-socket opt-in). Verified fact is only the new value 15/5/3.
- Upstream default of MaxResolverThreads() stated as '8' by prior docs but not re-derived here; it is pref-driven (network.dns.max_any_priority_threads + max_high_priority_threads).
- happy_eyeballs_resolution_delay=50 (RFC 8305 aligned, cited in the room guardrails) is NOT one of these four C++ patches — it is a pref, out of scope for this room; not audited here.

## SECTION F: PHASED PLAN

### Phase 0 — `build/preflight — sysctl contract`
- **Change:** Assert /proc/sys/net/core/rmem_max >= 67108864 (and wmem_max), warn loudly on mismatch.
- **Expected impact:** Removes the silent-clamp failure mode on fresh/untuned installs.

### Phase 1 — `netwerk/protocol/http/nsHttpTransaction.cpp — pacing threshold`
- **Change:** Replace the inline 10 MB literal with a named constexpr; optionally make it adaptive to measured BBR bandwidth x RTT.
- **Expected impact:** Removes the magic number; adaptive form improves BBR interaction across very slow and very fast links.

### Phase 1 — `netwerk/base/nsSocketTransport2.cpp — TCP Fast Open`
- **Change:** Enable TFO to hosts that advertised a cookie (kernel net.ipv4.tcp_fastopen=3 already shipped in the .conf).
- **Expected impact:** One-RTT saving on TCP reconnects — noticeable on slow links.

### Phase 2 — `cross-topic — network.gorilla.* prefs`
- **Change:** Gate the Necko literals (DNS pool, negative TTL, buffer sizes) behind a master pref, mirroring 01.MEDIA's hardware_only_mode.
- **Expected impact:** Runtime A/B against upstream; testability.

## POSITIVE OBSERVATIONS

- All three prior-audit defects (HIGH-001/MED-001/LOW-001) are closed in code — a rare outcome; most audit findings age in a backlog.
- The graceful-degradation rewrite (log + continue vs vanilla's Close + return rv) is the correct call for a heterogeneous distribution fleet: the reference machine gets the full buffer, an untuned ~4 GB target degrades instead of failing.
- The 10 MB upload-pacing gate is a genuine nuance — small uploads skip the pacing overhead, only large uploads (where BBR's RTT estimation benefits) are chunked.
- The room-clearing correctly caught and neutralised the false-VERIFIED telemetry claims; the current docs no longer overstate what the code does.
- Buffer sizes are tied to explicit derivations rather than guessed — the 64 MB figure to a written kernel BDP calc, the 4 MB figure to a written project calc.

## VERIFICATION COMMANDS

Run these to check the claims above rather than trusting them.

```bash
grep -n 'NEGATIVE_RECORD_LIFETIME\|SetThreadLimit\|SetIdleThreadLimit' $FF_SRC/netwerk/dns/nsHostResolver.cpp   # expect 3 / 16 / 12
grep -n 'keepIdle\|keepIntvl\|keepCnt' $FF_SRC/netwerk/base/nsSocketTransport2.cpp   # expect 15 / 5 / 3
grep -n 'SetRecvBufferSize\|SetSendBufferSize\|graceful' $FF_SRC/netwerk/protocol/http/HttpConnectionUDP.cpp   # expect 67108864 / 4194304 / two graceful-degradation comments
grep -n 'kGorillaUploadChunkSize\|mRequestSize > 10' $FF_SRC/netwerk/protocol/http/nsHttpTransaction.cpp   # expect defn :79 + gate :847
grep -rln 'GLEAN_DISABLED\|MOZ_TELEMETRY_REPORTING 0' $FF_SRC/netwerk/protocol/http/HttpChannelParent.cpp $FF_SRC/netwerk/protocol/http/nsHttpConnectionMgr.cpp $FF_SRC/netwerk/protocol/http/Http3Session.cpp $FF_SRC/netwerk/base/nsUDPSocket.cpp   # expect NO output (revert intact)
ls $FF_SRC/../*/03.NETWORKING/*.patch 2>/dev/null; grep -E 'rmem_max|wmem_max|congestion_control' /etc/sysctl.d/99-gorilla-network.conf   # expect 4 patches; 67108864 / 67108864 / bbr
cat /proc/sys/net/core/rmem_max /proc/sys/net/ipv4/tcp_congestion_control /proc/sys/net/core/default_qdisc   # expect >=67108864 / bbr / fq_codel (qdisc from kernel build, not the .conf)
```

## Claim Sources

| Claim | Basis | Evidence |
|-------|-------|----------|
| Recv 64 MB hardcoded, no longer from pref | 📄 stated in input | rv = mSocket->SetRecvBufferSize(67108864);  // 64MB |
| Send 4 MB added; graceful degradation | 📄 stated in input | rv = mSocket->SetSendBufferSize(4194304); ... // Do not abort — graceful degradation. |
| Vanilla aborted on recv failure | 📄 stated in input | -    mSocket->Close(); -    mSocket = nullptr; -    return rv; |
| Keepalive 15/5/3 | 📄 stated in input | keepIdle = 15; keepIntvl = 5; keepCnt = 3; |
| DNS 16/12 | 📄 stated in input | SetThreadLimit(16)) ... SetIdleThreadLimit(12)) |
| NEGATIVE_RECORD_LIFETIME 3 | 📄 stated in input | static const unsigned int NEGATIVE_RECORD_LIFETIME = 3; |
| kGorillaUploadChunkSize used, gated at 10 MB | 📄 stated in input | if (mRequestSize > 10 * 1024 * 1024 && readCount > kGorillaUploadChunkSize) |
| Telemetry fencing reverted (files vanilla, patches deleted) | 📄 stated in input | all four files are byte-identical to the vanilla vault; their four .patch files were deleted (POR_2026-08-03_room_clearing.md) |
| 64 MB traces to kernel BDP 6.2 | 📄 stated in input | BDP = 125 MB/s * 0.150 s = 18.75 MB ... 64 MiB (06-MATHEMATICAL-DERIVATIONS.md 6.2) |
| .conf has bbr + 64 MB but no default_qdisc line | 📄 stated in input | net.core.rmem_max = 67108864 ... net.ipv4.tcp_congestion_control = bbr (no default_qdisc line) |
| sysctl not re-measurable this pass; live figures carried from POR | 🤖 model inference | *(none — model judgment)* |
| No performance measured for this topic | 🤖 model inference | *(none — model judgment)* |
| happy_eyeballs_resolution_delay=50 is a pref, not in these 4 patches | 🤖 model inference | *(none — model judgment)* |


---
**How to verify this document:**
`📄 stated in input` — the model's phrasing of something your source text said.
Find the matching line in the original to verify.
`🤖 model inference` — the model's own judgment or synthesis. Treat as opinion,
not measurement. Re-run on the same input and check whether specific numbers
stay consistent between runs.


---

# ═══ MERGED DOCUMENT: 03-networking.DEVELOPER.md (verbatim · sha256:0006f9cd2528590c · regenerated 2026-08-04) ═══

# Necko Socket / DNS / Buffer Tuning for the Custom 7.1.2 BBR + FQ-CoDel Kernel

> Generated 2026-08-04 | Source: `03.NETWORKING`

---

## Purpose

Four Necko-layer patches that re-tune existing kernel-facing knobs so Firefox 154 cooperates with the target machine's custom Linux 7.1.2 kernel (BBR congestion control, FQ-CoDel queue discipline, raised socket-buffer ceilings). No new mechanism is introduced; each patch changes numeric values or adds one setsockopt path. Trust level is unchanged from upstream: the code runs in the parent/socket process it already ran in, and every buffer request is still bounded by the kernel's net.core.*_max ceilings. This topic contains no telemetry, tracking, or experimentation code — a prior claim to the contrary was reverted and is documented as corrected below.

## Design Rationale

The values are co-designed with the 7.1.2 kernel and must not be read in isolation. The 64 MB HTTP/3 receive buffer is the browser-side half of the kernel's bandwidth-delay-product analysis (Debian.Kernel.Work/Reports/06-MATHEMATICAL-DERIVATIONS.md 6.2: transoceanic 1 Gbps x 150 ms = 18.75 MB in flight, socket buffer ceiling set to 64 MiB). The 4 MB send buffer is derived in this project's master log Part 4 (1 Gbps x 32 ms = 4 MB BDP; 16 concurrent QUIC streams x 4 MB = 64 MB bounded commit). The keepalive triple, the 16/12 DNS pool, the 3 s negative-cache TTL, and the 256 KB upload chunk are operational choices justified in the in-source comments (NAT dead-peer detection, multi-domain concurrency, dynamic-host DNS recovery, BBR pacing-clock drain) but have no located formal derivation in the kernel reports. A deliberate departure from upstream: HttpConnectionUDP now degrades gracefully (log + continue) where vanilla aborted (Close + return rv) on a buffer-size failure — correct for the distribution fleet whose ~4 GB machines may run an untuned kernel.

## Architecture

- **Pattern:** Numeric re-tuning of existing knobs plus one added setsockopt path (TCP keepalive). No new abstraction, no runtime feature flag. Cross-layer contract with the kernel via /etc/sysctl.d/99-gorilla-network.conf.
- **Trust boundary:** Necko sits between content/render processes and the kernel socket layer. Firefox cannot exceed the kernel's net.core.*_max ceilings; it can only request a size, which the kernel grants or clamps. The sysctl file is the trust artifact shared between Firefox and the kernel. Content-process code is not more trusted than before — these patches only change sizes and timers on connections the browser already opens.
- **Attack surface:** Unchanged entry points. A remote peer can influence how much of a requested receive buffer is filled, so the 64 MB receive request marginally widens a memory-consumption angle, but the kernel's net.core.rmem_max bounds it — same ceiling as any other high-throughput app on the host. No new parser, no new deserialization, no new network-reachable code path is added.
- **Dependencies:** `Custom Linux 7.1.2 kernel with BBR compiled in and FQ-CoDel as default qdisc (per POR_2026-08-03_room_clearing.md and the kernel reports; not re-measured in this pass)`, `/etc/sysctl.d/99-gorilla-network.conf raising net.core.rmem_max/wmem_max to 67108864 (verified present on the reference machine)`, `NSPR PR_GetIdentitiesLayer / PR_FileDesc2NativeHandle to reach the native TCP socket fd (nsSocketTransport2.cpp)`, `Linux TCP socket options TCP_KEEPIDLE / TCP_KEEPINTVL / TCP_KEEPCNT (guarded by #if defined)`, `nsIThreadPool (SetThreadLimit / SetIdleThreadLimit) in nsHostResolver.cpp`, `nsISocketTransport SetRecvBufferSize / SetSendBufferSize in HttpConnectionUDP.cpp`

## Flags & Configuration

| Name | Type | Default | Effect | Notes |
|------|------|---------|--------|-------|
| `NEGATIVE_RECORD_LIFETIME` | `int (compile-time const, seconds)` | `3 (upstream 60)` | Lifetime of a cached failed DNS lookup before retry is permitted. | netwerk/dns/nsHostResolver.cpp:69, consumed at :1306 rec->SetExpiration(..., NEGATIVE_RECORD_LIFETIME, 0). More aggressive than the 2026-07-10 audit's recommended 15 s. |
| `DNS thread limit` | `int` | `16 (upstream MaxResolverThreads(), pref-driven, defaults to 8)` | Maximum concurrent DNS resolver threads. | nsHostResolver.cpp:190 SetThreadLimit(16) replaces SetThreadLimit(MaxResolverThreads()); MaxResolverThreads() = network.dns.max_any_priority_threads + network.dns.max_high_priority_threads (nsHostResolver.h:47). Hardcoding removes the pref path. |
| `DNS idle thread limit` | `int` | `12 (upstream 8)` | Warm resolver threads kept alive between bursts. | nsHostResolver.cpp:191 SetIdleThreadLimit(12). |
| `TCP keepalive idle/intvl/cnt` | `int (seconds/seconds/count)` | `15 / 5 / 3, forced unconditionally` | Dead-peer detection ~30 s (15 + 5x3) on every TCP socket. | nsSocketTransport2.cpp:1527-1529 + setsockopt at :1531/:1536/:1541. Replaces Firefox's per-socket opt-in keepalive with an unconditional path. Exact prior effective idle value not traced this pass (in-source comment cites 300 s; Linux default is 7200 s). |
| `HTTP/3 UDP receive buffer` | `int (bytes)` | `67108864 (64 MB), hardcoded` | SO_RCVBUF request on each QUIC socket. | HttpConnectionUDP.cpp:301. Replaces vanilla SetRecvBufferSize(StaticPrefs::network_http_http3_recvBufferSize()) — the pref is no longer consulted. |
| `HTTP/3 UDP send buffer` | `int (bytes)` | `4194304 (4 MB), hardcoded` | SO_SNDBUF request on each QUIC socket (new; upstream set none). | HttpConnectionUDP.cpp:311. |
| `kGorillaUploadChunkSize` | `uint32_t (bytes)` | `262144 (256 KB)` | Caps ReadSegments read count per iteration for uploads over 10 MB. | nsHttpTransaction.cpp:79, gated at :847-848 (mRequestSize > 10*1024*1024). |

## API Surface

| Symbol | Description | Side Effects |
|--------|-------------|--------------|
| `nsHttpTransaction::ReadSegments()` | Reads request-body segments to send; now clamps readCount to 256 KB for >10 MB uploads before delegating to mRequestStream->ReadSegments. | Emits data to the send path in smaller chunks for large uploads; no behavioural change below 10 MB. |
| `HttpConnectionUDP::InitCommon()` | Sizes SO_RCVBUF (64 MB) and SO_SNDBUF (4 MB), continuing on failure. | Requests large kernel socket buffers; logs and proceeds if the kernel clamps or refuses. |
| `nsHostResolver::Init()` | Sets DNS thread pool to 16 workers, 12 idle. | Higher concurrent DNS fan-out; more warm threads resident. |
| `nsSocketTransport2 socket-attach path` | Applies TCP keepalive triple to every TCP socket via setsockopt. | One keepalive probe per ~15 s of idle per TCP socket. |

## Kill Switches

### `netwerk/dns/nsHostResolver.cpp:190-191 (SetThreadLimit/SetIdleThreadLimit)`
- **Condition:** Always, at resolver init.
- **Effect:** DNS worker pool sized 16/12 instead of MaxResolverThreads()/8. Reverting means editing the literals back.
- reversible
- No runtime pref gates this; it is a hardcoded value. Idle 12 keeps threads warm without unbounded growth.

### `netwerk/dns/nsHostResolver.cpp:69 (NEGATIVE_RECORD_LIFETIME)`
- **Condition:** Compile-time constant; effective on every negative-cache expiry.
- **Effect:** Failed lookups retried after 3 s instead of 60 s.
- reversible
- Kernel-independent; safe to revert to 60 without touching sysctl.

### `netwerk/base/nsSocketTransport2.cpp:1527-1541 (keepalive block)`
- **Condition:** Every TCP socket creation where the native fd is obtainable.
- **Effect:** Forces TCP_KEEPIDLE=15 / TCP_KEEPINTVL=5 / TCP_KEEPCNT=3 unconditionally.
- reversible
- Delete the block to restore per-socket opt-in keepalive. setsockopt failures are logged via SOCKET_LOG and ignored (non-fatal).

### `netwerk/protocol/http/HttpConnectionUDP.cpp:301,311 (buffer sizing)`
- **Condition:** At InitCommon for each QUIC socket.
- **Effect:** Requests 64 MB recv + 4 MB send; on NS_FAILED, logs and continues (graceful degradation).
- reversible
- Remove SetSendBufferSize line and/or restore the pref-driven recv size and the abort branch to return to upstream behaviour. The graceful-degradation branch is the operative safety net for untuned kernels.

### `netwerk/protocol/http/nsHttpTransaction.cpp:847-851 (upload pacing gate)`
- **Condition:** mRequestSize > 10 MB and readCount > 256 KB.
- **Effect:** Clamps per-iteration ReadSegments read count to 256 KB.
- reversible
- Below 10 MB the original count is used unchanged; deleting the gate restores unpaced reads.

## Dead Code

- **`None in the four patches.`** — kGorillaUploadChunkSize is defined at nsHttpTransaction.cpp:79 and used at :847-848 — it is live, not the unused constant the 2026-07-10 audit flagged as MED-001. (risk: N/A — removing it would break the pacing gate that references it.)

## Performance

- **CPU:** Not measured for this topic. Qualitatively: negligible added CPU (one keepalive probe per idle socket per ~15 s; a bounded compare in ReadSegments). No before/after CPU number is claimed.
- **MEMORY:** Up to 64 MB SO_RCVBUF + 4 MB SO_SNDBUF requested per QUIC socket, bounded by kernel ceilings. Master log Part 4 caps the design at ~16 concurrent QUIC streams (4 MB send x 16 = 64 MB send commit); receive worst case is larger and is the primary watch item on ~4 GB distribution targets. Comfortable on the 16 GiB (UMA-shared) reference machine. Not empirically measured.
- **IO:** Larger receive buffers absorb burst arrivals without loss; explicit send buffer removes upload head-of-line blocking; 16-way DNS parallelism removes lookup serialization on multi-domain pages; 256 KB upload chunking keeps BBR's RTT estimate clean on large uploads.
- **NOTES:** Every buffer figure is contingent on the kernel granting it; graceful degradation means the Firefox side never fails when the kernel is untuned, it only under-performs.

## Security

- **Remote execution:** None introduced. No new parser, deserializer, or executable path.
- **Data handling:** No user data is read, stored, or transmitted by any line in this topic. This is pure socket/DNS/buffer configuration.
- **Attack surface:** Marginally wider memory-consumption angle from the 64 MB receive request, bounded by net.core.rmem_max — no unbounded growth. No change to authentication, TLS, or origin handling.
- **Notes:** Prior documentation claimed Necko-layer Glean/telemetry excision (GLEAN_DISABLED / MOZ_TELEMETRY_REPORTING) in HttpChannelParent/nsHttpConnectionMgr/Http3Session/nsUDPSocket. That is FALSE for the current tree: those four files are byte-identical to vanilla and their patches were removed in the 2026-08-01/02 reconciliation; grep for GLEAN_DISABLED across the netwerk files returns zero matches (verified 2026-08-04). Telemetry containment for the build lives in locked prefs (datareporting.glean.uploadEnabled=false, toolkit.telemetry.enabled=false — 05.PREFS) and topic 13.TELEMETRY.KILL, not here.

## Error Conditions

| Error | Cause | Remedy |
|-------|-------|--------|
| `HttpConnectionUDP::InitCommon SetRecvBufferSize failed ... Continuing with default kernel receive buffers.` | Kernel net.core.rmem_max lower than 64 MB (untuned kernel). | Non-fatal by design; throughput on very high-BDP links is reduced. Install /etc/sysctl.d/99-gorilla-network.conf and reload sysctl to grant the full size. |
| `HttpConnectionUDP::InitCommon SetSendBufferSize failed ... Continuing with default kernel send buffers.` | Kernel net.core.wmem_max lower than 4 MB. | Non-fatal; upload pacing falls back to kernel default send buffer. Same remedy as above. |
| `nsSocketTransport: TCP_KEEPIDLE/INTVL/CNT failed` | setsockopt rejected on the platform (e.g. option unsupported). | Logged via SOCKET_LOG and ignored; connection proceeds with platform-default keepalive. No action required. |

## Tasks

### Verify the four patches match the live tree

Confirm the documented values are the values in netwerk before trusting this doc.

**Prerequisites:**
- FF_SRC points at the patched tree (the source tree)

**Step 1:** grep -n 'NEGATIVE_RECORD_LIFETIME\|SetThreadLimit\|SetIdleThreadLimit' $FF_SRC/netwerk/dns/nsHostResolver.cpp
  - Expected: NEGATIVE_RECORD_LIFETIME = 3 (:69), SetThreadLimit(16) (:190), SetIdleThreadLimit(12) (:191).
**Step 2:** grep -n 'keepIdle\|keepIntvl\|keepCnt\|TCP_KEEPIDLE' $FF_SRC/netwerk/base/nsSocketTransport2.cpp
  - Expected: keepIdle=15 (:1527), keepIntvl=5 (:1528), keepCnt=3 (:1529), setsockopt at :1531/:1536/:1541.
**Step 3:** grep -n 'SetRecvBufferSize\|SetSendBufferSize\|graceful' $FF_SRC/netwerk/protocol/http/HttpConnectionUDP.cpp
  - Expected: SetRecvBufferSize(67108864) (:301), SetSendBufferSize(4194304) (:311), two 'graceful degradation' comments (:306/:316).
**Step 4:** grep -n 'kGorillaUploadChunkSize\|mRequestSize > 10' $FF_SRC/netwerk/protocol/http/nsHttpTransaction.cpp
  - Expected: constant at :79 (256*1024), gate at :847, applied at :851.

**After this task:** All four values reproduce the patch files byte-for-byte (already confirmed by POR_2026-08-03 and re-checked 2026-08-04).

### Confirm the telemetry-fencing revert is still in effect

Guard against a stale re-application of the reverted Glean fencing.

**Prerequisites:**
- FF_SRC set

**Step 1:** grep -rln 'GLEAN_DISABLED\|MOZ_TELEMETRY_REPORTING 0' $FF_SRC/netwerk/protocol/http/HttpChannelParent.cpp $FF_SRC/netwerk/protocol/http/nsHttpConnectionMgr.cpp $FF_SRC/netwerk/protocol/http/Http3Session.cpp $FF_SRC/netwerk/base/nsUDPSocket.cpp
  - Expected: No output. Any match means the reverted fencing was re-introduced and must be removed again (do NOT re-apply it).

**After this task:** Zero matches; the four files remain vanilla.

### Confirm the kernel-side contract

The buffer sizes are meaningless unless the kernel grants them.

**Prerequisites:**
- Root or read access to /etc/sysctl.d and /proc/sys

**Step 1:** grep -E 'rmem_max|wmem_max|congestion_control' /etc/sysctl.d/99-gorilla-network.conf
  - Expected: net.core.rmem_max = 67108864, net.core.wmem_max = 67108864, net.ipv4.tcp_congestion_control = bbr.
**Step 2:** cat /proc/sys/net/core/rmem_max /proc/sys/net/ipv4/tcp_congestion_control /proc/sys/net/core/default_qdisc
  - Expected: rmem_max at least 67108864; tcp_congestion_control 'bbr'; default_qdisc 'fq_codel'. NOTE: fq_codel is the custom kernel's compiled-in default — the .conf file ships bbr but does NOT contain a default_qdisc line.

**After this task:** Kernel grants at least the requested buffer sizes and runs bbr + fq_codel.

## Troubleshooting

**Symptom:** High-BDP transfers do not reach expected throughput.
**Cause:** Kernel net.core.rmem_max below 64 MB, so the receive-buffer request was clamped.
**Remedy:** Install and reload /etc/sysctl.d/99-gorilla-network.conf.
**Verify:** cat /proc/sys/net/core/rmem_max returns at least 67108864.

**Symptom:** Large uploads still burst instead of pacing.
**Cause:** Upload below the 10 MB gate, or the gate was reverted.
**Remedy:** Confirm the payload exceeds 10 MB; re-check the gate at nsHttpTransaction.cpp:847.
**Verify:** grep -n 'mRequestSize > 10' nsHttpTransaction.cpp returns the gate.

**Symptom:** Idle TCP connections still die on cheap NAT gear.
**Cause:** setsockopt keepalive was rejected on the platform (logged, ignored).
**Remedy:** Check SOCKET_LOG output for 'TCP_KEEPIDLE failed'; confirm the platform supports the options.
**Verify:** MOZ_LOG=nsSocketTransport:5 shows the keepalive path executing without the failure log.

**Symptom:** A doc or patch references HttpChannelParent/Http3Session/nsUDPSocket telemetry fencing.
**Cause:** Stale material from before the 2026-08-03 revert.
**Remedy:** Ignore/remove it; do not re-apply. Telemetry is handled by locked prefs and topic 13.
**Verify:** grep for GLEAN_DISABLED in those files returns nothing.

## Technical Debt

🟡 **LOW** — DNS thread limit and NEGATIVE_RECORD_LIFETIME are hardcoded literals, bypassing the pref path (MaxResolverThreads() and the negative-TTL constant). → Acceptable for a fixed-hardware build; if a runtime A/B is ever wanted, route through a network.gorilla.* pref instead of literals.
🟡 **LOW** — The 10 MB upload-pacing threshold is a magic number inline in the gate. → Extract to a named constexpr adjacent to kGorillaUploadChunkSize with a comment on why pacing overhead is not worth it below that size.
🟠 **MEDIUM** — No preflight assertion that /etc/sysctl.d/99-gorilla-network.conf is installed and active; buffer requests silently clamp on a fresh/untuned install. → Add a build/preflight check that /proc/sys/net/core/rmem_max >= 67108864 and warns loudly otherwise.
🟡 **LOW** — Master log's 'Kernel Configuration Contract' lists net.core.default_qdisc = fq_codel as shipped in the .conf, but the on-disk .conf contains no default_qdisc line (fq_codel is the kernel's compiled-in default). → Correct the master log's contract block to reflect that fq_codel comes from the kernel build, not this sysctl file, to avoid a false verification expectation.

## Impact If Removed

Reverting the four patches restores upstream Necko behaviour: (1) DNS becomes a serialization point on multi-domain pages (lower concurrency, warmer-thread churn); (2) failed DNS lookups block retry for 60 s instead of 3 s, hurting dynamic-host and mobile UX; (3) TCP connections revert to per-socket opt-in keepalive and silently die on NAT-heavy links, causing reload hangs; (4) HTTP/3 receive buffer reverts to the pref value AND the abort-on-failure branch returns, so a buffer-size failure again tears down the QUIC socket rather than degrading; (5) the explicit 4 MB send buffer disappears and uploads bottleneck at the kernel default; (6) large uploads stream unpaced, distorting BBR's RTT estimation. No security posture is lost by removal — this topic adds none.

## Claim Sources

| Claim | Basis | Evidence |
|-------|-------|----------|
| Receive buffer hardcoded 67108864, not from StaticPrefs | 📄 stated in input | rv = mSocket->SetRecvBufferSize(67108864);  // 64MB |
| Vanilla used the pref and aborted on failure | 📄 stated in input | -  rv = mSocket->SetRecvBufferSize(
-      StaticPrefs::network_http_http3_recvBufferSize()); ... -    mSocket->Close(); |
| Send buffer 4194304 added, graceful degradation | 📄 stated in input | rv = mSocket->SetSendBufferSize(4194304); ... // Do not abort — graceful degradation. |
| Keepalive 15/5/3 unconditional | 📄 stated in input | int32_t keepIdle = 15; int32_t keepIntvl = 5; int32_t keepCnt = 3; |
| DNS 16 threads / 12 idle, replacing MaxResolverThreads()/8 | 📄 stated in input | -  MOZ_ALWAYS_SUCCEEDS(threadPool->SetThreadLimit(MaxResolverThreads())); ... +  SetThreadLimit(16)) ... +  SetIdleThreadLimit(12)) |
| MaxResolverThreads() = any + high priority pref sums | 📄 stated in input | return MaxResolverThreadsAnyPriority() + MaxResolverThreadsHighPriority(); (nsHostResolver.h:47) |
| NEGATIVE_RECORD_LIFETIME 60 -> 3 | 📄 stated in input | static const unsigned int NEGATIVE_RECORD_LIFETIME = 3; |
| Upload chunk 256 KB gated at 10 MB, and is used (not dead) | 📄 stated in input | if (mRequestSize > 10 * 1024 * 1024 && readCount > kGorillaUploadChunkSize) { readCount = kGorillaUploadChunkSize; } |
| 64 MB recv buffer traces to kernel BDP derivation 6.2 | 📄 stated in input | BDP = 125 MB/s * 0.150 s = 18.75 MB ... configured at 64 MiB (Reports/06-MATHEMATICAL-DERIVATIONS.md 6.2) |
| 4 MB send buffer traces to master-log Part 4 BDP | 📄 stated in input | 1000 Mbps * 0.032 s = 4 MB (master log Part 4) |
| Telemetry fencing reverted; files vanilla; patches deleted | 📄 stated in input | all four files are byte-identical to the vanilla vault; their four .patch files were deleted (POR_2026-08-03_room_clearing.md) |
| GLEAN_DISABLED grep returns zero in the four files | 🤖 model inference | *(none — model judgment)* |
| .conf ships bbr + 64 MB but no default_qdisc line | 📄 stated in input | net.core.rmem_max = 67108864 ... net.ipv4.tcp_congestion_control = bbr (no fq_codel/default_qdisc line in /etc/sysctl.d/99-gorilla-network.conf) |
| keepalive/DNS/chunk lack formal kernel derivation | 🤖 model inference | *(none — model judgment)* |
| No CPU/memory/throughput measured for this topic | 🤖 model inference | *(none — model judgment)* |
| Exact prior keepalive idle value not traced | 🤖 model inference | *(none — model judgment)* |


---
**How to verify this document:**
`📄 stated in input` — the model's phrasing of something your source text said.
Find the matching line in the original to verify.
`🤖 model inference` — the model's own judgment or synthesis. Treat as opinion,
not measurement. Re-run on the same input and check whether specific numbers
stay consistent between runs.

*Auto-generated DITA-structured developer documentation.*


---

# ═══ MERGED DOCUMENT: 03-networking.LAYMAN.md (verbatim · sha256:daf1efead97b01d0 · regenerated 2026-08-04) ═══

# Retuning Firefox's Network Plumbing to Match a Custom Linux Kernel — Plain Language Guide

> Generated 2026-08-04 from `03.NETWORKING`

---

## Should You Run This?

Yes, if you are running this build on the target hardware — it is low-risk network tuning with a graceful-degradation safety net, and nothing here touches your data. The one caveat is memory on very low-RAM machines during heavy simultaneous transfers; watch that if you have far less than the 16 GB reference machine. If you are on a fast, unmetered local connection you may not notice much, but nothing here will hurt you.

## Worst Case, Honestly

The realistic worst case is wasted memory, not danger. On a busy browsing session with many video/QUIC connections open at once, Firefox asks the kernel for a 64 MB receive buffer and a 4 MB send buffer per connection. If dozens are open, that memory adds up. On the 16 GB reference machine that is comfortable; on a low-RAM (~4 GB) target machine it is the main thing to watch. The code is written to degrade gracefully — if the kernel refuses the large size, Firefox keeps going with a smaller buffer instead of failing — so the bad outcome is 'slower on a huge transfer', not 'crash' or 'data leak'.

## What Data This Touches

These four changes send nothing anywhere. They set connection sizes and timers on your own machine. No data about you is collected, stored, or transmitted by any line in this topic. If you are worried about tracking, this is not the code to worry about — and an earlier draft that claimed this room 'severs telemetry' was mistaken. That claim was checked against the actual code on 2026-08-03 and removed: the telemetry-blocking work was reverted here and lives instead in the build's locked settings and in a separate topic (13.TELEMETRY.KILL).

## Before You Trust It

You are about to run a browser build a stranger tuned. You cannot audit C++, but you can confirm the headline numbers in this guide are actually the numbers in the code. If they match, the guide is honest about what it changed.

**Step 1:** Open the file patches/new.patches/03.NETWORKING/netwerk_protocol_http_HttpConnectionUDP.cpp.patch in any text viewer.
  - Look for: You should see the number 67108864 (that is 64 MB) for the receive buffer and 4194304 (that is 4 MB) for the send buffer, each with a comment saying 'graceful degradation' / 'Do not abort'.
**Step 2:** Open netwerk_dns_nsHostResolver.cpp.patch in the same folder.
  - Look for: You should see NEGATIVE_RECORD_LIFETIME set to 3, SetThreadLimit(16) and SetIdleThreadLimit(12). If those match, the DNS claims in this guide are accurate.
**Step 3:** Open netwerk_base_nsSocketTransport2.cpp.patch and look at the keepalive block.
  - Look for: keepIdle = 15, keepIntvl = 5, keepCnt = 3. These are the three keepalive numbers this guide describes.
**Step 4:** Confirm this room contains exactly four .patch files and no telemetry file.
  - Look for: The folder should list four patch files (nsSocketTransport2, nsHostResolver, HttpConnectionUDP, nsHttpTransaction). If you see a patch touching HttpChannelParent, Http3Session or nsUDPSocket, your copy is out of date — those were removed on 2026-08-03.

## The Big Picture

This is four small changes to the part of Firefox that talks to the internet (Mozilla calls it Necko). None of them add a feature you click. They change the numbers Firefox uses when it opens a connection: how big its incoming and outgoing buffers are, how often it checks that an idle connection is still alive, how many name-lookups it can do at once, and how long it waits before retrying a lookup that just failed.

Why bother? Because the computer this build targets runs a custom Linux kernel (version 7.1.2) that was hand-tuned for two modern traffic algorithms called BBR and FQ-CoDel. Firefox's stock numbers assume a fast, cheap, always-on broadband line. On a slow or shared connection those stock numbers fight the kernel instead of cooperating with it. These four patches change Firefox's numbers so the browser and the kernel pull in the same direction.

There is one thing this topic is NOT, and it is worth saying plainly because an earlier version of these notes got it wrong: this room does not touch telemetry or tracking. It is pure network tuning. The privacy work lives in other parts of the build.

## Key Concepts

| Name | What It Means | Real-World Comparison |
|------|--------------|------------------------|
| `Necko` | Firefox's networking code — everything that sends or receives data over the internet passes through it. | The mail room of a large office: every letter in or out goes through it. |
| `Buffer` | A holding area in memory where data waits to be processed or sent. | The counter space at a shipping desk. Too small and parcels pile up on the floor; too big and the desk hogs the whole room. |
| `BBR` | A congestion-control method from Google that measures how fast the connection really is and sends at that pace. | A driver who watches the road and keeps a steady speed, instead of flooring it until they rear-end the car ahead. |
| `FQ-CoDel` | A queueing method that stops one heavy download from freezing everyone else's traffic on a shared line. | A shop that opens an express lane the moment one giant trolley starts blocking the till. |
| `TCP keepalive` | A tiny 'are you still there?' packet Firefox sends on an idle connection so a router does not quietly kill it. | Saying 'you still on the line?' when the other person has gone quiet for a while. |
| `DNS` | The internet's phonebook — it turns names like example.com into the numeric address a computer dials. | The receptionist who looks up an extension. If she is slow, the whole call feels slow. |

## How It Works — Step by Step

### Step 1: Ask for a big incoming buffer, but do not insist

When Firefox opens an HTTP/3 (QUIC) connection, the code in HttpConnectionUDP.cpp asks the kernel for a 64 MB receive buffer (the exact number 67108864). That is room to swallow a big burst of video without dropping packets. The important part: if the kernel says no (because its own limit is lower), Firefox writes a note to its log and carries on with whatever it can get. It does not abort the connection. The stock Firefox code did the opposite — it closed the socket and gave up. This 'keep going' behaviour is what makes the change safe to ship to machines whose kernel was never tuned.

### Step 2: Set a matching outgoing buffer for uploads

Right after, the same code asks for a 4 MB send buffer (the number 4194304). For years the download side was widened while the upload side was left tiny, so video calls and file uploads bottlenecked on the way out. 4 MB is deliberately modest: big enough to keep a fast uplink full, small enough that many open connections do not eat hundreds of megabytes of memory. Same rule as step 1 — if the kernel refuses, Firefox continues with a smaller buffer instead of failing.

### Step 3: Keep every TCP connection on a short leash

In nsSocketTransport2.cpp, for every TCP connection Firefox opens, the code tells the operating system: check if this connection is still alive after 15 seconds of silence, then probe every 5 seconds, and give up after 3 failed probes. Cheap home routers and mobile-carrier equipment often kill a quiet connection without telling anyone; this makes Firefox notice within about half a minute and reconnect, instead of hanging when you reload the page.

### Step 4: Do more name-lookups at once, and forget failures faster

In nsHostResolver.cpp two things change. Firefox can now run 16 DNS lookups in parallel (and keep 12 lookup workers warm), instead of the smaller stock number. A modern web page pulls resources from dozens of different domains, so more parallel lookups means the page stops waiting in a queue. Separately, when a lookup fails, Firefox now forgets that failure after 3 seconds instead of 60. On a mobile network where addresses change quickly, a 60-second memory of a failure is a wall between you and a site that has already come back.

### Step 5: Feed big uploads to the network in small, steady bites

In nsHttpTransaction.cpp, when you upload something larger than 10 MB, Firefox now hands the data to the network in 256 KB pieces instead of one giant shove. BBR (in the custom kernel) works by measuring how packets get through; a giant shove distorts that measurement and makes pacing worse. Small uploads are left alone — the extra bookkeeping is not worth it below 10 MB. Only big uploads, where BBR's pacing actually matters, are chunked.

## Quirky Things Worth Knowing

### The 64 MB number only works if the kernel agrees

Firefox asking for a 64 MB buffer means nothing unless the kernel is willing to grant it. On this build the kernel setting net.core.rmem_max is raised to match (in the file /etc/sysctl.d/99-gorilla-network.conf). Two halves of one machine have to agree. If you copy just the Firefox side to an untuned computer, the request is simply trimmed down — which is fine, because of the 'keep going' design in steps 1 and 2.

### Every number is arithmetic, not a hunch

The 64 MB receive buffer comes from a bandwidth-delay calculation in the kernel project's own math notes: a 1 Gbps link across an ocean (150 ms round trip) can have about 18.75 MB of data in flight, and 64 MB leaves comfortable headroom. The 4 MB send buffer comes from a smaller version of the same sum (a 1 Gbps uplink at 32 ms is about 4 MB). Those two are written down. The keepalive timings, the 16 lookup workers, and the 256 KB chunk size are engineering judgements explained in the code comments, but they do not have a formal written derivation — this guide does not pretend they do.

### An earlier version of these notes overstated things

The previous documentation for this room claimed the receive buffer size came from a Firefox preference and that Firefox 'fails visibly' if the kernel is untuned, and it claimed the network code blocks telemetry. All three statements are now false in the actual code: the size is hard-coded to 64 MB, Firefox degrades gracefully rather than failing, and the telemetry-blocking was removed from this room. This is exactly why open documentation with dates and line numbers matters — a mistake can be caught and corrected in public.

## What This Means For You

### Battery, Processor & Memory

Not measured for this topic. The honest expectation: slightly more memory used when many large transfers run at once (bigger buffers), and a negligible amount of CPU for the keepalive probes. No before/after numbers were taken, so none are claimed.

### Speed

Not measured as a number. By design: pages that touch many domains should feel quicker (more parallel DNS), high-bitrate video should stutter less (bigger receive buffer), uploads should stop bottlenecking (send buffer plus paced chunks), and connections that used to silently die on cheap routers should recover. No throughput or page-load measurement was recorded, so no percentage is claimed here.

### Your Privacy

No effect. This topic collects and sends nothing about you. Privacy is handled elsewhere in the build.

### Your Internet

Uses your connection more efficiently, not more heavily. It does not add background traffic. The only extra bytes are the small keepalive probes on idle connections, which are tiny and are what keep a connection from dying.

## The Off Switch

**What it is:** There is no single on/off switch for this topic — the changes are numbers baked into the code, not a feature flag. But each one is independently reversible: change 16 back to the stock lookup count, delete the send-buffer line, restore the failure-lifetime to 60, or remove the keepalive block. The kernel side has its own switch: the file /etc/sysctl.d/99-gorilla-network.conf. Remove it and the kernel goes back to its defaults, and Firefox's large-buffer requests are simply trimmed (thanks to the graceful-degradation design).

**Without it:** Without these changes, on a slow or shared line you get the stock behaviour: video can stutter on bursts, big uploads bottleneck, connections silently die on cheap routers and Firefox hangs on reload, many-domain pages feel sluggish because lookups queue up, and a failed lookup is remembered for a full minute.

**Think of it like:** It is less like one light switch and more like a car service: a wider fuel line (buffers), smoother throttle control (BBR-friendly pacing), a faster restart when the engine stalls (keepalives), and more staff at the parts desk (DNS workers). Each part can be undone on its own; together they make the car actually move.

## How to use this

**Before you start:**
- You are building or running the Gorilla Unleashed Firefox 154 build, not stock Firefox.
- For the full benefit, the companion kernel file /etc/sysctl.d/99-gorilla-network.conf is installed and active (it raises the kernel buffer limits to match).
- The custom 7.1.2 kernel with BBR available is what these numbers were designed against; on a stock kernel the changes still work but do less.

**Step 1:** Build Firefox with these four patches applied (they are part of the standard patch set).
  - You should see: The build completes; the four netwerk source files carry the GORILLA v2 comments.
**Step 2:** Confirm the kernel side is in place if you want the large buffers to actually be granted.
  - You should see: The sysctl file exists with net.core.rmem_max = 67108864 and net.core.wmem_max = 67108864. Without it, Firefox still runs and simply gets smaller buffers.
**Step 3:** Just use the browser normally — there is nothing to switch on.
  - You should see: Multi-domain pages, video, uploads and flaky-router reconnects behave better on slow or shared links than stock Firefox would.

## If Something Goes Wrong

**Firefox uses more memory than you expected during heavy video or many downloads.**
Each HTTP/3 connection can request up to a 64 MB receive buffer; several at once add up.
What to do: This is expected on the 16 GB reference machine. On a low-RAM (~4 GB) machine, close some tabs; or lower the 67108864 figure in HttpConnectionUDP.cpp and rebuild if it is a real problem for you.

**You do not see any speed improvement over stock Firefox.**
The kernel side may not be installed, so your buffer requests are being trimmed; or your connection was never the bottleneck.
What to do: Confirm /etc/sysctl.d/99-gorilla-network.conf is installed and active. The gains are largest on slow, shared, or high-latency links — on a fast local line you may notice little.

**You read an older note claiming this room blocks telemetry and are confused.**
That claim was true of a since-reverted version and was corrected on 2026-08-03.
What to do: Trust the current four patches: they contain no telemetry code. Privacy/telemetry work is in the locked settings and in topic 13.TELEMETRY.KILL.

## Why a Developer Would Do This

A developer makes these choices because the browser and the kernel are two halves of one machine, and stock Firefox assumes a rich-world broadband line that the target user does not have. Matching Firefox's buffer sizes and timers to the custom kernel's BBR/FQ-CoDel design — and making the code degrade gracefully when the kernel is not tuned — is the difference between a page that loads and one that gives up on a slow or shared connection.

## Why It Matters That You Can Read This

You cannot read C++ to check this, and you should not have to. What you can do is check that the claims here match the code, because both are in the same folder with line numbers. This guide points you at HttpConnectionUDP.cpp line 301 for the 64 MB number and line 311 for the 4 MB number; anyone can open those and see the exact figures. A closed browser would ship these numbers with no way to see them, no way to know a past version had a bug, and no way to correct a documentation mistake in public. This room already demonstrates the value: an earlier draft's false claims were caught precisely because the code was open and dated.

## Glossary

**Necko** — Firefox's internal name for all of its networking code.

**Buffer** — A temporary holding area in memory for data waiting to be sent or processed.

**TCP** — The common, reliable way two computers hold a connection and exchange an ordered stream of data.

**UDP / QUIC / HTTP/3** — A newer, faster way to load pages that sends data as individually addressed packets; used by YouTube, Cloudflare and Google.

**DNS** — The internet's phonebook, which turns a name like example.com into a numeric address.

**BBR** — A congestion-control method that measures the connection's real speed and paces packets to match.

**FQ-CoDel** — A queueing method that keeps one heavy flow from freezing everyone else on a shared line.

**Keepalive** — A tiny periodic packet that keeps an idle connection from being silently killed by a router.

**Negative DNS cache** — Firefox's short memory of a failed name lookup so it does not immediately retry; shortened here from 60 seconds to 3.

**Bandwidth-delay product** — How much data can be in flight on a connection at once — its speed times its round-trip delay; it sets the smallest buffer that keeps the link full.

**sysctl** — The Linux mechanism for reading and setting kernel tuning knobs, such as the maximum socket buffer size.

**Graceful degradation** — Continuing with a smaller/simpler result when the ideal one is not available, instead of failing outright.

## Claim Sources

| Claim | Basis | Evidence |
|-------|-------|----------|
| Topic is four patch files, no telemetry code | 📄 stated in input | Siblings: netwerk_base_nsSocketTransport2.cpp.patch, netwerk_dns_nsHostResolver.cpp.patch, netwerk_protocol_http_HttpConnectionUDP.cpp.patch, netwerk_protocol_http_nsHttpTransaction.cpp.patch |
| Receive buffer hard-coded to 64 MB (67108864) | 📄 stated in input | rv = mSocket->SetRecvBufferSize(67108864);  // 64MB |
| Send buffer set to 4 MB (4194304) | 📄 stated in input | rv = mSocket->SetSendBufferSize(4194304); |
| Buffers degrade gracefully instead of aborting | 📄 stated in input | // Do not abort — graceful degradation. |
| Vanilla aborted on receive-buffer failure | 📄 stated in input | -    mSocket->Close();
-    mSocket = nullptr;
-    return rv; |
| TCP keepalive 15s idle / 5s interval / 3 probes | 📄 stated in input | int32_t keepIdle = 15;
 int32_t keepIntvl = 5;
 int32_t keepCnt = 3; |
| DNS thread limit 16, idle 12 | 📄 stated in input | SetThreadLimit(16)) ... SetIdleThreadLimit(12)) |
| NEGATIVE_RECORD_LIFETIME 60 -> 3 | 📄 stated in input | static const unsigned int NEGATIVE_RECORD_LIFETIME = 3; |
| Upload chunk 256 KB for uploads over 10 MB | 📄 stated in input | if (mRequestSize > 10 * 1024 * 1024 && readCount > kGorillaUploadChunkSize) |
| 64 MB buffer justified by transoceanic BDP ~18.75 MB | 📄 stated in input | BDP = 125 MB/s * 0.150 s = 18.75 MB ... maximum socket buffer is configured at 64 MiB (Reports/06-MATHEMATICAL-DERIVATIONS.md 6.2) |
| 4 MB send buffer justified by 1 Gbps x 32 ms BDP | 📄 stated in input | 1000 Mbps * 0.032 s = 4 MB (master log Part 4) |
| Kernel contract file raises rmem_max/wmem_max to 64 MB | 📄 stated in input | net.core.rmem_max = 67108864 / net.core.wmem_max = 67108864 in /etc/sysctl.d/99-gorilla-network.conf |
| Telemetry fencing was reverted from this room 2026-08-03 | 📄 stated in input | all four files are byte-identical to the vanilla vault; their four .patch files were deleted (POR_2026-08-03_room_clearing.md) |
| No performance numbers were measured for this topic | 🤖 model inference | *(none — model judgment)* |
| keepalive/DNS/chunk values have no formal kernel-side derivation | 🤖 model inference | *(none — model judgment)* |


---
**How to verify this document:**
`📄 stated in input` — the model's phrasing of something your source text said.
Find the matching line in the original to verify.
`🤖 model inference` — the model's own judgment or synthesis. Treat as opinion,
not measurement. Re-run on the same input and check whether specific numbers
stay consistent between runs.

*Human Track. Its Developer Track twin covers the same changes in technical detail. Neither is a simplified copy of the other — they are the same truth in two languages.*


---

# ═══ MERGED DOCUMENT: 03-networking.PRECHECK.md (verbatim · sha256:a3d898d26517a744 · regenerated 2026-08-04) ═══

# Offline Pre-Check: 03-networking

*Generated 2026-08-04 07:03:19 by rules only. No model was involved, so everything below is a deterministic finding about the files as they are on disk.*

## Files Scanned

| File | Language | Lines | Code | Complexity | SHA-256 |
|---|---|---|---|---|---|
| `netwerk_base_nsSocketTransport2.cpp.patch` | patch | 39 | 34 | 11 | `b4b5207ee51fb047` |
| `netwerk_dns_nsHostResolver.cpp.patch` | patch | 28 | 21 | 3 | `ee6d15014a340da1` |
| `netwerk_protocol_http_HttpConnectionUDP.cpp.patch` | patch | 36 | 34 | 5 | `2b3767c6f91867f3` |
| `netwerk_protocol_http_nsHttpTransaction.cpp.patch` | patch | 32 | 26 | 4 | `615849f3646a4f02` |

## Findings

🔴 P0: 0 · 🟠 P1: 0 · 🟡 P2: 0 · 🟢 P3: 0

*No findings. The rules found nothing wrong; this is not a statement that the code is correct.*


---

# ═══ VERIFICATION 2026-08-02 — 01.MEDIA-grade SOP (folder #3) ═══

**Byte-exact:** 8/8 patches CLEAN apply + byte-IDENTICAL (vanilla+patch == live).

**Two species in this folder:**

### Species A — kernel-matched network tuning (LEGITIMATE, keep)
Socket-layer counterpart to the custom kernel (BBR + fq_codel + 64MB buffers, CWND 128):
- nsSocketTransport2: unconditional TCP keepalive 15s idle / 5s intvl / 3 probes (fast dead-peer
  detection under fq_codel).
- HttpConnectionUDP: 64MB HTTP/3 recv + 4MB send, cooperating with BBR pacing — REWRITTEN to
  graceful-degrade (log + continue) instead of vanilla's abort-on-failure. Correct for the
  distribution fleet whose kernels lack the tuned rmem_max.
- nsHttpTransaction: kGorillaUploadChunkSize 256KB cap on ReadSegments for >10MB uploads so the
  BBR pacing clock drains between writes.
- nsHostResolver: DNS pool 16 threads / 12 idle; NEGATIVE_RECORD_LIFETIME 60s→3s (faster
  stale-DNS recovery for dynamic WebRTC hosts).
These are deliberate hw/kernel-matched values ([[reference-build-is-tuned]]); NOT bloat.

### Species B — "Surgical Telemetry Lobotomy" header blocks (INEFFECTIVE THEATER — 6 files)
nsUDPSocket, nsHostResolver, Http3Session, HttpChannelParent, nsHttpConnectionMgr,
nsHttpTransaction each carry an identical top-of-file block:
  #undef MOZ_TELEMETRY_REPORTING / #define MOZ_TELEMETRY_REPORTING 0 / #define GLEAN_DISABLED 1
PROVEN INERT three ways (2026-08-02):
1. GLEAN_DISABLED — read by NOTHING in netwerk/toolkit/mozglue/xpcom. Invented macro, pure no-op.
2. The glean:: calls in these files (5–34 each) are UNCONDITIONAL function calls, not guarded by
   MOZ_TELEMETRY_REPORTING. The #define has nothing to act on.
3. BINARY: glean net metrics survive into libxul (http_1_download_throughput ×2,
   http3_tls_handshake ×2, dns_lookup_time ×3). The "lobotomy" removed zero telemetry.
LATENT RISK (plausible, NOT proven to fire): elsewhere in-tree, telemetry is gated by
`#if defined(MOZ_TELEMETRY_REPORTING)` — an idiom TRUE whenever the macro is defined AT ALL,
even to 0. Defining it at the top of these 6 TUs could, IF such a guard is reachable in their
include graph after the #define, FLIP dormant telemetry ON — the opposite of intent. Not
confirmed active (build uses --disable-official-branding; not traced through every include).

**THE ACTUAL, EFFECTIVE CONTAINMENT (the real "fly in the jar"):** locked prefs in baked
firefox.js — datareporting.glean.uploadEnabled=false LOCKED (3699), toolkit.telemetry.enabled
=false LOCKED (3791), toolkit.telemetry.server="" LOCKED (3792), datareporting.policy.
dataSubmissionEnabled=false LOCKED (3702). glean:: records locally; nothing egresses. The 6
header blocks are irrelevant to this and contribute nothing.

**OWNER DECISION PENDING** (telemetry = ask-first rule): what to do with the 6 inert blocks —
(A) remove them (behavior-neutral vs telemetry; kills misleading source + latent flip risk;
regen 6 patches + rebuild), (B) leave + this log documents them inert, (C) replace theater with
an HONEST comment pointing to the locked-pref defense. Related: [[telemetry-strategy]]
(excision abandoned; stubs/const-guards/egress is doctrine), [[prefs-canonical-source]].

## RESOLUTION 2026-08-02 — flip-risk traced + Species-B theater REMOVED (owner: "remove them entirely")

**Flip-risk traced to ground — does NOT fire (removal proven behavior-neutral):**
- MOZ_TELEMETRY_REPORTING is NOT globally defined in this build (mozinfo/mozilla-config: absent),
  so the per-file `#define ...0` did introduce it locally — but:
- the ONLY bare `#if defined(MOZ_TELEMETRY_REPORTING)` consumers in-tree are
  toolkit/xre/nsAppRunner.cpp and dom/base/nsFrameLoader.cpp — separate .cpp TRANSLATION UNITS,
  never #included by the 6 files, so unreachable from their macro state;
- the 6 files include only generated Glean metric headers (NetwerkMetrics.h, NetwerkDnsMetrics.h,
  NetwerkProtocolHttpMetrics.h) — unconditional metric objects, zero MOZ_TELEMETRY_REPORTING
  guards. Net: the macro was introduced into 6 TUs with no consumer of it = true no-op, no flip.

**Action:** removed the identical 3-line "Surgical Telemetry Lobotomy" block
(#undef/#define MOZ_TELEMETRY_REPORTING 0 / #define GLEAN_DISABLED 1) from all 6 files.
- 4 files had ONLY that block → now byte-identical to vanilla → their patches DELETED:
  nsUDPSocket, Http3Session, HttpChannelParent, nsHttpConnectionMgr.
- 2 files kept their Species-A tuning → patches REGENERATED: nsHostResolver (DNS pool 16/12 +
  NEGATIVE_RECORD_LIFETIME 3s), nsHttpTransaction (kGorillaUploadChunkSize 256KB).
Folder now holds 4 patches (was 8), all CLEAN + byte-IDENTICAL, all Species-A kernel-matched
tuning. Telemetry containment UNCHANGED and intact: datareporting.glean.uploadEnabled=false
LOCKED + toolkit.telemetry.* LOCKED in baked firefox.js (the real "fly in the jar").
Takes effect at next ./mach build (6 netwerk TUs recompile). Provenance note: removing inert
inert leftover scaffolding is NOT the abandoned excision ([[telemetry-strategy]]) — no telemetry CODE was
touched; the glean:: calls remain, contained by prefs exactly as doctrine requires.

---

## AUDIT CORRECTION — 2026-08-03 (room-clearing pass; append-only, supersedes the rows it names)

The "Telemetry Lobotomy" and "Parent Backpressure Telemetry" rows above (marked ✅ VERIFIED)
and the grand-summary sentence "Necko-layer Glean metrics fenced with MOZ_TELEMETRY_REPORTING 0
+ GLEAN_DISABLED 1 in HttpChannelParent/nsHttpConnectionMgr/Http3Session/nsUDPSocket" are
**NO LONGER TRUE and must not be relied on.** Ground truth 2026-08-03: all four files are
byte-identical to the vanilla vault; their .patch files were removed in the 2026-08-01/02
reconciliation. The fencing was deliberately REVERTED when compile-time telemetry excision was
abandoned project-wide in favour of the 13.TELEMETRY.KILL stub/const-guard doctrine. Do not
re-apply it. The log's own verification command (`grep -l 'GLEAN_DISABLED…' netwerk/…`) now
correctly returns nothing.

Everything else in this log was re-verified against the live tree on 2026-08-03 and stands:
all 4 surviving patches reproduce the live tree from vanilla byte-exactly; DNS 3 s negative
TTL + 16/12 pool, keepalive 15/5/3, 256 KB upload pacing, 4 MB UDP send buffer, sysctl
contract satisfied (live kernel 128 MB > conf 64 MB, bbr + fq_codel). Full verdicts:
`POR_2026-08-03_room_clearing.md`. Fortress atom:
`Necko_Glean_Fencing_REVERTED_Room_Clearing_2026_08_03`.
