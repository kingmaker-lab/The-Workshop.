"""Tests for non-invasive Science catalog validation."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from science.validate import CATALOG, ROOT, validate, render_markdown


class ScienceCatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = json.loads(CATALOG.read_text(encoding="utf-8"))

    def test_current_inventory(self):
        self.assertEqual([], validate(self.catalog, ROOT))

    def test_duplicate_id(self):
        data = copy.deepcopy(self.catalog)
        data["projects"].append(copy.deepcopy(data["projects"][0]))
        self.assertTrue(any("duplicate id" in e for e in validate(data, ROOT)))

    def test_missing_path(self):
        data = copy.deepcopy(self.catalog)
        data["projects"][0]["source_path"] = "not-a-real-research-project"
        self.assertTrue(any("missing source_path" in e for e in validate(data, ROOT)))

    def test_path_traversal(self):
        data = copy.deepcopy(self.catalog)
        data["projects"][0]["source_path"] = "../outside"
        self.assertTrue(any("unsafe or invalid source_path" in e for e in validate(data, ROOT)))

    def test_invalid_maturity(self):
        data = copy.deepcopy(self.catalog)
        data["projects"][0]["maturity"] = "production-ready"
        self.assertTrue(any("invalid maturity" in e for e in validate(data, ROOT)))

    def test_command_requires_tests(self):
        data = copy.deepcopy(self.catalog)
        data["projects"][0]["tests_path"] = None
        self.assertTrue(any("without tests_path" in e for e in validate(data, ROOT)))

    def test_report_never_claims_tests_passed(self):
        report = render_markdown(self.catalog)
        self.assertIn("SCI-001", report)
        self.assertIn("command documented", report)
        self.assertNotIn("tests passed", report.lower())


if __name__ == "__main__":
    unittest.main()
