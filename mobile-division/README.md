# The Workshop | Mobile Division

**Pulse · DECONSTRUCTION · Explore. Deconstruct. Rebuild.**

Cycle 01 (EXP-001–006): implementation committed; test execution and scientific results pending. Android first, local own fixtures, no paid service required.

| Experiment | Hypothesis / acceptance criterion |
| --- | --- |
| 001 ANATOMY | Bounded ZIP inventory matches known APK entries and independent SHA-256 unit control; malformed paths and declared resource limits are rejected. |
| 002 GENESIS | SDK decoder recovers binary manifest package, requested permissions and activity; compare with source manifest. |
| 003 BLUEPRINT | DEX header, section bounds and SHA-1/Adler-32 agree with the compiled fixture; reject corrupted or truncated synthetic headers. |
| 004 NATIVE | ELF class and machine match expected ABIs; inspect JNI exports using readelf. With NDK, expect arm64-v8a and x86_64 and the named JNI symbol. |
| 005 SEAL | Official apksigner accepts the signed fixture and rejects its unsigned aligned control. |
| 006 AWAKENING | Explicit local emulator installs and starts the freshly built fixture; collect three process-cold startup and PSS samples. No speed threshold is asserted. |

## Debian / Linux prerequisites

Python 3.10+, Bash, JDK 17 (javac/keytool), binutils (readelf), Android SDK with platform android-35, build-tools 35.0.0, command-line tools (apkanalyzer), platform-tools (ADB), Android Emulator and a booted API-compatible AVD. Full EXP-004 also needs a locally installed NDK with the Linux x86_64 LLVM toolchain. Install these using the official Android SDK manager; this project does not download or install dependencies automatically.

From the repository root:

```bash
cd mobile-division
export ANDROID_SDK_ROOT="$HOME/Android/Sdk"
export BUILD_TOOLS_VERSION=35.0.0
export PATH="$ANDROID_SDK_ROOT/platform-tools:$ANDROID_SDK_ROOT/cmdline-tools/latest/bin:$PATH"
ls "$ANDROID_SDK_ROOT/ndk"
adb devices
```

Set NDK_CLANG_DIR to your actual installed NDK toolchain bin directory, e.g.:

```bash
export NDK_CLANG_DIR="$ANDROID_SDK_ROOT/ndk/<installed-version>/toolchains/llvm/prebuilt/linux-x86_64/bin"
```

Replace <installed-version> with the directory from ls. Use the emulator serial reported by adb devices (emulator-5554 is an example). Prefer a fresh disposable emulator; do not point this at a personal phone.

## One command: whole cycle

```bash
python3 run_all.py --build --emulator emulator-5554
```

This invokes all 24 Python unit cases, builds a fresh APK from the included Java/C source, generates a disposable local test key, runs static experiments, compares known fixture metadata, verifies the unsigned control and runs the emulator experiment. The emulator action is opt-in through --emulator and restricted to emulator serials and the APK just built by this invocation. It does not overwrite an already-installed fixture; use a fresh emulator or manually remove only lab.workshop.pulsefixture from a disposable emulator before another run. The fixture remains installed after the run.

The combined JSON report is written to reports-local/suite.json; local build files and keys are ignored by Git. Preserve the report for evaluation. Exit codes: 0 all pass; 1 failure/error; 2 partial (including skipped experiments). A skip is not a pass.

## Alternatives

```bash
python3 run_all.py
python3 run_all.py --build
python3 run_all.py --apk /path/to/owned.apk
python3 -m unittest discover -s tests -v
```

No arguments runs unit tests only; --build without --emulator skips EXP-006. Without NDK, the fixture is Java-only and EXP-004 is skipped. --apk does static analysis only. SDK binary locations can be overridden with APKANALYZER, APKSIGNER, ADB and READELF environment variables. The unit cases include synthetic headers and mocked SDK/ADB responses: they do not establish that Android integration works. Real integration is tested by the built fixture.

## Scope and limits

EXP-001 retains its existing implementation and conservative limits: 64 MiB archive, 4096 entries, 64 MiB declared member, 256 MiB declared expanded total, maximum declared compression ratio 200:1. The ZIP parser loads the central directory before checking entry count. Selected static experiment members are capped at 16 MiB each. No archive paths are used for extraction; EXP-004 writes one bounded native member to a fixed temporary filename for readelf. SDK tools have timeouts; output capture uses a temporary file and checks its size after exit. This is not a hardened sandbox; use owned samples and isolated resources. No third-party APKs are executed or uploaded.

EXP-002 delegates binary XML decoding to the Android SDK; it is not a custom AXML parser. EXP-003 supports classic little-endian DEX 035/037/038/039/040 headers, not full bytecode or semantic validation. EXP-004 inspects ELF headers and symbol-name candidates, not full relocation or JNI behavior. EXP-005 delegates verification to the official SDK, not an independent cryptographic implementation. EXP-006 measures process startup and PSS, not device cold boot, CPU profiling or proof of JNI execution. Test key is ephemeral and for the fixture only; never reuse it for production.

No measured results are asserted until local execution and report review. Keep changes on the experiment branch until validation.
