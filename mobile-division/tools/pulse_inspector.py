"""Pulse Inspector EXP-001: bounded, metadata-only APK inventory."""
import argparse
import hashlib
import json
import re
import stat
import sys
import zipfile
from pathlib import Path

MAX_ARCHIVE = 64 * 1024 * 1024
MAX_ENTRIES = 4096
MAX_MEMBER = 64 * 1024 * 1024
MAX_EXPANDED = 256 * 1024 * 1024
MAX_RATIO = 200
DEX = re.compile(r"classes(?:[2-9]|[1-9][0-9]+)?\.dex\Z")
NATIVE = re.compile(r"lib/([^/]+)/([^/]+\.so)\Z")
SIGNATURE = re.compile(r"META-INF/[^/]+\.(?:RSA|DSA|EC|SF)\Z", re.I)


def inspect_apk(path):
    path = Path(path)
    if not path.is_file():
        raise ValueError("input must be a regular file")
    with path.open("rb") as source:
        source.seek(0, 2)
        size = source.tell()
        if not 0 < size <= MAX_ARCHIVE:
            raise ValueError("archive size outside allowed bounds")
        source.seek(0)
        digest = hashlib.sha256()
        remaining = size
        while remaining:
            chunk = source.read(min(65536, remaining))
            if not chunk:
                raise ValueError("input changed during hashing")
            digest.update(chunk)
            remaining -= len(chunk)
        source.seek(0)
        with zipfile.ZipFile(source) as archive:
            entries = archive.infolist()
            if len(entries) > MAX_ENTRIES:
                raise ValueError("too many archive entries")
            seen = set()
            expanded = 0
            dex, native, signatures = [], [], []
            manifest = False
            for item in entries:
                name = item.orig_filename
                parts = name.rstrip("/").split("/")
                if (not name or "\\" in name or "\x00" in name
                        or any(ord(c) < 32 or ord(c) == 127 for c in name)
                        or any(p in ("", ".", "..") for p in parts)
                        or ":" in parts[0]):
                    raise ValueError("unsafe archive path")
                canonical = name.rstrip("/")
                if canonical in seen:
                    raise ValueError("duplicate archive entry")
                seen.add(canonical)
                if stat.S_ISLNK(item.external_attr >> 16):
                    raise ValueError("symbolic link entry")
                if item.flag_bits & 1:
                    raise ValueError("encrypted archive entry")
                if item.file_size > MAX_MEMBER:
                    raise ValueError("member too large")
                expanded += item.file_size
                if expanded > MAX_EXPANDED:
                    raise ValueError("declared expanded size too large")
                if item.file_size > 0 and (
                    item.compress_size == 0
                    or item.file_size > MAX_RATIO * item.compress_size
                ):
                    raise ValueError("declared compression ratio too high")
                if item.is_dir():
                    continue
                if name == "AndroidManifest.xml":
                    manifest = True
                if DEX.fullmatch(name):
                    dex.append(name)
                match = NATIVE.fullmatch(name)
                if match:
                    native.append({"abi": match[1], "path": name})
                if SIGNATURE.fullmatch(name):
                    signatures.append(name)
            return {
                "schema": "pulse.exp001.v1",
                "sha256": digest.hexdigest(),
                "archive_bytes": size,
                "entry_count": len(entries),
                "declared_uncompressed_bytes": expanded,
                "manifest_present": manifest,
                "dex_candidates": sorted(dex),
                "native_candidates": sorted(native, key=lambda x: x["path"]),
                "abi_candidates": sorted({x["abi"] for x in native}),
                "v1_signature_artifacts": sorted(signatures),
                "signature_verified": False,
                "payload_validated": False,
                "scope": "ZIP central directory metadata only; no extraction or execution",
            }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("apk", type=Path)
    args = parser.parse_args()
    try:
        report = inspect_apk(args.apk)
    except (OSError, ValueError, zipfile.BadZipFile, NotImplementedError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=True), file=sys.stderr)
        return 1
    print(json.dumps(report, indent=2, ensure_ascii=True, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
