# 🔢 RUNBOOK — do exactly this, in this order

**For a small model, a tired human, or anyone who does not want to think.**

Every step is: **one command → what you should see → what to do if it fails.**
There are no judgement calls. If a step does not match, do the recovery and
run the step again.

- Do **not** skip steps.
- Do **not** run steps out of order.
- If a command prints `FAIL` or `BLOCKER`, **stop** and do the recovery.
- Every path below is literal except `%USERPROFILE%`, which Windows expands
  to your own home folder. The project lives in
  `%USERPROFILE%\Documents\Gorilla.firefox`; everything runs from there.

```
cd %USERPROFILE%\Documents\Gorilla.firefox
```

For deeper reasoning behind any check, read `BUILD-PLAYBOOK.md`. You do not
need it to follow this page.

---

# PART A — Build the browser from nothing

Do PART A once. If the browser already builds, skip to PART B.

### A1. Check the machine

```
python harness/gorilla_build.py preflight
```

**Expect:** the last line says `Preflight cleared`.

**If it says a BLOCKER failed:** the failure prints its own `fix :` line
directly underneath. Run that fix. Then run A1 again.

### A2. Download the toolchain

```
python harness/gorilla_build.py deps
```

**Expect:** it finishes without error. It only downloads.

**If it fails:** you have no internet, or a download hash changed. Run again.

### A3. Install the toolchain — NEEDS ADMINISTRATOR

Open a **new** terminal **as Administrator**, then:

```
cd %USERPROFILE%\Documents\Gorilla.firefox
python harness/gorilla_build.py deps --install
```

**Expect:** MozillaBuild and the Visual Studio Build Tools install.

**If it says "not elevated":** you did not open the terminal as Administrator.
Close it and do that.

### A4. Get the Firefox source

```
python harness/gorilla_build.py source
```

**Expect:** a clone finishes and the tree is clean.

**If it fails on long paths:** run A1 — the `long-paths` check prints the two
registry/git commands you need.

### A5. Fetch mach's own tools

```
python harness/gorilla_build.py bootstrap
```

**Expect:** cbindgen, nasm, clang and nsis land in `~/.mozbuild`.

### A6. Measure the safe processor speed — NEEDS ADMINISTRATOR

In the Administrator terminal:

```
python harness/gorilla_build.py calibrate
```

**Expect:** it writes `state/thermal_profile.json`.

**Why:** this keeps the laptop under 75 °C for the whole build. Do not skip it.

### A7. Apply the Gorilla changes

```
python harness/gorilla_build.py patches
```

**Expect:** a count of applied patches, no failures.

### A8. Rebuild the new-tab bundle

```
python harness/gorilla_build.py generated
```

### A9. Compile

```
python harness/gorilla_build.py build
```

**Expect:** `Build succeeded`, and a peak temperature under 75 °C.

**If it refuses to start:** a BLOCKER failed. Read the `fix :` line, do it, run
A9 again. **Do not use `--force`.**

### A10. Make the installer

```
python harness/gorilla_build.py package
```

**Expect:** a line ending `installer.exe` with a size around 91 MB.

### A11. Install it

```
python harness/gorilla_build.py install
```

If that stage does not exist, run the installer directly:

```
"C:\gfobj\dist\firefox-155.0.1.en-US.win64.installer.exe" -ms /InstallDirectoryPath="%LOCALAPPDATA%\Gorilla Unleashed"
```

### A12. Prove the install matches the build

```
python "working scripts/verify_installed_build.py"
```

**Expect:** `OK: the installed build carries every tracked fix.`

**If it FAILs:** the install is older than the build. Redo A10 and A11.

---

# PART B — Add an extension (e.g. uBlock Origin)

The browser cannot install add-ons — that is deliberate. This *bundles* one
inside the browser instead. It does not undo the block.

### B1. Bundle it

```
python "working scripts/add_builtin_extension.py" --amo ublock-origin
```

**Expect:** it prints the id, the version, and then five lines starting
`unpacked`, `jar.mn`, `registered in`, `wrote`, `hooked into`.

**Other extensions:** replace `ublock-origin` with its add-ons-site slug.
For a local file: `--xpi C:\path\to\thing.xpi`.

**Before you do:** check the extension's licence permits redistribution.
uBlock Origin is GPLv3 and does, provided its `LICENSE.txt` ships (the tool
keeps it).

### B2. Compile

```
python harness/gorilla_build.py build
```

**Expect:** `Build succeeded`.

**If it fails with `UnsortedError`:** re-run B1; it sorts the module list
case-insensitively, which is what mozbuild requires.

### B3. Package and install

```
python harness/gorilla_build.py package
"C:\gfobj\dist\firefox-155.0.1.en-US.win64.installer.exe" -ms /InstallDirectoryPath="%LOCALAPPDATA%\Gorilla Unleashed"
```

### B4. Prove it is there AND VISIBLE

```
python "working scripts/verify_builtin_extension.py"
```

**Expect:** three sections all `+`, ending
`OK: every bundled extension is packaged, registered, and VISIBLE.`

**If section 3 says `location=app-builtin-addons`:** it is in the *invisible*
location — it will run but never appear in the Add-ons Manager. Re-run B1 and
rebuild. (Cause and cure: `docs/HOWTO-BUNDLE-AN-EXTENSION.md`.)

**If section 3 says `NOT PRESENT`:** delete the stale copy and rebuild:

```
rmdir /s /q C:\gfobj\dist\bin\browser\chrome\browser\builtin-addons\ublock-origin
python harness/gorilla_build.py build
```

### B5. Look at it with your own eyes

Open the browser. Press **Ctrl+Shift+A**. You should see the extension listed
under **Enabled**, and its icon on the toolbar.

> ⚠ **Do not verify this headless.** `-headless -screenshot` does not run the
> code that registers the extension, so it will look absent when it is fine.
> This has caused a wrong diagnosis twice. Use a real window.

---

# PART C — Every time you change anything

In this order. Never skip C1.

```
python harness/gorilla_build.py preflight        C1  must say "cleared"
python harness/gorilla_build.py build            C2
python harness/gorilla_build.py package          C3
   (install the installer)                       C4
python "working scripts/verify_installed_build.py"    C5
python "working scripts/verify_builtin_extension.py"  C6  (if you bundled one)
```

---

# PART D — Publishing

### D1. Make the fixes survive a rebuild

```
python "working scripts/export_session_fixes.py"
python "working scripts/verify_patches_apply.py"
```

**Expect:** `N applied and matched, 0 failed`.

**Why:** `src/` is generated from upstream + the patch set. Anything you edited
by hand there is lost on the next rebuild unless it is exported.

### D2. Regenerate the playbook

```
python "working scripts/generate_playbook.py"
```

### D3. Check nothing private is going public

```
python "working scripts/audit_privacy_claims.py"
```

Then look through `git diff` yourself for machine names, usernames and paths.

---

# The five rules

1. **Never claim it works until you have watched it work.** A green build says
   the compiler was happy. Nothing more.
2. **Test with a real window.** Headless skips code the user runs.
3. **When a check and your eyes disagree, believe your eyes** and go fix the
   check. Several checks in this project passed while the defect was on screen.
4. **A check is not finished until you have watched it fail.** Break the thing
   on purpose and confirm the check catches it.
5. **Test on a copy before touching a working install.** It cost nothing the
   day it mattered.

---

# If something is wrong and you do not know why

```
python harness/gorilla_build.py status
```

Then find the check id in `BUILD-PLAYBOOK.md`. Every failure this project has
ever hit is written there with its cause and its fix — including the wrong
guesses, which are usually the useful part.
