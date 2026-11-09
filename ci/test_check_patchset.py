"""Each check of ci/check_patchset.py passes on a good tree and FAILS on a deliberately broken one."""
import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import check_patchset as cp  # noqa: E402

GOOD_PATCH = "diff --git a/x.txt b/x.txt\n--- a/x.txt\n+++ b/x.txt\n@@ -1,2 +1,2 @@\n keep\n-old\n+new\n"
NAME = "001-fix-the-thing.patch"
PATCH = f"patches/01.G/{NAME}"
POLICY = "config/patch_policy.json"
DECISIONS = "decisions/gorilla_decisions.json"


def tree(**over):
    """A tiny good patch-set tree as {path: text}; over maps a path (with / written as @) to new text, None drops it."""
    t = {
        POLICY: json.dumps({"groups": {"01.G": {"status": "enabled", "exclude": []}}}),
        PATCH: GOOD_PATCH,
        "patches/01.G/README.md": f"# 01.G\n\n- `{NAME}`: the fix\n",
        DECISIONS: json.dumps({"decisions": {"a.b": ["false", True]}, "final_block": []}),
    }
    for k, v in over.items():
        k = k.replace("@", "/")
        if v is None:
            t.pop(k, None)
        else:
            t[k] = v
    return t


def run(check, t):
    with tempfile.TemporaryDirectory() as d:
        for rel, text in t.items():
            p = os.path.join(d, rel)
            os.makedirs(os.path.dirname(p), exist_ok=True)
            with open(p, "w", encoding="utf-8", newline="") as f:
                f.write(text)
        return cp.RUN[check](d)


def at(path, text):
    return {path.replace("/", "@"): text}


class Checks(unittest.TestCase):
    def test_good_tree_passes_every_check(self):
        for c in cp.CHECKS:
            self.assertEqual(run(c, tree()), [], c)

    def test_patch_format_fails_on_each_breakage(self):
        for bad in ("just prose, not a diff\n", "", GOOD_PATCH.replace("-1,2 +1,2", "-1,5 +1,5"),
                    GOOD_PATCH.replace("-old\n", "?old\n")):
            self.assertTrue(run("patch-format", tree(**at(PATCH, bad))), repr(bad))

    def test_patch_format_accepts_new_file_and_binary_forms(self):
        new = "diff --git a/n b/n\nnew file mode 100644\n--- /dev/null\n+++ b/n\n@@ -0,0 +1 @@\n+hi\n"
        binary = "diff --git a/i.png b/i.png\nnew file mode 100644\nGIT binary patch\nliteral 0\n"
        for ok in (new, binary):
            self.assertEqual(run("patch-format", tree(**at(PATCH, ok))), [])

    def test_policy_listing_fails_on_missing_file_unknown_group_and_missing_patch(self):
        self.assertTrue(run("policy-listing", tree(**at(POLICY, None))))
        missing = {"groups": {"01.G": {"exclude": ["002-gone.patch"]}}}
        self.assertTrue(any("does not exist" in f for f in run("policy-listing", tree(**at(POLICY, json.dumps(missing))))))
        self.assertTrue(any("not named" in f for f in run("policy-listing", tree(**at("patches/02.NEW/a.patch", GOOD_PATCH)))))
        nofolder = {"groups": {"01.G": {}, "09.NOPE": {}}}
        self.assertTrue(any("no folder" in f for f in run("policy-listing", tree(**at(POLICY, json.dumps(nofolder))))))

    def test_known_drift_silences_only_what_it_names(self):
        p = {"groups": {"01.G": {"exclude": ["002-gone.patch", "003-gone.patch"]}}}
        k = {"policy-listing": [{"item": "01.G/exclude/002-gone.patch", "reason": "r"}]}
        out = run("policy-listing", tree(**at(POLICY, json.dumps(p)), **at("ci/known-drift.json", json.dumps(k))))
        self.assertEqual(len(out), 1)
        self.assertIn("003-gone", out[0])

    def test_readme_listing_fails_both_ways(self):
        unlisted = tree(**at("patches/01.G/002-other.patch", GOOD_PATCH))
        self.assertTrue(any("does not list" in f for f in run("readme-listing", unlisted)))
        ghost = tree(**at("patches/01.G/README.md", f"- `{NAME}`: a\n- `002-ghost.patch`: b\n"))
        self.assertTrue(any("does not exist" in f for f in run("readme-listing", ghost)))

    def test_decisions_fails_on_bad_json_missing_key_and_bad_entry(self):
        for bad in ("{not json", json.dumps({"decisions": {}}),
                    json.dumps({"decisions": {"a": "false"}, "final_block": []}), json.dumps([1])):
            self.assertTrue(run("decisions", tree(**at(DECISIONS, bad))), bad)

    def test_secrets_fails_on_a_token_and_a_key_block(self):
        for secret in ("ghp_" + "a1B2" * 9, "-----BEGIN " + "PRIVATE KEY-----", "AKIA" + "ABCDEFGHIJKLMNOP"):
            readme = f"- `{NAME}`: x\n{secret}\n"
            self.assertTrue(run("secrets", tree(**at("patches/01.G/README.md", readme))), secret)

    def test_telemetry_fails_on_an_added_endpoint_not_on_a_removed_one(self):
        url = "https://incoming.telemetry." + "mozilla.org/submit"
        add = GOOD_PATCH.replace("+new", f"+fetch(\"{url}\")")
        rem = GOOD_PATCH.replace("-old", f"-fetch(\"{url}\")")
        self.assertTrue(run("telemetry", tree(**at(PATCH, add))))
        self.assertEqual(run("telemetry", tree(**at(PATCH, rem))), [])

    def test_cli_exit_codes(self):
        script = os.path.join(HERE, "check_patchset.py")
        self.assertEqual(subprocess.run([sys.executable, script, "bogus"], capture_output=True).returncode, 2)
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(subprocess.run([sys.executable, script, "policy-listing", "--root", d],
                                            capture_output=True).returncode, 3)


if __name__ == "__main__":
    unittest.main()
