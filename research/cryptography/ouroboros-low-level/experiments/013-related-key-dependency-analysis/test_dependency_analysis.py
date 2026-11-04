"""Tests for the EXP-013 KS1 dependency and related-key analyzer."""
import csv
import json
import tempfile
import unittest
from pathlib import Path

from dependency_analysis import (
    analyze, bit_pair_analysis, dense_byte_delta_scan, joint_metrics,
    output_bitplanes, sample_keys, save_results, schedule_stream, verify_telescoping_xor_identity,\n    invert_internal_state_transition, recover_master_keys_from_schedule,
)


class Exp013Tests(unittest.TestCase):
    def test_exact_subkey_telescoping_xor_identity(self):
        for key in (0, 1, 0x01234567, 0x89ABCDEF, 0xFFFFFFFF):
            self.assertTrue(verify_telescoping_xor_identity(key))

    def test_internal_state_transition_inverse(self):
        for key in (0, 1, 0x01234567, 0x89ABCDEF, 0xFFFFFFFF):
            state = key
            for round_index, t_value in enumerate(internal_t_sequence(key)):
                next_state = ((state << 8) & 0xFFFFFFFF) | t_value
                self.assertEqual(invert_internal_state_transition(next_state, round_index), state)
                state = next_state

    def test_schedule_preimage_recovery_with_256_initial_byte_guesses(self):
        keys = (0, 1, 0x01234567, 0x89ABCDEF, 0xFFFFFFFF)
        for master_key in keys:
            schedule = expand_key(master_key)
            candidates = recover_master_keys_from_schedule(schedule)
            self.assertIn(master_key, candidates)
            self.assertTrue(all(expand_key(candidate) == schedule for candidate in candidates))

    def test_schedule_preimage_recovery_rejects_malformed_schedule(self):
        with self.assertRaises(ValueError):
            recover_master_keys_from_schedule((0, 1, 2))
        with self.assertRaises(ValueError):
            recover_master_keys_from_schedule((0,) * 7 + (256,))

    def test_sample_is_deterministic_and_pins_corner_keys(self):
        a = sample_keys(64, 12345)
        b = sample_keys(64, 12345)
        self.assertEqual(a, b)
        self.assertEqual(a[0], 0)
        self.assertEqual(a[1], 0xFFFFFFFF)

    def test_joint_metrics_perfect_equal_and_complement(self):
        # 8 samples; low 4 bits set for A, B equals A or its complement.
        a = int("00001111", 2)
        equal = joint_metrics(a, a, 8)
        complement = joint_metrics(a, ((1 << 8) - 1) ^ a, 8)
        self.assertAlmostEqual(equal["pearson"], 1.0)
        self.assertAlmostEqual(complement["pearson"], -1.0)
        self.assertAlmostEqual(equal["mutual_information_bits"], 1.0)
        self.assertAlmostEqual(complement["mutual_information_bits"], 1.0)

    def test_pair_matrix_has_2016_unique_pairs(self):
        streams = [schedule_stream(key) for key in sample_keys(64, 7)]
        rows, summary = bit_pair_analysis(streams)
        self.assertEqual(len(rows), 64 * 63 // 2)
        self.assertEqual(summary["cross_round_pairs"], 28 * 64)
        self.assertEqual(summary["within_round_pairs"], 8 * (8 * 7 // 2))

    def test_dense_scan_covers_all_byte_deltas(self):
        rows = dense_byte_delta_scan(sample_keys(8, 11))
        self.assertEqual(len(rows), 4 * 255)
        for position in range(4):
            selected = [row for row in rows if row["master_key_byte_position"] == position]
            self.assertEqual(len(selected), 255)
            self.assertEqual({row["byte_delta"] for row in selected}, set(range(1, 256)))

    def test_analysis_has_expected_shapes(self):
        report = analyze(64, 16, 123)
        self.assertEqual(len(report["master_key_to_round_key_bit_dependencies"]["rows"]), 32 * 64)
        self.assertEqual(len(report["unit_related_key_deltas"]), 32)
        self.assertEqual(len(report["dense_byte_delta_scan"]["rows"]), 1020)
        self.assertEqual(report["cross_round_and_output_bit_dependencies"]["output_bit_pairs"], 2016)

    def test_csv_and_json_serialization(self):
        report = analyze(64, 16, 123)
        with tempfile.TemporaryDirectory() as tmp:
            save_results(report, Path(tmp))
            for name in (
                "summary.json", "summary_compact.json", "output_bit_dependencies.csv",
                "master_to_subkey_dependencies.csv", "related_key_unit_deltas.csv",
                "dense_byte_delta_scan.csv",
            ):
                self.assertTrue((Path(tmp) / name).is_file())
            with (Path(tmp) / "dense_byte_delta_scan.csv").open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(len(rows), 1020)
            parsed = json.loads((Path(tmp) / "summary_compact.json").read_text(encoding="utf-8"))
            self.assertEqual(parsed["experiment"], "OUROBOROS-013")


if __name__ == "__main__":
    unittest.main()
