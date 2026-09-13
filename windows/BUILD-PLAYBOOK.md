# Building Gorilla Firefox on Windows - the playbook

> **This file is generated.** Edit `harness/lib/preflight.py` and re-run
> `python "working scripts/generate_playbook.py"`. Do not hand-edit.

## For whoever picks this up next

Building Firefox on Windows is not hard, but it fails in ways that are hard to
*read*: errors arrive an hour in, name a file you never touched, and say
nothing about the real cause. Every failure below was hit for real, diagnosed,
fixed, and turned into a check that now runs before the build starts.

If a check fails, the fix is printed with it. If you hit a NEW failure: fix it,
then add a `Check` to `harness/lib/preflight.py` with the `why` field naming
the actual incident, and re-run this generator. That `why` is what stops
someone deleting the check later for looking pointless.

## The order that works

```
gorilla preflight          verify the machine (never destructive)
gorilla deps               download the toolchain, hash-pinned
gorilla deps --install     ADMIN: MozillaBuild, VS Build Tools, Defender
gorilla source             clone and pin the exact revision
gorilla bootstrap          mach's own artifacts: cbindgen, nasm, clang, nsis
gorilla calibrate          ADMIN: measure the sustainable thermal cap
gorilla patches            apply the Gorilla patch set
gorilla generated          rebuild the newtab webpack bundle from patched src
gorilla build              compile, capped and logged
gorilla package            produce the installer
```

`status` shows current state. `restore` puts the power scheme back after an
interrupted run - it reads the previous GUID from disk, so it survives a crash.

### One ordering that matters: enabling sccache

`config/mozconfig.win64` ships with `--with-ccache=sccache` COMMENTED OUT, and
the `sccache` check warns about it deliberately. Enabling it changes the
compiler invocation, so mach reconfigures and every existing object is thrown
away.

So: **package a good build first**, then uncomment, then rebuild. That rebuild
is full-length while the cache fills; every one after it is far faster. Flip it
mid-session and you discard whatever has already compiled.

## Three things that cost the most time

**1. Readable is not the same as working.** `MSAcpi_ThermalZoneTemperature`
returned a plausible, constant 71.05 C whether idle or fully loaded. It passed
an "is a temperature available?" check and produced a completely fictitious
calibration. Sources are now proven against load before they are trusted.

**2. Present is not the same as reachable.** clang-cl was installed and
findable from Python, and the build still failed with "Cannot find the target
C compiler" - MozillaBuild's login profile rebuilds PATH from scratch and
discarded the injection. The check now starts the login shell and asks *it*.

**3. Applies cleanly is not the same as correct.** ~958 Fluent attributes were
mangled into multiline values by the patch set. Every one applied without
complaint, and shipped in the Linux build with broken labels and destroyed
keyboard shortcuts.

The pattern: verify the thing you actually depend on, never a proxy for it.

## Thermal policy

The cap is applied BEFORE the build and never changes during it. The build is
not paused when the machine gets warm - reactive duty-cycling does not lower
peak temperature (it triggers *at* the ceiling), it induces thermal cycling,
and it makes wall-clock a function of room temperature.

Measured on the i7-1255U: uncapped with turbo ~96 C; turbo off, 62.9 C
synthetic / 74.8 C on a real 48-minute build. Turbo is what generates the
spike. Note the gap between those last two numbers - chassis heat soak takes
tens of minutes, so a short calibration soak reports a transient. Real build
observations in `state/thermal_profile.json` outrank the synthetic ladder.


## How to diagnose a new failure

Ten failures were worked through to get this building. In nearly every one the
FIRST hypothesis was wrong and plausible, and testing it was what cost the
time. The recurring shape:

**1. Cheap test before expensive fix.** The objdir failure looked like a
parallel-make race. Re-running cost 43 seconds and failed identically -
reproducible means structural, not a race. That 43 seconds ruled out a
two-hour clobber.

**2. When iteration is expensive, hunt the class, not the instance.** At fifty
minutes per build, fixing one split patch cluster and rebuilding would have
been the obvious move and the wrong one. Writing a detector and sweeping all
430 patches showed the problem was isolated - worth knowing before spending
another hour.

**3. Verify the thing you depend on, never a proxy.** This accounts for three
separate failures on its own:

- a temperature sensor that returned a plausible constant
- a compiler that was installed and findable, but not by the build shell
- patches that applied cleanly and were semantically wrong

"Is a value available?" is not a test. "Does it respond to the thing I am
measuring?" is.

**4. If the error looks impossible, you are reading a different string than
the program is.** "No rule to make target <file>" for a file that plainly
exists meant make was stat-ing a 266-character unresolved path while `ls` saw
the 235-character resolved one.

**5. Read the project's own notes first.** The Linux mozconfig already
documented stripping CLAUDECODE before calling mach. That workaround existed;
it had simply not been carried across to Windows.

**6. Suspect the reporting before the build.** A build that fails while
printing nothing useful may be suppressing its own output.

Each entry below carries its full investigation, wrong turns included.


## The failure catalogue

60 checks: 37 blocking, 23 advisory. `build` refuses to start while any blocker fails.


### Blocking

#### `clang-cl` - clang-cl compiler

**What went wrong:** 2026-09-09: build died after 25s with 'Cannot find the target C compiler'. cl.exe and the SDK were both installed - Firefox wants clang-cl, and the VS LLVM components are not on PATH even once present.

**Fix:** Install the VS 'C++ Clang tools for Windows' components, or run gorilla deps --install. The harness adds its bin dir to PATH itself.

<details><summary>How this was diagnosed (including the wrong hypotheses)</summary>

```
SYMPTOM
    ERROR: Cannot find the target C compiler   (25 seconds in)

WRONG HYPOTHESIS #1 - "the compiler is not installed"
    It was. cl.exe was present, vswhere reported Build Tools 17.14, and the
    Windows SDK was there. Chasing "install the compiler" would have wasted
    the whole session.

    What settled it: config.log said `_cc: Looking for clang-cl` - not cl.exe.
    Firefox on Windows builds with clang-cl. cl.exe is irrelevant.

WRONG HYPOTHESIS #2 - "clang-cl is missing, then"
    Also wrong, and this one cost a second failed build. clang-cl WAS present
    at VC/Tools/Llvm/x64/bin. It simply was not on PATH.

    So PATH was injected from Python via env= ... and the build failed
    IDENTICALLY. That is the interesting part: the fix looked right, the check
    passed, and nothing changed.

ACTUAL CAUSE
    MozillaBuild's LOGIN PROFILE rebuilds PATH from scratch. `bash -l` runs
    that profile AFTER inheriting the environment, so anything Python prepends
    is discarded before mach ever runs.

HOW IT WAS PROVEN
    Ran `bash -l -c 'command -v clang-cl'` directly. Empty. Then with an
    export INSIDE the command - found. That distinguishes "not present" from
    "not reachable", which look identical from outside.

LESSON
    Present is not the same as reachable. The check now starts the login shell
    and asks IT, rather than asking Python. Test the thing you depend on.
```

</details>

#### `windows-sdk` - Windows SDK

**What went wrong:** Gecko needs the SDK headers and libs; without them configure fails late.

**Fix:** gorilla deps --install (installs Windows11SDK.22621).

#### `mozillabuild` - MozillaBuild shell

**What went wrong:** mach must run inside MozillaBuild's bash; nothing builds without it.

**Fix:** gorilla deps --install

#### `long-paths` - Long path support

**What went wrong:** 2026-09-08: git clone exited 0 with a THREE-QUARTERS populated tree. testing/web-platform paths run ~270 chars against MAX_PATH of 260. The failure is silent - the clone reports success.

**Fix:** Set LongPathsEnabled=1 in HKLM\SYSTEM\CurrentControlSet\Control\FileSystem AND git config --global core.longpaths true.

#### `autocrlf` - Line endings

**What went wrong:** CRLF breaks Firefox build scripts and makes every patch fuzz.

**Fix:** git -C src config core.autocrlf false, then re-checkout.

#### `source` - Source tree

**What went wrong:** Obvious, but worth failing fast rather than inside mach.

**Fix:** gorilla source

#### `mozconfig` - mozconfig

**What went wrong:** Without it the build silently uses upstream defaults - unbranded, untrimmed.

**Fix:** Restore config/mozconfig.win64.

#### `branding` - Branding directory

**What went wrong:** The mozconfig names a branding dir. If the patches did not land it, configure fails on a path that does not exist.

**Fix:** Run gorilla patches - 08.Look/NEW_FILES supplies browser/branding/gorilla.

#### `mozbuild-toolchain` - mach bootstrap artifacts

**What went wrong:** 2026-09-09: configure died with 'Cannot find cbindgen. Please run mach bootstrap'. cbindgen and nasm come from neither Visual Studio, MozillaBuild nor rustup - only mach bootstrap fetches them into ~/.mozbuild.

**Fix:** gorilla bootstrap

<details><summary>How this was diagnosed (including the wrong hypotheses)</summary>

```
SYMPTOM
    ERROR: Cannot find cbindgen. Please run `mach bootstrap`

    Clear message. The interesting failure was the one that followed it.

WHAT HAPPENED NEXT
    mach bootstrap crashed:

        mozboot/bootstrap.py:554 in _check_for_dev_drive
        file_system_type = file_system_info.strip().split("\n")[2]
        IndexError: list index out of range

    That code runs `Get-Item -Path <src> | Get-Volume | Select-Object
    FileSystem` and takes line [2] unconditionally.

ROOT CAUSE
    Get-Volume returns NOTHING on this machine:
        "No MSFT_Volume objects found with property 'DriveLetter' equal to 'C'"
        MSFT_Volume rows: 0

    The Storage Management provider needs 'defragsvc' and 'vds'. Both are
    Stopped and Disabled here - a deliberate debloat. Win32_LogicalDisk still
    works fine (C: NTFS), which is why nothing else noticed.

THE DECISION
    Re-enabling those services would have fixed it and been wrong: they are
    the user's deliberate configuration, and NEITHER IS NEEDED TO BUILD. The
    dev-drive check is purely cosmetic advice.

    So the bootstrap stage applies a defensive one-line fix to mach, runs, and
    REVERTS it. bootstrap.py ends byte-identical to upstream and nothing
    reaches the regenerated patch set.

LESSON
    When someone else's tool crashes on your machine's configuration, fixing
    the machine is not automatically the right move. Ask whether the thing it
    is probing for even matters.
```

</details>

#### `split-clusters` - No split patch clusters

**What went wrong:** 2026-09-09, FIFTY MINUTES into a build: PDMFactory.h was patched by 16.SNAPSHOT.DELTA (enabled) declaring a constructor, a method and a const member, while PDMFactory.cpp - which implements them - was patched by 01.MEDIA, disabled as Linux-specific. Groups are curated by THEME, not by code dependency, so disabling one can strand another's files.

**Fix:** Revert the enabled file to upstream, or enable its counterpart. See "working scripts/find_split_clusters.py".

<details><summary>How this was diagnosed (including the wrong hypotheses)</summary>

```
SYMPTOM
    PDMFactory.cpp(301,13): out-of-line definition of 'PDMFactory' does not
    match any declaration
    ... must explicitly initialize the const member 'mForWebCodecs'

    Fifty minutes into a build.

WRONG HYPOTHESIS - "our patch to the .cpp is stale"
    Natural reading: the .cpp was patched against an older header. Backwards.

    git diff --stat on both files settled it in one command:
        PDMFactory.cpp   NOT patched by us
        PDMFactory.h     patched, +12 -1

ACTUAL CAUSE
    A three-file cluster split across enabled and disabled groups:

        PDMFactory.cpp    01.MEDIA            DISABLED  implements the API
        PDMFactory.h      16.SNAPSHOT.DELTA   enabled   declares it
        DecoderAgent.cpp  16.SNAPSHOT.DELTA   enabled   calls it

    Patch groups are curated by THEME (media, GPU, prefs), not by code
    dependency. Disabling 01.MEDIA as Linux-specific was correct - it gates
    codecs on VAAPI - but it stranded the header that declares its API.

THE DECISION THAT MATTERED
    At fifty minutes per iteration, fixing this one and rebuilding would have
    been the obvious move and the wrong one. Instead: write a detector, sweep
    all 430 patches for the same shape, THEN rebuild.

    Result: exactly one split pair, plus two same-directory adjacencies (one
    the same cluster, one benign - gfxPlatformGtk.cpp is never compiled on
    Windows). Isolated, not systemic - which was worth knowing before
    committing another hour.

LESSON
    When iteration is expensive, stop fixing instances and go looking for the
    class. See "working scripts/find_split_clusters.py".
```

</details>

#### `branding-icons` - Branding icons valid

**What went wrong:** 2026-09-09, 48 MINUTES into a build: llvm-rc failed on firefox.exe.res and private_browsing.exe.res because pbmode.ico was a 68-byte 1x1 PNG renamed .ico - an unfinished placeholder. Linux never compiles Windows resources, so it had gone unnoticed.

**Fix:** Replace the offending file with a real multi-resolution .ico. Pillow can write one: Image.open(src).save(dst, format='ICO', sizes=[(16,16),...]).

<details><summary>How this was diagnosed (including the wrong hypotheses)</summary>

```
SYMPTOM
    llvm-rc: Error in ICON statement (ID 5):
    Incorrect icon/cursor Reserved field; should be 0.

    48 minutes in, on firefox.exe.res and private_browsing.exe.res. The error
    names neither a file nor the branding.

HOW IT WAS FOUND
    `file` on every .ico in the branding directory. Six were valid
    multi-resolution icons. One was not:

        pbmode.ico   68 bytes   PNG image data, 1 x 1, 8-bit gray+alpha

    A 1x1 PNG renamed .ico. llvm-rc reads the PNG's header bytes as an ICO
    header and reports a bad Reserved field.

WHY IT SURVIVED THIS LONG
    Linux never compiles Windows resources. The placeholder was harmless there
    and had presumably been in the branding for as long as it has existed.

    All three private-browsing assets are the same 68-byte stub
    (PrivateBrowsing_150.png, _70.png, pbmode.ico) - that part of the branding
    was never finished.

FIX
    Generated a valid 6-resolution ICO from the project's own firefox.ico, so
    it stays Gorilla-branded. Still a placeholder: it is the main icon, not
    private-mode art. The two PNGs remain 1x1 stubs - valid PNGs, so they do
    not break the build, but Windows tiles will render blank.

LESSON
    Cross-platform ports surface unfinished work that the origin platform
    never exercised. Check assets, not just code.
```

</details>

#### `bundled-files` - Bundled files exist

**What went wrong:** 2026-09-09: configure aborted with 'File listed in FINAL_TARGET_FILES does not exist: browser/fonts/consola.ttf'. 11.FONT.SYSTEM bundles MS fonts that Debian fetches via get-microsoft-fonts.sh; on Windows they are OS fonts and were never downloaded.

**Fix:** Drop the patch that adds them, or supply the files. On Windows the MS fonts are OS-provided and not redistributable - do not copy them in.

<details><summary>How this was diagnosed (including the wrong hypotheses)</summary>

```
SYMPTOM
    File listed in FINAL_TARGET_FILES does not exist:
    browser/fonts/consola.ttf

TEMPTING FIX - "copy the fonts in from C:\Windows\Fonts"
    They are right there. It would have worked, and it would have been wrong
    twice over:

      1. Consolas, Segoe UI and Yu Gothic are NOT redistributable. Bundling
         them inside a browser is a licensing problem, not a build fix.
      2. They are already present on every Windows machine, so bundling them
         achieves nothing even if it were permitted.

ACTUAL CAUSE
    11.FONT.SYSTEM adds those fonts to the bundle list. On Debian they are
    fetched by that group's own get-microsoft-fonts.sh. On Windows they are OS
    fonts, so the files were never downloaded and the mozbuild reader aborts.

    Upstream's list - TwemojiMozilla.ttf only - is simply correct here.

LESSON
    A build error is not always asking you to supply the missing thing.
    Sometimes it is telling you the patch does not belong on this platform.
```

</details>

#### `objdir-path` - Objdir path length

**What went wrong:** 2026-09-09: objdir inside the source tree gave a 266-char unresolved target path, 6 over MAX_PATH. Build failed with 'No rule to make target ...Unified_cpp_etwork_controller_gn0.obj' for a file that existed - mozmake stats the path with the dot-dot segments still in it. The resolved path was only 235, so the error looked impossible. Long paths do not help.

**Fix:** Set MOZ_OBJDIR in config/mozconfig.win64 to a SHORT absolute path outside the source tree, e.g. C:/gfobj.

<details><summary>How this was diagnosed (including the wrong hypotheses)</summary>

```
SYMPTOM
    No rule to make target '..\..\..\third_party\libwebrtc\...\
    Unified_cpp_etwork_controller_gn0.obj', needed by 'xul.dll'

    The file EXISTED. 26,813 bytes, valid, written during that very build, and
    backend.mk contained a rule for it. `ls` found it without trouble.

WRONG HYPOTHESIS #1 - "truncated filename"
    The object is named Unified_cpp_ETWORK_controller_gn0 - the "n" of
    "network" is missing, which looks like corruption. It is not: mozbuild
    truncates unified-source names by design when the directory is long.
    A red herring, but a convincing one.

WRONG HYPOTHESIS #2 - "parallel-make race"
    Plausible: -j12, and the object's mtime was inside the failing build's
    window, suggesting it appeared after make had looked for it.

    Cost to test: 43 seconds (just re-run). It failed IDENTICALLY at the same
    target. Reproducible means structural, not a race. Cheap test, decisive
    answer - run it before reaching for a two-hour clobber.

ACTUAL CAUSE
    mozmake stats the target path UNRESOLVED - the '..\..\..' stays in the
    string. Measured from toolkit/library/build:

        resolved   235 chars   <- what ls sees, fine
        unresolved 266 chars   <- what make stats, 6 OVER MAX_PATH

    Only this object fails in the entire tree, because
    goog_cc_scream_network_controller appears TWICE in its path.

    Windows long-path support does not help: mozmake does not use the
    extended API for this stat.

FIX
    MOZ_OBJDIR moved out of the source tree to C:/gfobj. Deepest target goes
    266 -> 200 chars, 60 spare.

LESSON
    When an error says a file is missing and the file is plainly there, the
    program is looking at a different string than you are. Measure the string
    the program actually uses.
```

</details>

#### `clobber` - Objdir vs CLOBBER

**What went wrong:** Not yet hit here, but standard Firefox behaviour: some moz.build changes invalidate the build backend and incremental builds cannot reconcile them. Detecting it up front beats a mid-build abort.

**Fix:** Delete the objdir (or ./mach clobber) and rebuild from scratch.

<details><summary>How this was diagnosed (including the wrong hypotheses)</summary>

```
SYMPTOM
    None from a build. This was a FALSE POSITIVE in a check I had just
    written, caught before it ever blocked anything.

WHAT HAPPENED
    A new 'clobber' check compared the CONTENT of the tree's CLOBBER file
    against the objdir's copy and announced "a clobber is required" - while a
    build was compiling perfectly well against that very objdir. The
    contradiction is what exposed it.

CAUSE
    The objdir's CLOBBER is a ZERO-BYTE MARKER that mozbuild touches. It is
    never a copy of the tree's file. Firefox compares MTIMES: a clobber is
    needed when the tree's CLOBBER is newer than the objdir's marker.

    Comparing contents therefore reports "clobber required" for every healthy
    objdir in existence.

WHY THIS IS RECORDED
    It is the same mistake this file keeps warning about - testing a PROXY
    (file contents) rather than the real condition (relative mtime) - made
    while writing the checks meant to prevent exactly that.

    A blocking check that is wrong is worse than no check. It stops good
    builds and teaches people to reach for --force, which then hides the real
    failures too.

LESSON
    Validate a new check against a state you already believe is healthy. If it
    fails there, suspect the check before the system.
```

</details>

#### `capability-guards` - Core capabilities intact

**What went wrong:** The Linux mozconfig records these as COMMENTS: --disable-eme breaks Netflix/Prime/Disney+/Spotify, --disable-webrtc breaks WhatsApp/Meet/Discord calls, --disable-safe-browsing removes phishing protection. A comment does not stop someone adding them while trimming for size, and the damage would not surface until a video call failed. Also enforces that 02.GPU stays enabled - 'GPUs unblocked' is a stated requirement.

**Fix:** Remove the offending --disable-* from the mozconfig, or re-enable 02.GPU.

#### `mozconfig-drift` - No unexplained mozconfig drops

**What went wrong:** The Windows mozconfig was written from memory rather than diffed against the Linux original. sccache and six other options went missing. No behavioural check can catch that - an absent option produces no error - so the guarantee has to be structural: every drop is a written decision.

**Fix:** Run: python "working scripts/diff_mozconfig.py" and either carry each dropped option or document why it is not carried.

#### `package-manifest` - Package manifest resolves

**What went wrong:** 2026-09-09: mach package failed with 'Missing file(s): bin/onnxruntime.dll'. The entry sits behind #ifdef ONNX_RUNTIME, which configure defined because mach bootstrap fetched the toolchain - while the AI/ML excision meant the DLL was never built. Enumerating such cases individually would need a hundred checks; evaluating the manifest covers all of them.

**Fix:** Run: python "working scripts/validate_package_manifest.py" - then either build the missing file or put its manifest entry behind a condition that is false for this configuration.

#### `win-branding-assets` - Windows installer artwork

**What went wrong:** 2026-09-09: the first packaged installer shipped with blank artwork panels. Eight Windows-only assets had come from the Linux branding directory as 68-byte 1x1 PNG placeholders, three of them named .bmp. NSIS bitmap controls cannot decode a PNG and do not complain - the build was green, the package stage reported success, and only opening the installer would have shown it. BLOCKER because the remedy takes two seconds and the alternative is shipping a visibly broken installer.

**Fix:** Run: python "working scripts/generate_windows_branding_assets.py" - it derives them from the real icon artwork at upstream dimensions.

<details><summary>How this was diagnosed (including the wrong hypotheses)</summary>

```
SYMPTOM
    None. That is the point of this entry.

    The build was green, `mach package` reported success, the installer .exe
    was produced at the expected size, and every icon check passed. Nothing
    anywhere said a word.

    The installer would simply have displayed blank white and black panels
    where its header and welcome artwork belong.

HOW IT WAS FOUND
    Not by a failure - by opening the branding directory and noticing that
    several files were 68 bytes:

        wizHeader.bmp            68
        wizWatermark.bmp         68
        VisualElements_150.png   68

    68 bytes is a 1x1 PNG. Eight of the Windows-only assets were 1x1
    placeholders, and three of those were PNG data carrying a .bmp NAME:

        $ xxd -l 8 wizHeader.bmp
        00000000: 8950 4e47 0d0a 1a0a   .PNG....

    NSIS draws these through MUI bitmap controls
    (browser/installer/windows/nsis/installer.nsi:177-188). A bitmap control
    cannot decode a PNG. But NSIS does not validate what it embeds, so there
    is no build error - the bytes go in and the control draws nothing.

WHY THEY WERE LIKE THAT
    The branding directory was lifted wholesale from the Linux build, where
    wizHeader/wizWatermark/VisualElements are never rendered by anything. The
    Linux build had no reason to carry real ones, so it carried stubs. The
    genuine artwork (icon1024/512/256.png, firefox.ico, pbmode.ico) came
    across intact - firefox.ico has real 16/32/48/256 images - so every
    icon-shaped check passed and the gap stayed invisible.

    This is the general shape of a cross-platform branding port: the assets
    the SOURCE platform uses arrive correct, and the ones only the TARGET
    platform uses arrive as whatever the source happened to have.

WHY THE CHECK LOOKS AT MAGIC, NOT EXTENSION
    A check that trusted the .bmp extension would have passed all eight
    files. The extension is exactly what concealed the problem, so it is the
    one thing the check must not believe.

DIMENSIONS
    Taken from browser/branding/nightly, not invented. Note that
    VisualElements_70.png is 142x142 and _150.png is 300x300 - the number in
    the name is the DIP size Windows composites at, and the file is the 2x
    asset. Do not "correct" these to match their names.

    The BMPs must be 24bpp. Some Windows versions render a 32bpp BMP in an
    MUI bitmap control with the alpha misread, which shows as a black box -
    which is why the generator composites RGBA onto a solid background rather
    than saving with alpha.

LESSON
    A green build proves the compiler was satisfied. It proves nothing about
    what the artifact looks like. Anything the build embeds without parsing -
    images, fonts, licence text, manifests - needs its own check, because the
    build will never object.
```

</details>

#### `branding-nsi` - Installer identity

**What went wrong:** 2026-09-09: branding.nsi was still the stock unofficial template, so the installer announced itself as Mozilla Developer Preview from mozilla.org even though every other piece of branding was correct. MOZ_APP_DISPLAYNAME does not reach NSIS - branding.nsi is a separate, independent declaration, and it is the one the user sees first.

**Fix:** Edit branding.nsi: BrandFullName, BrandFullNameInternal, CompanyName, URLInfoAbout, HelpLink, Channel.

<details><summary>How this was diagnosed (including the wrong hypotheses)</summary>

```
SYMPTOM
    The packaged installer identified itself as:

        ProductName : Firefox
        CompanyName : Mozilla

    and its UI would have read "Mozilla Developer Preview" throughout, from
    mozilla.org - despite every other piece of branding being correct. The
    app was "Gorilla Unleashed" everywhere the app itself was concerned.

WRONG HYPOTHESIS - "MOZ_APP_DISPLAYNAME did not take"
    It took. configure.sh sets MOZ_APP_DISPLAYNAME="Gorilla Unleashed" and
    that value was present in the build - application.ini carried
    CodeName=Gorilla Unleashed, and the running browser reported it.

    The mistake was assuming a single source of branding truth. There is not
    one. NSIS reads branding.nsi, a SEPARATE and INDEPENDENT declaration that
    no configure variable feeds. It shipped as the stock unofficial-build
    template:

        !define BrandFullName "Mozilla Developer Preview"
        !define CompanyName   "mozilla.org"

    Nothing overrides it, nothing warns about it, and it is the first thing
    a user ever sees.

THE PART THAT WAS NEARLY MISSED
    The first fix corrected the obvious names - BrandFullName, CompanyName,
    URLInfoAbout, HelpLink, Channel - and the preflight check still failed,
    on five URLs that had not been considered:

        URLStubDownloadX86/AMD64/AArch64  ->  download.mozilla.org
        URLManualDownload, URLSystemRequirements

    Those are the stub installer's DOWNLOAD SOURCES. The stub is not built
    here, so they are inert - but had anyone ever built it, it would have
    downloaded and installed upstream Firefox while wearing this project's
    name. A defined-and-wrong URL is worse than a defined-and-inert one.

    Worth noting: the check caught what the hand edit missed. That is the
    argument for writing the check before believing the fix.

STILL MOZILLA, DELIBERATELY
    CertNameDownload / CertIssuerDownload name the code-signing certificate
    the stub expects. They are meaningless without the stub and are left
    alone rather than replaced with something invented.

LESSON
    Branding is not one setting. On Windows it is at least three independent
    layers - configure.sh (the app), branding.nsi (the installer), and the
    image assets - and getting one right tells you nothing about the others.
```

</details>

#### `sfx-stub-icon` - Installer self-extractor icon

**What went wrong:** 2026-09-09: after branding.nsi, the branding directory and every icon check were correct, the packaged installer STILL showed Firefox's icon and reported ProductName=Firefox, CompanyName=Mozilla, FileVersion=18.05 - which is 7-Zip's version, the giveaway. dist/*.installer.exe is a 7-Zip self-extractor built from a vendored prebuilt stub whose resources no build setting touches. It is the outermost thing a user sees and was the last piece still wearing upstream's identity.

**Fix:** Run: python "working scripts/brand_installer_stub.py" (keeps a .orig backup; --restore undoes it), then repackage.

<details><summary>How this was diagnosed (including the wrong hypotheses)</summary>

```
SYMPTOM
    Everything was rebranded. branding.nsi carried the right names, all eight
    Windows assets were real, firefox.ico held genuine gorilla artwork, and
    preflight was green. The packaged installer still reported:

        ProductName : Firefox
        CompanyName : Mozilla
        FileVersion : 18.05

    and Explorer still drew Mozilla's Firefox installer icon on it.

THE GIVEAWAY
    FileVersion 18.05. There is no Firefox 18.05, and this build is 155.0.1.
    18.05 is 7-ZIP's version. That single field said the file being inspected
    was not the NSIS installer at all.

WHAT IT ACTUALLY IS
    dist/*.installer.exe is a 7-Zip self-extracting archive:

        other-licenses/7zstub/firefox/7zSD.Win32.sfx   (prebuilt, vendored)
          + tagfile
          + app.7z            (which contains the real NSIS setup.exe)

    browser/installer/windows/Makefile.in:11 names the stub. It is a binary
    committed to the tree with Mozilla's icon and 7-Zip's version resource
    already compiled in. Nothing in configure, branding.nsi, or the branding
    directory reaches it - which is precisely why every branding fix in the
    normal places had no effect on it.

WRONG HYPOTHESIS - "patch the finished installer.exe"
    The obvious move, and it would have produced a broken installer.

    Resource editing via BeginUpdateResource/EndUpdateResource rewrites the
    PE and does NOT preserve OVERLAY data - bytes appended after the last
    section. On the finished installer that overlay is app.7z: the entire
    browser. The result would be a well-formed, correctly-iconed executable
    that extracts nothing.

    The stub, before concatenation, has no overlay. It is the only safe place
    to patch, and it must happen BEFORE packaging.

A SECOND WRONG TURN WORTH RECORDING
    The first attempt to inspect icons used EnumResourceNamesW through
    ctypes. It did not fail - it killed the interpreter outright:

        Fatal Python error: _PyThreadState_Attach: non-NULL old thread state

    The replacement parses the PE resource directory by hand. No callbacks,
    no LoadLibrary, and it works on a file that is about to be modified.

AND A THIRD - "firefox.exe has the wrong icon too"
    Icon extraction via .NET ExtractAssociatedIcon showed a blue globe for
    firefox.exe, which looked like a second branding failure. It was not.
    ExtractAssociatedIcon returns the FIRST icon group in the PE, and
    firefox.exe carries several - document, newwindow, newtab, pbmode -
    besides the application icon.

    Byte-matching each image in the branding .ico files against firefox.exe
    showed ALL of them embedded: firefox.ico 4/4, document.ico 4/4,
    pbmode.ico 6/6, newtab.ico 2/2. The binary was correct; the measurement
    was not. Confirm what a tool is actually reporting before believing it
    found a bug.

FIX
    working scripts/brand_installer_stub.py patches the stub's RT_ICON and
    RT_GROUP_ICON from the branding firefox.ico, reusing the stub's existing
    group id - Windows displays the icon group with the LOWEST id, so adding
    a new higher-numbered group would leave the original winning and change
    nothing visible. The original is kept as .orig and --restore undoes it.

    The version resource (ProductName/CompanyName) is left alone for now:
    rewriting VS_VERSIONINFO means synthesising the whole blob, and it is
    much less visible than the icon. It is recorded here so the next session
    knows it is a known remaining gap, not an oversight.

LESSON
    "The installer" is not one artifact. On Windows it is a vendored 7-Zip
    stub wrapping an NSIS installer wrapping the application, and each layer
    has its own independent branding. Getting the inner layers right tells
    you nothing about the outer one - and the outer one is the only layer the
    user sees before double-clicking.
```

</details>

#### `css-dropped-imports` - No dropped upstream @import

**What went wrong:** 2026-09-09: the nav toolbar shipped unstyled. browser-shared.css had the tabs-navbar token stylesheet import REPLACED by the Gorilla theme's import rather than added beside it. CSS raises no error for a stylesheet that is never loaded, so the build, the package and every icon check were green.

**Fix:** Run: python "working scripts/check_dropped_imports.py" and re-add each lost import, KEEPING the patch's own import alongside it.

<details><summary>How this was diagnosed (including the wrong hypotheses)</summary>

```
THE FAMILY THIS BELONGS TO
    The Gorilla patch set was authored against Firefox 154 and applied
    unchanged to 155. Three separate defects came from that single fact, and
    NONE of them failed the build:

      - an upstream @import replaced instead of added   (this entry)
      - a prebuilt React bundle from 154 inside a 155 addon  (prebuilt-drift)
      - a colour theme keyed to 154's design tokens     (see below)

    Read all three together. Individually each looks like bad luck; together
    they are one predictable consequence of a version bump.

SYMPTOM
    The navigation toolbar looked EMPTY. No back, forward or reload, no
    address bar, no menu - just a magnifying glass floating in black.

WRONG HYPOTHESIS #1 - "the toolbar collapsed"
    The obvious reading, and wrong. A diagnostic stylesheet that gave #nav-bar
    a visible background and outlined every child showed EVERY button present
    and correctly laid out. Nothing had collapsed. They were black icons on a
    black toolbar.

    Cost of not testing this first: two rounds of chasing layout and height
    that could not have worked.

WRONG HYPOTHESIS #2 - "the dropped @import caused it"
    While investigating, browser-shared.css turned out to have this:

        -@import url(".../tabbrowser/tabs-navbar.tokens.css");
        +@import url(".../master-redirect.css");

    The theme patch REPLACED an upstream import instead of adding beside it.
    That is a genuine bug and it is what this check now guards. But it was NOT
    the cause of the invisible toolbar - tabs-navbar.tokens.css defines only
    two separator tokens. Restoring it via userChrome.css changed nothing
    visible, which is how it was ruled out.

    Two real bugs in the same file. Finding one is not finishing.

THE ACTUAL CAUSE (recorded here because it has no check of its own)
    master-redirect.css blanket-assigns every --color-gray-NN token to
    #000000 to force black surfaces. Firefox 155 derives FOREGROUNDS from that
    same palette:

        --toolbarbutton-icon-fill: light-dark(var(--color-gray-70),
                                              var(--color-gray-05));

    So blacking the greys for backgrounds blacked the icons. On 154 that
    palette did not feed the toolbar, which is why the theme worked there.

WHY THE FIX IS `color`/`fill` AND NOT TOKENS
    Setting --toolbarbutton-icon-fill on :root was tried and did not work.
    Chasing token names is what caused the bug in the first place. `color` and
    `fill` are stable CSS and are what the token resolves to anyway
    (currentColor).

    The descendant selector is load-bearing: the inner .toolbarbutton-icon
    elements carry their own fill, so a rule on the button alone never reaches
    them. Confirmed by screenshotting both forms.

HOW ANY OF THIS WAS SEEN AT ALL
    `firefox -headless -screenshot` captures the CONTENT area only - it can
    never show a toolbar. The whole defect is invisible to it. working
    scripts/capture_chrome.py launches the real GUI and captures the desktop,
    and applies a candidate userChrome.css so a fix is tested in seconds
    instead of a rebuild-repackage-reinstall cycle.

LESSON
    A version bump does not announce itself. When a patch set written for
    release N is applied to release N+1, look for the places where N+1 reuses
    something N did not - a palette, a token, a bundle format. Nothing will
    error; things will just quietly stop being right.
```

</details>

#### `prebuilt-drift` - Prebuilt bundles match upstream

**What went wrong:** 2026-09-09: the new tab page showed 'Oops, something went wrong loading this content.' activity-stream.bundle.js - the COMPILED newtab app, shipped prebuilt - had been replaced with a stripped 154-era build (847 KB vs 1.23 MB) inside a 155.2.0 addon. It is copied verbatim into omni.ja and never parsed by the build, so nothing could have caught it but running the browser.

**Fix:** Restore from the pinned tag: git checkout <tag> -- <path>. Achieve the same intent through prefs, which is where it already lives.

<details><summary>How this was diagnosed (including the wrong hypotheses)</summary>

```
SYMPTOM
    The new tab page rendered:

        Oops, something went wrong loading this content.
        Refresh Gorilla page to try again.

    That string is newtab-error-fallback-info in newtab.ftl - the React error
    boundary. So the page LOADED and its JavaScript threw.

WRONG HYPOTHESIS #1 - "resource://newtab is not registered"
    A headless run produced a real, specific error:

        AboutNewTabRedirector.sys.mjs, line 550: NS_ERROR_NOT_AVAILABLE
        [nsIIOService.newChannelFromURIWithLoadInfo]

    which says the channel for resource://newtab/prerendered/
    activity-stream.html could not be opened. That sent the investigation into
    built_in_addons.json, the omni.ja contents and the addon registry - all of
    which turned out to be perfectly correct.

    It was a HEADLESS-ONLY artifact: the built-in addon had not finished
    initialising before the screenshot gave up. The GUI, where the user
    actually saw the failure, got past it - the error boundary proves the HTML
    loaded. Chasing an error from a different environment than the report.

WRONG HYPOTHESIS #2 - "AboutNewTabRedirector.sys.mjs is a Gorilla file"
    It has an unusual name and upstream has AboutNewTab.sys.mjs, so it looked
    like a local addition. `git log` on the file showed the release commit and
    no local diff. Checking took ten seconds and saved reading 600 lines of
    somebody else's module.

ACTUAL CAUSE
    browser/extensions/newtab/data/content/activity-stream.bundle.js is the
    COMPILED newtab React application, shipped prebuilt in the tree. The
    Gorilla patch had replaced it with a stripped 154-era build:

        ours      847 KB      TopSites references: 20
        upstream 1226 KB      TopSites references: 110

    inside an addon whose manifest says 155.2.0. The bundle and its host
    disagreed, it threw, and the boundary caught it.

    Nothing in the build could have noticed. The file is copied verbatim into
    omni.ja - never parsed, compiled, linted or type-checked. The ONLY way to
    find it is to run the browser and look at the page.

FIX, AND WHY IT COSTS NOTHING
    Restored from the pinned tag. The stripping existed to remove top sites,
    sponsored content and Pocket - and every one of those is ALREADY disabled
    by locked prefs in firefox.js:

        browser.newtabpage.activity-stream.feeds.topsites        false, locked
        browser.newtabpage.activity-stream.showSponsored         false, locked
        browser.newtabpage.activity-stream.feeds.section.topstories false, locked

    The patched bundle bought nothing the prefs did not already deliver, and
    cost a broken new tab page.

LESSON
    Treat a committed build product as a version-locked dependency, not as
    source. If the intent can be expressed in configuration - and here it
    already was, twice over - express it there. Prefs survive a version bump;
    a forked compiled bundle does not.
```

</details>

#### `lazy-getters` - Lazy imports resolve

**What went wrong:** 2026-09-09: the address bar accepted typing but Enter did nothing. Two urlbar providers used lazy.UrlbarShared after the excision deleted their getter; `get type()` is read at provider REGISTRATION, so the urlbar's provider set never came up. `lazy.Foo` on a missing getter is plain undefined - no import error, no build error, no lint error.

**Fix:** Run: python "working scripts/check_lazy_getters.py" and restore the getter in each module it names (or remove the remaining uses).

<details><summary>How this was diagnosed (including the wrong hypotheses)</summary>

```
SYMPTOM
    The address bar accepted typing - the text appeared, correctly styled -
    and pressing Enter did nothing at all. No navigation, no error visible to
    the user, no crash.

    "It renders" had already been mistaken for "it works" twice in this
    project, which is why the address bar was tested by actually typing into
    it (Ctrl+L, SendKeys, screenshot before and after Enter) rather than by
    looking at it.

CAUSE
    UrlbarProviderQuickSuggest.sys.mjs:32

        get type() { return lazy.UrlbarShared.PROVIDER_TYPE.NETWORK; }

    with no UrlbarShared entry in the file's defineESModuleGetters(lazy, ...)
    block. The Gorilla patch had stripped QuickSuggest and removed the getter
    while leaving four uses behind. `get type()` is read when a provider is
    REGISTERED, so the throw happened during urlbar startup and took the
    provider set with it - hence a urlbar that accepts text and has nothing to
    navigate to.

    UrlbarProviderSearchSuggestions.sys.mjs had the identical defect, five
    uses, and had not yet been noticed.

WHY NOTHING CAUGHT IT
    `lazy.Foo` where Foo has no getter is not an error. It is `undefined`.
    There is no import failure, no build failure, no lint failure; the module
    loads perfectly and fails later, at the exact line, at runtime.

    This is the quietest member of the excision family:

        bare global   -> ReferenceError            (AIWindow)
        lazy.Foo      -> undefined, then TypeError (UrlbarShared)
        selector list -> SyntaxError at click time (navigator-toolbox)

WRITING THE CHECK WAS ITS OWN LESSON
    The first version knew only defineESModuleGetters and flagged 60 modules,
    almost all of them untouched upstream files using a different but valid
    shape (defineLazyServiceGetters, XPCOMUtils.declareLazy, the singular
    getters, direct assignment). A check that noisy is worse than no check:
    it teaches people to ignore it, and then someone deletes it.

    After teaching it every shape, and matching braces instead of using a lazy
    regex, the count fell 60 -> 9. Of those 9, exactly the 3 files WE had
    modified were real; the other 6 were upstream platform-conditional
    declarations. `git diff --stat <tag> -- <file>` was what separated them,
    and that filter is worth remembering: our regressions are in our diff.

    One of the 9 was a false positive of a familiar kind - a JSDoc line
    mentioning `lazy.lazy.UrlbarShared`. That is the SECOND time a checker in
    this harness counted a comment as code; check_dropped_imports.py did the
    same with a quoted @import. Strip comments before scanning. Always.

LESSON
    When a feature is stripped, the deletions are the easy part. Grep for what
    remains, and prefer a checker that states the invariant over a promise to
    be careful.
```

</details>

#### `closest-selectors` - closest() selector lists

**What went wrong:** 2026-09-09: the excision deleted the last two entries of two selector lists in navigator-toolbox.js and left the comma. Element.closest threw SyntaxError at CLICK time, so the error named a line far from the cause and the toolbar's click handlers were dead.

**Fix:** Remove the trailing comma left where selectors were deleted.

<details><summary>How this was diagnosed (including the wrong hypotheses)</summary>

```
SYMPTOM
    JavaScript error: chrome://browser/content/navigator-toolbox.js,
    line 200: SyntaxError: Element.closest: '

    The message is truncated mid-quote, which is itself the clue: the selector
    string it is complaining about ends where it should not.

CAUSE
    The AI excision deleted the last two entries from two closest() selector
    lists and left the preceding comma:

            #split-view-button,
            `);

    A trailing comma is invalid selector syntax. closest() throws.

WHY IT WAS HARD TO SEE
    The throw happens where the handler RUNS, not where it is written, so the
    error names an onClick body far from anything the excision touched. And
    the visible symptom was "the toolbar buttons do nothing", which reads as a
    CSS or layout problem, not a syntax error.

    A stray space in `#reload-button ,` a few lines up was the tell that
    something had been mechanically edited there.

ALSO IN THAT FILE
    The same excision removed the AIWindowUI ESModule getter but left two
    `case "smartwindow-group-tabs-button":` blocks calling
    AIWindowUI.toggleGroupTabsPanel(). Those cases were unreachable - their
    selectors had just been deleted - but an unreachable reference to a
    binding that no longer exists is a landmine for the next person to edit
    the file, so they were removed too.

LESSON
    Deleting the last item from a list is the dangerous one. In CSS selector
    lists, argument lists and array literals, removing the tail leaves a
    separator behind. Whenever a patch deletes list entries, check the
    boundary.
```

</details>

#### `excised-globals` - Excised modules not referenced

**What went wrong:** 2026-09-09: browser-places.js - unmodified upstream - called AIWindow after the excision removed the module and its getters. The ReferenceError landed in _isNewTabURI(), so every new tab opened blank. A stub was chosen over editing upstream callers because a missed call site stays invisible until someone walks that path.

**Fix:** Keep browser/modules/AIWindowStub.sys.mjs and the AIWindow getters in browser.js and SessionStore.sys.mjs, or remove every remaining caller.

<details><summary>How this was diagnosed (including the wrong hypotheses)</summary>

```
SYMPTOM
    Two things at once, which is why they were not connected at first:

      - JavaScript error: browser-places.js, line 1562:
        ReferenceError: AIWindow is not defined
      - every new tab opened blank

    They are the same bug. Line 1562 sits inside _isNewTabURI(), which
    answers "is this the new tab page?". It threw before it could answer.

CAUSE
    The AI Window was excised: browser/components/aiwindow has no moz.build
    and is commented out of browser/components/moz.build, so nothing in it is
    built. The excision also deleted the ChromeUtils.defineESModuleGetters
    entries that exposed `AIWindow` in browser.js and SessionStore.sys.mjs.

    But it did not remove every CALLER, and the callers are UNMODIFIED
    UPSTREAM FILES:

        browser/base/content/browser-places.js                3 calls
        browser/components/sessionstore/SessionStore.sys.mjs  2 calls

WRONG HYPOTHESIS - "AboutNewTabRedirector.sys.mjs is a Gorilla file"
    A headless run produced a confident, specific error:

        AboutNewTabRedirector.sys.mjs:550: NS_ERROR_NOT_AVAILABLE
        [nsIIOService.newChannelFromURIWithLoadInfo]

    and the module has an unusual name, so it looked local. `git log` on the
    file showed the release commit and no local diff - ten seconds that saved
    reading 600 lines. The error itself was a HEADLESS-ONLY artifact: the
    built-in addon had not finished initialising before the screenshot gave
    up. Chasing an error from a different environment than the report.

FIX: A STUB, NOT EDITS TO THE CALLERS
    browser/modules/AIWindowStub.sys.mjs answers false to every predicate, and
    the two getters point at it. Four members, five call sites.

    Editing the upstream callers was the alternative and was rejected: it adds
    permanent local diff to files that change every release, and a missed call
    site stays invisible until someone walks that path - which is precisely
    how this shipped. A stub makes every call site safe at once, including the
    ones nobody has exercised.

A MOZBUILD TRAP ON THE WAY
    Registering the stub failed the build:

        UnsortedError: We expected "AboutNewTab.sys.mjs" but got
                       "AIWindowStub.sys.mjs"

    EXTRA_JS_MODULES is a StrictOrderingOnAppendList and mozbuild sorts it
    CASE-INSENSITIVELY. "AIWindowStub" sorts BEFORE "AboutNewTab" in ASCII
    (uppercase I < lowercase b) and AFTER it case-insensitively. Insert by the
    case-insensitive order.

LESSON
    An excision has three parts: delete the code, delete the references, and
    prove there are none left. The third is the one that gets skipped, and it
    is the only one a machine can do for you.
```

</details>

#### `l10n-resources` - Localization resources resolve

**What went wrong:** 2026-09-09: the app menu rendered with no labels at all and the menu bar was empty. browser.xhtml requests preview/genai.ftl; the genai excision had deleted it from browser/locales/jar.mn. One unresolvable resource stops the window's whole Fluent bundle, so every data-l10n-id came back empty. Four rounds of CSS work were spent on it before the cause was found - the tell was that the JS-generated '100%' zoom row rendered fine, meaning the labels were ABSENT, not invisible.

**Fix:** Run: python "working scripts/check_l10n_resources.py". Restore the jar.mn mapping, or ship an EMPTY .ftl at that path if the feature behind it was excised on purpose.

<details><summary>How this was diagnosed (including the wrong hypotheses)</summary>

```
SYMPTOM
    Every localized label in the browser chrome was empty. The app menu was a
    panel with no items, the menu bar had no text, and the console filled with

        <key id="key_newNavigatorTab" data-l10n-id="tab-new-shortcut">
        is missing "key" and "keycode" attributes

    one per keyboard shortcut, because those attributes come from Fluent too.

CAUSE
    ONE unresolvable localization resource. browser.xhtml declares 45 of them;
    the genai excision deleted preview/genai.ftl from browser/locales/jar.mn
    along with the file it mapped. browser.xhtml is unmodified upstream and
    still asks for it.

    Fluent does not degrade gracefully here: one missing resource in the
    document's list stops the whole bundle, and every data-l10n-id in that
    document returns empty.

WHY CHECKING THE FTL FILES FOUND NOTHING
    Both the source and the packaged appmenu.ftl were verified complete - 176
    message ids, 95 .label attributes, byte-identical to upstream.
    browserSets.ftl had tab-new-shortcut with its .key intact, in the source
    AND in omni.ja.

    Every file that shipped was perfect. The problem was the one that did not
    ship, and no amount of inspecting the others could reveal it. The check
    therefore compares the REQUESTED list against the STAGED list, rather than
    validating content.

FIX
    An empty browser/locales-preview/genai.ftl plus the jar.mn mapping. An
    empty file is the right answer when the feature behind the resource was
    excised on purpose: the resource resolves, nothing comes back.

    Deleting the <link> from browser.xhtml would also work, but that is an
    upstream file which changes every release - a local diff there is a
    permanent merge cost, and the empty stub is not.

LESSON
    An excision must account for what still REFERENCES the thing removed, and
    references are not only code. Manifests, jar.mn entries, localization
    resource lists and package manifests all point at files, and every one of
    them fails silently.
```

</details>

#### `icon-artwork` - Branding icons depict the brand

**What went wrong:** 2026-09-09: the desktop shortcut showed a BLUE GLOBE. Every .ico in the branding directory was Mozilla's unofficial-branding placeholder, while the real gorilla art sat beside them as PNGs - the same trap as the 1x1 wizHeader.bmp, because Linux never renders a .ico. The existing 'Branding icons valid' check passed all 7: it validated STRUCTURE and never asked what they depicted.

**Fix:** Run: python "working scripts/generate_branding_icons.py" (regenerates them from the PNG artwork; keeps the originals as .ico.unofficial). Then re-run brand_installer_stub.py and delete objdir/browser/app/*.res.

<details><summary>How this was diagnosed (including the wrong hypotheses)</summary>

```
SYMPTOM
    The desktop shortcut showed a BLUE GLOBE instead of the gorilla. So did
    the Start Menu entry and the taskbar.

WRONG HYPOTHESIS - "the shell is showing a stale cached icon"
    Plausible, and wrong. Dumping the PE resource directory of firefox.exe
    showed 15 icon groups, and group 1 - the lowest-numbered, which is the one
    Explorer displays - genuinely was a blue globe. Groups 1100-1107 were
    Mozilla's official Firefox logos. There was no gorilla anywhere in the
    binary.

A WORSE WRONG TURN, EARLIER THE SAME DAY
    Hours before, .NET's ExtractAssociatedIcon had returned a blue globe for
    firefox.exe. It was dismissed as a measurement artifact, on the strength
    of a "verification" that byte-matched a 512-byte slice of each branding
    .ico against the exe and found every one present.

    The slice was not distinctive. It matched the blue-globe data that really
    was in there. The conclusion "all gorilla icons are embedded" was false,
    and it silenced a correct signal for hours.

    A test that can pass for the wrong reason is worse than no test.

ACTUAL CAUSE
    The build was innocent. Every .ico in browser/branding/gorilla WAS a blue
    globe - Mozilla's unofficial-branding placeholder set, the icons you get
    when building without official branding:

        firefox.ico  firefox64.ico  document.ico
        pbmode.ico   newtab.ico     newwindow.ico

    while the real gorilla artwork sat beside them as icon1024.png,
    icon512.png, icon256.png and default128.png, all correct.

    Identical in kind to the 68-byte wizHeader.bmp: the branding directory
    came from a Linux build, Linux renders the PNGs and never opens a .ico,
    so the Windows-only files were whatever happened to be lying there.

WHY THE EXISTING CHECK PASSED THEM
    "Branding icons valid - 7 .ico file(s) valid". Every file was a valid,
    well-formed, multi-size ICO. The check validated STRUCTURE. Nothing asked
    what the icons DEPICTED.

    Whenever a check reports a count of "valid" things, ask what property it
    actually tested.

AND THE FIX'S OWN FALSE PASS
    The first version of the new check compared a binarised GRAYSCALE
    signature and passed firefox.ico - the one file that mattered. A blue
    sphere and a gorilla inside a circular badge are both centred round blobs;
    in grayscale they are nearly the same picture. Switching to mean RGB over
    an 8x8 grid separates them cleanly: placeholders score 60-111 against the
    artwork, correct icons score under 1.

THEN THE REBUILD SHIPPED THE OLD ICON ANYWAY
    make does not track the branding .ico as a dependency of
    browser/app/splash.rc, so browser/app/firefox.exe.res was never
    recompiled. The build was green and the binary was unchanged.

    Detected by counting: the new firefox.ico has five images, the rebuilt
    firefox.exe still reported four. Deleting the stale .res files fixed it.
    That is now its own WARN check.

LESSON
    Three checks in a row passed this: structural icon validation, a byte
    match with a bad probe, and a grayscale fingerprint. Each tested something
    ADJACENT to the property that mattered. When a check and your eyes
    disagree, believe your eyes and go fix the check.
```

</details>

#### `dtls-cap` - WebRTC DTLS capped at 1.2

**What went wrong:** Meta's WhatsApp relays complete a DTLS 1.3 handshake and then discard every application-data record. Measured 2026-08-26: 223 SCTP INIT writes, zero replies, no error anywhere - the call just rings. Two Windows installers shipped with 772 because the value lived only in a comment in a document that was never committed, so a correct build from a correct clone was still broken.

**Fix:** Add pref("media.peerconnection.dtls.version.max", 771) to browser/app/profile/firefox.js - it loads after all.js and wins. Put it in BOTH patches/05.PREFS/ and patches/17.WINDOWS.FIXES.../ browser_app_profile_firefox.js.patch: they are separate full copies, not a base and a delta.

#### `prefs-last-wins` - Hardening is not overridden later

**What went wrong:** 2026-09-13: nine prefs the patch set hardened in all.js shipped with the opposite value because upstream firefox.js redefines them later and the last definition wins. Among them: captive-portal polling of detectportal.firefox.com, Google Safe Browsing for malware and phishing, Firefox Accounts, and two sponsored-content settings - in a browser whose release notes say telemetry and sponsored content are removed. Nothing failed, nothing logged, and the privacy audit had already passed. It was noticed because the account icon was visible in a screenshot.

**Fix:** Move the affected prefs into the Gorilla block at the END of browser/app/profile/firefox.js, where they win, and mark them locked where the value must not be changeable. Hardening all.js alone is not enough - firefox.js loads after it.

#### `local-only` - Repository stays local-only

**What went wrong:** 2026-09-13: this tree was put under version control as a safety net, not as a publication channel. It carries thermal calibration measured on one specific laptop, an artifact ledger of local absolute paths, and an unreviewed history. .git/hooks/ is not itself tracked by git, so the pre-push guard vanishes on any re-init or clone - a guard that silently disappears is worse than none, because it is still believed in. An accidental publication cannot be un-published.

**Fix:** Remove the remote: git remote remove <name>. To publish, copy what you mean to share into gorilla-patchset/ and push that - it is the curated, reviewed subset. If the pre-push hook went missing this check reinstalls it from harness/hooks/ automatically.

#### `builtin-extensions` - Bundled extensions are visible

**What went wrong:** 2026-09-13: uBlock Origin was bundled under builtin-addons/, which gen_built_in_addons.py globs into built_in_addons.json - the app-builtin-addons location, whose class hard-codes hidden() -> true. It loaded, ran, downloaded 181,551 filters and blocked ads with a toolbar badge, while being completely absent from about:addons. An ad blocker with no reachable settings or off switch. Nothing logged it.

**Fix:** Run: python "working scripts/add_builtin_extension.py" --amo <slug> to regenerate the packaging correctly, then rebuild. Full verification (including a real-window check) is verify_builtin_extension.py. The mechanism and its traps are in docs/HOWTO-BUNDLE-AN-EXTENSION.md.

<details><summary>How this was diagnosed (including the wrong hypotheses)</summary>

```
THE QUESTION THAT STARTED IT
    "Can we build in uBlock Origin? Is it doable without reverting all the
    patches?"

    Yes - and it took three wrong turns to get there.

THE SETTING
    This build blocks every add-on install route on purpose (07.TOOLKIT, the
    API LOBOTOMY, 14 rejection points). But a sealed browser can still ship
    what the BUILDER puts inside it - Mullvad Browser ships uBlock Origin this
    way, Tor Browser ships NoScript. It needs NO change to the lobotomy:

        maybeInstallBuiltinAddon -> installBuiltinAddon -> loadManifest
                                                        -> _activateAddon

    never reaches AddonInstall.install(), and BuiltInLocation.makeInstaller()
    returns no-ops rather than the throwing installer. The proof was already on
    screen - seven Mozilla built-ins run here with all 14 blocks intact.

WRONG TURN 1 - THE HIDDEN LOCATION
    The obvious route is built_in_addons.json, and it "works" in the worst
    sense. uBlock Origin loaded, was active, got a runtime UUID, downloaded
    181,551 network and 43,792 cosmetic filters, and blocked ads on YouTube
    with a badge on its toolbar button.

    It did not appear in about:addons. At all.

        app-builtin          hidden() -> false   listed, toggleable
        app-builtin-addons   hidden() -> true    invisible, permanently

    built_in_addons.json feeds the second, and `hidden` is a property of the
    LOCATION - there is no per-addon override. Worse, the routing is
    automatic: gen_built_in_addons.py globs builtin-addons/*/manifest.json at
    build time, so packaging beside Mozilla's own built-ins forces the
    invisible location.

    Fix: package under a different resource root (gorilla-addons/) so the
    generator never claims it, then register with maybeInstallBuiltinAddon().

    For an ad blocker, "runs but has no settings page, no filter-list controls
    and no off switch" is not partial success. The working toolbar button is
    exactly what made it look finished.

WRONG TURN 2 - THE FIX MADE IT VANISH
    Moving to the visible route correctly removed it from built_in_addons.json
    - and the extension then disappeared completely.

        "moz-src:///browser/modules/GorillaBuiltinExtensions.sys.mjs"  wrong
        "resource:///modules/GorillaBuiltinExtensions.sys.mjs"         right

    browser/modules/ maps to resource:///modules/. The lazy getter pointed at
    a URL that does not exist, install() threw inside _onFirstWindowLoaded,
    and with built_in_addons.json no longer listing it there was NO FALLBACK.
    Nothing in the log named the cause. Every neighbouring entry in
    BrowserGlue.sys.mjs uses the correct form.

    What prevented damage: the risk was predicted before acting, so the test
    ran against a COPY of the install. The working browser was never broken.

WRONG TURN 3 - THE TEST WAS WRONG, NOT THE CODE
    After the URL fix it was STILL absent, which suggested something deeper.
    There was nothing deeper.

    `firefox -headless -screenshot` does not run BrowserGlue's
    _onFirstWindowLoaded, so the registration never fires. With a real window
    it worked first try.

    This file already carried a headless-only-artifact entry, from the
    AboutNewTabRedirector red herring. Hit again, same way, same project.
    Headless is a convenience for whoever is testing; it is not the
    environment the user runs.

LESSON
    Three failures at three different layers: a location whose visibility is
    fixed by its class, a URL scheme that fails silently with no fallback, and
    a test harness that does not execute the code path under test.

    The common thread is the one this file keeps repeating - something looked
    like success while being wrong. A working ad blocker with no entry in the
    Add-ons Manager is the purest example yet, because every visible signal
    said finished.
```

</details>

#### `linux-prefs-guarded` - No Linux-only pref fires on Windows

**What went wrong:** 2026-09-11: the patchset set layers.gpu-process.enabled and media.gpu-process-decoder to false unconditionally. That is a correct Wayland workaround and a Windows regression - upstream StaticPrefList.yaml sets both TRUE on XP_WIN, because on Windows the GPU process IS the hardware decode path. The build asked for hardware decode and disabled the process that performs it. Nothing failed at build time; the only symptom was video decoding on the CPU.

**Fix:** Run: python "working scripts/guard_linux_prefs.py" - it wraps each one in #ifndef XP_WIN. Then rebuild and repackage; these files are baked into omni.ja.

<details><summary>How this was diagnosed (including the wrong hypotheses)</summary>

```
THE QUESTION THAT EXPOSED THIS
    "How many of those tweaks and improvements from Linux are transferable on
    a Windows machine?"

    The question was about the profile user.js. The answer to THAT was clean:
    11 prefs, of which 3 already ship baked into the build and 8 name Linux
    subsystems - 0 need to transfer.

    But counting them meant enumerating what the build already bakes in, and
    that enumeration turned up the real problem. The Linux prefs were not
    confined to user.js at all. Ten of them were compiled into the shipping
    Windows build.

WHAT WAS WRONG
    The Gorilla pref injection lands in two files that ship on every platform:

        modules/libpref/init/all.js
        browser/app/profile/firefox.js

    Six of the ten were merely inert on Windows - VA-API, dmabuf, fontconfig,
    X11-EGL name subsystems that do not exist there. Four were not:

        layers.gpu-process.enabled              false
        layers.gpu-process.force-enabled        false
        media.gpu-process-decoder               false
        media.gpu-process-decoder.force-enabled false

    On Linux/Wayland that is correct and deliberate: the GPU-process compositor
    widget carries no wl_egl_window, EGL surface creation fails, and the window
    renders black. VA-API decodes in the RDD process instead.

    On Windows the GPU process IS the hardware path. Disabling it moves
    compositing into the parent process, drops graphics-stack crash isolation,
    and turns off Media Foundation hardware video decode - while
    media.hardware-video-decoding.enabled was still true. The build requested
    hardware decode and disabled the process that performs it.

WHY THIS IS NOT A JUDGEMENT CALL
    Upstream gates the very same prefs by platform:

        - name: layers.gpu-process.enabled
        #if defined(XP_WIN) || defined(MOZ_WIDGET_ANDROID) || defined(XP_MACOSX)
          value: true
        #elif defined(MOZ_X11)
          value: false

        - name: media.gpu-process-decoder
        #if defined(XP_WIN)
          value: true
        #else
          value: false

    Mozilla chose true for Windows on purpose. The patchset overrode it
    unconditionally, so on Windows it inverted a deliberate upstream default.
    Checking what upstream does - rather than reasoning about what the pref
    ought to be - is what turned an opinion into a finding.

THE FIX
    guard_linux_prefs.py wraps each line in #ifndef XP_WIN. Both pref files are
    preprocessed and already carry 170+ such directives, so this is the
    mechanism they are built for. Guarding rather than deleting keeps ONE
    patchset serving both platforms.

    Verified in the build output, not in the source: after rebuilding, all ten
    were gone from dist/bin/greprefs.js and
    dist/bin/browser/defaults/preferences/firefox.js, while all 277 other
    Gorilla prefs survived. Then verified again inside the packaged installer.

HOW IT HID FOR SO LONG
    Nothing failed. The build succeeded, the browser launched, every preflight
    check passed, and the UI was correct. A pref that disables hardware decode
    produces no error - only heat, on laptops running under a hard 75 C cap.

    This is the same shape as the AI-excision defects: JavaScript has no link
    step, and a pref file has no type checker. The failure mode of a data file
    is silence.

LESSON
    A cross-platform patchset authored on one platform will carry that
    platform's assumptions into every other one, and pref files are where they
    hide - because they are data, and data does not fail to compile.

    When overriding an upstream default, read what upstream actually does
    first. StaticPrefList.yaml said, in the file, that this pref is
    platform-dependent.
```

</details>

#### `base-tools` - git/rustc/cargo/node/python

**What went wrong:** Gecko's build needs all of them.

**Fix:** Install whatever is missing.

#### `disk` - Disk space

**What went wrong:** Running out mid-link wastes the whole build.

**Fix:** Free space on C: - objdir alone runs tens of GB.

#### `thermal-profile` - Thermal profile

**What went wrong:** 2026-09-09: a profile measured against a STATIC sensor claimed 71.1 C at every cap. Building on that would have run the machine at ~96 C while believing it was capped. A missing or INVALID profile must stop the build.

**Fix:** gorilla calibrate

#### `build-graph` - Build graph consistency

**What went wrong:** 2026-09-09: the AI excision deleted third_party/llama.cpp's sources but left toolkit/components/ml/backends/llama compiling against them. That fails about an hour in, with an error pointing nowhere near the cause.

**Fix:** Run: python "working scripts/check_deleted_file_refs.py" and fix what it lists.

#### `fluent-attrs` - Fluent attributes intact

**What went wrong:** ~958 attributes in the patch set were mangled into multiline values, destroying labels and access keys. They apply CLEANLY, so the build succeeds and the UI is silently broken - it shipped that way on Linux.

**Fix:** Run: python "working scripts/repair_fluent_attrs.py" --apply

<details><summary>How this was diagnosed (including the wrong hypotheses)</summary>

```
SYMPTOM
    None at build time. These patches apply CLEANLY. The build succeeds.

WHAT SURFACED IT
    While rebasing, a reject showed a transformation that looked wrong:

        .label = Check for updates        ->    .label =
        .accesskey = C                              Check for updates
                                                    .accesskey = C

    In Fluent the second form is not two attributes. '.accesskey = C' becomes
    literal text inside the label value. The button renders
    "Check for updates .accesskey = C" and loses its keyboard shortcut.

HOW IT WAS PROVEN
    git show HEAD:<file> to get pristine upstream, diffed against the patched
    tree. Unambiguous - upstream had two attributes, the patched tree had one
    mangled value.

    Then counted: ~958 occurrences across 84 files.

THE PART THAT MATTERS
    Most of these hunks APPLIED CLEANLY, which is why nobody caught it. It is
    not a rebase artifact - it shipped in the Linux .deb. Every affected menu
    label and access key is broken in the browser people are using today.

    Cause looks like an automated reflow pass that rewrote 'attr = value' into
    'attr =' + indented value and swallowed the following attribute line.

FIX
    working scripts/repair_fluent_attrs.py - classifies before repairing:
    BREAKING (958, repaired), COSMETIC (21, left), LEGITIMATE (91 PLATFORM()
    selectors, never touched). A blind regex would have destroyed the last
    group.

LESSON
    "Applies cleanly" is a statement about patch context matching, not about
    correctness. A patch set can be internally consistent and still wrong.
```

</details>


### Advisory

#### `staged-options` - Staged mozconfig options

**What went wrong:** Options held back pending a single rebuild. Batching avoids paying for several full rebuilds; this check exists so they are not forgotten.

**Fix:** Uncomment them and rebuild once. They are batched because each changes configure flags and invalidates the objdir.

#### `sccache` - Compilation cache

**What went wrong:** The Linux mozconfig had it; the Windows one did not. Eight consecutive builds recompiled from scratch with sccache.exe sitting unused in ~/.mozbuild. Nothing failed - it was simply hours slower than necessary.

**Fix:** Add 'ac_add_options --with-ccache=sccache' to config/mozconfig.win64. NOTE: changing it triggers a reconfigure, so the next build is a full rebuild while the cache populates - do it after packaging a good build.

<details><summary>How this was diagnosed (including the wrong hypotheses)</summary>

```
SYMPTOM
    None. Nothing failed. Every build simply took as long as a clean build,
    forever, and nobody noticed because that is what a Firefox build feels
    like anyway.

    Found only because the user asked "you ARE using ccache, aren't you?".

WHAT WAS WRONG
    The Linux gorilla mozconfig carries:

        # SECTION 4 - COMPILATION CACHE: SCCACHE
        ac_add_options --with-ccache=sccache

    That line was not carried across when mozconfig.win64 was written. The
    evidence had been visible in config.log the whole time:

        checking for ccache...
        not found

    And sccache.exe was present at ~/.mozbuild/sccache/, fetched by mach
    bootstrap, entirely unused. Eight consecutive builds - most of them failed
    ones that were re-run minutes later - recompiled everything from scratch.

WHY IT WENT UNNOTICED
    Absence of an optimisation produces no error. The build is CORRECT without
    it; it is only slow, and "Firefox takes an hour" is unremarkable enough
    that nothing looks wrong.

    Contrast every other entry in this file: those announced themselves with a
    failure. This one could have persisted indefinitely.

THE ORDERING TRAP
    Enabling it is not free. --with-ccache changes the compiler invocation, so
    mach reconfigures and invalidates every existing object. Turning it on
    mid-session throws away whatever has been built.

    Correct sequence: finish the build, PACKAGE it, then enable and accept one
    full rebuild while the cache populates.

LESSON
    Checks catch things that fail. They do not catch things that are merely
    absent. When porting a configuration, diff it against the original rather
    than rewriting from memory - and treat a missing optimisation as a defect,
    not a preference.
```

</details>

#### `app-identity` - application.ini identity

**What went wrong:** 2026-09-09: dist/bin/application.ini read Vendor=Mozilla, Name=Firefox with CodeName=Gorilla Unleashed. MOZ_APP_DISPLAYNAME sets only CodeName; Vendor and Name have their own variables. WARN because it cannot be fixed at package time - and because MOZ_APP_BASENAME also selects the profile directory and registry keys, so changing it after release orphans profiles.

**Fix:** Set MOZ_APP_VENDOR and MOZ_APP_BASENAME in the branding configure.sh. This needs a RECONFIGURE, so batch it with the next build rather than paying for a full rebuild on its own.

<details><summary>How this was diagnosed (including the wrong hypotheses)</summary>

```
SYMPTOM
    dist/bin/application.ini, after a fully successful branded build:

        Vendor=Mozilla
        Name=Firefox
        RemotingName=firefox-default
        CodeName=Gorilla Unleashed

    Three out of four fields still Mozilla's.

WHY
    MOZ_APP_DISPLAYNAME - the only identity variable the branding
    configure.sh sets - populates CodeName and the user-visible display
    name. It does NOT set Vendor or Name. Those come from MOZ_APP_VENDOR and
    MOZ_APP_BASENAME, which default to Mozilla and Firefox respectively and
    have to be set explicitly.

WHY THIS IS A WARN AND NOT A BLOCKER
    Two reasons, and the second is the important one.

    1. It cannot be fixed at package time. These are configure variables, so
       correcting them forces a reconfigure and therefore a full rebuild -
       roughly ninety minutes on this machine. Blocking a package on it would
       mean blocking on something the packaging step cannot do.

    2. MOZ_APP_BASENAME also selects the profile directory
       (%APPDATA%/<vendor>/<name>) and the registry keys. Changing it after
       anyone has installed the browser ORPHANS their profile - bookmarks,
       history, passwords all still on disk, and the new build looking in a
       different place. So it is a decision to make deliberately and early,
       not a box to tick because a checker is red.

LESSON
    Batch reconfigure-requiring changes. This one belongs with sccache, LTO
    and the optimisation flags in a single rebuild, not four separate ones.
```

</details>

#### `stale-objdir` - No abandoned objdir

**What went wrong:** 2026-09-09: MOZ_OBJDIR was moved to C:/gfobj for MAX_PATH headroom, and src/obj-x86_64-pc-windows-msvc was left behind. The package stage derived the objdir from the lock file rather than the mozconfig, found that stale tree, passed its is_dir() guard, and recorded old binaries - with sha256 hashes - as the artifacts of a build whose real 122 MB zip and 81 MB installer it never saw. WARN, not BLOCKER: the directory harms nothing by existing. It is the guessing that harms, and the guess is now fixed.

**Fix:** Delete it: it is not used by anything. The build reads MOZ_OBJDIR from config/mozconfig.win64 and ignores whatever else is on disk.

<details><summary>How this was diagnosed (including the wrong hypotheses)</summary>

```
SYMPTOM
    The package stage reported success and listed its artifacts:

        dist/bin/firefox.exe               1.4 MB  96aa66d04df496dc...
        dist/bin/nmhproxy.exe              0.6 MB  b0f63744fb66301b...
        ... five more, all under 1 MB

    Everything about that looks fine until you ask the obvious question: where
    is the 122 MB zip, and where is the 81 MB installer that mach had just
    said it created? The list is sorted by size descending, so if they existed
    they would be at the top.

    They existed. They were on disk with fresh timestamps. This stage simply
    could not see them.

CAUSE
    The stage resolved the objdir as:

        objdir = src / lock["build"]["objdir"]
              -> src/obj-x86_64-pc-windows-msvc

    which is where Firefox puts an objdir by DEFAULT, and not where this build
    puts it. config/mozconfig.win64 sets MOZ_OBJDIR=C:/gfobj, moved there to
    keep paths clear of MAX_PATH.

WHY IT SURVIVED
    Two independent guards should have caught it, and neither did:

      - `if not objdir.is_dir(): halt()` passed, because the old objdir was
        still sitting there from before the move.
      - The glob found .exe files, so the "no artifacts" warning never fired.

    A wrong path that happens to exist and happens to contain plausible files
    defeats both an existence check and an emptiness check. Only comparing
    against what mach ACTUALLY produced exposes it.

WHY IT MATTERS MORE THAN IT LOOKS
    state/artifacts.json exists so that a rebuild of a pinned revision can be
    verified against a previous one. It was being filled with sha256 hashes of
    stale binaries from an abandoned tree. Hashes of the wrong files are worse
    than no hashes at all - they make a false verification look rigorous.

FIX
    Two parts, and both are needed:

      1. The stage now reads MOZ_OBJDIR from the mozconfig, the same source
         the build reads, and logs which objdir it resolved.
      2. A check warns whenever an abandoned obj-* directory exists beside the
         source tree, because that is the thing that turned a wrong guess into
         a silent wrong answer.

LESSON
    Never derive a path a tool already knows. mach reads MOZ_OBJDIR; anything
    that needs the objdir must read the same variable rather than reconstruct
    it from a default. The default is right often enough to hide the bug and
    wrong exactly when it costs the most.
```

</details>

#### `realtime-off` - Defender real-time protection

**What went wrong:** 2026-09-09: real-time protection was disabled by hand for the first build because the exclusions were incomplete - the objdir had moved to C:/gfobj and was never added, so Defender was still scanning 4.4 GB of build output. The exclusions were then fixed, but protection stayed off, and nothing would ever have mentioned it again. Turning it off is remembered; turning it back on is not.

**Fix:** python harness/gorilla_build.py defender --enable-realtime  (elevated, via UAC). The build-path exclusions stay in place, so builds are not slowed by turning it back on.

#### `icon-resource-fresh` - Compiled icon resource is current

**What went wrong:** 2026-09-09: after fixing the branding icons, a rebuild shipped the OLD icon anyway. make does not track the .ico as a dependency of splash.rc, so the compiled .res was never regenerated - silently, with a green build. Caught only by counting icon images in the PE (5 expected, 4 present).

**Fix:** Delete <objdir>/browser/app/firefox.exe.res (and desktop-launcher/pbproxy ones) and rebuild.

#### `logo-provenance` - Internal-pages logo is crisp

**What went wrong:** 2026-09-09: the new tab gorilla is blurry, and the same fault is recorded on Linux. Two compounding causes: about-logo.svg embeds an 800px raster painted into a 600px box (1.33x headroom, needs 2x), and the raster scores 6.62 edge energy against the doctrine's 26.10 for a true downsample of the canonical master. Every PNG in this branding directory carries the same ~45 edge energy when normalised to 128px, so icon1024.png is an upscale and there is no sharper source in this tree.

**Fix:** Obtain canonical_about_logo.png (2598x2626) from the Linux build, Lanczos-downsample it to at least 2x the CSS box, base64-embed it in about-logo.svg, and set the svg intrinsic to match.

<details><summary>How this was diagnosed (including the wrong hypotheses)</summary>

```
SYMPTOM
    The gorilla on the new tab page is blurry. Reported as happening on Linux
    too, which is the clue that it is an ASSET problem and not a Windows one.

THE DOCTRINE THIS COMES FROM
    An external handoff document, crisp-icon-kit/CRISP_ICON_DOCTRINE.md, wrote
    up everything learned on the Linux build between 2026-05-29 and
    2026-08-27. Its one rule: NEVER CSS-UPSCALE A RASTER. Its most valuable
    section: blur is a PROVENANCE problem, not a size problem - an asset can
    carry the right dimensions, pass every size check, and still be soft
    because its pixels never came from the master.

MEASURED ON THIS TREE
    newtab CSS box      600x600   activity-stream.css:19301
    raster in svg       800x800
    headroom            1.33x     gate ASSET-002 wants 2x
    edge energy         6.62      doctrine records 26.10 for a true
                                  downsample of the canonical master

    6.62 is not an approximation of the doctrine's number - it is the SAME
    number the Linux build measured before its fix. This tree carries the
    identical pre-fix asset.

THE SECOND-ORDER TRAP, which is the reusable lesson
    Running the provenance gate here produced:

        shipped raster                     6.62
        "true downsample" of our master     6.64     ratio 1.00 -> PASS

    A perfect pass, and worthless. The reference was built from icon1024.png,
    and icon1024.png is itself soft. Normalise every branding PNG to 128px and
    they all score ~45.2:

        default128 45.24   icon256 45.35   icon512 45.18   icon1024 44.89

    Identical detail at every size means the big files add no information:
    icon1024 is an upscale. The gate was comparing a soft asset against an
    equally soft reference.

    A check whose REFERENCE is unverified can only confirm your assumptions.
    The checker now reports UNVERIFIABLE rather than PASS when the master
    cannot be shown to out-resolve the asset it is validating.

    This is the third time today a check passed for the wrong reason - the
    others were structural .ico validation and a byte-match with a
    non-distinctive probe. All three tested something ADJACENT to the property
    that mattered.

WHAT IS BLOCKED, AND ON WHAT
    Both causes need one input this machine does not have: the canonical
    master, canonical_about_logo.png, 2598x2626, about 8 MB, on the Linux box.
    With it: Lanczos-downsample to 1200px, base64-embed, set the svg intrinsic
    to 1200, keep the 600px box. That restores 2:1 headroom and real detail.

    Without it, the only lever is shrinking the CSS box to 400px for 2:1
    headroom - sharper, but a smaller logo, which is the opposite of what was
    asked for. Recorded as the trade-off, not applied.

WHAT WAS FIXED WITHOUT IT
    The Windows shell icons, which are a separate asset chain and were a
    separate bug. See "icon-artwork".
```

</details>

#### `png-sharpness` - Branding PNGs match the master

**What went wrong:** 2026-09-09: every derived asset was soft because the PNG ladder it came from was soft. icon1024.png scored 5.31 edge energy against the canonical master's 22.83 at the same size - it was an upscale. The canonical 2598x2626 master was in the repo the whole time, in a directory named 1024x1024.

**Fix:** Run, in this order: regen_branding_pngs.py, then generate_branding_icons.py --force, generate_windows_branding_assets.py --force, brand_installer_stub.py, then delete <objdir>/browser/app/*.res and rebuild. See doctrine/ICON-DOCTRINE-WINDOWS.md section 7.

<details><summary>How this was diagnosed (including the wrong hypotheses)</summary>

```
THE FULL ICON STORY. Read doctrine/ICON-DOCTRINE-WINDOWS.md for the complete
version; this is the diagnostic trail.

SYMPTOM, in two parts that looked unrelated
    - the desktop shortcut showed a blue globe, then after that was fixed,
      showed a correct but small and blurry gorilla
    - the gorilla on the new tab page was blurry, and had been on Linux too

CAUSE, in three layers
    1. The branding .ico files were Mozilla's UNOFFICIAL-BRANDING placeholders
       (a blue globe). Real gorilla artwork sat beside them as PNGs. Linux
       never opens a .ico, so the Windows-only slots held whatever was there.
    2. The .ico ladder had no 96px frame. Explorer draws desktop icons at 96
       in "Large icons", so the shell upscaled the 64px one. That is what
       "too small and too blurry" is.
    3. The PNGs themselves were soft. icon1024.png scored 5.31 edge energy
       against 22.83 for the canonical master at the same size. Every derived
       asset inherited that ceiling.

WHERE THE MASTER WAS
    In the repo the whole time:

        gorilla-patchset/deb_template/usr/share/icons/hicolor/1024x1024/
            apps/gorilla-unleashed.png        2598x2626, 8 MB

    It is in a directory named "1024x1024" and is 2598px. The folder name
    lies. It was found by matching the path shape referenced in the Linux
    release pipeline's own gate, after concluding - wrongly - that no such
    master existed on this machine and asking for it to be fetched.

    Look in the repo before asking for a file.

FOUR CHECKS PASSED WHILE THE ARTWORK WAS WRONG
    This is the reusable part.

    1. Structural .ico validation: "7 .ico file(s) valid". Every file WAS a
       valid multi-size ICO. It tested structure, never content.
    2. A byte-match "verification" comparing a 512-byte slice of each branding
       icon against firefox.exe. The slice was not distinctive; it matched the
       blue-globe data that really was there. This one was worse than useless:
       it was used to DISMISS a correct signal from ExtractAssociatedIcon.
    3. A grayscale icon fingerprint, which gave a false PASS on firefox.ico -
       a blue sphere and a gorilla in a circular badge are both centred round
       blobs. Colour separates them; structure does not.
    4. The provenance gate itself, which passed at ratio 1.00 by comparing a
       soft asset against an equally soft reference.

    Every one tested something ADJACENT to the property that mattered.

AND TWO OF MY OWN MEASUREMENTS WERE WRONG IN OPPOSITE DIRECTIONS
    - "all branding PNGs have identical detail" was concluded from a 128px
      probe, which cannot distinguish sharp from soft. The conclusion was
      right; the evidence did not support it.
    - the same 128px probe, reused as the vacuity guard, then FALSE-ALARMED on
      a genuinely correct 1200px asset (48.03 vs the master's 48.11).

    Measure at the size where the difference lives.

THE GUARD THAT NOW EXISTS
    check_logo_provenance.py reports UNVERIFIABLE, not PASS, when the master
    cannot be shown to carry real detail at the asset's size. It establishes
    that with a self-control: degrade the master to a quarter and back, and
    require the metric to separate them by >1.25x.

        canonical master   19.94 intact vs 6.83 degraded   2.92x  usable
        icon1024.png       flat                            0.95x  refuses

    Controlled independently: destroying a known-good image that way drops the
    metric to 0.43, so a flat reading means soft input, not a blind metric.

RESULTS
    about-logo.svg   800px / 6.62   ->  1200px / 19.94, 2.00x headroom
    icon1024.png     5.31           ->  22.83 (equals the master)
    shipped app icon 29.2           ->  37.23 (ceiling 37.25)
    .ico frames      5, no 96px     ->  10, every one a real downsample

LESSON
    A gate is only as good as its reference. When a check and your eyes
    disagree, believe your eyes and go fix the check.
```

</details>

#### `shortcuts-objdir` - Shortcuts point at the install

**What went wrong:** 2026-09-13: the Private Browsing Start Menu entry pointed at C:/gfobj/dist/bin/private_browsing.exe. It worked, because the objdir happened to exist - so it launched a DIFFERENT browser from the installed one, and would have broken silently at the next clobber. The NSIS installer uses $INSTDIR correctly; the entry was created by Firefox itself during objdir testing. Running the browser from dist/bin writes real shortcuts that outlive the test.

**Fix:** Repoint each one at <install>/<exe>. The installed browser is under %USERPROFILE%/Gorilla Unleashed. A shortcut into C:/gfobj launches an unpackaged build and dies the next time the objdir is clobbered.

#### `pref-block-divergence` - The two pref blocks agree

**What went wrong:** 2026-09-13: patches/05.PREFS and patches/17.WINDOWS.FIXES each carry a FULL copy of the Gorilla pref block (253 and 240 added pref lines), not a base and a delta. The DTLS 1.2 cap was added to the Linux one alone, so Windows stayed broken while the diff looked like a fix. Any pref edited in one file and not the other silently diverges the platforms.

**Fix:** For each pref listed, decide deliberately whether the platforms should differ. If they should not, add it to whichever patch is missing it. If they should - a Linux-only GPU workaround, say - that is fine, but it must be a decision rather than an omission.

#### `theme-dead-selectors` - Theme selectors match real elements

**What went wrong:** 2026-09-13: the address bar's cyan edge was written as #urlbar-background. FF155 creates that element with class= and no id, so all three rules were dead code and the field drew no border at all. A comment at the bottom of the very same file already recorded the ID-to-CLASS rename; a later rescue block was written against the ID anyway. Dead CSS throws nothing and renders fine - only a human noticing a missing colour ever finds it.

**Fix:** For each id reported, find how FF155 actually builds that element (grep the .mjs/.xhtml that creates it) and use the selector it really has. If it is a class now, use the class - and prefer outline over border, which is this project's CSS invariant.

#### `address-bar` - Address bar proven to navigate

**What went wrong:** 2026-09-13: a browser shipped in which typing in the address bar was reported to do nothing, and every check in the harness passed - green build, all tracked fixes installed, theme rendering, 122 search engines with google as global default, 20 of 20 network prefs. Nothing had ever tried to type an address and go somewhere. A browser whose address bar does not navigate is not a browser.

**Fix:** Run: python "working scripts/verify_address_bar.py" - it warns you before it takes the keyboard for ~60s, then types about:robots, a bare hostname and a search term into a real window and reads the window title to prove each one navigated. Do not touch the keyboard while it runs. The result is recorded against this build only.

#### `builtin-ext-updates` - Bundled extensions are current

**What went wrong:** A bundled extension is frozen at build time, so it goes stale while the browser does not. This reports when the add-ons site has a newer version. It does NOT fetch it: every other input to this build is hash-pinned, and an extension with access to every page the user visits is the last thing that should update itself unreviewed.

**Fix:** Run: python "working scripts/add_builtin_extension.py" --amo <slug> --update, then rebuild and re-verify. Deliberately manual - see the diagnosis for why this is not automatic.

<details><summary>How this was diagnosed (including the wrong hypotheses)</summary>

```
THE PROPOSAL
    "Every time we rebuild we will have to fetch the latest uBlock Origin from
    GitHub. This way we should be able to keep it relatively up to date."

    The goal is right. The mechanism is not, and the reason is worth keeping.

WHY THE GOAL IS RIGHT
    A bundled extension is frozen at build time. It does not update itself -
    that is the whole point of bundling, and it is also the whole cost. uBlock
    Origin ships fixes for anti-adblock breakage constantly; a build six months
    old is measurably worse at its job than the same build was on release day.
    Doing nothing is not a neutral choice.

WHY AUTO-FETCH IS THE WRONG LEVER HERE
    1. It would be the only unpinned input in the build.
       config/versions.lock.json pins MozillaBuild, the VS toolchain, the
       Firefox revision, cbindgen and nasm by SHA-256. The doctrine of this
       harness is that it refuses to continue if anything has quietly changed.
       An auto-fetched extension means two builds of the same source revision
       ship different code, with no way to say afterwards which one someone is
       running. The extension recorded only a version string until 2026-09-13,
       which made it exactly that hole.

    2. It is a supply-chain decision wearing a convenience costume.
       A bundled extension reads every page the user visits and cannot be
       uninstalled by them. Taking whatever a third party published that
       morning, unreviewed, straight into a browser handed to other people, is
       not a sensible default. Once, deliberately, is fine. On a timer is not.

    3. It turns an upstream outage into a build failure.
       No network, AMO down, CDN hiccup - the build stops. A reproducible build
       should not depend on someone else's uptime.

WHAT WAS DONE INSTEAD
    Pin and notify. Same outcome, reached by decision:

      - version AND sha256 recorded in state/builtin_extensions.json
      - this check queries the add-ons site on EVERY preflight run and reports
        when something newer exists
      - re-running the bundler REFUSES if the served version no longer matches
        the pin, rather than silently substituting one
      - --update takes the new version in one command
      - --check-updates asks without writing anything
      - --latest restores the original fetch-newest behaviour for anyone who
        wants it

    WARN, never BLOCKER, for two reasons: it needs the network, and being one
    release behind is not a reason to refuse to build.

BOTH PATHS WERE TESTED BY BREAKING THEM
    Rolling the pin back to 1.60.0 fired the warning. Re-running the bundler
    without --update refused, naming both versions. Rule 4 of the runbook: a
    check is not finished until you have watched it fail.

THE GENERAL SHAPE
    "Keep it current" and "fetch it automatically" are not the same
    requirement, and conflating them is how an unreviewed dependency gets into
    a shipped product. Notification satisfies the first without conceding the
    second. The user still gets told on every single build; taking the update
    costs one command.
```

</details>

#### `privacy-claims` - Package matches the privacy claims

**What went wrong:** 2026-09-11: the release notes claim telemetry, AI and sponsored content are removed. 26 of 26 core prefs verified false-and-locked in the shipped package, and a 60-second socket capture on a fresh profile reached no telemetry, Normandy, Glean, Contile, Pocket or Merino endpoint. But four belt-and-braces prefs from the project's own hardening plan (14.EGRESS.LOCKDOWN Column A) exist only in the profile-level user.js, which no installer deploys - so they are absent from the build defaults on both platforms.

**Fix:** Run: python "working scripts/audit_privacy_claims.py" to see which prefs differ. For a live check that nothing is actually sent, run verify_no_phone_home.py - it watches the socket table on a clean profile.

<details><summary>How this was diagnosed (including the wrong hypotheses)</summary>

```
THE QUESTION THAT EXPOSED THIS
    "Is the telemetry and data collection stripped out, the AI features
    removed, sponsored tiles gone? I could check the hardware decode myself,
    but how about the telemetry?"

    A fair challenge to a claim made in a release note to strangers who are
    trusting a binary they cannot read.

FOUR LAYERS, BECAUSE NO SINGLE ONE IS PROOF
    1. PREFS IN THE PACKAGE - 26 of 26 core prefs false and LOCKED, read out
       of the shipped omni.ja rather than the source.
    2. CODE ABSENT - the ML engine, AI Window and Link Preview modules are not
       in the package at all. A pref says what code is told to do; absence
       says it cannot be told anything.
    3. C++ - FOG.cpp returns NS_OK before Glean initialises, so the dispatcher
       thread is never spawned. Not a pref, cannot be flipped.
    4. THE WIRE - a 60-second socket capture on a brand new profile. No
       telemetry, Normandy, Glean, Shield, Contile, Pocket or Merino endpoint
       was contacted.

    Only the fourth is evidence about behaviour. The first three are evidence
    about intent.

THE BUG IN THE AUDIT, WHICH INVERTED THE ANSWER
    Firefox pref files are read top to bottom and the LAST definition wins.
    The Gorilla injection is appended, so its values sit BELOW upstream's.

    The first version of the audit grepped for the first match and reported:

        app.shield.optoutstudies.enabled = true     (Shield studies ENABLED)
        extensions.ml.enabled = true                (ML for extensions ON)

    Both false alarms. The same files set them false 475 and 864 lines further
    down. Reading the first match inverts the answer for every pref the
    patchset overrides - which is precisely the set worth checking.

THE BUG IN THE NETWORK CHECK
    The socket filter excluded localhost with the regex

        ^(0[.]0[.]0[.]0|127[.]|::1|::)$

    '127[.]' followed by '$' cannot match '127.0.0.1'. Firefox's own
    inter-process sockets sailed through and were reported as four
    unidentified external endpoints - which is exactly the kind of scary,
    wrong result that destroys trust in a privacy audit.

    Reverse DNS then failed on the real endpoints, because Mozilla's services
    sit behind Fastly and Google Cloud and resolve to nothing useful. "Four
    unidentified IPs" is not good enough to support a privacy claim, so the
    check now reads the DNS client cache for the names actually looked up.

WHAT IT ACTUALLY FOUND
    No surveillance endpoint. But not silence either:

        services.addons.mozilla.org           add-on blocklist
        content-signature-2.cdn.mozilla.net   signature verification
        mozilla.map.fastly.net                CDN

    These are deliberate. patches/14.EGRESS.LOCKDOWN states the doctrine:
    close surveillance doors, PRESERVE the infrastructure that makes a browser
    usable, and document every kept door so a later over-zealous pass does not
    harden cert revocation into oblivion. So the honest claim is "no
    surveillance", not the stronger and false "contacts nothing".

    And a real gap: four belt-and-braces prefs from that plan's own Column A
    (rsexperimentloader, ping-centre, activity-stream feed telemetry,
    coverage.opt-out) exist only in 10.OVERRIDES/user.js - a PROFILE file that
    no installer deploys. They are missing from the build defaults on both
    platforms. The plan document is still headed "Status: PLAN".

    Not a leak: the transports they belt are already dead, and the wire
    capture confirms it. Defence-in-depth that was designed and never landed.

LESSON
    Check the claim against the artefact you shipped, not the tree you built
    it from - and check behaviour, not only configuration.

    Then check your checker. Two of the three findings in the first run were
    bugs in the audit, and both of them accused the build of something it had
    not done.
```

</details>

#### `decode-profile` - Per-machine hardware decode profile

**What went wrong:** The shipped codec policy is H.264-only, chosen for the oldest machine in the fleet (Ivy Bridge, no VP9/HEVC/AV1 decoder at all). On newer hardware it leaves the AV1 and VP9 decoders idle and caps YouTube at 1080p. The codec prefs are deliberately unlocked so a per-machine default in <install>/defaults/pref/ can override them without a rebuild.

**Fix:** Run on the target machine: python "working scripts/make_decode_profile.py" --detect --apply, then --verify.

#### `installed-build` - Installed browser carries the fixes

**What went wrong:** 2026-09-11: nothing in the harness looked at what was actually INSTALLED. A fix can be perfectly present in src/, exported to the patchset, covered by a check - and absent from the browser you are about to test, because the install predates it. WARN rather than BLOCKER: a stale install does not make the next build wrong, it makes the next test session wrong.

**Fix:** Re-package and re-install: python harness/gorilla_build.py package, then run the installer. Verify with: python "working scripts/verify_installed_build.py".

<details><summary>How this was diagnosed (including the wrong hypotheses)</summary>

```
THE QUESTION THAT EXPOSED THIS
    "Is the new build installed on my computer containing all the fixes we
    have created so far?"

    Four questions were asked together, and three of them the harness could
    answer immediately:

        do the fixes survive a rebuild?   yes - 9 patches + 39 files, verified
        are they in the Windows source?   yes - every marker present in src/
        are they in the harness?          yes - 47 checks, 30 diagnoses
        are they in the INSTALL?          nothing could say

    Every check in preflight.py reads src/ or the objdir. Not one of them
    looked at the browser that actually launches when you click the icon.

WHY THAT IS A REAL GAP, NOT A PEDANTIC ONE
    The chain from a fix to a running browser has three links:

        src/ has the fix          a check covers this
        the BUILD has the fix     only if src/ predates the build
        the INSTALL has the fix   only if the install matches that build

    Break the second link - edit a file after building - and every check in
    the harness still passes while the browser on screen behaves as though
    the fix was never made. That is indistinguishable from the fix not
    working, and it is how an afternoon gets spent re-debugging something
    that was already correct.

THE WRONG GREP, AGAIN
    Answering the question by hand, one probe reported the UrlbarShared
    getter MISSING from the installed package. It was present. Firefox ships
    two archives:

        browser/omni.ja   chrome://browser content, actors, themes, .ftl
        omni.ja           moz-src/, which holds the urlbar providers

    The probe searched only the first. Same shape as every other bad check in
    this project: it tested something ADJACENT to the property that mattered.
    verify_installed_build.py therefore searches BOTH archives by filename
    suffix and never by a guessed path.

AND THE CHECK ITSELF FAILED ITS OWN FAILURE TEST
    Three broken installs were built to prove the checker fires: a corrupted
    binary, a package with genai.ftl removed, and an install backdated so
    every source file postdates it.

    The first two failed correctly. The third PASSED.

    Section 2 read its "when was this built" timestamp from the objdir before
    the install. The objdir had been rebuilt since, so the stamp came from
    the newer tree and hid the staleness of the very thing being audited -
    which is exactly the real-world case of installing a build and then
    rebuilding. Fixed to read the install's own timestamp, because the
    install is what is being audited.

LESSON
    "Fixed", "built", and "installed" are three different states. A harness
    that only checks the first will confidently tell you a browser is correct
    while you are looking at one that is not.

    And the failure test is not ceremony. Two of three broken cases were
    caught; the third exposed a real bug in the checker, in the section that
    looked most obviously right.
```

</details>

#### `patchset-export` - Fixes survive a tree rebuild

**What went wrong:** 2026-09-09: an audit asked whether the session's fixes were reusable. Detection was 18 of 18 and every fix had a written diagnosis, but only 5 of 18 had a script that re-applies them - the rest were hand edits to src/, which is a derived tree. Four of those files appeared in no patch group, so a rebuild from upstream plus the patchset would have silently lost them.

**Fix:** Run: python "working scripts/export_session_fixes.py", then verify with verify_patches_apply.py. Both are in working scripts/.

<details><summary>How this was diagnosed (including the wrong hypotheses)</summary>

```
THE QUESTION THAT EXPOSED THIS
    "Have all the fixes been turned into python scripts so they can be used
    later on?"

    The honest answer required an audit rather than a claim, and the audit
    split into three questions that had been quietly conflated:

        DETECT    is there a check that catches this coming back?  18 of 18
        RECORD    is the reasoning written down?                   18 of 18
        RE-APPLY  is there something that performs the fix?          5 of 18

    Detection and documentation were complete. Re-application was not.

WHY THAT MATTERS MORE THAN IT SOUNDS
    src/ is a DERIVED tree - upstream Firefox 155.0.1 plus gorilla-patchset.
    Every fix made by hand in src/ survives exactly until someone rebuilds the
    tree from its inputs.

    Checking which hand-fixed files existed in the patchset:

        browser/modules/AIWindowStub.sys.mjs                   NOT in patchset
        browser/locales-preview/genai.ftl                      NOT in patchset
        browser/base/content/navigator-toolbox.js              NOT in patchset
        browser/components/urlbar/UrlbarProviderQuickSuggest   NOT in patchset
        browser/themes/shared/master-redirect.css              in patchset (stale)

    A preflight check that catches a regression is not the same thing as a fix
    that survives a rebuild. The harness was strong on the first and had a
    hole in the second.

THE FIX
    export_session_fixes.py writes a patch group in the conventions the tree
    already uses - .patch files for anything upstream also has, NEW_FILES/ for
    everything else and for binaries, plus a README naming the reason for each
    item. 9 patches, 4 new files, 35 regenerated artwork files.

VERIFYING IT, AND THE BUG THAT FOUND
    "The patches exist" is not "the patches work". verify_patches_apply.py
    extracts each PRISTINE upstream file, applies the patch to it, and
    compares the result byte-for-byte against src/.

    First run: 8 of 9 passed. SessionStore.sys.mjs failed, and the error text
    showed why:

        restore / crash recovery a<U+0080><U+0094> so this forces Smart

    Mojibake. The export had used subprocess text=True, which on Windows
    decodes git's UTF-8 output through cp1252; writing it back as UTF-8
    double-encoded every non-ASCII character. An em-dash in a comment was
    enough for git apply to reject the whole patch.

    SessionStore.sys.mjs was the only patched region in the set containing a
    non-ASCII character. Nine files, one em-dash, and without the verification
    the export would have been declared done.

    Fixed by reading and writing patches as raw bytes. Second run: 9 of 9
    apply and match.

LESSON
    Three different senses of "done" were being treated as one: detected,
    documented, reproducible. Ask which one you actually have.

    And an export is not verified until you have applied it to the thing it
    claims to patch. Encoding bugs are invisible in every other test.
```

</details>

#### `nsis` - NSIS for packaging

**What went wrong:** Not yet hit: the build succeeds without NSIS and only the package stage fails, an hour later. WARN rather than BLOCKER because a build with no installer is still a usable result.

**Fix:** gorilla bootstrap (fetches NSIS into ~/.mozbuild/nsis).

#### `dev-drive-probe` - Get-Volume probe

**What went wrong:** 2026-09-09: mach bootstrap died with IndexError because Get-Volume returned nothing - its dev-drive check takes line [2] unconditionally. Get-Volume needs defragsvc and vds, both disabled on this machine.

**Fix:** Nothing to fix - the bootstrap stage patches mach temporarily and reverts it. Re-enabling defragsvc/vds would work too but is not needed to build.

#### `agent-env` - Coding-agent env markers

**What went wrong:** 2026-09-09: mozbuild forces quiet mode when CLAUDECODE/CODEX_SANDBOX/GEMINI_CLI/OPENCODE are set, and its fallback log file failed to create, so a failing build printed only '*** Fix above errors'.

**Fix:** Nothing to fix - the build stage strips them from the child environment.

<details><summary>How this was diagnosed (including the wrong hypotheses)</summary>

```
SYMPTOM
    A failing build that printed nothing useful:

        0:01.60 W AI agent detected. Terminal output limited to warnings and errors.
        0:01.60 W Log file could not be created.
        0:57.53 E *** Fix above errors and then restart with "./mach build"

    No error above it. One failure was diagnosed essentially blind.

CAUSE
    mozbuild/util.py::is_running_under_coding_agent() checks CLAUDECODE,
    CODEX_SANDBOX, GEMINI_CLI and OPENCODE. build_commands.py then forces
    quiet=True. Its fallback - writing full output to a log file - ALSO failed
    ("Log file could not be created"), so the detail went nowhere.

WHERE THE ANSWER ALREADY WAS
    The project's own Linux mozconfig documents stripping CLAUDECODE before
    calling mach "to prevent configure errors". The workaround predated this
    port; it just had not been carried across.

FIX
    The build stage strips all four markers from the child environment. The
    very next build surfaced a real mozbuild error that had been invisible.

LESSON
    Read the project's existing notes before diagnosing from scratch. And when
    a build fails silently, suspect the reporting before the build.
```

</details>

#### `thermal-margin` - Thermal headroom (real builds)

**What went wrong:** 2026-09-09: the 120s synthetic soak predicted 62.9 C; a real 48-minute build reached 74.8 C against a 75.0 C target. Chassis heat soak takes tens of minutes, so a short soak measures a transient, not equilibrium.

**Fix:** Lower the cap (calibrate --target, or step PROCTHROTTLEMAX down) to buy margin, or accept it if builds have never exceeded target.

<details><summary>How this was diagnosed (including the wrong hypotheses)</summary>

```
SYMPTOM
    None. Two successful-looking measurements that disagreed.

        synthetic calibration, 120s soak :  62.9 C peak
        real build #1, 50 min            :  63.9 C peak   <- looked like proof
        real build #2, 48 min            :  74.8 C peak   <- 0.2 C from target

WRONG HYPOTHESIS - "the cap slipped, or my mid-build powercfg change did it"
    Power settings had been changed mid-build (disabling sleep), so this was
    the obvious suspect.

    Disproved from the telemetry CSV: perf_pct peaked at 99.1% and never
    exceeded 100 for the whole run. The cap held perfectly throughout.

ACTUAL CAUSE
    Heat soak. The temperature climbed MONOTONICALLY over 48 minutes:

        11s 60.9   587s 65.8   1164s 68.8   1736s 70.8   2596s 73.8  -> 74.8

    The CPU never drew more power; the chassis and heatsink slowly saturated.

    At the 2-minute mark the real build read ~63 C - matching the synthetic
    calibration EXACTLY - and then kept climbing for another 45 minutes. The
    120-second soak measured a transient and called it equilibrium.

    Build #1 peaked lower because it was Rust-heavy, with lower average CPU
    occupancy. Workload composition matters as much as duration.

FIX
    Soak raised 120s -> 600s. More importantly, real_build_observations in
    thermal_profile.json are now marked AUTHORITATIVE over the synthetic
    ladder, because even 600s under-predicts a multi-hour build.

LESSON
    A thermal steady state in a laptop chassis takes tens of minutes. Any
    calibration shorter than that reports a number that is real, reproducible,
    and too low.
```

</details>

#### `temp-source` - Live temperature source

**What went wrong:** Without a live sensor the build cannot be verified as thermally safe, though the cap itself still applies.

**Fix:** The 'Thermal Zone Information' perf counter works unelevated on this box. MSAcpi is readable but STATIC here and must not be trusted.

<details><summary>How this was diagnosed (including the wrong hypotheses)</summary>

```
SYMPTOM
    None. That is what makes this the worst one here.

    Calibration ran, reported "cap 100% -> peak 71.1 C, avg 71.1 C", declared
    it under the 75 C target, and wrote a confident profile. Everything looked
    successful.

WHAT LOOKED WRONG (and was the only clue)
    peak == avg, identical to 0.1 C across ~45 samples. Real temperature
    varies; a perfectly flat reading is suspicious even when plausible.

HOW IT WAS PROVEN
    Sampled MSAcpi_ThermalZoneTemperature eight times AT IDLE:

        raw=3442  C=71.05   (x8, unchanging)

    71 C is implausible for an idle laptop, and it was the SAME value recorded
    under full all-core load. The sensor is a constant, not a reading.

    Cross-checked against the "Thermal Zone Information" perf counter:

        idle  52-55 C   loaded 90-96 C   (+40 C, live)

    Same machine, both claiming to report an ACPI thermal zone. One is a
    sensor; the other is a number.

CONSEQUENCE IF MISSED
    The build would have run at ~96 C while the harness reported it capped and
    safe. A confident, wrong measurement is worse than no measurement - it
    stops you looking.

FIX
    ThermalZone perf counter is now the primary source (and needs no
    elevation). MSAcpi is ranked LAST. validate_provider() saturates the cores
    and requires the reading to MOVE before any source is trusted.

LESSON
    Readable is not the same as working. "Is a value available?" is not a
    test. "Does it respond to the thing I am measuring?" is.
```

</details>

#### `defender` - Defender exclusion

**What went wrong:** Real-time scanning of an objdir can double or triple build time.

**Fix:** gorilla deps --install (elevated) adds the exclusions.

<details><summary>How this was diagnosed (including the wrong hypotheses)</summary>

```
SYMPTOM
    Builds felt heavy on CPU even with Defender exclusions supposedly in
    place, to the point that the user disabled real-time protection machine-
    wide to get relief.

ACTUAL CAUSE
    Only TWO of the FOUR build paths were excluded. The exclusion list was
    hardcoded as [source tree, C:\mozilla-build] in stage 10. When MOZ_OBJDIR
    was later moved to C:\gfobj to fix the MAX_PATH failure, nobody updated
    the list - so Defender scanned 4.4 GB of objdir on every single object
    file written, for the entire 89-minute build. ~/.mozbuild was missing too.

    The preflight check said "build tree excluded" and was telling the truth
    about the wrong thing.

TWO SELF-INFLICTED BUGS WHILE FIXING IT

  1. Get-MpPreference does NOT fail when unelevated. It returns the string
     "N/A: Must be an administrator to view exclusions" where the list should
     be. The code counted that as one exclusion and reported "1 path
     exclusion, 4 build paths not excluded" - a completely invented result.
     The exclusions had in fact applied correctly; only the verification was
     blind. A check that fabricates a number is worse than one that says "I
     cannot see".

  2. The elevated script ended with Read-Host while the launcher used -Wait,
     so the harness would hang forever whenever nobody was sitting at the
     machine to press Enter.

RESOLUTION
    Exclusion paths are now DERIVED (source, mozilla-build, ~/.mozbuild, and
    MOZ_OBJDIR parsed from the mozconfig) rather than hardcoded, so moving the
    objdir cannot silently drop coverage again. The stage requests elevation
    via UAC rather than demanding an already-elevated shell.

    With correct coverage, real-time protection can go back ON - which is the
    right end state. Disabling it machine-wide is available behind
    --disable-realtime, but it is a blunt instrument: it removes protection
    from everything, and Windows re-enables it on its own anyway.

LESSON
    A derived list stays correct when the thing it describes moves; a
    hardcoded one rots silently. And when a query can fail soft, check for the
    failure - "readable" and "readable AND meaningful" are different tests.
```

</details>


---

## Lessons with no check

These are failures that were diagnosed and fixed permanently in the
harness itself, so there is nothing left for a check to test. They are
recorded because the reasoning is what saves the time, not the fix.


### mach-installer

```
SYMPTOM
    The build succeeded, `mach package` succeeded, and then the packaging
    stage ended with:

        packager.mk:162: *** "make install" is not supported on this
        platform. Use "make package" instead..  Stop.
        mozmake: *** [browser/build.mk:15: install] Error 2

WRONG HYPOTHESIS - "Windows cannot build an installer from mach"
    That is what the message says, near enough, and it is completely wrong.
    It sent the investigation looking for the "real" Windows installer target:
    a make target inside browser/installer, a MOZ_INSTALLER configure flag, an
    --enable-installer option. None of those exist.

    What the message actually describes is a target NOBODY ASKED FOR. The
    harness called `./mach installer`. There is no such mach command. mach did
    not error - it guessed:

        We're assuming the 'installer' command is 'install' and we're
        executing it for you.

    That line was four lines above the failure in the captured log, and it is
    the whole story. `mach install` maps to `make install`, which packager.mk
    rejects on Windows. The error is real, the target is real, and neither had
    anything to do with what was wanted.

WHAT WAS ACTUALLY TRUE
    On Windows, `mach package` ALREADY builds the NSIS installer, in the same
    run. The log showed it plainly, a minute BEFORE the failure:

        1:23.78 Creating archive: .../app.7z
        1:23.93 mozmake[3]: Leaving directory 'C:/gfobj/browser/installer/windows'

    And dist/ held firefox-155.0.1.en-US.win64.installer.exe, 85 MB, with a
    timestamp NEWER than the zip. The work had already succeeded. The failing
    step was redundant.

LESSON
    When a tool says it is assuming what you meant, that assumption is the
    first thing to check - before believing the error that follows it. And
    when a stage fails, look at what is already on disk before deciding the
    work was not done. The timestamps settled this in one command.

    More generally: capture the FULL log. The give-away line scrolled past in
    the summarised output; it was only visible in state/pkg_full.log.
```


### panel-theme-stock

```
THE MOST EXPENSIVE WRONG DIAGNOSIS IN THIS PROJECT.

    This entry originally recorded a decision to abandon the Gorilla panel
    theme because it "could not be made to work on FF155". That was wrong.
    The theme was fine. It has been restored. What follows is the corrected
    account, kept in full because the wrong turns are the valuable part.

SYMPTOM
    The app menu opened as a panel with no labels - a few chevrons, a "100%"
    zoom row, and nothing else. The menu bar was empty too.

FOUR ROUNDS OF THE WRONG WORK
    1. cyan `color`/`fill` on panel containers and their children
    2. un-blacking --color-gray-05 at the root
    3. color-scheme:dark plus --color-gray-100 overrides
    4. reading the theme and finding FF154-era panel[type="arrow"] cyan rules
       already present and already not working

    Then, on the theory that the theme simply could not be ported, all panel
    and menu styling was stripped out and left to stock Firefox.

    The menu was still blank.

    THAT is the moment the diagnosis should have collapsed, and it is worth
    noticing why it took so long to get there: every round produced a small
    real improvement somewhere else, which felt like progress.

THE ACTUAL CAUSE
    browser/base/content/browser.xhtml - UNMODIFIED UPSTREAM - declares

        <link rel="localization" href="preview/genai.ftl"/>

    and the genai excision had removed the line that packages it from
    browser/locales/jar.mn:

        preview/genai.ftl   (../components/genai/content/genai.ftl)

    A localization resource that cannot be resolved stops the window's Fluent
    bundle from resolving AT ALL. Every data-l10n-id in the chrome then
    returns empty. Not black-on-black. EMPTY.

    Fix: an empty browser/locales-preview/genai.ftl, mapped in jar.mn. The
    menu came back fully populated on the next build, in the Gorilla theme,
    with keyboard shortcuts.

THE TELL THAT WAS THERE THE WHOLE TIME
    The "100%" zoom row rendered normally in every screenshot. It is generated
    by JavaScript, not by Fluent.

    When some text in a container renders and other text does not, the missing
    text is ABSENT, not invisible. Colour cannot do that. Two seconds of
    thought about why one label survived would have saved four rounds.

    A second signal was ignored for just as long: a flood of console warnings,

        <key id="key_newNavigatorTab" data-l10n-id="tab-new-shortcut">
        is missing "key" and "keycode" attributes

    Those attributes come from the FTL. The console was saying "localization
    is not resolving" in plain language, and it was read as unrelated noise
    because it did not mention menus.

WHAT THE CSS ROUNDS DID ACHIEVE - they were not all waste
    - Un-blacking --color-gray-05 genuinely repaired the toolbar icons, the
      address bar text and the tab strip. FF155 resolves every dark-mode
      foreground token to that one token, so blacking it for backgrounds
      blacked every foreground in the browser. Real bug, real fix.
    - .urlbar-background is a CLASS in FF155, not an ID. Every #urlbar* rule
      in the theme was dead code. Real bug, real fix.

    Both stay. Only the panel work was chasing a ghost.

LESSONS
    1. Missing text and unreadable text are different failures. Establish
       which one you have before touching a stylesheet.
    2. When a fix does not work, prefer "my diagnosis is wrong" over "my fix
       was not aggressive enough". Four rounds of escalating !important is a
       signal, not a strategy.
    3. Read the console warnings that do not obviously relate to the symptom.
       The answer was in them from the first run.
    4. Reverting a feature is not a fix when you cannot explain the failure.
       The revert here removed working code and left the bug untouched.
```


## Tools

- `add_builtin_extension.py` - Bundle a WebExtension INTO the browser, as a visible built-in add-on.
- `analyze_prefs_portability.py` - Which Linux Gorilla prefs transfer to Windows, and what already ships?
- `apply_partial_for_rebase.py` - Half-apply the failing patches on purpose, to generate .rej files.
- `audit_fix_coverage.py` - Audit: is every fix from this session actually reproducible?
- `audit_harness_wiring.py` - Are the checks and tools actually WIRED INTO the build, or just present?
- `audit_privacy_claims.py` - Verify the privacy claims against the SHIPPED package, not the source.
- `brand_installer_stub.py` - Put this build's icon on the installer's outer self-extractor.
- `capture_chrome.py` - Screenshot the browser CHROME, and iterate on chrome CSS without rebuilding.
- `check_deleted_file_refs.py` - Find build files that still reference deleted sources.
- `check_dropped_imports.py` - Find upstream @import rules that a patch REPLACED instead of adding to.
- `check_embedded_icon.py` - Is the gorilla artwork actually embedded in firefox.exe?
- `check_l10n_resources.py` - Every <link rel="localization"> must resolve to a packaged .ftl.
- `check_lazy_getters.py` - Find `lazy.Foo` used in a module that never declares a getter for Foo.
- `check_logo_provenance.py` - Is the internal-pages logo crisp, and can we even tell?
- `close_privacy_gap.py` - Land the Column A close-list prefs that only ever existed in a user.js.
- `css_override_from_rejects.py` - Turn rejected CSS hunks into an appended override block.
- `diff_mozconfig.py` - Diff the ported mozconfig against the original it was derived from.
- `dump_icons.py` - Extract the main icon from PE files so we can LOOK at them.
- `dump_pe_icons.py` - List every icon group in a PE and save each one, so you can SEE them.
- `export_session_fixes.py` - Export this session's source fixes into gorilla-patchset, so they survive.
- `extract_failing_hunks.py` - Dump each failing hunk next to the source it ACTUALLY failed against.
- `find_split_clusters.py` - Find files whose patches were split across enabled and disabled groups.
- `fix_prefs_last_wins.py` - Repair hardening that a later pref file silently undoes.
- `fix_theme_dead_selectors.py` - Find theme rules that select an element which does not exist.
- `ftl_rebase_helper.py` - Rebase Fluent brand-injection hunks onto reworded upstream strings.
- `generate_branding_icons.py` - Build the Windows .ico files from the real gorilla PNG artwork.
- `generate_playbook.py` - Generate BUILD-PLAYBOOK.md from the live preflight check registry.
- `generate_windows_branding_assets.py` - Generate the Windows-only branding assets from the real icon artwork.
- `guard_linux_prefs.py` - Platform-gate the Linux-only Gorilla prefs so they stop firing on Windows.
- `make_decode_profile.py` - Emit a per-machine hardware-decode pref file for a Gorilla Unleashed install.
- `publish_gate.py` - Refuse to publish a browser nobody has proven works.
- `rebuild_about_logo.py` - Rebuild about-logo.svg from a canonical master, the way the doctrine says.
- `regen_branding_pngs.py` - Regenerate the branding PNG ladder from the canonical master.
- `repair_fluent_attrs.py` - Repair Fluent attributes mangled into multiline values.
- `shell_icon.py` - Ask the Windows shell what icon it resolves for a file, at a given size.
- `tally_failed_hunks.py` - Turn "39 patches failed" into the number that actually matters.
- `test_decode_detection.py` - Failure test for make_decode_profile.py's GPU tier detection.
- `triage_build_failure.py` - Classify a build failure and draft the check that would have caught it.
- `triage_patch_groups.py` - Triage a Gorilla patch group against a Firefox source tree.
- `validate_package_manifest.py` - Check every file package-manifest.in demands actually exists.
- `verify_address_bar.py` - Prove the address bar WORKS - not that it renders.
- `verify_builtin_extension.py` - Prove a bundled extension is present AND VISIBLE, not merely loaded.
- `verify_icon_check.py` - Prove the icon check flags the blue-globe placeholders and passes the real ones.
- `verify_import_check.py` - Prove check_dropped_imports.py catches the actual defect, not just passes.
- `verify_installed_build.py` - Does the browser INSTALLED ON THIS MACHINE actually contain our fixes?
- `verify_installer.py` - Verify the packaged installer: right icon, and payload still intact.
- `verify_no_phone_home.py` - Watch the browser start on a clean profile and record every host it contacts.
- `verify_patches_apply.py` - Prove the exported patches apply to a PRISTINE upstream tree.
- `watch_thermals.py` - Watch CPU temperature during a build, and stop it before it cooks.
