# 🤖 How to bundle a WebExtension into Firefox — for the next LLM

**Audience: an AI assistant, or a person, told to "add uBlock Origin to the
browser".** Linux and Windows both covered. Everything here was done for real
and verified in a running browser; the traps are the ones actually hit, in the
order they were hit.

If you only read one thing:

> **Firefox has two built-in add-on locations. One is permanently invisible.
> Almost every obvious route puts you in the invisible one.**

---

## 0. Before you start: is this even the right job?

You want this if:

- the browser blocks add-on installation (as this one does, deliberately), or
- you want an extension present for every user with no setup, or
- you want an extension that cannot be removed by malware or by a third party.

Precedent: **Mullvad Browser ships uBlock Origin this way. Tor Browser ships
NoScript.** This is a normal thing to do, not a hack.

You do **not** need to revert any add-on-blocking patch. A bundled extension
never travels the install path, so the block does not apply to it.

---

## 1. The mechanism, and the trap

`XPIProvider.sys.mjs` defines two locations:

```js
// app-builtin-addons   <- populated from built_in_addons.json
get hidden()   { return true; }     // ALWAYS invisible in about:addons
get isSystem() { return true; }

// app-builtin          <- populated by maybeInstallBuiltinAddon()
get hidden()   { return false; }    // visible, listed, toggleable
get isSystem() { return false; }
```

**The trap:** `toolkit/mozapps/extensions/gen_built_in_addons.py` runs at build
time and globs

```
builtin-addons/*/manifest.json
```

Every match is written into `built_in_addons.json`, which means the *hidden*
location. So if you package your extension under `builtin-addons/` — the
obvious place, right next to Mozilla's own — the build silently routes it to
the invisible location and there is nothing you can do about it from the
extension's side.

The symptom is nasty because it half-works: the extension **loads, runs, gets a
runtime UUID, initialises storage and does its job**, while being absent from
`about:addons`. For an ad blocker that means a user cannot reach its settings,
its filter lists, or its off switch.

**Therefore: package under your own resource root**, not `builtin-addons/`.

### Why it does not trip an add-on-install block

```
maybeInstallBuiltinAddon()
  -> installBuiltinAddon()
       -> loadManifest()
       -> _activateAddon()
```

It never calls `AddonInstall.install()`. And `BuiltInLocation.makeInstaller()`
returns `{ installAddon() {}, uninstallAddon() {} }` — no-ops, not the
directory installer that a lockdown patch typically throws from.

Empirical proof: seven Mozilla built-ins run in this browser with all 14
rejection points intact.

---

## 2. The five pieces

Identical on Linux and Windows — this is all `moz.build` and `jar.mn`, which
are cross-platform.

### 2.1 Unpack the extension into the source tree

```
src/browser/extensions/<name>/          <- contents of the .xpi
```

**Delete `META-INF/`.** A built-in is not signature-checked, and leaving a
stale signature in the tree is only misleading.

### 2.2 `src/browser/extensions/<name>/jar.mn`

```
browser.jar:
%   resource gorilla-addons %gorilla-addons/  contentaccessible=yes
    gorilla-addons/<name>/manifest.json (manifest.json)
    gorilla-addons/<name>/js/ (js/**)
    gorilla-addons/<name>/css/ (css/**)
    ... one line per top-level file, one glob per top-level directory
```

Root files individually; directories with the `(dir/**)` glob. The pattern is
copied from `browser/extensions/pictureinpicture/jar.mn`.

Note the `%` resource line — that is what makes `resource://gorilla-addons/`
resolve. **Use your own root name, not `builtin-addons`,** for the reason in §1.

### 2.3 `src/browser/extensions/<name>/moz.build`

```python
JAR_MANIFESTS += ["jar.mn"]
```

### 2.4 Register the directory

`src/browser/extensions/moz.build`:

```python
DIRS += [
    ...
    "<name>",
]
```

### 2.5 Install it at startup, into the VISIBLE location

A module, e.g. `src/browser/modules/GorillaBuiltinExtensions.sys.mjs`:

```js
await lazy.AddonManager.maybeInstallBuiltinAddon(
  "uBlock0@raymondhill.net",
  "1.74.0",
  "resource://gorilla-addons/ublock-origin/"
);
```

Register it in `src/browser/modules/moz.build` under `EXTRA_JS_MODULES`, and
call it from `BrowserGlue.sys.mjs` in `_onFirstWindowLoaded`.

> ⚠ **`EXTRA_JS_MODULES` is a `StrictOrderingOnAppendList` sorted
> CASE-INSENSITIVELY.** Insert in the wrong place and the build fails with
> `UnsortedError`. This project has hit that before, with
> `AIWindowStub` vs `AboutNewTab`.

---

## 3. The three traps that cost real time

### Trap 1 — the wrong module URL scheme

```js
"moz-src:///browser/modules/GorillaBuiltinExtensions.sys.mjs"   // WRONG
"resource:///modules/GorillaBuiltinExtensions.sys.mjs"          // right
```

`browser/modules/` maps to `resource:///modules/`. Get it wrong and the lazy
getter points at a URL that does not exist; the call throws inside
`_onFirstWindowLoaded`; and because the extension is (correctly) absent from
`built_in_addons.json` there is **no fallback** — it vanishes completely, with
nothing in the log naming the cause.

Check what neighbouring entries in `BrowserGlue.sys.mjs` use. They are right.

### Trap 2 — testing headless

`firefox -headless -screenshot` **does not run `_onFirstWindowLoaded`.** The
registration never fires, the extension is absent, and you conclude your code
is broken when it is fine.

**Always verify with a real window.** This project's playbook already carried a
"headless-only artifact" entry before this happened again.

```bash
firefox -profile /tmp/test -no-remote about:addons     # real window
sleep 25
grep -o '"location":"[^"]*"' /tmp/test/extensions.json
```

You want `app-builtin`. If you see `app-builtin-addons`, you are in the hidden
location — re-read §1.

### Trap 3 — a stale objdir copy

If you first packaged under `builtin-addons/` and then moved, the old copy sits
in the objdir and the generator keeps finding it:

```bash
rm -rf <objdir>/dist/bin/browser/chrome/browser/builtin-addons/<name>
```

---

## 4. Pinning the toolbar button

An extension's button defaults to the puzzle-piece overflow panel. In a browser
where the user cannot install anything, an ad blocker they cannot see is one
they will assume is missing. Pin it:

```js
CustomizableUI.addWidgetToArea(widgetId, CustomizableUI.AREA_NAVBAR);
```

The widget id is the extension id, lowercased, every non-alphanumeric character
replaced with `_`, plus `-browser-action`:

```
uBlock0@raymondhill.net  ->  ublock0_raymondhill_net-browser-action
```

**Pin once only**, recorded in a pref. Re-pinning on every startup means a
browser that argues with a user who deliberately removed the button.

---

## 5. Build, package, verify

### Windows

```bash
python harness/gorilla_build.py build
python harness/gorilla_build.py package
python "working scripts/verify_builtin_extension.py"
```

Then install and check with a **real window**, as in Trap 2.

### Linux

Same source changes; different driver. From the Firefox source tree:

```bash
./mach build
./mach package
```

Verify before packaging the `.deb`:

```bash
ls objdir/dist/bin/browser/chrome/browser/gorilla-addons/
python3 -c "import json;d=json.load(open('objdir/dist/bin/browser/chrome/browser/content/browser/built_in_addons.json'));print([b['addon_id'] for b in d['builtins']])"
```

The second command must **NOT** list your extension. If it does, you packaged
under `builtin-addons/` — see §1.

Then a real-window check:

```bash
./mach run --temp-profile -- about:addons
```

and finally the `.deb`:

```bash
bash scripts/build_deb.sh
```

### What differs between the platforms

| | Linux | Windows |
|---|---|---|
| source changes | identical | identical |
| driver | `./mach build` | `gorilla_build.py build` |
| objdir | in-tree by default | `C:/gfobj` (MAX_PATH headroom) |
| package | `.deb` via `scripts/build_deb.sh` | NSIS installer inside a 7-Zip SFX |
| verify | `./mach run --temp-profile` | install, then launch a real window |

Nothing about the extension mechanism is platform-specific. If it works on one,
the same five pieces work on the other.

---

## 6. Just run the tool

All of the above is automated:

```bash
python "working scripts/add_builtin_extension.py" --amo ublock-origin
python harness/gorilla_build.py build
python harness/gorilla_build.py package
python "working scripts/verify_builtin_extension.py"
```

`--amo <slug>` downloads from the add-ons site; `--xpi <file>` uses a local
file. `--check` reports without writing. `--list` shows what is bundled.

It writes every one of the five pieces, gets the case-insensitive sort right,
uses the correct resource root and the correct module URL, and computes the
widget id.

---

## 7. Licensing — do not skip this

Bundling someone else's extension means **redistributing their code**.

uBlock Origin is **GPLv3**. Firefox is MPL-2.0. Shipping a separate,
unmodified extension alongside an MPL application is *mere aggregation*, which
the GPL explicitly permits — but you must:

1. **ship the licence.** `LICENSE.txt` is inside the `.xpi`; keep it. The tool
   does (it strips only `META-INF/`).
2. **offer the source.** Unmodified upstream plus a link satisfies this.
3. **not modify it** without publishing your changes.

Check the licence of whatever you bundle. Not every extension permits it.

---

## 8. What it costs

| | |
|---|---|
| **No auto-update** | frozen at build time; a new version needs a rebuild |
| **Size** | uBlock Origin adds ~17 MB unpacked, ~7 MB to the installer |
| **Network** | uBO ships 21 filter lists and fetches 53 more; reconcile that with any egress policy |
| **Support burden** | users will report *its* bugs to *you* |

The update one is the real cost. Decide who rebuilds when uBlock Origin ships a
fix, and write it down.
