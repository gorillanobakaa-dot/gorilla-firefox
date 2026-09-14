#!/usr/bin/env python3
"""
Clang 21 compatibility pre-flight check (v2, regression-guarded)
===============================================================
Runs before ./mach build to catch and auto-fix known breakage patterns in the
Gorilla Unleashed out-of-tree Firefox build.

WHAT v2 ADDS
------------
A persistent journal (.preflight_state.json) fingerprinting every file this
script touches. On each run it distinguishes "still broken", "fixed and still
fixed", and "was fixed and has since been reverted", and reports the third
case loudly. A reverted fix is otherwise invisible: the build simply fails
again on an error that was already solved once.

SCOPE
-----
The checks below (MaybeStorage, UnionMember::Construct, IPDL resolver
typedefs, FFmpeg %p/%d logging, StaticPrefList.yaml entries, the Wayland GPU
patch) are Mozilla-internal breakage patterns, most of them specific to this
patched tree. They are downstream symptoms of Clang 21's stricter generic
rules and are not documented under these names by LLVM. Section F covers the
actual generic Clang 21.1.0 language-conformance changes from the upstream
release notes separately, so the two are not conflated.

Install: place in the Firefox source root and add to the mach pre-build hook.
"""
import hashlib
import json
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).parent.resolve()
DIST_INCLUDE = ROOT / "obj-x86_64-pc-linux-gnu" / "dist" / "include" / "mozilla" / "dom"
SRC_DOM = ROOT / "dom"
STATE_FILE = ROOT / ".preflight_state.json"
CHANGELOG_FILE = ROOT / "preflight_clang21_changelog.txt"

FIXES_APPLIED = []
WARNINGS = []
ERRORS = []
REGRESSIONS = []          # things that were fixed before and are broken again
NOOP_EDITS_BLOCKED = []   # sanity counter, not really used by this script itself,
                          # kept so other tooling (e.g. an editing agent) can import
                          # safe_replace() below and get the same guard.


# ---------------------------------------------------------------------------
# Journal / regression detection
# ---------------------------------------------------------------------------
def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()[:16]


def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except json.JSONDecodeError:
            log_warn(f"{STATE_FILE.name} was corrupt/unreadable — starting a fresh journal")
    return {"checks": {}}


def save_state(state: dict):
    STATE_FILE.write_text(json.dumps(state, indent=2, sort_keys=True))


STATE = load_state()


def record_check(check_id: str, file_path: Path, status: str, detail: str = ""):
    """
    status is one of: "fixed", "broken", "clean" (never needed the fix), "n/a"
    This is the core anti-circular-editing guard: if a check was previously
    "fixed" and is now "broken" again, that is flagged as a REGRESSION, which
    is exactly the AddCertExceptionResolver bug from an earlier build attempt (fixed,
    then silently reverted to the original broken text ~90 tool calls later).
    """
    key = f"{check_id}::{file_path.relative_to(ROOT) if file_path.exists() else file_path}"
    prev = STATE["checks"].get(key)
    now = {"status": status, "detail": detail, "ts": time.time()}
    if prev and prev["status"] == "fixed" and status == "broken":
        msg = (f"REGRESSION: '{check_id}' on {file_path.relative_to(ROOT)} was previously "
               f"marked fixed, but the broken pattern is back. Something reverted this file. "
               f"({detail})")
        REGRESSIONS.append(msg)
        log_error(msg)
    STATE["checks"][key] = now


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
def log_fix(msg):
    FIXES_APPLIED.append(msg)
    print(f"  \u2705 FIXED: {msg}")
    append_changelog("FIXED", msg)


def log_warn(msg):
    WARNINGS.append(msg)
    print(f"  \u26a0\ufe0f  WARNING: {msg}")


def log_error(msg):
    ERRORS.append(msg)
    print(f"  \u274c ERROR: {msg}")


def append_changelog(kind: str, msg: str):
    """
    Dedup guard for the changelog file itself. An earlier build attempt logged the exact
    same 'newChild scope issue' as FIXED four times with no edit in between
    three of those four entries. This refuses to write a duplicate line.
    """
    line = f"[{kind}] {msg}"
    if CHANGELOG_FILE.exists():
        existing = CHANGELOG_FILE.read_text()
        if line in existing:
            return  # already logged verbatim — do not pad the file
    with CHANGELOG_FILE.open("a") as f:
        f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} {line}\n")


def safe_replace(path: Path, old: str, new: str, description: str) -> bool:
    """
    Guarded string replace for use by this script (and importable by any
    editing agent working on this tree). Refuses:
      - no-op edits where old == new (cost 2 build cycles in an earlier run)
      - edits where `old` does not actually appear (silently doing nothing
        while claiming success is how the false "brain_payload_final.json"
        summary happened)
    Returns True only if a real, verified change was written to disk.
    """
    if old == new:
        log_warn(f"safe_replace refused a no-op edit in {path.name}: '{description}' "
                 f"(oldString == newString)")
        return False
    if not path.exists():
        return False
    txt = path.read_text()
    if old not in txt:
        return False
    txt2 = txt.replace(old, new)
    path.write_text(txt2)
    log_fix(f"{path.relative_to(ROOT)}: {description}")
    return True


# --- 1. MaybeStorage.mIsSome must be public (Clang 21 template access) -----
def fix_maybe_storage_protected():
    f = ROOT / "mfbt/Maybe.h"
    if not f.exists():
        return
    txt = f.read_text()
    pairs = [
        ("struct MaybeStorage<T, false> : MaybeStorageBase<T> {\n protected:\n   char mIsSome",
         "struct MaybeStorage<T, false> : MaybeStorageBase<T> {\n public:\n   char mIsSome"),
        ("struct MaybeStorage<T, true> : MaybeStorageBase<T> {\n protected:\n   char mIsSome",
         "struct MaybeStorage<T, true> : MaybeStorageBase<T> {\n public:\n   char mIsSome"),
    ]
    any_broken = False
    for old, new in pairs:
        if old in txt:
            any_broken = True
            safe_replace(f, old, new, "protected\u2192public mIsSome (Clang 21 template access)")
    record_check("maybe_storage_public", f, "broken" if any_broken else "fixed")


# --- 2. UnionMember.Construct() -> SetValue() -------------------------------
def fix_unionmember_construct():
    if not DIST_INCLUDE.exists():
        return
    for f in DIST_INCLUDE.rglob("*.h"):
        txt = f.read_text()
        broken = "mValue.mArrayBufferView.Construct(" in txt or "mValue.mArrayBuffer.Construct(" in txt
        if "mValue.mArrayBufferView.Construct(" in txt:
            safe_replace(f, "mValue.mArrayBufferView.Construct(", "mValue.mArrayBufferView.SetValue(",
                         "UnionMember.Construct()\u2192SetValue()")
        if "mValue.mArrayBuffer.Construct(" in txt:
            safe_replace(f, "mValue.mArrayBuffer.Construct(", "mValue.mArrayBuffer.SetValue(",
                         "UnionMember.Construct()\u2192SetValue()")
        record_check("unionmember_setvalue", f, "broken" if broken else "fixed")


# --- 3. Duplicate class definitions -----------------------------------------
def check_duplicate_class_defs():
    if not DIST_INCLUDE.exists():
        return
    seen = {}
    for f in DIST_INCLUDE.rglob("*.h"):
        txt = f.read_text()
        for m in re.finditer(r"class\s+MOZ_EMPTY_BASES\s+(\w+)\s*:", txt):
            cls = m.group(1)
            if cls in seen:
                log_warn(f"Duplicate class: {cls} in {seen[cls]} and {f.relative_to(ROOT)}")
            else:
                seen[cls] = f.relative_to(ROOT)


# --- 4. Forward-decl used as field without full def -------------------------
def check_forward_decl_usage():
    if not DIST_INCLUDE.exists():
        return
    for f in DIST_INCLUDE.rglob("*.h"):
        txt = f.read_text()
        if "class OwningArrayBufferViewOrArrayBuffer;" in txt and "class MOZ_EMPTY_BASES OwningArrayBufferViewOrArrayBuffer :" not in txt:
            log_warn(f"Forward decl only: OwningArrayBufferViewOrArrayBuffer in {f.relative_to(ROOT)} \u2014 ensure UnionTypes.h is included")
        if "class ArrayBufferViewOrArrayBuffer;" in txt and "class MOZ_EMPTY_BASES ArrayBufferViewOrArrayBuffer :" not in txt:
            log_warn(f"Forward decl only: ArrayBufferViewOrArrayBuffer in {f.relative_to(ROOT)} \u2014 ensure UnionTypes.h is included")


# --- 5. Union classes need required methods ---------------------------------
def check_union_methods():
    if not DIST_INCLUDE.exists():
        return
    required = {"Init", "TraceUnion", "ToJSVal", "TrySetToArrayBufferView", "TrySetToArrayBuffer", "Uninit", "operator="}
    for f in DIST_INCLUDE.rglob("*.h"):
        txt = f.read_text()
        for m in re.finditer(r"class MOZ_EMPTY_BASES (\w+) : public AllOwningUnionBase", txt):
            cls = m.group(1)
            for req in required:
                pattern = rf"{cls}::{req}\s*\("
                if not re.search(pattern, txt):
                    log_warn(f"Missing method: {cls}::{req} not found in {f.relative_to(ROOT)} (may be in .cpp)")


# --- 6. No pragma clang diagnostic to silence errors ------------------------
def check_pragma_clang():
    for f in ROOT.glob("*.h"):
        if "pragma clang diagnostic" in f.read_text():
            log_warn(f"Pragma suppression found in {f.relative_to(ROOT)}")


# --- 7. UnionTypes.h included where union types used as fields --------------
def check_uniontypes_includes():
    patterns = [
        (r"typedef\s+ArrayBufferViewOrArrayBuffer\s+\w+", "ArrayBufferViewOrArrayBuffer typedef"),
        (r"typedef\s+OwningArrayBufferViewOrArrayBuffer\s+\w+", "OwningArrayBufferViewOrArrayBuffer typedef"),
        (r"const\s+ArrayBufferViewOrArrayBuffer&", "ArrayBufferViewOrArrayBuffer reference"),
        (r"const\s+OwningArrayBufferViewOrArrayBuffer&", "OwningArrayBufferViewOrArrayBuffer reference"),
        (r"ArrayBufferViewOrArrayBuffer\s+\w+[;,)]", "ArrayBufferViewOrArrayBuffer field"),
        (r"OwningArrayBufferViewOrArrayBuffer\s+\w+[;,)]", "OwningArrayBufferViewOrArrayBuffer field"),
        (r"RootedUnion<\s*OwningBufferSource\s*>", "RootedUnion<OwningBufferSource>"),
        (r"RootedUnion<\s*BufferSource\s*>", "RootedUnion<BufferSource>"),
    ]
    files_to_check = list(SRC_DOM.rglob("*.h")) + list(SRC_DOM.rglob("*.cpp"))
    for f in files_to_check:
        try:
            txt = f.read_text()
        except UnicodeDecodeError:
            continue
        has_uniontypes = '#include "mozilla/dom/UnionTypes.h"' in txt or '#include <mozilla/dom/UnionTypes.h>' in txt
        for pattern, desc in patterns:
            if re.search(pattern, txt) and not has_uniontypes:
                log_warn(f"Missing include: {f.relative_to(ROOT)} uses {desc} but doesn't include UnionTypes.h")
                break


# --- 8. Maybe<T> where T is forward-declared union type ---------------------
def check_maybe_instantiation():
    for f in SRC_DOM.rglob("*.h"):
        try:
            txt = f.read_text()
        except UnicodeDecodeError:
            continue
        if re.search(r"Maybe<\s*ArrayBufferViewOrArrayBuffer\s*>", txt) or \
           re.search(r"Maybe<\s*OwningArrayBufferViewOrArrayBuffer\s*>", txt):
            has_uniontypes = '#include "mozilla/dom/UnionTypes.h"' in txt or '#include <mozilla/dom/UnionTypes.h>' in txt
            if not has_uniontypes:
                log_warn(f"Maybe instantiation: {f.relative_to(ROOT)} uses Maybe<union> but missing UnionTypes.h include")


# --- 9. IPC signature mismatches & resolver sanity (hardened) ---------------
def check_ipc_signatures():
    cc_path = SRC_DOM / "ipc/ContentChild.cpp"
    if cc_path.exists():
        txt = cc_path.read_text()
        if "SendCreateWindowInDifferentProcess" in txt:
            log_error("ContentChild.cpp uses deprecated SendCreateWindowInDifferentProcess")

    for path in [SRC_DOM / "ipc/ContentChild.h", SRC_DOM / "ipc/ContentChild.cpp"]:
        if path.exists():
            txt = path.read_text()
            if "LoadURIResolver" in txt:
                log_error(f"{path.relative_to(ROOT)} still mentions LoadURIResolver - must match IPDL LoadURI (no returns)")

    cp_path = SRC_DOM / "ipc/ContentParent.cpp"
    if cp_path.exists():
        txt = cp_path.read_text()
        if "RecvAddCertException" in txt:
            log_error("ContentParent.cpp still implements RecvAddCertException (spurious/undeclared method)")

    # --- 9a. AddCertExceptionResolver: THE bug from an earlier build attempt -----------
    # An earlier build attempt tried 6+ different wordings of this line across ~90 tool
    # calls and ended up back at the ORIGINAL broken text. The one form that
    # is actually valid C++ for "pull a nested type out of a dependent-ish
    # scope for local use" is a type ALIAS, not a bare using-declaration:
    #   using AddCertExceptionResolver = PWindowGlobalParent::AddCertExceptionResolver;
    # A bare `using PWindowGlobalParent::AddCertExceptionResolver;` or a
    # doubly-qualified `using mozilla::dom::PWindowGlobalParent::X;` are both
    # the broken forms seen in the logs. Auto-fix to the alias form and then
    # journal it so any future revert back to the bare form is caught as a
    # REGRESSION instead of silently re-debugged from scratch.
    if cp_path.exists():
        txt = cp_path.read_text()
        correct_alias = "using AddCertExceptionResolver = PWindowGlobalParent::AddCertExceptionResolver;"
        broken_forms = [
            "using PWindowGlobalParent::AddCertExceptionResolver;",
            "using mozilla::dom::PWindowGlobalParent::AddCertExceptionResolver;",
            "using mozilla::dom::AddCertExceptionResolver;",
            "// using mozilla::AddCertExceptionResolver;  // Type is in PWindowGlobalParent scope",
        ]
        if correct_alias in txt:
            record_check("addcertexception_resolver", cp_path, "fixed")
        else:
            found_broken = next((b for b in broken_forms if b in txt), None)
            if found_broken:
                safe_replace(cp_path, found_broken, correct_alias,
                             "AddCertExceptionResolver: bare/qualified using \u2192 type alias (only valid form)")
                record_check("addcertexception_resolver", cp_path, "broken", detail=found_broken)
            elif "AddCertExceptionResolver" in txt:
                log_warn("ContentParent.cpp references AddCertExceptionResolver in an unrecognized "
                         "form \u2014 verify manually against the generated PWindowGlobalParent.h "
                         "(obj-.../ipc/ipdl/_ipdlheaders/mozilla/dom/PWindowGlobalParent.h), not just the .ipdl")

    # --- 9b. `this` used in a non-member context (Phase 1 bug #2) ----------
    # An earlier build attempt added a bare `this` argument to CreateDisconnected() calls
    # without checking whether the enclosing function was actually a member
    # function, producing "invalid use of 'this' outside of a non-static
    # member function" — and never reverted it. Detect that specific shape:
    # a call to CreateDisconnected(..., this) sitting inside a function whose
    # signature doesn't look like a class member (best-effort heuristic:
    # flag any use of bare `this` that appears before the first `::` scoped
    # member-function definition above it in the same file).
    if cp_path.exists():
        txt = cp_path.read_text()
        for m in re.finditer(r"CreateDisconnected\([^)]*\bthis\b[^)]*\)", txt):
            line_no = txt[:m.start()].count("\n") + 1
            # crude but effective: walk backwards to the nearest enclosing
            # function signature and check it has a `ClassName::` qualifier
            preceding = txt[:m.start()]
            func_sigs = list(re.finditer(r"\n[\w:<>,\s\*&]+\s+(\w+::)?(\w+)\s*\([^)]*\)\s*\{", preceding))
            if func_sigs:
                last_sig = func_sigs[-1].group(0)
                if "::" not in last_sig:
                    log_error(f"ContentParent.cpp:{line_no}: CreateDisconnected(..., this) is called "
                              f"inside what looks like a non-member/free function \u2014 `this` is not "
                              f"valid there. This is the exact bug from the an earlier build attempt that was "
                              f"never reverted; use the explicit ContentParent* argument instead.")

    # --- 9c. RecvLoadURIExternal signature vs generated header -------------
    ch_path = SRC_DOM / "ipc/ContentChild.h"
    if ch_path.exists():
        txt = ch_path.read_text()
        m = re.search(r"RecvLoadURIExternal\s*\(([^)]*)\)", txt)
        if m:
            params = m.group(1)
            uses_notnull_uri = bool(re.search(r"NotNull<\s*nsIURI\s*\*?\s*>", params))
            if uses_notnull_uri:
                log_error("ContentChild.h: RecvLoadURIExternal takes NotNull<nsIURI*> for the uri "
                          "param. An earlier build attempt's own generated-header check showed the real call "
                          "site uses a raw nsIURI* here (only the principal is NotNull<>). Verify "
                          "against obj-.../_ipdlheaders before trusting this signature.")


# --- 10. FFmpeg logging formats (%p, %d, %s vs {}) — hardened for re-drift --
def check_ffmpeg_logging_format():
    f = ROOT / "dom/media/platforms/ffmpeg/FFmpegVideoDecoder.cpp"
    if not f.exists():
        return
    txt = f.read_text()
    pattern = r'FFMPEG[VEAP]?_LOG\s*\(\s*"([^"]*)"'
    any_bad = False
    for m in re.finditer(pattern, txt):
        log_str = m.group(1)
        if any(fmt_spec in log_str for fmt_spec in ["%p", "%d", "%s"]):
            any_bad = True
            log_line = txt[:m.start()].count("\n") + 1
            log_error(f"FFmpegVideoDecoder.cpp:{log_line} uses printf-style format specifier in "
                      f"FFMPEG_LOG: \"{log_str}\" (should use fmt braces {{}} instead)")
    # journal per-file rather than per-line: an earlier build attempt re-fixed the exact
    # same cast 3 times because it kept losing/regaining across edits done
    # against a stale in-memory copy. If this file flips from fixed->broken
    # between runs, that pattern is now caught explicitly.
    record_check("ffmpeg_log_format", f, "broken" if any_bad else "fixed")


# --- 11. Wayland GPU Process Unblock ----------------------------------------
def check_wayland_gpu_unblock():
    f = ROOT / "gfx/thebes/gfxPlatformGtk.cpp"
    if not f.exists():
        return
    txt = f.read_text()
    block = "if (IsWaylandDisplay())"
    any_active = False
    if block in txt:
        lines = txt.splitlines()
        for idx, line in enumerate(lines):
            if block in line and not line.strip().startswith("//"):
                any_active = True
                log_error(f"gfxPlatformGtk.cpp:{idx+1} has active ForceDisable block on Wayland GPU "
                          f"process (should remain commented out for hardware VA-API decode!)")
    record_check("wayland_gpu_unblock", f, "broken" if any_active else "fixed")


# --- 12. Missing StaticPrefs definitions ------------------------------------
def check_missing_static_prefs():
    f = ROOT / "modules/libpref/init/StaticPrefList.yaml"
    if not f.exists():
        return
    txt = f.read_text()
    if "security.csp.truncate_blocked_uri_for_frame_navigations" not in txt:
        log_error("StaticPrefList.yaml is missing security.csp.truncate_blocked_uri_for_frame_navigations preference")
    if "javascript.options.warn_asmjs_deprecation" not in txt:
        log_error("StaticPrefList.yaml is missing javascript.options.warn_asmjs_deprecation preference")
    else:
        pref_block = txt.split("javascript.options.warn_asmjs_deprecation")[1][:200]
        if "set_spidermonkey_pref: startup" not in pref_block and "set_spidermonkey_pref: always" not in pref_block:
            log_error("javascript.options.warn_asmjs_deprecation in StaticPrefList.yaml is missing set_spidermonkey_pref: startup attribute")


# --- 13. AudioStream custom "hardware-only volume" patch (Phase 2 #74/#81) --
# This is the pre-existing, incompletely-applied out-of-tree patch that
# surfaced only AFTER a successful IPDL/webidl regeneration an earlier build attempt
# (i.e. it was masked by the IPC errors the whole time). Check it up front
# so it doesn't ambush a build 12 hours in again.
def check_audiostream_patch():
    h = ROOT / "dom/media/AudioStream.h"
    cpp = ROOT / "dom/media/AudioStream.cpp"
    if not (h.exists() and cpp.exists()):
        return
    h_txt = h.read_text()
    cpp_txt = cpp.read_text()
    members = ["mPsychoEnhancer", "mVolume", "mUseSoftwareVolume"]
    missing = [m for m in members if m in cpp_txt and m not in h_txt]
    if missing:
        log_error(f"AudioStream.cpp references {', '.join(missing)} but AudioStream.h never "
                  f"declares them \u2014 the custom hardware-volume patch is incompletely applied. "
                  f"This surfaces only AFTER dom/ipc compiles clean, so fix it now rather than "
                  f"being surprised by it late in a build.")
    record_check("audiostream_patch_members", h, "broken" if missing else "fixed")


# --- 14. mozwebidlcodegen — correct invocation, verified ---------------------
# An earlier build attempt lost 2 of 3 attempts on a basic PYTHONPATH mistake: adding
# the package's OWN directory (dom/bindings/mozwebidlcodegen) instead of its
# PARENT (dom/bindings) to sys.path. Provide one correct, pre-verified helper
# instead of letting an agent rediscover this by trial and error.
def run_mozwebidlcodegen(dry_run=True):
    bindings_parent = ROOT / "dom" / "bindings"
    pkg_dir = bindings_parent / "mozwebidlcodegen"
    if not pkg_dir.exists():
        log_warn("dom/bindings/mozwebidlcodegen not found \u2014 skipping codegen helper check")
        return
    if dry_run:
        print(f"  \u2139\ufe0f  mozwebidlcodegen helper available: run with PYTHONPATH including "
              f"'{bindings_parent}' (its PARENT dir, not the package dir itself). "
              f"Call preflight_clang21.run_mozwebidlcodegen(dry_run=False) to actually invoke it.")
        return
    cmd = [sys.executable, "-c",
           "import mozwebidlcodegen; print('Codegen module import OK')"]
    env_note = f"PYTHONPATH={bindings_parent}"
    result = subprocess.run(cmd, cwd=ROOT, env={"PYTHONPATH": str(bindings_parent)},
                             capture_output=True, text=True)
    if result.returncode != 0:
        log_error(f"mozwebidlcodegen import failed even with correct PYTHONPATH ({env_note}): "
                  f"{result.stderr.strip()[-300:]}")
    else:
        log_fix(f"mozwebidlcodegen imports cleanly with {env_note}")


# ---------------------------------------------------------------------------
# Section F — GENERIC Clang 21.1.0 conformance changes (from the real
# releases.llvm.org/21.1.0 release notes, not Firefox-specific patches).
# These are best-effort greps for patterns the notes call out explicitly.
# ---------------------------------------------------------------------------
def check_generic_clang21_conformance():
    cpp_like = list(ROOT.glob("**/*.cpp")) if False else []  # deliberately not a full-tree scan;
    # scanning the whole 40M-line tree on every preflight run is not
    # practical. Instead, scan the same dom/ + gfx/ + modules/ subtrees this
    # script already touches, which is where the Gorilla patches live.
    scan_dirs = [SRC_DOM, ROOT / "gfx", ROOT / "modules" / "libpref", ROOT / "dom" / "media"]
    files = []
    for d in scan_dirs:
        if d.exists():
            files.extend(d.rglob("*.h"))
            files.extend(d.rglob("*.cpp"))

    seen_shift_bool = False
    seen_is_referenceable = False
    seen_enum_const_cast = False

    for f in files:
        try:
            txt = f.read_text()
        except UnicodeDecodeError:
            continue

        # New in 21.1.0: -Wshift-bool warns on shifting a boolean value.
        if re.search(r"\bbool\b[^;=]{0,40}(<<|>>)=?\s", txt) or re.search(r"(<<|>>)\s*\(?\s*true\b", txt):
            seen_shift_bool = True
            log_warn(f"{f.relative_to(ROOT)}: possible bool-shift pattern \u2014 new in Clang 21.1.0, "
                     f"-Wshift-bool now warns on shifting a boolean value")

        # __is_referenceable builtin was removed in 21.1.0.
        if "__is_referenceable" in txt:
            seen_is_referenceable = True
            log_error(f"{f.relative_to(ROOT)}: uses __is_referenceable, which was REMOVED in "
                      f"Clang 21.1.0 (no replacement needed \u2014 the standard library type traits "
                      f"that used it now have their own builtins)")

        # 21.1.0 tightened integer->enum conversions in constant expressions:
        # `const E x = (E)-1;` is no longer treated as a constant if out of range.
        if re.search(r"const\s+\w+\s+\w+\s*=\s*\(\s*\w+\s*\)\s*-?\d+\s*;", txt):
            for m in re.finditer(r"const\s+(\w+)\s+(\w+)\s*=\s*\(\s*(\w+)\s*\)\s*(-?\d+)\s*;", txt):
                if m.group(1) == m.group(3):  # cast target type matches declared type -> likely an enum cast
                    seen_enum_const_cast = True
                    line_no = txt[:m.start()].count("\n") + 1
                    log_warn(f"{f.relative_to(ROOT)}:{line_no}: `const {m.group(1)} {m.group(2)} = "
                             f"({m.group(3)}){m.group(4)};` \u2014 Clang 21.1.0 more strictly checks "
                             f"integer-to-enum conversions in constant expressions; verify {m.group(4)} "
                             f"is in range for {m.group(1)}, or this may no longer be treated as constant")

    if not (seen_shift_bool or seen_is_referenceable or seen_enum_const_cast):
        print("  \u2705 No generic Clang 21.1.0 conformance-change patterns found in scanned subtrees")


# ---------------------------------------------------------------------------
# Section G — build-log loop detector
# ---------------------------------------------------------------------------
def detect_build_loop(log_paths, min_repeats=2):
    """
    Feed this the last N `./mach build` log paths (oldest first). If the same
    error signature (file:line: error: ...) appears unchanged across
    `min_repeats` consecutive logs, that means an edit cycle did NOT change
    the outcome for that error — which is exactly what happened with
    AddCertExceptionResolver and the ContentChild scope issue an earlier build attempt,
    for 8+ build cycles each, without anyone stopping to say "this isn't
    working, stop editing blindly and re-diagnose."
    """
    sig_re = re.compile(r"([\w./]+\.(?:cpp|h)):(\d+):\d+:\s*error:\s*(.+)")
    all_sigs = []
    for p in log_paths:
        p = Path(p)
        if not p.exists():
            continue
        sigs = set()
        for line in p.read_text(errors="replace").splitlines():
            m = sig_re.search(line)
            if m:
                sigs.add((m.group(1), m.group(2), m.group(3).strip()[:120]))
        all_sigs.append(sigs)

    if len(all_sigs) < min_repeats:
        return

    # find signatures present in every one of the last `min_repeats` logs
    recent = all_sigs[-min_repeats:]
    persistent = set.intersection(*recent) if recent else set()
    for file_, line_, msg in sorted(persistent):
        log_error(f"BUILD LOOP: {file_}:{line_}: '{msg}' has appeared unchanged in the last "
                  f"{min_repeats} build logs. STOP making incremental edits to this symbol \u2014 "
                  f"re-read the actual generated header / .ipdl source before touching it again.")


# ---------------------------------------------------------------------------
def main():
    print("\U0001F50D Clang 21 Pre-Flight Check v2 (regression-guarded)")
    print(f"   Root: {ROOT}")

    fix_maybe_storage_protected()
    fix_unionmember_construct()
    check_duplicate_class_defs()
    check_forward_decl_usage()
    check_union_methods()
    check_pragma_clang()
    check_uniontypes_includes()
    check_maybe_instantiation()
    check_ipc_signatures()
    check_ffmpeg_logging_format()
    check_wayland_gpu_unblock()
    check_missing_static_prefs()
    check_audiostream_patch()
    run_mozwebidlcodegen(dry_run=True)
    check_generic_clang21_conformance()

    # Optional: if recent build logs exist at the conventional /tmp/build*.log
    # paths this tree's build tooling has used, check them for loops.
    recent_logs = sorted(Path("/tmp").glob("build*.log"), key=lambda p: p.stat().st_mtime)[-4:]
    if recent_logs:
        detect_build_loop(recent_logs)

    save_state(STATE)

    if FIXES_APPLIED:
        print("\n\u2705 Auto-fixes applied:")
        for fx in FIXES_APPLIED:
            print(f"  - {fx}")
    else:
        print("\n\u2705 No auto-fixes needed")

    if REGRESSIONS:
        print(f"\n\U0001F6A8 {len(REGRESSIONS)} REGRESSION(S) \u2014 something reverted a prior fix:")
        for r in REGRESSIONS:
            print(f"  - {r}")

    if WARNINGS:
        print(f"\n\u26a0\ufe0f  {len(WARNINGS)} warnings \u2014 review before build")

    if ERRORS:
        print(f"\n\u274c {len(ERRORS)} errors \u2014 build will fail")
        return 1

    print("\n\U0001F3C1 Pre-flight complete")
    return 0


if __name__ == "__main__":
    sys.exit(main())
