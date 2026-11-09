#!/usr/bin/env python3
"""Cheap, deterministic checks for the Gorilla Firefox patch set (stdlib only; runs on Linux and Windows).

    python ci/check_patchset.py CHECK [--root DIR]

CHECK is one of: patch-format, policy-listing, readme-listing, decisions, secrets, telemetry, all.
Exit 0 fine, 3 findings (each printed as `CHECK: path: what`), 2 bad usage.
Each check reads the files git tracks under --root (a plain walk when --root is not a checkout), so a broken
fixture folder proves the check can fail (ci/test_check_patchset.py).
Known drift that predates these checks is recorded with its reason in ci/known-drift.json: new drift fails.
"""
import json
import os
import re
import subprocess
import sys

CHECKS = ("patch-format", "policy-listing", "readme-listing", "decisions", "secrets", "telemetry")
DECISIONS_KEYS = ("decisions", "final_block")


def files(root):
    try:
        out = subprocess.run(["git", "-C", root, "ls-files", "-z"], capture_output=True, check=True).stdout
        names = [n for n in out.decode("utf-8", "surrogateescape").split("\0") if n]
        if names:
            return sorted(n for n in names if os.path.isfile(os.path.join(root, n)))
    except (OSError, subprocess.CalledProcessError):
        pass
    found = []
    for d, _, fs in os.walk(root):
        if ".git" in d.split(os.sep):
            continue
        found += [os.path.relpath(os.path.join(d, f), root).replace(os.sep, "/") for f in fs]
    return sorted(found)


def read(root, rel):
    with open(os.path.join(root, rel), "rb") as f:
        return f.read().decode("utf-8", "replace")


def known(root, check):
    p = os.path.join(root, "ci", "known-drift.json")
    if not os.path.isfile(p):
        return set()
    with open(p, encoding="utf-8") as f:
        return {e["item"] for e in json.load(f).get(check, [])}


HUNK = re.compile(r"^@@ -\d+(?:,(\d+))? \+\d+(?:,(\d+))? @@")
STRUCTURAL = re.compile(r"(GIT binary patch|similarity index|rename from|old mode|new mode|deleted file mode|new file mode)")


def check_patch(text):
    """None when text is a well-formed unified diff, else the reason."""
    lines = text.replace("\r\n", "\n").split("\n")
    if not any(l.startswith("diff --git ") or l.startswith("--- ") for l in lines):
        return "no diff header (diff --git / ---)"
    hunks = 0
    i = 0
    structural = False
    while i < len(lines):
        m = HUNK.match(lines[i])
        if not m:
            structural = structural or bool(STRUCTURAL.match(lines[i]))
            i += 1
            continue
        hunks += 1
        old = int(m.group(1) if m.group(1) is not None else 1)
        new = int(m.group(2) if m.group(2) is not None else 1)
        i += 1
        while (old > 0 or new > 0) and i < len(lines):
            c = lines[i][:1]
            if c == " " or lines[i] == "":
                old, new = old - 1, new - 1
            elif c == "-":
                old -= 1
            elif c == "+":
                new -= 1
            elif c != "\\":
                return f"hunk {hunks}: unexpected line {lines[i][:40]!r}"
            i += 1
        if old > 0 or new > 0:
            return f"hunk {hunks}: ends {max(old, new)} line(s) short of its header"
    if hunks == 0 and not structural:
        return "no @@ hunk"
    return None


def run_patch_format(root):
    skip = known(root, "patch-format")
    return [f"{n}: {r}" for n in files(root) if n.endswith(".patch") and n not in skip
            for r in [check_patch(read(root, n))] if r]


def run_policy_listing(root):
    """patch_policy.json names exactly the group folders, and every excluded / superseded patch exists in its group."""
    out = []
    p = "config/patch_policy.json"
    if not os.path.isfile(os.path.join(root, p)):
        return [f"{p}: missing"]
    try:
        policy = json.loads(read(root, p))
    except ValueError as e:
        return [f"{p}: not JSON ({e})"]
    groups = policy.get("groups")
    if not isinstance(groups, dict):
        return [f"{p}: no 'groups' object"]
    fs = files(root)
    dirs = {n.split("/")[1] for n in fs if n.startswith("patches/") and n.count("/") >= 2}
    skip = known(root, "policy-listing")
    for g in sorted(set(groups) - dirs):
        out.append(f"{p}: group {g} has no folder under patches/")
    for g in sorted(dirs - set(groups)):
        out.append(f"patches/{g}: folder not named in {p}")
    have = set(fs)
    for g, v in sorted(groups.items()):
        for key in ("exclude", "superseded_158"):
            for name in v.get(key, []):
                item = f"{g}/{key}/{name}"
                if f"patches/{g}/{name}" not in have and item not in skip:
                    out.append(f"{p}: {item}: patch does not exist")
    return out


BULLET = re.compile(r"^- `(\d{3,4}-[^`/]+\.patch)`", re.M)  # the numbered-group convention; older READMEs differ


def run_readme_listing(root):
    """A group README that lists patches lists every top-level patch of its folder, and each one exists."""
    out = []
    skip = known(root, "readme-listing")
    fs = files(root)
    for readme in (n for n in fs if re.fullmatch(r"patches/[^/]+/README\.md", n)):
        listed = set(BULLET.findall(read(root, readme)))
        if not listed:
            continue
        folder = readme.rsplit("/", 1)[0]
        on_disk = {n.rsplit("/", 1)[1] for n in fs
                   if n.startswith(folder + "/") and n.count("/") == 2 and re.match(r"\d{3,4}-.*\.patch$", n.rsplit("/", 1)[1])}
        for n in sorted(listed - on_disk):
            if f"{readme}/{n}" not in skip:
                out.append(f"{readme}: lists {n}, which does not exist")
        for n in sorted(on_disk - listed):
            if f"{readme}/{n}" not in skip:
                out.append(f"{readme}: does not list {folder}/{n}")
    return out


def run_decisions(root):
    p = "decisions/gorilla_decisions.json"
    if p not in files(root):
        return []  # not every checkout tracks it; checked whenever it is committed
    try:
        d = json.loads(read(root, p))
    except ValueError as e:
        return [f"{p}: not JSON ({e})"]
    if not isinstance(d, dict):
        return [f"{p}: top level is not an object"]
    out = [f"{p}: missing key {k!r}" for k in DECISIONS_KEYS if k not in d]
    dec = d.get("decisions")
    if isinstance(dec, dict):
        for k, v in dec.items():
            if not (isinstance(v, list) and len(v) == 2 and isinstance(v[0], str) and isinstance(v[1], bool)):
                out.append(f"{p}: decisions[{k!r}] is not [value-string, locked-bool]")
    elif "decisions" in d:
        out.append(f"{p}: 'decisions' is not an object")
    if "final_block" in d and not isinstance(d["final_block"], list):
        out.append(f"{p}: 'final_block' is not a list")
    return out


SECRETS = [
    ("private key block", re.compile(r"-----BEGIN (?:RSA |EC |DSA |OPENSSH |PGP )?PRIVATE KEY")),
    ("GitHub token", re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{30,}\b|\bgithub_pat_[A-Za-z0-9_]{40,}")),
    ("AWS access key id", re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b")),
    ("Slack token", re.compile(r"\bxox[baprs]-[0-9A-Za-z-]{10,}")),
    ("Google API key", re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b")),
    ("Anthropic/OpenAI key", re.compile(r"\bsk-(?:ant-)?[A-Za-z0-9_-]{32,}")),
]
# An added line of a patch must not bring in a URL to a vendor endpoint that reports home (comments that merely
# name a host, and prefs that lock a ping off, are the patch set's whole point and are fine).
TELEMETRY = re.compile(
    r"https?://[\w.-]*(?:incoming\.telemetry\.mozilla\.org|telemetry\.mozilla\.org|crash-reports\.mozilla\.com"
    r"|crash-stats\.mozilla\.org|sentry\.io|google-analytics\.com|googletagmanager\.com|app\.adjust\.com"
    r"|data\.mozilla\.org|ping-centre\.)", re.I)
TEXT_EXT = (".patch", ".md", ".txt", ".yaml", ".yml", ".json", ".sh", ".py", ".js", ".ps1", ".toml", ".cfg", ".ini")


def run_secrets(root):
    skip = known(root, "secrets")
    out = []
    for n in files(root):
        if not n.endswith(TEXT_EXT) or n in skip:
            continue
        text = read(root, n)
        for label, rx in SECRETS:
            m = rx.search(text)
            if m:
                out.append(f"{n}: {label} ({m.group(0)[:8]}...)")
    return out


def run_telemetry(root):
    """A patch may mention a telemetry host in a context or removed line; it may not ADD one (a '+' line)."""
    skip = known(root, "telemetry")
    out = []
    for n in files(root):
        if not n.endswith(".patch") or n in skip:
            continue
        for i, line in enumerate(read(root, n).split("\n"), 1):
            if line.startswith("+") and not line.startswith("+++") and TELEMETRY.search(line):
                out.append(f"{n}:{i}: adds a telemetry endpoint: {line[:80].strip()}")
                break
    return out


RUN = {"patch-format": run_patch_format, "policy-listing": run_policy_listing, "readme-listing": run_readme_listing,
       "decisions": run_decisions, "secrets": run_secrets, "telemetry": run_telemetry}


def main(argv):
    args = argv[1:]
    root = "."
    if "--root" in args:
        i = args.index("--root")
        root = args[i + 1]
        del args[i:i + 2]
    if len(args) != 1 or args[0] not in CHECKS + ("all",):
        print(__doc__)
        return 2
    names = CHECKS if args[0] == "all" else (args[0],)
    bad = 0
    for name in names:
        found = RUN[name](root)
        for f in found:
            print(f"{name}: {f}")
        print(f"{name}: {'FAIL ' + str(len(found)) if found else 'ok'}")
        bad += len(found)
    return 3 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
