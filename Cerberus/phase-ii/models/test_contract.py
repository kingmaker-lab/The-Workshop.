import struct
import subprocess
import unittest


ENCODERS = [
    ["java", "-cp", "build", "Frame"],
    ["build/frame-pascal"],
]


def encode(command, operation, *words):
    return subprocess.run([*command, operation, *map(str, words)],
                          capture_output=True, timeout=5)


def verdict(frame):
    return subprocess.run(["build/gate"], input=frame, capture_output=True, timeout=5)


class BinaryContract(unittest.TestCase):
    def check_cases(self, operation, opcode, cases):
        for words, expected in cases:
            payload = struct.pack("<IIII", opcode, *words)
            for encoder in ENCODERS:
                with self.subTest(words=words, encoder=encoder[0]):
                    result = encode(encoder, operation, *words)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertEqual(result.stdout, payload)
                    gate = verdict(result.stdout)
                    self.assertEqual(gate.returncode, expected)
                    self.assertEqual((gate.stdout, gate.stderr), (b"", b""))

    def test_admission(self):
        self.check_cases("admission", 1, [
            ((0, 2, 3), 0),
            ((1, 2, 3), 1),
            ((1, 3, 3), 1),
            ((0, 3, 3), 2),
            ((0, 0xffffffff, 1), 2),
            ((0, 9999, 10000), 0),
            ((0, 0, 0), 64),
            ((0, 0, 10001), 64),
            ((2, 0, 1), 64),
        ])

    def test_recovery(self):
        self.check_cases("recovery", 2, [
            ((3, 3, 0), 0),
            ((3, 2, 0), 1),
            ((3, 3, 3), 2),
            ((3, 3, 4), 2),
            ((0, 0, 0), 2),
            ((0xfffffffe, 0xfffffffe, 0x80000000), 0),
            ((0xffffffff, 0xffffffff, 0xfffffffe), 3),
        ])

    def test_invalid_encoder_input(self):
        for encoder in ENCODERS:
            for args in [("unknown", 0, 0, 0), ("admission", "+0", 0, 1),
                         ("admission", 0, "-1", 1), ("recovery", 0, 0, 4294967296),
                         ("recovery", 0, ""), ("recovery", 0, 0, ""),
                         ("recovery", "00000000000", 0, 0)]:
                with self.subTest(encoder=encoder[0], args=args):
                    result = encode(encoder, *args)
                    self.assertEqual(result.returncode, 64)
                    self.assertEqual(result.stdout, b"")

    def test_gate_rejects_incomplete_extra_and_unknown_frames(self):
        valid_frame = struct.pack("<IIII", 1, 0, 0, 1)
        for frame in (b"", valid_frame[:8], valid_frame[:15], valid_frame + b"x",
                      struct.pack("<IIII", 3, 0, 0, 0)):
            with self.subTest(frame=frame):
                self.assertEqual(verdict(frame).returncode, 64)
