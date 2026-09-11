"""Watch the browser start on a clean profile and record every host it contacts.

WHY THIS EXISTS
  Preferences say what the code is CONFIGURED to do. A file listing says what
  code is PRESENT. Neither proves that nothing is sent.

  The only honest test of "it does not phone home" is to start it with a brand
  new profile, touch nothing, and watch the socket table.

WHAT IT DOES
  1. Creates a throwaway profile.
  2. Starts the browser on about:blank.
  3. Polls the TCP connection table for that process tree for N seconds.
  4. Resolves each remote address back to a hostname.
  5. Classifies what it found.

HOW TO READ THE RESULT
  A clean run contacts NOTHING, or contacts only hosts you can account for.
  Stock Firefox on a new profile reaches out to a dozen Mozilla endpoints in
  the first minute - telemetry, Normandy, Remote Settings, Contile tiles,
  Pocket, detectportal, safebrowsing. Their absence is the finding.

  Connections are classified, not just listed, because "0 connections" and
  "connections only to the update server" are different claims and both are
  defensible - but only if you say which one you are making.

LIMITS, STATED PLAINLY
  - It observes a startup window, not a browsing session. A ping scheduled for
    24 hours later would not appear.
  - It sees TCP endpoints, not payloads. It proves WHO was contacted, not what
    was said.
  - Windows' connection table is polled, so a very short-lived connection
    between two polls can be missed. Poll interval is deliberately short.
  - DNS-over-HTTPS, if enabled, hides hostnames behind the resolver's IP.

USAGE
    python "working scripts/verify_no_phone_home.py"
    python "working scripts/verify_no_phone_home.py" --seconds 90
    python "working scripts/verify_no_phone_home.py" --visible
"""
import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

# Hosts that mean data collection, if any of them appear.
COLLECTION = [
    ("telemetry", r"telemetry|incoming\.telemetry"),
    ("Normandy / Shield experiments", r"normandy"),
    ("Remote Settings", r"firefox\.settings\.services|remote-settings"),
    ("sponsored tiles (Contile)", r"contile|tiles\.services"),
    ("Pocket / recommendations", r"pocket|getpocket|spocs"),
    ("Merino / Firefox Suggest", r"merino"),
    ("Ads / ad-attribution", r"ads\.mozilla|adm\.|admarketplace"),
    ("crash reporting", r"crash-reports|socorro"),
    ("Glean/FOG", r"glean"),
]
# Hosts that are not collection but are still outbound - worth naming.
BENIGN = [
    ("update check", r"aus\d|update\.mozilla|download\.mozilla"),
    ("captive-portal probe", r"detectportal"),
    ("certificate revocation (OCSP)", r"ocsp|digicert|letsencrypt|amazontrust"),
    ("Safe Browsing", r"safebrowsing|googleapis|google\.com"),
    ("add-on blocklist", r"addons\.mozilla|services\.addons"),
    ("DNS-over-HTTPS", r"mozilla\.cloudflare-dns|dns\.google"),
]


def ps(cmd, timeout=120):
    r = subprocess.run(["powershell", "-NoProfile", "-Command", cmd],
                       capture_output=True, text=True, timeout=timeout)
    return (r.stdout or "").strip()


def find_install():
    lnk = Path(os.environ.get("USERPROFILE", "")) / "Desktop" / "Gorilla Unleashed.lnk"
    if lnk.is_file():
        out = ps("$s=(New-Object -ComObject WScript.Shell).CreateShortcut("
                 + repr(str(lnk)).replace('"', "'") + ");Write-Output $s.TargetPath")
        if out and Path(out).is_file():
            return Path(out).parent
    c = Path(os.environ.get("USERPROFILE", "")) / "Gorilla Unleashed"
    return c if (c / "firefox.exe").is_file() else None


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--install", default=None)
    ap.add_argument("--seconds", type=int, default=60)
    ap.add_argument("--visible", action="store_true",
                    help="run with a real window instead of headless")
    args = ap.parse_args()

    install = Path(args.install) if args.install else find_install()
    if not install:
        print("no installed build found - pass --install <dir>")
        return 2
    exe = install / "firefox.exe"

    prof = Path(tempfile.mkdtemp(prefix="phonehome_"))
    print("install : %s" % install)
    print("profile : %s  (brand new, thrown away afterwards)" % prof)
    print("watching for %d seconds, on about:blank, with no interaction" % args.seconds)
    print("")

    mode = "" if args.visible else "-headless"
    script = (
        "$p = Start-Process -FilePath '%s' -ArgumentList "
        "'-profile','%s','-no-remote','about:blank'%s -PassThru;"
        "$seen = @{};"
        "$deadline = (Get-Date).AddSeconds(%d);"
        "while ((Get-Date) -lt $deadline) {"
        "  $ids = @($p.Id);"
        "  $kids = Get-CimInstance Win32_Process -Filter \"Name='firefox.exe'\" "
        "          | Select-Object -ExpandProperty ProcessId;"
        "  $ids += $kids;"
        "  foreach ($id in ($ids | Select-Object -Unique)) {"
        "    try {"
        "      Get-NetTCPConnection -OwningProcess $id -ErrorAction SilentlyContinue |"
        # The anchor matters. A first version wrote '^(...|127\\.|::1|::)$',
        # and '127\\.' followed by '$' can never match '127.0.0.1' - so
        # Firefox's own localhost IPC sockets sailed through the filter and
        # were then reported as unexplained external endpoints.
        "      Where-Object { $_.RemoteAddress -notmatch "
        "'^(0\\.0\\.0\\.0|127\\.|169\\.254\\.|::1$|::$|fe80:)' } |"
        "      ForEach-Object { $seen[\"$($_.RemoteAddress):$($_.RemotePort)\"] = $true }"
        "    } catch {}"
        "  }"
        "  Start-Sleep -Milliseconds 400"
        "};"
        "Get-Process firefox -ErrorAction SilentlyContinue | Stop-Process -Force;"
        # Reverse DNS is useless for CDN-hosted services: a Fastly or Google
        # Cloud address resolves to nothing, or to a generic cloud PTR, and
        # 'four unidentified IPs' is not good enough to support a privacy
        # claim. The DNS client cache records the names that were actually
        # LOOKED UP, which is what we need.
        "Write-Output '---DNS---';"
        "try { Get-DnsClientCache -ErrorAction SilentlyContinue |"
        "  Select-Object -ExpandProperty Entry -Unique } catch {};"
        "Write-Output '---END---';"
        "$seen.Keys | Sort-Object"
    ) % (str(exe), str(prof), (",'%s'" % mode if mode else ""), args.seconds)

    out = ps(script, timeout=args.seconds + 180)
    dns, endpoints, bucket = [], [], None
    for line in out.splitlines():
        t = line.strip()
        if t == "---DNS---":
            bucket = "dns"
            continue
        if t == "---END---":
            bucket = "ep"
            continue
        if not t:
            continue
        if bucket == "dns":
            dns.append(t.lower())
        elif ":" in t:
            endpoints.append(t)

    # Resolve addresses back to names.
    rows = []
    for ep in endpoints:
        addr, _, port = ep.rpartition(":")
        host = ""
        try:
            import socket
            host = socket.gethostbyaddr(addr)[0]
        except Exception:
            host = ""
        rows.append((addr, port, host))

    print("=" * 74)
    print("OUTBOUND CONNECTIONS DURING STARTUP")
    print("=" * 74)
    if not rows:
        print("  none - the browser contacted nothing at all")
    else:
        for addr, port, host in rows:
            print("  %-40s :%-6s %s" % (addr, port, host or "(no reverse DNS)"))

    # Names resolved during the window, minus the noise every Windows box
    # generates regardless of the browser.
    NOISE = re.compile(r"(_tcp|_udp|\.local$|^wpad|^isatap|in-addr\.arpa|"
                       r"microsoft|windows|msftconnecttest|msedge|bing|"
                       r"office|live\.com|azure|akadns)")
    interesting = sorted(set(d for d in dns if "." in d and not NOISE.search(d)))
    if dns:
        print("")
        print("=" * 74)
        print("HOSTNAMES RESOLVED DURING THE WINDOW")
        print("=" * 74)
        print("  (from the DNS client cache - system-wide, so not every name here")
        print("   is necessarily the browser's. Mozilla-related ones are flagged.)")
        print("")
        for d in interesting:
            moz = "mozilla" in d or "mozaws" in d or "firefox" in d
            print("  %s %s" % ("<-- MOZILLA" if moz else "  ", d) if moz
                  else "    %s" % d)
        if not interesting:
            print("    none beyond routine Windows traffic")

    hay = " ".join(
        ["%s %s" % (h, a) for a, _p, h in rows] + interesting).lower()

    print("")
    print("=" * 74)
    print("DATA COLLECTION ENDPOINTS")
    print("=" * 74)
    found = 0
    for label, pat in COLLECTION:
        hit = re.search(pat, hay)
        print("  %s %-34s %s" % ("!" if hit else "+", label,
                                 "CONTACTED" if hit else "not contacted"))
        found += bool(hit)

    print("")
    print("=" * 74)
    print("OTHER OUTBOUND (not collection, but not nothing)")
    print("=" * 74)
    for label, pat in BENIGN:
        if re.search(pat, hay):
            print("  . %s" % label)
    unexplained = [r for r in rows if not any(
        re.search(p, ("%s %s" % (r[2], r[0])).lower())
        for _l, p in COLLECTION + BENIGN)]
    if unexplained:
        print("  ? %d endpoint(s) not matched by any rule above:" % len(unexplained))
        for a, p, h in unexplained:
            print("      %s:%s %s" % (a, p, h or ""))

    print("")
    print("=" * 74)
    print("VERDICT")
    print("=" * 74)
    if found:
        print("  %d data-collection endpoint(s) were contacted. The claim does NOT"
              % found)
        print("  hold as written.")
    elif not rows:
        print("  Nothing was contacted. On a clean profile, at startup, this build")
        print("  made no outbound connection of any kind.")
    else:
        print("  No data-collection endpoint was contacted. %d other connection(s)"
              % len(rows))
        print("  were made - listed above, so you can judge them yourself.")
    print("")
    print("  Scope: a %ds startup window. Not a browsing session, and payloads" % args.seconds)
    print("  are not inspected - this shows WHO was contacted, not what was said.")

    shutil.rmtree(prof, ignore_errors=True)
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
