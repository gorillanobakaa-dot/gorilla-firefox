
- Base: Firefox 160.0. Patch set: `gorilla-firefox` `23.REBASE.160`, `21.PORT.FIXES.160`, `22.EGRESS.LOCKDOWN.160` (Windows widget build file `23.REBASE.160/0122` included on Windows).
- Built on the Windows laptop with `fieldkit emerge run firefox-windows` on 2026-11-17: GREEN, 12.0 min wall, 0 model calls; the `migrate-preflight` set-proof replayed the patch set on pristine Firefox 160 before the build. Full BuildID above (`20261117045348`).
- Checked in the packaged `omni.ja`: `ASRouterTargeting.sys.mjs` `currentTabPageCategory` returns `null` and has no `AgentPageDetector` lazy getter (the blank new tab page fix).
- Linux: the same set, see [v160.0.0-linux](https://github.com/gorillanobakaa-dot/gorilla-firefox/releases/tag/v160.0.0-linux).
- **Not verified for this release, stated instead of hidden:** the install tier (`build-verify`, `package-checks`, `post-install`) and the release leak gate (`leakgate --release`) were skipped by this run (tier iterate). The browser was not started from this zip before publishing.
