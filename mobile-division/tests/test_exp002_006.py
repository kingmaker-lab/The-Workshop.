"""Unit-level ground truth; SDK integration is exercised by run_all --build."""
import hashlib
import struct
import unittest
import zlib
from pathlib import Path
from unittest.mock import patch

from tools.static_experiments import manifest_xml, dex_header, elf_header, exp005
from run_all import runtime


def synthetic_dex():
    data = bytearray(112)
    data[:8] = b"dex\n035\x00"
    struct.pack_into("<III", data, 32, 112, 112, 0x12345678)
    data[12:32] = hashlib.sha1(data[32:]).digest()
    struct.pack_into("<I", data, 8, zlib.adler32(data[12:]) & 0xffffffff)
    return data


def synthetic_elf():
    data = bytearray(64)
    data[:7] = b"\x7fELF\x02\x01\x01"
    struct.pack_into("<HH", data, 16, 3, 183)
    return data


class Genesis(unittest.TestCase):
    def test_permissions_components(self):
        result = manifest_xml(b'<manifest xmlns:android="http://schemas.android.com/apk/res/android" package="test"><uses-permission android:name="android.permission.VIBRATE"/><application><activity android:name=".Main" android:exported="true"/></application></manifest>')
        self.assertEqual(result["package"], "test")
        self.assertEqual(result["permissions"], ["android.permission.VIBRATE"])
        self.assertEqual(result["components"][0]["exported"], "true")

    def test_reject_doctype(self):
        with self.assertRaises(ValueError):
            manifest_xml(b'<!DOCTYPE manifest [<!ENTITY a "x">]><manifest/>')

    def test_reject_wrong_root(self):
        with self.assertRaises(ValueError):
            manifest_xml(b"<notmanifest/>")


class Blueprint(unittest.TestCase):
    def test_header_only_fixture(self):
        result = dex_header(synthetic_dex())
        self.assertTrue(result["sha1_matches"])
        self.assertTrue(result["adler32_matches"])
        self.assertEqual(result["sections"]["methods"], 0)

    def test_corrupt_checksum(self):
        data = synthetic_dex()
        data[12] ^= 1
        result = dex_header(data)
        self.assertFalse(result["sha1_matches"])
        self.assertFalse(result["adler32_matches"])

    def test_section_bounds(self):
        data = synthetic_dex()
        struct.pack_into("<II", data, 56, 1, 1000)
        with self.assertRaises(ValueError):
            dex_header(data)

    def test_truncated(self):
        with self.assertRaises(ValueError):
            dex_header(b"dex\n035\x00")


class Native(unittest.TestCase):
    def test_abi_match(self):
        result = elf_header(synthetic_elf(), "arm64-v8a")
        self.assertTrue(result["abi_matches"])
        self.assertTrue(result["shared_object"])

    def test_abi_mismatch(self):
        self.assertFalse(elf_header(synthetic_elf(), "x86_64")["abi_matches"])

    def test_truncated(self):
        with self.assertRaises(ValueError):
            elf_header(synthetic_elf()[:20], "arm64-v8a")


class Seal(unittest.TestCase):
    @patch("tools.static_experiments.tool", return_value=None)
    def test_missing_sdk(self, mocked):
        self.assertIsNone(exp005(Path("fixture.apk"), {"sha256": "x"})["signature_verified"])

    @patch("tools.static_experiments.tool", return_value="apksigner")
    @patch("tools.static_experiments.command", return_value=(1, "verification failed"))
    def test_invalid_signature(self, cmd, sdk):
        self.assertEqual(exp005(Path("fixture.apk"), {"sha256": "x"})["status"], "fail")

    @patch("tools.static_experiments.tool", return_value="apksigner")
    @patch("tools.static_experiments.command", return_value=(0, "verified"))
    def test_verified_signature(self, cmd, sdk):
        self.assertTrue(exp005(Path("fixture.apk"), {"sha256": "x"})["signature_verified"])


class Awakening(unittest.TestCase):
    def test_explicit_emulator_only(self):
        with self.assertRaises(ValueError):
            runtime(Path("fixture.apk"), "physical-device")

    @patch("run_all.tool", return_value="adb")
    @patch("run_all.command", side_effect=[(0, "device"), (0, "package:/existing.apk")])
    def test_existing_app_not_replaced(self, cmd, adb):
        self.assertEqual(runtime(Path("fixture.apk"), "emulator-5554")["status"], "skip")
        self.assertEqual(cmd.call_count, 2)

    @patch("run_all.tool", return_value="adb")
    @patch("run_all.command", side_effect=[(0, "device"), (1, ""), (0, "Success"),
                                          (0, ""), (0, "Status: ok\nTotalTime: 120\n"),
                                          (0, "TOTAL PSS: 12345")])
    def test_telemetry_parser(self, cmd, adb):
        result = runtime(Path("fixture.apk"), "emulator-5554", samples=1)
        self.assertEqual(result["status"], "pass")
        self.assertEqual(result["median_startup_ms"], 120)
        self.assertEqual(result["median_pss_kib"], 12345)


if __name__ == "__main__":
    unittest.main()
