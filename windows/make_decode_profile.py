"""Emit a per-machine hardware-decode pref file for a Gorilla Unleashed install.

THE PROBLEM THIS SOLVES
  The Gorilla codec policy is H.264-only:

      media.av1.enabled             false
      media.vp9.enabled             false
      media.mediasource.vp9.enabled false
      media.webm.enabled            false
      media.hevc.enabled            false

  On Linux that is correct AND enforced in C++ (PDMFactory rejects anything
  the decoder does not report as HardwareDecode). It was chosen for the
  weakest machine in the fleet - the Ivy Bridge VAIO, whose HD 4000 and
  Radeon HD 7670M can hardware-decode H.264 and nothing newer. Software VP9
  on that machine is CPU burn, and the fleet runs under a hard thermal cap.

  On Windows the C++ half does NOT exist - the patchset touches no file under
  dom/media. The policy is prefs only, so it is per-machine tunable without a
  rebuild. And on modern hardware it is actively wasteful: an Arrow Lake or
  Xe-LP media engine has dedicated AV1 and VP9 decoders that these prefs
  leave idle, while YouTube, denied VP9/AV1, falls back to H.264 and caps at
  1080p.

  H.264-only is the right FLEET-WIDE default because it is the only codec
  every machine can decode in hardware. It is the wrong PER-MACHINE setting
  for anything newer than Kaby Lake.

WHAT THIS WRITES
  A file placed in the INSTALL directory:

      <install>\\defaults\\pref\\gorilla-decode.js

  That location is read at startup and applies to every profile on the
  machine - no profile editing, no user.js, nothing lost when a profile is
  recreated. The Gorilla codec prefs are NOT locked, so a later default here
  legitimately overrides the baked-in value.

  Prerequisite, and the reason this tool is worth anything: hardware decode on
  Windows runs in the GPU process. The patchset shipped Wayland's
  `layers.gpu-process.enabled=false` unguarded, which disabled it on Windows
  entirely. Fixed by guard_linux_prefs.py - without that fix every tier below
  decodes in software regardless of what this file says.

USAGE
    python "working scripts/make_decode_profile.py" --detect
    python "working scripts/make_decode_profile.py" --machine p16 --print
    python "working scripts/make_decode_profile.py" --detect --apply
    python "working scripts/make_decode_profile.py" --list
"""
import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

# Resolve the project root portably. A hardcoded user directory works on
# exactly one machine and leaks a username into a published file.
# Order: --root, then $GORILLA_ROOT, then the parent of this script's dir.
ROOT = Path(os.environ.get("GORILLA_ROOT")
            or Path(__file__).resolve().parent.parent)

# Capability tiers. Each lists what the MEDIA ENGINE can decode in hardware.
# Ordered weakest to strongest. RANK matters: on a machine with more than one
# GPU we take the WEAKEST, see pick_tier().
TIERS = {
    "h264": {
        "rank": 0,
        "label": "H.264-only (Intel Gen7 Ivy Bridge and older, NVIDIA Maxwell gen1, AMD TeraScale/UVD3)",
        "codecs": ["h264"],
    },
    "hevc": {
        "rank": 1,
        "label": "H.264 + HEVC, no VP9 (AMD Polaris/UVD6, NVIDIA Maxwell gen2)",
        "codecs": ["h264", "hevc"],
    },
    "vp9": {
        "rank": 2,
        "label": "VP9-class (Intel Gen9/9.5 Skylake-Coffee Lake, NVIDIA Pascal/Turing)",
        "codecs": ["h264", "vp9", "hevc"],
    },
    "av1": {
        "rank": 3,
        "label": "AV1-class (Intel Gen12 Xe-LP / Xe-LPG / Arc, NVIDIA RTX 30+, AMD RDNA2+)",
        "codecs": ["h264", "vp9", "hevc", "av1"],
    },
}

# Known hardware profiles. `note` records anything uncertain -
# a guess presented as a fact is how the wrong pref ends up shipped.
FLEET = {
    "p16": {
        "name": "ThinkPad P16 Gen 3",
        "cpu": "Core Ultra 9 285HX (Arrow Lake-HX)",
        "gpu": "Intel Arc / Xe-LPG integrated",
        "tier": "av1",
        "note": "may also carry a discrete NVIDIA workstation GPU; either way the "
                "tier is AV1-class. Run --detect on the machine to confirm.",
    },
    "l15": {
        "name": "ThinkPad L15 Gen 3",
        "cpu": "i7-1255U (Alder Lake-U)",
        "gpu": "Iris Xe, Gen12 Xe-LP 96EU",
        "tier": "av1",
        "note": "AV1 decode arrived with Gen12 (Tiger Lake) and is present here. "
                "The reference build machine.",
    },
    "p7520q": {
        "name": "Dell Precision 7520 + Quadro M1200",
        "cpu": "i7-7820HQ (Kaby Lake)",
        "gpu": "NVIDIA Quadro M1200 4GB (+ Intel HD 630 if Optimus is enabled)",
        "tier": "h264",
        "note": "The Quadro M1200 is GM107 - 1st-generation "
                "Maxwell, whose NVDEC does H.264/MPEG-2/VC-1 and nothing else "
                "(HEVC arrived with GM206, VP9 with Pascal). So whether the BIOS "
                "is in discrete-only mode or Optimus, the weakest adapter is "
                "H.264-only and the tier is h264 either way. The shipped build "
                "already sets exactly this, so such a machine needs NO tuning file. "
                "Not the same silicon as the VAIO despite the similar verdict: the "
                "7520's HD 630 iGPU is Gen9.5 and could do VP9+HEVC, it is simply "
                "outvoted by the Quadro.",
    },
    "p7520": {
        "name": "Dell Precision 7520 (other configurations)",
        "cpu": "i7-7920HQ / Xeon E3-1505M v6 (Kaby Lake)",
        "gpu": "Intel HD 630 / HD P630 + Quadro M2200 or Radeon Pro WX 4130/4150",
        "tier": "h264",
        "note": "NOT the same silicon as the VAIO - five generations newer. Its "
                "Intel iGPU is Gen9.5 and decodes H.264, VP9 and HEVC. But the "
                "Quadro M-series option is 1st-gen Maxwell (H.264 only), and which "
                "GPU Firefox decodes on depends on the switchable-graphics mode. "
                "Recorded at the FLOOR. Run --detect on the actual unit: if it "
                "reports only the HD 630, it earns the vp9 tier.",
    },
    "vaio": {
        "name": "Sony VAIO SVE14A3AJ",
        "cpu": "i7-3632QM (Ivy Bridge)",
        "gpu": "HD 4000 + Radeon HD 7670M (Turks, UVD3)",
        "tier": "h264",
        "note": "NEITHER GPU decodes VP9, HEVC or AV1. The fleet-wide H.264-only "
                "policy exists for this machine. Currently runs Linux.",
    },
    "dell": {
        "name": "Dell Inspiron 13 7373",
        "cpu": "i5-8250U / i7-8550U (Kaby Lake-R)",
        "gpu": "UHD 620, Gen9.5",
        "tier": "vp9",
        "note": "VP9 Profile 0/2 and HEVC Main/Main10 in hardware; NO AV1. "
                "Currently runs Linux.",
    },
    "unknown": {
        "name": "Unsurveyed machine",
        "cpu": "unknown",
        "gpu": "unknown",
        "tier": None,
        "note": "Hardware not recorded - do not guess. Run --detect on it.",
    },
}

# Detection patterns, most specific first. Intel generation is the hard part:
# the marketing name rarely says the generation, so CPU model is checked too.
# ORDER MATTERS - most specific first, and the Intel families are listed
# oldest-name-first because the generic "Intel ... Graphics <nnn>" pattern for
# Arc 130V/140V happily swallows "UHD Graphics 620". It did exactly that in
# the first version and promoted a Kaby Lake machine to the AV1 tier, which
# would have enabled AV1 on a GPU with no AV1 decoder - software decode on a
# thermally capped laptop, the precise outcome this tool exists to avoid.
#
# Model numbers may carry a trailing letter (7670M, 140V), so no pattern ends
# in \b after a digit group - "radeon hd 7670m" failed to match `[67]\d{3}\b`.
GPU_RULES = [
    # --- Intel, specific families before the generic Arc catch-all ---------
    (r"\bhd graphics (2000|3000)", "h264"),                   # Sandy Bridge, Gen6
    (r"\bhd graphics 4[0-9]{3}", "h264"),                     # Ivy Bridge Gen7 / Haswell
    # "UHD" does NOT imply a generation - UHD 620 is Gen9.5 (no AV1) while
    # UHD 730/770 is Alder Lake Gen12.2 (AV1 decode present). The NUMBER is
    # what carries the media engine, so these two rules must stay separate.
    (r"\buhd graphics 7[0-9]{2}", "av1"),                     # Gen12.2, Alder Lake-S
    # The "P" variants (HD P530/P630) are the workstation-certified bin of the
    # same silicon - the Precision 7520's Xeon option reports HD P630. Without
    # the optional p this pattern refused its own deployment target.
    (r"\b(u?hd) graphics p?(5[0-9]{2}|6[0-9]{2})", "vp9"),    # Gen9 / Gen9.5
    (r"\biris\s*(plus|pro)?\s*graphics (5|6)\d{2}", "vp9"),   # Gen9 Iris
    (r"\biris\s*xe", "av1"),                                  # Gen12 Xe-LP, Tiger Lake+
    (r"\b(arc|xe-lpg|xe2|battlemage|alchemist|lunar lake)", "av1"),
    (r"\bintel.*\bgraphics\s*1[3-9]\d[a-z]?\b", "av1"),       # Arc 130V/140V
    # --- NVIDIA ------------------------------------------------------------
    (r"\brtx\s*[3-9]\d{3}", "av1"),                           # RTX 30-series+
    (r"\brtx\s*(a\d{3,4}|2\d{3})", "vp9"),                    # Turing incl. RTX A-series
    (r"\bgtx\s*(9\d{2}|1[0-9]{3}|16\d{2})", "vp9"),
    (r"\bquadro\s*[pt]\d{3,4}", "vp9"),                       # Quadro Pascal / Turing
    # Quadro M-series is 1st-gen Maxwell (GM107): NVDEC does H.264/VC-1/MPEG-2
    # only. HEVC arrived with GM206, VP9 with Pascal. The Precision 7520's
    # M1200/M2200 are therefore H.264-only, NOT the same tier as its iGPU.
    (r"\bquadro\s*m\d{3,4}", "h264"),
    (r"\bquadro\s*k\d{3,4}", "h264"),                         # Kepler
    # --- AMD ---------------------------------------------------------------
    (r"\bradeon.*\b(rx\s*[6-9]\d{3}|[78]\d0m\b)", "av1"),     # RDNA2+ / RDNA3 iGPU
    (r"\bradeon.*\bvega", "vp9"),
    (r"\bradeon.*\brx\s*[45]\d{2}", "hevc"),                  # Polaris: HEVC yes, VP9 no
    (r"\bradeon pro\s*wx\s*\d{4}", "hevc"),                   # Polaris workstation
    (r"\bradeon hd [5-7]\d{3}", "h264"),                      # TeraScale / UVD3
]

CODEC_PREFS = {
    "h264": [("media.mp4.enabled", "true")],
    "vp9": [("media.vp9.enabled", "true"),
            ("media.mediasource.vp9.enabled", "true"),
            ("media.webm.enabled", "true")],
    "hevc": [("media.hevc.enabled", "true")],
    "av1": [("media.av1.enabled", "true")],
}


def normalise(s):
    """Strip the trademark noise Windows puts INSIDE product names.

    WMI reports "Intel(R) Iris(R) Xe Graphics". A pattern of `iris\\s*xe`
    never matches that, because "(R)" sits between the two words - so the
    first version of this tool failed to recognise its own build machine.
    It refused to guess rather than picking a tier, which is the only reason
    the bug was visible instead of silently producing the wrong pref file.
    """
    s = re.sub(r"\((?:r|tm|c)\)", " ", s, flags=re.I)
    s = re.sub(r"[®™]", " ", s)
    return re.sub(r"\s+", " ", s).strip().lower()


def classify(gpu, cpu=""):
    hay = normalise("%s %s" % (gpu, cpu))
    for pat, tier in GPU_RULES:
        if re.search(pat, hay):
            return tier
    return None


def pick_tier(tiers):
    """Take the WEAKEST tier across all adapters.

    A mobile workstation like the Precision 7520 has two GPUs - an Intel HD
    630 (VP9-class) and a Quadro M1200 (H.264-only, 1st-gen Maxwell NVDEC).
    Which one Firefox decodes on depends on the Optimus/switchable mode, the
    display wiring and the driver - none of which this script can see.

    An earlier version read `Select-Object -First 1` and took whatever WMI
    listed first, which is arbitrary. On a 7520 in discrete mode that would
    have enabled VP9 on a GPU with no VP9 decoder - software decode on an
    older laptop, the precise outcome the tool exists to prevent.

    So: the floor, not the ceiling. An unrecognised adapter makes the whole
    machine unrecognised, because an unknown GPU could be the weak one.
    """
    if not tiers or any(t is None for t in tiers):
        return None
    return min(tiers, key=lambda t: TIERS[t]["rank"])


def detect():
    """Return (adapters, cpu_name, tier or None).

    `adapters` is a list of (name, tier) for EVERY display adapter present.
    """
    ps = ("$g=(Get-CimInstance Win32_VideoController).Name -join '~';"
          "$c=(Get-CimInstance Win32_Processor|Select-Object -First 1).Name;"
          "Write-Output \"$g|$c\"")
    try:
        r = subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                           capture_output=True, text=True, timeout=90)
        gpus, _, cpu = (r.stdout or "").strip().partition("|")
    except Exception:
        return [], None, None
    names = [g.strip() for g in gpus.split("~") if g.strip()]
    if not names:
        return [], None, None
    cpu = cpu.strip()
    adapters = [(n, classify(n, cpu)) for n in names]
    return adapters, cpu, pick_tier([t for _n, t in adapters])


def render(tier, why):
    codecs = TIERS[tier]["codecs"]
    on = []
    for c in codecs:
        on.extend(CODEC_PREFS.get(c, []))
    lines = [
        "// Gorilla Unleashed - per-machine hardware decode profile",
        "//",
        "// Generated by working scripts/make_decode_profile.py",
        "// %s" % why,
        "//",
        "// The build ships an H.264-only codec policy, chosen for the OLDEST",
        "// machine in the fleet (Ivy Bridge, which has no VP9/HEVC/AV1 decoder",
        "// at all). This file re-enables the codecs THIS machine can decode in",
        "// hardware. Codecs left off are decoded in software or not at all -",
        "// which on a thermally capped laptop is the thing worth avoiding.",
        "//",
        "// Tier: %s" % TIERS[tier]["label"],
        "// Hardware-decodable here: %s" % ", ".join(codecs),
        "",
        "// Hardware decode runs in the GPU process on Windows. These are the",
        "// upstream Windows defaults and are restated only so that a machine",
        "// carrying an older Gorilla build is corrected too.",
        'pref("layers.gpu-process.enabled", true);',
        'pref("media.gpu-process-decoder", true);',
        'pref("media.hardware-video-decoding.enabled", true);',
        "",
    ]
    for name, val in on:
        lines.append('pref("%s", %s);' % (name, val))
    off = [c for c in ("vp9", "hevc", "av1") if c not in codecs]
    if off:
        lines += ["", "// No hardware decoder on this machine - left disabled on purpose:"]
        for c in off:
            for name, _ in CODEC_PREFS[c]:
                lines.append('// pref("%s", true);   // %s: software only here' % (name, c))
    return "\n".join(lines) + "\n"


def find_install():
    import os
    lnk = Path(os.environ.get("USERPROFILE", "")) / "Desktop" / "Gorilla Unleashed.lnk"
    if lnk.is_file():
        ps = ("$s=(New-Object -ComObject WScript.Shell).CreateShortcut("
              + repr(str(lnk)).replace('"', "'") + ");Write-Output $s.TargetPath")
        try:
            r = subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                               capture_output=True, text=True, timeout=60)
            t = (r.stdout or "").strip()
            if t and Path(t).is_file():
                return Path(t).parent
        except Exception:
            pass
    c = Path(os.environ.get("USERPROFILE", "")) / "Gorilla Unleashed"
    return c if (c / "firefox.exe").is_file() else None


def verify(install):
    """Prove the install actually READS defaults/pref/gorilla-decode.js.

    "It is the standard mechanism" is an assumption, and about:support in
    headless mode renders its value cells empty, so a screenshot proves
    nothing either.

    This exploits how Firefox persists prefs: prefs.js records only values
    that DIFFER from the running default. So force media.av1.enabled=false in
    a throwaway profile and see whether it gets written:

        written  -> the running default was true  -> our file was read
        absent   -> the default was already false -> our file was NOT read

    A clean decision either way, with no screenshot and no guessing.
    """
    import os
    import shutil
    import tempfile
    ff = install / "firefox.exe"
    if not ff.is_file():
        return None, "no firefox.exe at %s" % install
    prof = Path(tempfile.mkdtemp(prefix="gdecode_"))
    try:
        (prof / "user.js").write_text('user_pref("media.av1.enabled", false);\n',
                                      encoding="utf-8")
        subprocess.run([str(ff), "-profile", str(prof), "-headless",
                        "-screenshot", str(prof / "x.png"), "about:blank"],
                       capture_output=True, timeout=180)
        pj = prof / "prefs.js"
        body = pj.read_text(encoding="utf-8", errors="replace") if pj.is_file() else ""
        if "media.av1.enabled" in body:
            return True, "default is TRUE - gorilla-decode.js is being read"
        return False, ("default is still false - gorilla-decode.js is NOT being "
                       "read (wrong directory, or the file was never written)")
    except Exception as exc:
        return None, "could not run the check: %s" % exc
    finally:
        shutil.rmtree(prof, ignore_errors=True)


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--verify", action="store_true",
                    help="prove the install reads the generated pref file")
    ap.add_argument("--detect", action="store_true", help="inspect this machine's GPU")
    ap.add_argument("--machine", choices=sorted(FLEET), help="use a known fleet entry")
    ap.add_argument("--tier", choices=sorted(TIERS), help="force a tier")
    ap.add_argument("--list", action="store_true", help="print the fleet matrix")
    ap.add_argument("--print", dest="show", action="store_true", help="print, do not write")
    ap.add_argument("--apply", action="store_true", help="write into the install")
    ap.add_argument("--install", default=None)
    args = ap.parse_args()

    if args.list:
        print("FLEET HARDWARE DECODE MATRIX")
        print("=" * 78)
        print("%-6s %-30s %-6s %s" % ("key", "machine", "tier", "hardware-decodable"))
        print("-" * 78)
        for k, m in FLEET.items():
            t = m["tier"]
            print("%-6s %-30s %-6s %s"
                  % (k, m["name"][:30], t or "?",
                     ", ".join(TIERS[t]["codecs"]) if t else "unknown - run --detect"))
        print("")
        for k, m in FLEET.items():
            print("  %s: %s / %s" % (k, m["cpu"], m["gpu"]))
            print("      %s" % m["note"])
        print("")
        print("H.264 is the ONLY codec every machine decodes in hardware - which is")
        print("why the build defaults to it. Anything newer than Kaby Lake is being")
        print("held back by that default.")
        return 0

    if args.verify:
        install = Path(args.install) if args.install else find_install()
        if not install:
            print("no install found - pass --install <dir>")
            return 2
        f = install / "defaults" / "pref" / "gorilla-decode.js"
        print("install : %s" % install)
        print("file    : %s" % ("present" if f.is_file() else "ABSENT - run --apply first"))
        ok, msg = verify(install)
        print("read    : %s" % msg)
        return 0 if ok else 1

    tier, why = None, ""
    if args.tier:
        tier, why = args.tier, "Tier forced on the command line."
    elif args.machine:
        m = FLEET[args.machine]
        tier = m["tier"]
        why = "Machine: %s (%s / %s)" % (m["name"], m["cpu"], m["gpu"])
        if tier is None:
            print("%s has no recorded hardware - run --detect on it." % m["name"])
            print("  %s" % m["note"])
            return 2
    else:
        adapters, cpu, tier = detect()
        if not adapters:
            print("could not query the GPU (is this Windows?)")
            return 2
        print("detected CPU : %s" % cpu)
        for n, t in adapters:
            print("     adapter : %-42s %s" % (n, t or "UNRECOGNISED"))
        if tier is None:
            print("")
            print("NOT GUESSING. Re-run with --tier h264|hevc|vp9|av1 once you know")
            print("the media engine generation of every adapter above. A wrong tier")
            print("enables a codec the GPU cannot decode, which forces SOFTWARE")
            print("decode - the outcome this tool exists to prevent.")
            return 2
        if len(adapters) > 1:
            print("")
            print("%d adapters - taking the WEAKEST, since which one Firefox decodes"
                  % len(adapters))
            print("on depends on the switchable-graphics mode, not on this script.")
        print("tier         : %s" % TIERS[tier]["label"])
        why = "Detected on this machine: %s / %s" % (
            " + ".join(n for n, _t in adapters), cpu)

    body = render(tier, why)
    if args.show or not args.apply:
        print("")
        print(body)
        if not args.apply:
            print("# nothing written - pass --apply to install it")
        return 0

    install = Path(args.install) if args.install else find_install()
    if not install:
        print("no install found - pass --install <dir>")
        return 2
    dst = install / "defaults" / "pref" / "gorilla-decode.js"
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(body, encoding="utf-8", newline="\n")
    print("")
    print("wrote %s" % dst)
    print("restart the browser, then confirm in about:support under")
    print("'Media' that the decoder name is a hardware one (not 'ffvpx').")
    return 0


if __name__ == "__main__":
    sys.exit(main())
