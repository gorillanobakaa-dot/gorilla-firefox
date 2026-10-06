## 📊 Gorilla 157 by the numbers

From the first step of the move to Firefox 157 (**1 October 2026, 00:32**) to the leak test passing on the released build (**6 October 2026, 14:08**): **133 hours and 36 minutes**.

Every number below is counted from the build records, not estimated. The counting tool is `working scripts/count_release_tests.py` in the maintainer's build repository; it says where each number comes from.

| | What | How many |
|---|---|---|
| 🧰 | **Tests of the build tools themselves** (Fieldkit's test suite runs in full before every change is saved: 96 changes, the suite growing from 287 to 1,115 tests) | **61,840** |
| 🕵️ | **Leak test: observations judged** (every connection, name lookup, file, process and socket the browser made, each checked against the rules) | **117,597** |
| 🌐 | **Leak test: browser launches with every sensor watching** (12 runs started, 10 finished; the last one passed 19 of 19 rules) | **1,122** |
| ⚖️ | **Leak test: rule verdicts** (19 rules per finished run) | **182** |
| 📂 | **Source files checked against the published patches** (10 full passes over the tree) | **16,307** |
| 🧩 | **Patch applications in replay proofs**: the published patch set, applied to Mozilla's untouched Firefox 157.0 source, must give exactly the source that was compiled. Done 4 times as the set grew (434 + 436 + 454 + 456 patches); every time identical. The patches are in [`patches/`](https://github.com/gorillanobakaa-dot/gorilla-firefox/tree/master/patches) (456 used on Windows 157; the 20 in `01.MEDIA` are Linux-only) | **1,780** |
| 🔧 | **Changes to Firefox code checked one by one before they were accepted** | **293** |
| 📋 | **Proof scripts run on the installed browser** (32 rounds after installs) | **305** |
| 📶 | **Network speed benchmarks** (satellite, 5 KB/s and other emulated links; 26 rounds) | **42** |
| | **Total automated checks recorded** | **198,346** |

Also recorded: **42 build runs** (22 finished with a verified package), **20 installs**, and **910 problems** the checks caught and stopped, each one fixed before the release.

Not counted, because nothing records them: test-suite runs started by hand between saved changes, and checks done by eye in the browser.

### Progress of the leak test, run by run

| Run | Rules passed | What stopped it |
|---|---|---|
| 2 October, first trial runs | 3 of 15, then 4 of 15 | early versions of the test and of the browser |
| 3 to 4 October, builds 20 to 26 | 5 → 6 → 7 → 9 of 19 | real leaks (fixed in builds 21 to 27) and faults of the test |
| 5 October, 08:33 | 17 of 19 | the test lost track of the browser window it had to close; the first reference not yet recorded |
| 5 October, 20:05 | 15 of 19 | traffic from other programs on the test machine, blamed on the browser |
| 6 October, 04:13 | 17 of 19, then 18 | the test machine's new network address and the first reference were waiting for the maintainer; after the address was approved the same evidence was judged again (18 of 19), and the maintainer then recorded the reference |
| **6 October, 10:08** | **19 of 19 ✅** | **nothing: PASS** |
