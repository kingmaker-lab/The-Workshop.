"""Run all experiments locally; runtime requires an explicit emulator."""
import argparse
import json
import os
import platform
import re
import statistics
import subprocess
import sys
import time
from pathlib import Path

from tools.pulse_inspector import inspect_apk
from tools.static_experiments import command, exp002, exp003, exp004, exp005, tool

ROOT = Path(__file__).resolve().parent
PACKAGE = "lab.workshop.pulsefixture"


def configure_sdk():
    sdk = os.environ.get("ANDROID_SDK_ROOT")
    version = os.environ.get("BUILD_TOOLS_VERSION")
    if not sdk:
        return
    root = Path(sdk)
    candidates = {"ADB": root / "platform-tools/adb",
                  "APKANALYZER": root / "cmdline-tools/latest/bin/apkanalyzer"}
    if version:
        candidates["APKSIGNER"] = root / "build-tools" / version / "apksigner"
    for key, path in candidates.items():
        if path.is_file():
            os.environ.setdefault(key, str(path))


def runtime(apk, serial, samples=3):
    if not re.fullmatch(r"emulator-[0-9]+", serial):
        raise ValueError("only explicitly selected local emulator serials are accepted")
    adb = tool("adb")
    if not adb:
        return {"status": "skip", "reason": "adb unavailable"}
    base = [adb, "-s", serial]
    rc, state = command(base + ["get-state"])
    if rc or state.strip() != "device":
        return {"status": "skip", "reason": "emulator not connected"}
    rc, present = command(base + ["shell", "pm", "path", PACKAGE])
    if rc == 0 or "package:" in present:
        return {"status": "skip", "reason": "fixture already installed; use a fresh emulator or remove it manually"}
    rc, output = command(base + ["install", str(apk)], timeout=120)
    if rc or "Success" not in output:
        return {"status": "fail", "reason": "installation failed", "output": output}
    rows = []
    for _ in range(samples):
        rc, stop = command(base + ["shell", "am", "force-stop", PACKAGE])
        if rc:
            return {"status": "fail", "reason": "force-stop failed", "output": stop}
        rc, start = command(base + ["shell", "am", "start", "-W", "-n", PACKAGE + "/.MainActivity"])
        match = re.search(r"(?m)^TotalTime:\s*(\d+)\s*$", start)
        if rc or not match or not re.search(r"(?m)^Status:\s*ok\s*$", start):
            return {"status": "fail", "reason": "startup metric unavailable", "output": start}
        rc, mem = command(base + ["shell", "dumpsys", "meminfo", PACKAGE])
        pss = re.search(r"TOTAL PSS:\s*(\d+)", mem)
        if not pss:
            pss = re.search(r"(?m)^\s*TOTAL\s+(\d+)\s+", mem)
        rows.append({"startup_ms": int(match.group(1)),
                     "pss_kib": int(pss.group(1)) if rc == 0 and pss else None})
    pss_values = [r["pss_kib"] for r in rows if r["pss_kib"] is not None]
    return {"status": "pass" if len(pss_values) == samples else "partial",
            "samples": rows, "median_startup_ms": statistics.median(r["startup_ms"] for r in rows),
            "median_pss_kib": statistics.median(pss_values) if pss_values else None,
            "notes": "process cold starts, not device cold boots; fixture remains installed"}


def guarded(fn, *args):
    started = time.monotonic()
    try:
        value = fn(*args)
    except Exception as e:
        value = {"status": "error", "reason": str(e), "type": type(e).__name__}
    return {**value, "wall_seconds": round(time.monotonic() - started, 6)}


def build():
    rc, output = command(["bash", str(ROOT / "fixtures/build_fixture.sh")], timeout=300)
    if rc:
        raise RuntimeError("fixture build failed: " + output)
    paths = re.findall(r"(?m)^APK: (.+)$", output)
    if len(paths) != 1:
        raise RuntimeError("fixture build did not report a unique APK")
    path = Path(paths[0]).resolve()
    if path.parent.parent != ROOT or not path.parent.name.startswith(".pulse-build.") or not path.is_file():
        raise RuntimeError("unexpected fixture path")
    return path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--build", action="store_true", help="build our own Android fixture")
    group.add_argument("--apk", type=Path, help="inspect an owned APK; static only")
    parser.add_argument("--emulator", help="explicit serial for runtime; requires --build")
    parser.add_argument("--output", type=Path, default=ROOT / "reports-local" / "suite.json")
    args = parser.parse_args()
    if args.emulator and not args.build:
        parser.error("--emulator requires --build")
    configure_sdk()
    if args.apk:
        args.apk = args.apk.resolve()
    args.output = args.output.resolve()
    os.chdir(ROOT)
    report = {"schema": "pulse.suite.v1", "python": sys.version,
              "platform": platform.platform(), "experiments": {}}
    rc, output = command([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"], timeout=120)
    report["unit_tests"] = {"status": "pass" if rc == 0 else "fail", "output": output}
    ex = report["experiments"]
    path = args.apk
    if args.build:
        try:
            path = build()
            report["fixture_build"] = {"status": "pass", "path": str(path)}
        except Exception as e:
            report["fixture_build"] = {"status": "error", "reason": str(e)}
    if path:
        path = path.resolve()
        ex["001"] = guarded(lambda: {"status": "pass", **inspect_apk(path)})
        if ex["001"]["status"] == "pass":
            for number, fn in [("002", exp002), ("003", exp003), ("004", exp004), ("005", exp005)]:
                ex[number] = guarded(fn, path, ex["001"])
            if args.build:
                expected = {
                    "001": ex["001"].get("manifest_present") and ex["001"].get("dex_candidates") == ["classes.dex"],
                    "002": ex["002"].get("package") == PACKAGE and ex["002"].get("permissions") == ["android.permission.VIBRATE"] and any(c["name"] == ".MainActivity" or c["name"] == PACKAGE + ".MainActivity" for c in ex["002"].get("components", [])),
                    "003": bool(ex["003"].get("files")) and all(d.get("sections", {}).get("classes", 0) > 0 for d in ex["003"].get("files", [])),
                    "005": ex["005"].get("signature_verified") is True,
                }
                if os.environ.get("NDK_CLANG_DIR"):
                    expected["004"] = (ex["001"].get("abi_candidates") == ["arm64-v8a", "x86_64"]
                                       and bool(ex["004"].get("files"))
                                       and all("Java_lab_workshop_pulsefixture_MainActivity_nativeAnswer" in n.get("jni_exports", []) for n in ex["004"]["files"]))
                    if not tool("readelf") and ex["004"]["status"] == "pass":
                        ex["004"]["status"] = "partial"
                for number, matches in expected.items():
                    ex[number]["fixture_ground_truth_matches"] = bool(matches)
                    if not matches and ex[number]["status"] == "pass":
                        ex[number]["status"] = "fail"
                # Unsigned control: apksigner must reject the same payload before signing.
                if ex["005"]["status"] == "pass":
                    rc, output = command([tool("apksigner"), "verify", str(path.parent / "aligned.apk")])
                    ex["005"]["unsigned_control_rejected"] = rc != 0
                    if rc == 0:
                        ex["005"]["status"] = "fail"
            if args.emulator and args.build and ex["002"].get("package") == PACKAGE and ex["005"]["status"] == "pass":
                ex["006"] = guarded(runtime, path, args.emulator)
    for i in range(1, 7):
        ex.setdefault(f"{i:03}", {"status": "skip", "reason": "required input, SDK or explicit emulator not available"})
    statuses = [v["status"] for v in ex.values()] + [report["unit_tests"]["status"]]
    if "fixture_build" in report:
        statuses.append(report["fixture_build"]["status"])
    report["status"] = "fail" if any(s in ("fail", "error") for s in statuses) else ("pass" if all(s == "pass" for s in statuses) else "partial")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "experiments": {k: v["status"] for k,v in ex.items()}, "report": str(args.output)}, indent=2))
    return {"pass": 0, "fail": 1, "partial": 2}[report["status"]]


if __name__ == "__main__":
    sys.exit(main())
