"""Static experiments 002–005. Own APKs only. No execution of payload."""
import hashlib
import os
import re
import shutil
import struct
import subprocess
import tempfile
import xml.etree.ElementTree as ET
import zipfile
import zlib
from pathlib import Path
from tools.pulse_inspector import inspect_apk

MAX_READ = 16 * 1024 * 1024
ANDROID = "{http://schemas.android.com/apk/res/android}"
ABI = {"armeabi-v7a": (1, 40), "arm64-v8a": (2, 183),
       "x86": (1, 3), "x86_64": (2, 62), "riscv64": (2, 243)}


def tool(name):
    value = os.environ.get(name.upper())
    if value:
        return value
    return shutil.which(name)


def command(args, timeout=30):
    # Only SDK tools and locally owned fixtures are passed to this function.
    with tempfile.TemporaryFile() as out:
        p = subprocess.run(args, stdout=out, stderr=subprocess.STDOUT,
                           timeout=timeout, check=False)
        out.seek(0)
        data = out.read(2 * 1024 * 1024 + 1)
        if len(data) > 2 * 1024 * 1024:
            raise ValueError("tool output too large")
        return p.returncode, data.decode("utf-8", errors="replace")


def read_member(archive, name):
    info = archive.getinfo(name)
    if info.file_size > MAX_READ:
        raise ValueError("member exceeds analysis limit")
    with archive.open(info) as stream:
        data = stream.read(MAX_READ + 1)
    if len(data) > MAX_READ or len(data) != info.file_size:
        raise ValueError("member size mismatch")
    return data


def manifest_xml(data):
    if len(data) > MAX_READ or re.search(br"<!\s*(?:DOCTYPE|ENTITY)", data, re.I):
        raise ValueError("unsafe XML")
    root = ET.fromstring(data)
    if root.tag != "manifest":
        raise ValueError("not Android manifest")
    permissions = sorted({e.get(ANDROID + "name") for e in root
                          if e.tag in ("uses-permission", "uses-permission-sdk-23")
                          and e.get(ANDROID + "name")})
    return {"package": root.get("package"), "permissions": permissions,
            "components": [{"type": e.tag, "name": e.get(ANDROID + "name"),
                            "exported": e.get(ANDROID + "exported")}
                           for app in root.findall("application") for e in app
                           if e.tag in ("activity", "activity-alias", "service",
                                        "receiver", "provider")]}


def exp002(path, inventory):
    if not inventory["manifest_present"]:
        return {"status": "fail", "reason": "manifest missing"}
    with zipfile.ZipFile(path) as archive:
        data = read_member(archive, "AndroidManifest.xml")
    if data.lstrip().startswith(b"<"):
        return {"status": "pass", "format": "text fixture", **manifest_xml(data)}
    analyzer = tool("apkanalyzer")
    if not analyzer:
        return {"status": "skip", "reason": "apkanalyzer unavailable"}
    rc, output = command([analyzer, "manifest", "print", str(path)])
    if rc:
        return {"status": "fail", "reason": "SDK decoder failed", "output": output}
    return {"status": "pass", "format": "SDK-decoded binary XML",
            **manifest_xml(output.encode("utf-8"))}


def dex_header(data):
    if len(data) < 112 or not re.fullmatch(rb"dex\n(?:035|037|038|039|040)\x00", data[:8]):
        raise ValueError("unsupported DEX header/version")
    size, header, endian = struct.unpack_from("<III", data, 32)
    if size != len(data) or header != 112 or endian != 0x12345678:
        raise ValueError("inconsistent DEX size/header/endian")
    sha = hashlib.sha1(data[32:]).digest() == data[12:32]
    adler = zlib.adler32(data[12:]) & 0xffffffff == struct.unpack_from("<I", data, 8)[0]
    sections = {}
    for label, pos, width in (("strings", 56, 4), ("types", 64, 4),
                              ("protos", 72, 12), ("fields", 80, 8),
                              ("methods", 88, 8), ("classes", 96, 32)):
        count, off = struct.unpack_from("<II", data, pos)
        if (count == 0 and off != 0) or (count and (off < header or off % 4 or off + count * width > size)):
            raise ValueError("DEX section outside bounds: " + label)
        sections[label] = count
    return {"version": data[4:7].decode(), "sha1_matches": sha,
            "adler32_matches": adler, "sections": sections}


def exp003(path, inventory):
    results = []
    with zipfile.ZipFile(path) as archive:
        for name in inventory["dex_candidates"]:
            try:
                results.append({"name": name, **dex_header(read_member(archive, name))})
            except ValueError as e:
                results.append({"name": name, "error": str(e)})
    if not results:
        return {"status": "skip", "reason": "no DEX", "files": []}
    return {"status": "pass" if all(x.get("sha1_matches") and x.get("adler32_matches") for x in results) else "fail",
            "files": results}


def elf_header(data, abi):
    if len(data) < 16 or data[:4] != b"\x7fELF" or data[4] not in (1, 2) or data[5] != 1:
        raise ValueError("unsupported ELF identification")
    cls = data[4]
    if len(data) < (64 if cls == 2 else 52) or data[6] != 1:
        raise ValueError("truncated or invalid ELF")
    kind, machine = struct.unpack_from("<HH", data, 16)
    return {"class_bits": 64 if cls == 2 else 32, "machine": machine,
            "shared_object": kind == 3, "abi_matches": ABI.get(abi) == (cls, machine)}


def exp004(path, inventory):
    results = []
    readelf = tool("readelf")
    with zipfile.ZipFile(path) as archive:
        for entry in inventory["native_candidates"]:
            try:
                data = read_member(archive, entry["path"])
                result = {**entry, **elf_header(data, entry["abi"])}
                if readelf:
                    with tempfile.TemporaryDirectory() as tmp:
                        local = Path(tmp) / "sample.so"
                        local.write_bytes(data)
                        rc, output = command([readelf, "--dyn-syms", "--wide", str(local)])
                    result["symbol_scan_ok"] = rc == 0
                    result["jni_exports"] = sorted(set(re.findall(r"\b(?:Java_[A-Za-z0-9_]+|JNI_OnLoad)\b", output))) if rc == 0 else []
                else:
                    result["symbol_scan_ok"] = None
                results.append(result)
            except ValueError as e:
                results.append({**entry, "error": str(e)})
    if not results:
        return {"status": "skip", "reason": "no native libraries", "files": []}
    return {"status": "pass" if all(x.get("abi_matches") and x.get("shared_object") and x.get("symbol_scan_ok") is not False for x in results) else "fail",
            "jni_scan_available": bool(readelf), "files": results}


def exp005(path, inventory):
    signer = tool("apksigner")
    if not signer:
        return {"status": "skip", "signature_verified": None, "reason": "apksigner unavailable"}
    rc, output = command([signer, "verify", "--verbose", "--print-certs", str(path)])
    return {"status": "pass" if rc == 0 else "fail", "signature_verified": rc == 0,
            "sha256": inventory["sha256"], "sdk_output": output}
