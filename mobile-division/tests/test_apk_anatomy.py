"""Synthetic ZIP fixtures, not installable Android applications."""
import hashlib
import stat
import tempfile
import unittest
import warnings
import zipfile
from pathlib import Path

from tools.pulse_inspector import inspect_apk


class AnatomyTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.apk = Path(self.temp.name) / "fixture.apk"

    def make(self, entries, compression=zipfile.ZIP_STORED):
        with zipfile.ZipFile(self.apk, "w", compression=compression) as archive:
            for name, value in entries:
                archive.writestr(name, value)

    def test_inventory(self):
        self.make([
            ("AndroidManifest.xml", b"synthetic manifest"),
            ("classes.dex", b"not actual DEX"),
            ("classes2.dex", b"synthetic"),
            ("classes10.dex", b"synthetic"),
            ("lib/arm64-v8a/libdemo.so", b"not actual ELF"),
            ("META-INF/DEMO.RSA", b"not a real signature"),
            ("assets/readme.txt", b"hello"),
        ])
        r = inspect_apk(self.apk)
        self.assertEqual(r["entry_count"], 7)
        self.assertTrue(r["manifest_present"])
        self.assertEqual(r["dex_candidates"], ["classes.dex", "classes10.dex", "classes2.dex"])
        self.assertEqual(r["abi_candidates"], ["arm64-v8a"])
        self.assertEqual(r["v1_signature_artifacts"], ["META-INF/DEMO.RSA"])
        self.assertFalse(r["signature_verified"])
        self.assertFalse(r["payload_validated"])
        self.assertEqual(r["sha256"], hashlib.sha256(self.apk.read_bytes()).hexdigest())

    def test_missing_manifest(self):
        self.make([("assets/a", b"a")])
        self.assertFalse(inspect_apk(self.apk)["manifest_present"])

    def test_traversal(self):
        for name in ("../escape", "/absolute", "C:/escape", "assets\\escape"):
            with self.subTest(name=name):
                self.make([(name, b"x")])
                with self.assertRaises(ValueError):
                    inspect_apk(self.apk)

    def test_duplicates(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            self.make([("a", b"x"), ("a", b"y")])
        with self.assertRaises(ValueError):
            inspect_apk(self.apk)

    def test_symlink(self):
        info = zipfile.ZipInfo("link")
        info.create_system = 3
        info.external_attr = (stat.S_IFLNK | 0o777) << 16
        self.make([(info, b"target")])
        with self.assertRaises(ValueError):
            inspect_apk(self.apk)

    def test_compression_limit(self):
        self.make([("big", b"x" * 1000000)], zipfile.ZIP_DEFLATED)
        with self.assertRaises(ValueError):
            inspect_apk(self.apk)

    def test_entry_limit(self):
        self.make([(f"assets/{i}", b"x") for i in range(4097)])
        with self.assertRaises(ValueError):
            inspect_apk(self.apk)

    def test_invalid_zip(self):
        self.apk.write_bytes(b"not a zip")
        with self.assertRaises(zipfile.BadZipFile):
            inspect_apk(self.apk)


if __name__ == "__main__":
    unittest.main()
