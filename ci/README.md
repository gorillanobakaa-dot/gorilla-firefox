# CI checks

`.github/workflows/checks.yml` runs on every pull request and every push to `master`, on Linux and Windows
(required checks: `checks (ubuntu-latest)`, `checks (windows-latest)`). It runs `python ci/check_patchset.py all`:

| check | fails when |
|---|---|
| patch-format | a tracked `*.patch` is not a well-formed unified diff (header, hunk line counts) |
| policy-listing | `config/patch_policy.json` and `patches/` disagree on groups, or an excluded patch does not exist |
| readme-listing | a group README lists a numbered patch that is missing, or omits one that exists |
| decisions | `decisions/gorilla_decisions.json` (when tracked) is not JSON with `decisions` and `final_block` |
| secrets | a private-key block or a GitHub, AWS, Slack, Google or API-key token is in a text file |
| telemetry | a patch ADDS a URL to a telemetry or crash-report host |

`ci/test_check_patchset.py` feeds each check a deliberately broken tree and requires it to fail. Drift that
predates the checks is listed, with its reason, in `ci/known-drift.json`; new drift fails. Stdlib only, no
third-party action except `actions/checkout`, pinned by commit SHA.
