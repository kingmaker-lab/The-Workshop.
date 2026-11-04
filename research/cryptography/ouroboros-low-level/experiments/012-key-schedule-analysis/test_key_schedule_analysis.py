"""Regression and structural tests for OUROBOROS EXP-012."""
import sys
import tempfile
import unittest
from pathlib import Path

EXP008 = Path(__file__).resolve().parent.parent / "008-reduced-feistel"
sys.path.insert(0, str(EXP008))

from feistel16 import KEY_MASK, ROUNDS, expand_key
from key_schedule_analysis import (
    analyze, deterministic_keys, expand_key_reference, ks1_transition,
    round_constant, save_results,
)


class Exp012Tests(unittest.TestCase):
    def test_reference_transcription_matches_canonical_schedule(self):
        for key in (0, 1, 0x01234567, 0x89ABCDEF, KEY_MASK):
            self.assertEqual(expand_key_reference(key), expand_key(key))

    def test_round_constants_are_correct_and_distinct(self):
        values = [round_constant(r) for r in range(ROUNDS)]
        self.assertEqual(values, [0x9D, 0xDA, 0x17, 0x54, 0x91, 0xCE, 0x0B, 0x48])
        self.assertEqual(len(set(values)), ROUNDS)

    def test_fixed_context_transition_is_a_permutation_in_a(self):
        contexts = (
            (0x00, 0x00, 0x00), (0x12, 0x34, 0x56),
            (0xFF, 0xA5, 0x5A), (0x80, 0x01, 0xFE),
        )
        for round_index in range(ROUNDS):
            for b, c, d in contexts:
                outputs = set()
                key_bytes = set()
                for a in range(256):
                    state = (a << 24) | (b << 16) | (c << 8) | d
                    next_state, round_key = ks1_transition(state, round_index)
                    outputs.add(next_state & 0xFF)
                    key_bytes.add(round_key)
                self.assertEqual(len(outputs), 256)
                self.assertEqual(len(key_bytes), 256)

    def test_transition_matches_next_state_bytes(self):
        state = 0x12345678
        for r in range(ROUNDS):
            next_state, round_key = ks1_transition(state, r)
            self.assertEqual((next_state >> 24) & 0xFF, (state >> 16) & 0xFF)
            self.assertEqual((next_state >> 16) & 0xFF, (state >> 8) & 0xFF)
            self.assertEqual((next_state >> 8) & 0xFF, state & 0xFF)
            state = next_state
            self.assertEqual(round_key, expand_key_reference(0x12345678)[r])

    def test_deterministic_sample_pins_corner_keys(self):
        first = deterministic_keys(128, 0xABC)
        second = deterministic_keys(128, 0xABC)
        self.assertEqual(first, second)
        self.assertEqual(first[0], 0)
        self.assertEqual(first[1], KEY_MASK)

    def test_analysis_shape_and_reference_crosscheck(self):
        report = analyze(128, 0xABC)
        self.assertTrue(report["independent_reference_implementation_matches"])
        self.assertEqual(len(report["avalanche_matrix"]), 32 * 64)
        self.assertEqual(len(report["related_key_deltas"]), 32 + 10)
        self.assertEqual(len(report["round_key_byte_statistics"]), ROUNDS)
        self.assertEqual(report["output_stream_bit_correlations"]["pair_count"], 64 * 63 // 2)

    def test_result_serialization(self):
        report = analyze(64, 1234)
        with tempfile.TemporaryDirectory() as tmp:
            save_results(report, Path(tmp))
            expected = (
                "summary.json", "avalanche_matrix.csv",
                "related_key_deltas.csv", "round_key_statistics.csv",
            )
            for name in expected:
                self.assertTrue((Path(tmp) / name).is_file())


if __name__ == "__main__":
    unittest.main()
