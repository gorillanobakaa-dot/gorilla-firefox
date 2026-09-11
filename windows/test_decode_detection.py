"""Failure test for make_decode_profile.py's GPU tier detection.

A check is not finished until you have watched it fail. This file exists
because the first version of the detector got two of the five fleet machines
wrong, and both were silent - it produced a confident, incorrect tier:

  * "Intel(R) Iris(R) Xe Graphics" was UNRECOGNISED, because WMI puts "(R)"
    between the words and `iris\\s*xe` never matched. Visible only because the
    tool refuses to guess.

  * "Intel(R) UHD Graphics 620" was promoted to the AV1 tier, because the
    generic Arc 130V/140V pattern `graphics\\s*[2-9]\\d{2}` also matches "620".
    That would have enabled AV1 on a Kaby Lake iGPU with no AV1 decoder -
    software decode on a thermally capped laptop, the exact failure the tool
    is meant to prevent.

  * "AMD Radeon HD 7670M" matched nothing, because the pattern ended in \\b
    after a digit group and the model number carries a trailing "M".

Every case below is a real adapter string, and the fleet entries are marked.

USAGE
    python "working scripts/test_decode_detection.py"
"""
import importlib.util
import re
import sys
from pathlib import Path

TOOL = Path(__file__).resolve().parent / "make_decode_profile.py"

# (gpu as WMI reports it, cpu, expected tier, note)
CASES = [
    ("Intel(R) Iris(R) Xe Graphics", "12th Gen Intel(R) Core(TM) i7-1255U",
     "av1", "Alder Lake-U, the build machine"),
    ("Intel(R) Arc(TM) Graphics", "Intel(R) Core(TM) Ultra 9 285HX",
     "av1", "Arrow Lake-HX workstation"),
    ("Intel(R) UHD Graphics 620", "Intel(R) Core(TM) i5-8250U",
     "vp9", "Kaby Lake-R: VP9/HEVC yes, AV1 NO"),
    ("Intel(R) HD Graphics 4000", "Intel(R) Core(TM) i7-3632QM",
     "h264", "Ivy Bridge iGPU - H.264 only"),
    ("AMD Radeon HD 7670M", "Intel(R) Core(TM) i7-3632QM",
     "h264", "Turks/UVD3 dGPU - H.264 only"),
    ("NVIDIA GeForce RTX 4070 Laptop GPU", "Intel Core Ultra 9 285HX",
     "av1", "Ada-class discrete GPU"),
    ("NVIDIA GeForce RTX 2060", "Intel Core i7-9750H", "vp9", "Turing: no AV1"),
    ("NVIDIA GeForce GTX 1060", "Intel Core i7-7700", "vp9", "Pascal"),
    # This case was written with the WRONG expectation (vp9) and the detector
    # was "fixed" toward it before the hardware was checked. UHD 770 is Alder
    # Lake-S Gen12.2 and DOES decode AV1; UHD 620 is Gen9.5 and does not.
    # "UHD" names a brand, not a media engine - only the number tells you.
    ("Intel(R) UHD Graphics 770", "12th Gen Intel(R) Core(TM) i9-12900K",
     "av1", "Gen12.2 desktop - AV1 decode present, unlike the Gen9.5 UHD 6xx"),
    ("Intel(R) UHD Graphics 730", "12th Gen Intel(R) Core(TM) i5-12400",
     "av1", "same Gen12.2 media engine"),
    ("AMD Radeon RX 7600M XT", "AMD Ryzen 7 7840HS", "av1", "RDNA3"),
    # Polaris decodes HEVC but has only hybrid/driver-assisted VP9, so it is
    # the "hevc" tier, not "vp9". Getting this wrong enables VP9 on hardware
    # that then decodes it in software.
    ("AMD Radeon RX 580", "Intel Core i5-8400", "hevc", "Polaris: HEVC yes, VP9 no"),
    # --- Dell Precision 7520, the deployment target -----------------------
    ("Intel(R) HD Graphics 630", "Intel(R) Core(TM) i7-7820HQ",
     "vp9", "P7520 iGPU - Kaby Lake Gen9.5, NOT the VAIO's Gen7"),
    ("Intel(R) HD Graphics P630", "Intel(R) Xeon(R) E3-1505M v6",
     "vp9", "P7520 Xeon variant - the workstation bin of the same silicon"),
    ("NVIDIA Quadro M1200", "Intel(R) Core(TM) i7-7820HQ",
     "h264", "P7520 dGPU - 1st-gen Maxwell NVDEC, no HEVC and no VP9"),
    ("NVIDIA Quadro M2200", "Intel(R) Core(TM) i7-7920HQ", "h264", "as above"),
    ("NVIDIA Quadro P2000", "Intel Xeon E3-1505M v6", "vp9", "Pascal: VP9 yes"),
    ("AMD Radeon Pro WX 4150", "Intel(R) Core(TM) i7-7820HQ",
     "hevc", "P7520 dGPU - Polaris workstation"),
    ("Microsoft Basic Display Adapter", "Intel Core i5",
     None, "no driver - must NOT be assigned a tier"),
    ("Some Unknown Adapter", "Weird CPU", None, "must refuse rather than guess"),
]


def load():
    spec = importlib.util.spec_from_file_location("mdp", TOOL)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def main():
    m = load()
    ok = fail = 0
    print("%-38s %-6s %-6s %s" % ("adapter", "want", "got", ""))
    print("-" * 78)
    for gpu, cpu, want, note in CASES:
        hay = m.normalise("%s %s" % (gpu, cpu))
        got = None
        for pat, tier in m.GPU_RULES:
            if re.search(pat, hay):
                got = tier
                break
        good = (got == want)
        ok += good
        fail += (not good)
        print("%-4s %-38s %-6s %-6s %s"
              % ("ok" if good else "FAIL", gpu[:38], want or "-", got or "-",
                 note if not good else ""))
    print("-" * 78)
    print("%d passed, %d failed" % (ok, fail))

    # --- multi-GPU: the machine must take the WEAKEST adapter -------------
    print("")
    print("MULTI-GPU (must take the weakest adapter, not the first)")
    print("-" * 78)
    COMBOS = [
        (["Intel(R) HD Graphics 630", "NVIDIA Quadro M1200"], "h264",
         "Precision 7520: iGPU is vp9-class, Quadro is h264 - floor is h264"),
        (["Intel(R) HD Graphics 630", "AMD Radeon Pro WX 4150"], "hevc",
         "Precision 7520 AMD option - floor is hevc"),
        (["Intel(R) HD Graphics 4000", "AMD Radeon HD 7670M"], "h264",
         "Sony VAIO: both h264"),
        (["Intel(R) HD Graphics 630"], "vp9",
         "7520 with the iGPU only - earns vp9"),
        (["Intel(R) Iris(R) Xe Graphics", "Totally Unknown GPU"], None,
         "an unrecognised adapter must sink the whole machine"),
    ]
    for names, want, note in COMBOS:
        got = m.pick_tier([m.classify(n) for n in names])
        good = (got == want)
        ok += good
        fail += (not good)
        print("%-4s %-46s want=%-5s got=%s"
              % ("ok" if good else "FAIL", " + ".join(names)[:46], want or "-", got or "-"))
        if not good:
            print("       %s" % note)
    print("-" * 78)
    print("TOTAL: %d passed, %d failed" % (ok, fail))
    if fail:
        print("")
        print("A wrong tier is worse than no tier: enabling a codec the GPU cannot")
        print("decode forces SOFTWARE decode, which is what the thermal cap exists")
        print("to avoid. Fix the pattern rather than relaxing the expectation.")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
