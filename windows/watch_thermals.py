"""Watch CPU temperature during a build, and stop it before it cooks.

WHY THIS EXISTS
  The harness caps the processor and calibrates a thermal profile, and that
  works - but it is FEED-FORWARD. It picks a clock cap up front from a short
  soak test and then trusts it for the next several hours.

  2026-09-09 showed the limit of that: a 120-second synthetic soak predicted a
  62.9 C peak, and a real 48-minute build reached 74.8 C against a 75.0 C
  target. Chassis heat soak takes tens of minutes, so a short soak measures a
  transient, not equilibrium. The margin on this machine is 0.2 C.

  0.2 C is not a margin. It is a coincidence. This is the feedback half: it
  samples the real temperature while the real build runs, and can halt it.

WHAT IT DOES
  Samples every INTERVAL seconds. Logs to state/thermal_watch.log. If the
  temperature exceeds --limit for --breaches consecutive samples, it acts:

      --on-breach warn   say so and keep going          (default)
      --on-breach pause  SIGSTOP the compilers until it cools, then resume
      --on-breach stop   kill the build

  Consecutive samples, not one: a single spike while a link step starts is not
  a thermal problem, and a watchdog that cries wolf gets turned off.

USAGE
    python "working scripts/watch_thermals.py"
    python "working scripts/watch_thermals.py" --limit 78 --on-breach pause
    python "working scripts/watch_thermals.py" --once
"""
import argparse
import datetime
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(os.environ.get("GORILLA_ROOT")
            or Path(__file__).resolve().parent.parent)

COMPILERS = ("cl", "clang-cl", "clang", "rustc", "lld-link", "link", "cargo")

PS_LOAD = (
    "(Get-CimInstance Win32_Processor | "
    "Measure-Object -Property LoadPercentage -Average).Average"
)


def ps(cmd, timeout=30):
    try:
        r = subprocess.run(["powershell", "-NoProfile", "-Command", cmd],
                           capture_output=True, text=True, timeout=timeout)
        return (r.stdout or "").strip()
    except Exception:
        return ""


# Use the HARNESS's provider, not a hand-rolled WMI query.
#
# 2026-09-13: the first version of this file queried
# MSAcpi_ThermalZoneTemperature directly. harness/lib/thermal.py ranks that
# provider LAST, and its docstring says why: on this hardware it returns a
# CONSTANT 71.05 C, idle or loaded. A watchdog reading a frozen number is worse
# than no watchdog, because it looks like it is working.
#
# thermal.py already probes ThermalZone, LibreHardwareMonitor and MSAcpi in
# that order and picks one that actually varies. Use it.
sys.path.insert(0, str(ROOT / "harness" / "lib"))
try:
    import thermal as _thermal
except Exception:                                   # pragma: no cover
    _thermal = None


def temperature():
    if _thermal is None:
        return None
    try:
        name, fn = _thermal.temp_provider()
        v = fn()
        return float(v) if v is not None else None
    except Exception:
        return None


def core_spread():
    """Hottest-minus-coolest core, when the provider can see individual cores.

    An averaged chassis sensor hides this. Measured 2026-09-13 on the i7-1255U:
    one core at 58 C while the rest sat at 46 - a 12 C spread. The core that
    throttles is the hot one, so the spread is worth seeing.
    """
    try:
        d = _thermal.coretemp_detail() if _thermal else None
    except Exception:
        return ""
    if not d or not d.get("cores"):
        return ""
    v = [c["c"] for c in d["cores"]]
    return "   spread %.0f-%.0f C  TjMax %s" % (min(v), max(v), d.get("tjmax", "?"))


def provider_name():
    try:
        return _thermal.temp_provider()[0] if _thermal else "none"
    except Exception:
        return "none"


def cpu_load():
    v = ps(PS_LOAD)
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return None


def compiler_pids():
    names = ",".join(COMPILERS)
    out = ps("Get-Process -Name %s -ErrorAction SilentlyContinue | "
             "Select-Object -ExpandProperty Id" % names)
    return [int(x) for x in out.split() if x.strip().isdigit()]


def suspend(pids, resume=False):
    """Suspend or resume the compiler processes.

    Pausing is gentler than killing: the build resumes where it stopped
    instead of losing an hour of work to a spike.
    """
    verb = "Resume" if resume else "Suspend"
    for p in pids:
        ps("$h=[System.Diagnostics.Process]::GetProcessById(%d); "
           "Add-Type -Name N -Namespace W -MemberDefinition '"
           "[DllImport(\"ntdll.dll\")] public static extern int Nt%sProcess("
           "IntPtr h);' -ErrorAction SilentlyContinue; "
           "[W.N]::Nt%sProcess($h.Handle)" % (p, verb, verb))


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--limit", type=float, default=78.0,
                    help="degrees C that counts as a breach (default 78)")
    ap.add_argument("--interval", type=int, default=30)
    ap.add_argument("--breaches", type=int, default=3,
                    help="consecutive breaching samples before acting")
    ap.add_argument("--on-breach", choices=("warn", "pause", "stop"),
                    default="warn")
    ap.add_argument("--cool-to", type=float, default=70.0,
                    help="with --on-breach pause, resume below this")
    ap.add_argument("--once", action="store_true", help="sample once and exit")
    ap.add_argument("--root", default=str(ROOT))
    args = ap.parse_args()
    root = Path(args.root)

    t = temperature()
    if t is None:
        print("no temperature source - harness/lib/thermal.py found no provider")
        print("that reports a live value. This machine normally uses ThermalZone.")
        print("DO NOT run a long build unattended without one.")
        return 2

    if args.once:
        print("%.1f C   load %s%%" % (t, cpu_load()))
        return 0

    log = root / "state" / "thermal_watch.log"
    log.parent.mkdir(parents=True, exist_ok=True)
    peak, run, paused, n = t, 0, False, 0

    print("provider: %s   (harness-selected; MSAcpi is static on this box)"
          % provider_name())
    print("watching: limit %.1f C, %d consecutive samples, action=%s"
          % (args.limit, args.breaches, args.on_breach))
    print("log: %s" % log)
    print("Ctrl+C to stop watching (this does not stop the build)")
    print("")
    try:
        while True:
            t = temperature()
            if t is None:
                time.sleep(args.interval)
                continue
            n += 1
            peak = max(peak, t)
            pids = compiler_pids()
            stamp = datetime.datetime.now().strftime("%H:%M:%S")
            line = ("%s  %5.1f C   peak %5.1f   load %3s%%   %d compiler(s)%s%s"
                    % (stamp, t, peak, cpu_load(), len(pids),
                       core_spread(),
                       "   [PAUSED]" if paused else ""))
            print(line)
            with open(log, "a", encoding="utf-8") as fh:
                fh.write(line + "\n")

            if paused:
                if t <= args.cool_to:
                    suspend(pids, resume=True)
                    paused = False
                    print("   cooled to %.1f C - build resumed" % t)
                time.sleep(args.interval)
                continue

            if t >= args.limit:
                run += 1
                print("   over limit (%d/%d)" % (run, args.breaches))
            else:
                run = 0

            if run >= args.breaches:
                print("")
                print("   BREACH: %.1f C for %d consecutive samples"
                      % (t, args.breaches))
                if args.on_breach == "pause" and pids:
                    suspend(pids)
                    paused = True
                    print("   compilers SUSPENDED - will resume below %.1f C"
                          % args.cool_to)
                elif args.on_breach == "stop":
                    for p in pids:
                        ps("Stop-Process -Id %d -Force" % p)
                    print("   build KILLED. Lower the cap "
                          "(gorilla_build.py calibrate --target) and retry.")
                    return 1
                else:
                    print("   (warn only - pass --on-breach pause to act)")
                run = 0
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("")
        print("stopped watching after %d samples. peak %.1f C" % (n, peak))
        return 0


if __name__ == "__main__":
    sys.exit(main())
