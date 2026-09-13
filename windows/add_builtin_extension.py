"""Bundle a WebExtension INTO the browser, as a visible built-in add-on.

WHY THIS EXISTS
  This build blocks every add-on install route on purpose (the "API LOBOTOMY",
  patches/07.TOOLKIT). Users cannot install uBlock Origin, and that is the
  intended policy. But a *sealed* browser can still ship whatever the builder
  puts inside it - the same way Mullvad Browser ships uBlock Origin and Tor
  Browser ships NoScript.

  This tool does that, WITHOUT reverting a single line of the lobotomy.

THE PART THAT IS EASY TO GET WRONG
  Firefox has TWO built-in add-on locations and they behave differently:

    app-builtin-addons   listed in built_in_addons.json
                         XPIProvider.sys.mjs: get hidden() { return true; }
                         -> loads and runs, but is INVISIBLE in about:addons

    app-builtin          installed via maybeInstallBuiltinAddon()
                         XPIProvider.sys.mjs: get hidden() { return false; }
                         -> loads, runs, AND appears in about:addons

  A first attempt used built_in_addons.json. uBlock Origin loaded, was active,
  got a runtime UUID and initialised its storage - and was nowhere to be seen
  in the Add-ons Manager, with no toolbar button. Working and invisible is not
  the same as working, and for a browser that cannot install add-ons it is
  worse: the user has no way to reach its settings, its filter lists, or its
  on/off switch.

  So this tool uses maybeInstallBuiltinAddon(), the visible location.

WHY IT DOES NOT TRIP THE LOBOTOMY
  The blocks live in AddonInstall.install() and in a directory installer's
  installAddon(). maybeInstallBuiltinAddon() reaches neither:

      maybeInstallBuiltinAddon -> installBuiltinAddon -> loadManifest
                                                      -> _activateAddon

  and BuiltInLocation.makeInstaller() returns { installAddon() {} } - a no-op,
  not the throwing one. Verified empirically: seven Mozilla built-ins run in
  this build today with the lobotomy fully intact.

WHAT IT WRITES
    src/browser/extensions/<name>/            the unpacked extension
    src/browser/extensions/<name>/jar.mn      packaging into omni.ja
    src/browser/extensions/<name>/moz.build
    src/browser/extensions/moz.build          +DIRS entry
    src/browser/modules/GorillaBuiltinExtensions.sys.mjs   registration + pin
    src/browser/modules/moz.build             +EXTRA_JS_MODULES entry
    src/browser/components/BrowserGlue.sys.mjs             startup hook

USAGE
    python "working scripts/add_builtin_extension.py" --xpi <file.xpi>
    python "working scripts/add_builtin_extension.py" --amo ublock-origin
    python "working scripts/add_builtin_extension.py" --amo ublock-origin --check
    python "working scripts/add_builtin_extension.py" --list
    python "working scripts/add_builtin_extension.py" --remove ublock-origin

AFTER RUNNING IT
    python harness/gorilla_build.py build
    python harness/gorilla_build.py package
    python "working scripts/verify_builtin_extension.py"
"""
import argparse
import io
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(os.environ.get("GORILLA_ROOT")
            or Path(__file__).resolve().parent.parent)

REG_MODULE = "GorillaBuiltinExtensions.sys.mjs"
# Directories inside an .xpi that must NOT be packaged.
SKIP_TOP = {"META-INF"}


def log(m):
    print(m)


def slugify(addon_id, fallback):
    """A directory name: lowercase, safe characters only."""
    s = re.sub(r"[^a-z0-9]+", "-", (fallback or addon_id).lower()).strip("-")
    return s or "extension"


def widget_id(addon_id):
    """CustomizableUI widget id for a browser_action.

    Firefox lowercases the extension id and replaces every character that is
    not a letter or digit with an underscore, then appends -browser-action.
    Getting this wrong means the pin silently does nothing.
    """
    return re.sub(r"[^a-z0-9_]", "_", addon_id.lower()) + "-browser-action"


def fetch_amo(slug, dest):
    api = "https://addons.mozilla.org/api/v5/addons/addon/%s/" % slug
    with urllib.request.urlopen(api, timeout=60) as r:
        d = json.load(r)
    f = d["current_version"]["file"]
    log("  %s %s  (%d bytes)" % (slug, d["current_version"]["version"], f["size"]))
    urllib.request.urlretrieve(f["url"], dest)
    return d["current_version"]["version"]


def read_manifest(xpi):
    with zipfile.ZipFile(xpi) as z:
        m = json.loads(z.read("manifest.json").decode("utf-8-sig"))
    gecko = (m.get("browser_specific_settings", {}).get("gecko")
             or m.get("applications", {}).get("gecko") or {})
    return {
        "id": gecko.get("id"),
        "version": m.get("version"),
        "name": m.get("name"),
        "mv": m.get("manifest_version"),
        "has_action": bool(m.get("browser_action") or m.get("action")),
    }


def write_jar_mn(dirpath, name):
    """jar.mn packages the extension into omni.ja under builtin-addons/<name>/.

    Root files are listed individually; directories use the (dir/**) glob,
    which is the pattern browser/extensions/pictureinpicture uses.
    """
    roots = sorted(p.name for p in dirpath.iterdir() if p.is_file())
    dirs = sorted(p.name for p in dirpath.iterdir()
                  if p.is_dir() and p.name not in SKIP_TOP)
    lines = [
        "# This Source Code Form is subject to the terms of the Mozilla Public",
        "# License, v. 2.0. If a copy of the MPL was not distributed with this",
        "# file, You can obtain one at http://mozilla.org/MPL/2.0/.",
        "",
        "# Generated by working scripts/add_builtin_extension.py - do not hand-edit.",
        "#",
        "# NOTE THE DIRECTORY. This packages to gorilla-addons/, NOT to",
        "# builtin-addons/, and that is load-bearing.",
        "#",
        "# toolkit/mozapps/extensions/gen_built_in_addons.py globs",
        "#   builtin-addons/*/manifest.json",
        "# and writes every match into built_in_addons.json. Everything in that",
        "# file is loaded into the `app-builtin-addons` location, whose class in",
        "# XPIProvider.sys.mjs hard-codes `get hidden() { return true; }`.",
        "#",
        "# So an extension placed under builtin-addons/ RUNS but can never be",
        "# seen in about:addons and has no toolbar button - which was exactly",
        "# the first attempt, and it is useless for anything a user configures.",
        "# Using our own resource root keeps the generator from claiming it, so",
        "# maybeInstallBuiltinAddon() can put it in the VISIBLE location.",
        "",
        "browser.jar:",
        "%   resource gorilla-addons %gorilla-addons/  contentaccessible=yes",
    ]
    for f in roots:
        if f in ("jar.mn", "moz.build"):
            continue
        lines.append("    gorilla-addons/%s/%s (%s)" % (name, f, f))
    for d in dirs:
        lines.append("    gorilla-addons/%s/%s/ (%s/**)" % (name, d, d))
    (dirpath / "jar.mn").write_text("\n".join(lines) + "\n",
                                    encoding="utf-8", newline="\n")
    return len(roots), len(dirs)


def write_moz_build(dirpath, info):
    (dirpath / "moz.build").write_text(
        "# This Source Code Form is subject to the terms of the Mozilla Public\n"
        "# License, v. 2.0. If a copy of the MPL was not distributed with this\n"
        "# file, You can obtain one at http://mozilla.org/MPL/2.0/.\n"
        "\n"
        "# %s %s - bundled as a built-in add-on.\n"
        "# Generated by working scripts/add_builtin_extension.py.\n"
        "\n"
        'JAR_MANIFESTS += ["jar.mn"]\n' % (info["id"], info["version"]),
        encoding="utf-8", newline="\n")


def add_to_dirs(src, name):
    """Append the extension to browser/extensions/moz.build DIRS."""
    p = src / "browser" / "extensions" / "moz.build"
    s = io.open(p, encoding="utf-8", newline="").read()
    if '"%s"' % name in s:
        return False
    m = re.search(r"DIRS \+= \[\n(.*?)\]", s, re.S)
    if not m:
        raise SystemExit("could not find DIRS in %s" % p)
    block = m.group(1).rstrip()
    new = block + '\n    "%s",\n' % name
    s = s[:m.start(1)] + new + s[m.end(1):]
    io.open(p, "w", encoding="utf-8", newline="\n").write(s)
    return True


def registration_module(entries):
    """The module that installs each extension into the VISIBLE location."""
    rows = ",\n".join(
        '  {\n'
        '    id: "%(id)s",\n'
        '    version: "%(version)s",\n'
        '    resourceURI: "resource://gorilla-addons/%(dir)s/",\n'
        '    widgetId: %(widget)s,\n'
        '  }' % {
            "id": e["id"], "version": e["version"], "dir": e["dir"],
            "widget": ('"%s"' % e["widget"]) if e["widget"] else "null",
        } for e in entries)
    return '''/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

/**
 * Gorilla Unleashed - extensions bundled INTO the browser.
 *
 * GENERATED by working scripts/add_builtin_extension.py. Do not hand-edit;
 * re-run the tool instead.
 *
 * WHY THIS FILE EXISTS
 *   This build blocks every add-on install route on purpose (07.TOOLKIT, the
 *   "API LOBOTOMY"). Nothing can be added from outside. That policy is not
 *   changed here - this registers extensions that ship INSIDE the package,
 *   which is a different thing entirely.
 *
 * WHY maybeInstallBuiltinAddon AND NOT built_in_addons.json
 *   Firefox has two built-in locations. The one driven by built_in_addons.json
 *   is `app-builtin-addons`, whose location object hard-codes
 *   `get hidden() { return true; }` - the add-on loads and runs but never
 *   appears in about:addons and has no toolbar button. That was tried first
 *   and is useless for anything a user needs to configure.
 *
 *   maybeInstallBuiltinAddon() installs into `app-builtin`, whose location
 *   returns `hidden: false`. Visible, manageable, toggleable.
 *
 * WHY IT DOES NOT TRIP THE LOBOTOMY
 *   The blocks are in AddonInstall.install() and a directory installer's
 *   installAddon(). This path reaches neither - BuiltInLocation.makeInstaller()
 *   returns a no-op installer, and installBuiltinAddon() goes straight to
 *   loadManifest() and _activateAddon().
 */

const lazy = {};

ChromeUtils.defineESModuleGetters(lazy, {
  AddonManager: "resource://gre/modules/AddonManager.sys.mjs",
});

/** Extensions bundled into this build. */
const BUNDLED = [
%(rows)s,
];

/**
 * Pin an extension's toolbar button once, the first time it is seen.
 *
 * Only ONCE: after that the user's own choice wins. A browser that re-pins a
 * button the user deliberately removed, on every startup, is a browser that
 * argues with its owner.
 */
const PINNED_PREF = "gorilla.builtinExtensions.pinned";

export const GorillaBuiltinExtensions = {
  async install() {
    for (const ext of BUNDLED) {
      try {
        await lazy.AddonManager.maybeInstallBuiltinAddon(
          ext.id,
          ext.version,
          ext.resourceURI
        );
      } catch (e) {
        console.error(`GorillaBuiltinExtensions: ${ext.id} failed to install`, e);
      }
    }
  },

  /**
   * Put the button on the toolbar rather than leaving it inside the
   * puzzle-piece overflow panel.
   *
   * This matters more here than in stock Firefox. Normal users look for an
   * extension in exactly two places - the toolbar and about:addons - and in a
   * browser where they cannot install anything, an ad blocker they cannot find
   * is an ad blocker they will assume is missing.
   */
  pinToToolbar(window) {
    let already = [];
    try {
      already = Services.prefs.getStringPref(PINNED_PREF, "").split(",").filter(Boolean);
    } catch (e) {}

    const { CustomizableUI } = window;
    if (!CustomizableUI) {
      return;
    }
    let changed = false;
    for (const ext of BUNDLED) {
      if (!ext.widgetId || already.includes(ext.id)) {
        continue;
      }
      try {
        // Only place it if it is not already somewhere the user put it.
        if (!CustomizableUI.getPlacementOfWidget(ext.widgetId)) {
          CustomizableUI.addWidgetToArea(
            ext.widgetId,
            CustomizableUI.AREA_NAVBAR
          );
        }
        already.push(ext.id);
        changed = true;
      } catch (e) {
        console.error(`GorillaBuiltinExtensions: could not pin ${ext.id}`, e);
      }
    }
    if (changed) {
      Services.prefs.setStringPref(PINNED_PREF, already.join(","));
    }
  },
};
''' % {"rows": rows}


def register_module_in_mozbuild(src):
    """Add the module to browser/modules/moz.build.

    EXTRA_JS_MODULES is a StrictOrderingOnAppendList sorted CASE-INSENSITIVELY.
    Inserting in ASCII order fails the build with UnsortedError - this bit the
    project once already with AIWindowStub vs AboutNewTab.
    """
    p = src / "browser" / "modules" / "moz.build"
    s = io.open(p, encoding="utf-8", newline="").read()
    if REG_MODULE in s:
        return False
    m = re.search(r"EXTRA_JS_MODULES \+= \[\n(.*?)\n\]", s, re.S)
    if not m:
        raise SystemExit("could not find EXTRA_JS_MODULES in %s" % p)
    items = [l for l in m.group(1).split("\n") if l.strip()]
    new = '    "%s",' % REG_MODULE
    names = [(re.sub(r'^\s*"|",?$', "", l), l) for l in items]
    out, placed = [], False
    for nm, line in names:
        if not placed and REG_MODULE.lower() < nm.lower():
            out.append(new)
            placed = True
        out.append(line)
    if not placed:
        out.append(new)
    s = s[:m.start(1)] + "\n".join(out) + s[m.end(1):]
    io.open(p, "w", encoding="utf-8", newline="\n").write(s)
    return True


GLUE_MARK = "GorillaBuiltinExtensions"


def hook_browser_glue(src):
    """Call the registration at first-window and pin on idle."""
    p = src / "browser" / "components" / "BrowserGlue.sys.mjs"
    s = io.open(p, encoding="utf-8", newline="").read()
    if GLUE_MARK in s:
        return False

    # lazy getter
    anchor = "ChromeUtils.defineESModuleGetters(lazy, {"
    if anchor not in s:
        raise SystemExit("could not find the lazy getter block in BrowserGlue")
    s = s.replace(
        anchor,
        anchor + "\n  GorillaBuiltinExtensions:\n"
                 # browser/modules/ maps to resource:///modules/, NOT to
                 # moz-src:///browser/modules/. Getting this wrong points the
                 # lazy getter at a URL that does not exist. The failure is
                 # silent in the worst way: install() throws inside
                 # _onFirstWindowLoaded, the extension never registers, and
                 # because it is also (correctly) absent from
                 # built_in_addons.json there is no fallback - the add-on
                 # vanishes completely, with nothing in the log naming why.
                 '    "resource:///modules/GorillaBuiltinExtensions.sys.mjs",',
        1)

    # install at first window, pin on idle
    m = re.search(r"(_onFirstWindowLoaded: function BG__onFirstWindowLoaded\("
                  r"aWindow\) \{\n)", s)
    if not m:
        raise SystemExit("could not find _onFirstWindowLoaded in BrowserGlue")
    ins = (
        "    // Gorilla: extensions bundled into the package. See\n"
        "    // browser/modules/GorillaBuiltinExtensions.sys.mjs for why this\n"
        "    // uses maybeInstallBuiltinAddon rather than built_in_addons.json.\n"
        "    lazy.GorillaBuiltinExtensions.install().then(() => {\n"
        "      lazy.GorillaBuiltinExtensions.pinToToolbar(aWindow);\n"
        "    });\n\n"
    )
    s = s[:m.end(1)] + ins + s[m.end(1):]
    io.open(p, "w", encoding="utf-8", newline="\n").write(s)
    return True


def state_path(root):
    return root / "state" / "builtin_extensions.json"


def load_state(root):
    p = state_path(root)
    if p.is_file():
        return json.loads(p.read_text(encoding="utf-8"))
    return {"extensions": []}


def save_state(root, st):
    p = state_path(root)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(st, indent=2) + "\n", encoding="utf-8", newline="\n")


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=str(ROOT))
    ap.add_argument("--xpi", help="local .xpi to bundle")
    ap.add_argument("--amo", help="AMO slug to download and bundle, e.g. ublock-origin")
    ap.add_argument("--name", help="directory name (default: derived from the slug)")
    ap.add_argument("--no-pin", action="store_true",
                    help="do not place the toolbar button")
    ap.add_argument("--check", action="store_true", help="report, write nothing")
    ap.add_argument("--list", action="store_true", help="what is bundled already")
    ap.add_argument("--remove", help="remove a bundled extension by directory name")
    args = ap.parse_args()

    root = Path(args.root)
    src = root / "src"
    st = load_state(root)

    if args.list:
        if not st["extensions"]:
            print("nothing bundled")
            return 0
        for e in st["extensions"]:
            print("  %-22s %-30s %s" % (e["dir"], e["id"], e["version"]))
        return 0

    if args.remove:
        d = src / "browser" / "extensions" / args.remove
        if d.is_dir():
            shutil.rmtree(d)
            print("removed %s" % d)
        st["extensions"] = [e for e in st["extensions"] if e["dir"] != args.remove]
        save_state(root, st)
        print("NOTE: browser/extensions/moz.build, the registration module and")
        print("      the BrowserGlue hook are NOT reverted automatically -")
        print("      re-run without --remove to regenerate them consistently.")
        return 0

    if not args.xpi and not args.amo:
        ap.error("give --xpi or --amo")

    # --- acquire ---------------------------------------------------------
    tmp = root / "downloads" / "builtin-xpi"
    tmp.mkdir(parents=True, exist_ok=True)
    if args.amo:
        xpi = tmp / ("%s.xpi" % args.amo)
        print("downloading from AMO:")
        fetch_amo(args.amo, xpi)
    else:
        xpi = Path(args.xpi)
        if not xpi.is_file():
            raise SystemExit("no such file: %s" % xpi)

    info = read_manifest(xpi)
    name = args.name or slugify(info["id"], args.amo)
    print("")
    print("  id       : %s" % info["id"])
    print("  version  : %s" % info["version"])
    print("  manifest : v%s" % info["mv"])
    print("  directory: browser/extensions/%s" % name)
    print("  toolbar  : %s" % ("no browser_action" if not info["has_action"]
                               else ("skipped (--no-pin)" if args.no_pin
                                     else widget_id(info["id"]))))
    if not info["id"]:
        raise SystemExit("this extension has no gecko id - cannot bundle it")

    if args.check:
        print("")
        print("check mode - nothing written")
        return 0

    # --- unpack ----------------------------------------------------------
    dest = src / "browser" / "extensions" / name
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    with zipfile.ZipFile(xpi) as z:
        for n in z.namelist():
            top = n.split("/")[0]
            if top in SKIP_TOP:
                continue
            z.extract(n, dest)
    nfiles = sum(1 for _ in dest.rglob("*") if _.is_file())
    print("")
    print("  unpacked %d file(s)  (META-INF signature dir excluded - a built-in"
          % nfiles)
    print("           is not signature-checked, and the stale signature would")
    print("           only be misleading)")

    nroot, ndir = write_jar_mn(dest, name)
    write_moz_build(dest, info)
    print("  jar.mn   : %d root file(s), %d directory glob(s)" % (nroot, ndir))

    if add_to_dirs(src, name):
        print("  registered in browser/extensions/moz.build")

    # --- registration module --------------------------------------------
    st["extensions"] = [e for e in st["extensions"] if e["dir"] != name]
    st["extensions"].append({
        "dir": name, "id": info["id"], "version": info["version"],
        "widget": None if (args.no_pin or not info["has_action"])
                  else widget_id(info["id"]),
    })
    save_state(root, st)

    mod = src / "browser" / "modules" / REG_MODULE
    mod.write_text(registration_module(st["extensions"]),
                   encoding="utf-8", newline="\n")
    print("  wrote browser/modules/%s" % REG_MODULE)
    if register_module_in_mozbuild(src):
        print("  registered in browser/modules/moz.build (case-insensitive order)")
    if hook_browser_glue(src):
        print("  hooked into BrowserGlue._onFirstWindowLoaded")

    print("")
    print("NEXT:")
    print("    python harness/gorilla_build.py build")
    print("    python harness/gorilla_build.py package")
    print("    python \"working scripts/verify_builtin_extension.py\"")
    return 0


if __name__ == "__main__":
    sys.exit(main())
