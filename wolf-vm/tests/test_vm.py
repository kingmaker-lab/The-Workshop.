import struct
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BIN = ROOT / "build" / "wolfvm"


def run_file(data, *args):
    with tempfile.TemporaryDirectory() as directory:
        program = Path(directory) / "program.wvm"
        program.write_bytes(data)
        return subprocess.run([str(BIN), *args, str(program)], text=True, capture_output=True, timeout=5)


def binary(code):
    return struct.pack("<4sBBHI", b"WVM1", 1, 0, 0, len(code)) + code


class VMTests(unittest.TestCase):
    def run_example(self, name):
        program = ROOT / "build" / "examples" / f"{name}.wvm"
        return subprocess.run([str(BIN), str(program)], text=True, capture_output=True, timeout=5)

    def test_arithmetic(self):
        p = self.run_example("arith")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("R0=8", p.stdout)

    def test_call_and_return(self):
        p = self.run_example("function")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("R0=14", p.stdout)
        self.assertIn("SP=0", p.stdout)

    def test_loop(self):
        p = self.run_example("loop")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("R0=0", p.stdout)

    def test_memory(self):
        p = self.run_example("memory")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("R1=31337", p.stdout)

    def test_wrong_magic(self):
        p = run_file(b"ABCD" + binary(b"\x01")[4:])
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("formato", p.stderr)

    def test_wrong_version(self):
        p = run_file(struct.pack("<4sBBHI", b"WVM1", 2, 0, 0, 1) + b"\x01")
        self.assertNotEqual(p.returncode, 0)

    def test_wrong_length(self):
        p = run_file(struct.pack("<4sBBHI", b"WVM1", 1, 0, 0, 20) + b"\x01")
        self.assertNotEqual(p.returncode, 0)

    def test_unknown_instruction(self):
        p = run_file(binary(b"\xff"))
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("opcode", p.stderr)

    def test_truncated_instruction(self):
        p = run_file(binary(b"\x10\x00\x00"))
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("truncada", p.stderr)

    def test_register_bounds(self):
        p = run_file(binary(b"\x10\x08\x00\x00\x00\x00\x01"))
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("registrador invalido", p.stderr)

    def test_jump_into_immediate(self):
        # JMP address=2, then HALT. PC=2 lies inside JMP's address argument.
        p = run_file(binary(b"\x40\x02\x00\x00\x00\x01"))
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("salto invalido", p.stderr)

    def test_stack_underflow(self):
        p = run_file(binary(b"\x51\x00\x01"))
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("stack underflow", p.stderr)

    def test_stack_overflow(self):
        # PUSH R0; JMP 0 forever, until stack full.
        p = run_file(binary(b"\x50\x00\x40\x00\x00\x00\x00"), "--max-steps", "1000")
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("stack overflow", p.stderr)

    def test_infinite_loop_step_budget(self):
        p = run_file(binary(b"\x40\x00\x00\x00\x00"), "--max-steps", "17")
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("limite de execucao", p.stderr)

    def test_invalid_return(self):
        # Push R0=2, RET to invalid byte at address 2 (inside MOVI immediate).
        p = run_file(binary(b"\x10\x00\x02\x00\x00\x00\x50\x00\x53"))
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("RET tentou", p.stderr)

    def test_unaligned_memory(self):
        p = run_file(binary(b"\x60\x00\x01\x00\x01"))
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("desalinhado", p.stderr)

    def test_trace(self):
        program = ROOT / "build" / "examples" / "arith.wvm"
        p = subprocess.run([str(BIN), "--trace", str(program)], text=True, capture_output=True, timeout=5)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("[TRACE]", p.stdout)


if __name__ == "__main__":
    unittest.main()
