"""ARGUS v0.4 Sigma-shaped bounded subset: opt-in, fail-closed, deterministic."""
import tempfile
import unittest
from pathlib import Path

from argus.core.normalizer import normalize_event
from argus.detection.sigma_subset import (
    SigmaSubsetEngine, SigmaSubsetError, parse_sigma_subset,
)
from argus.main import PROJECT_DIR, build_engine


def event(**changes):
    record = dict(timestamp="2026-11-09T13:00:00Z", source="linux",
                  event="authentication", src_ip="192.0.2.4",
                  user="root", result="success", message="SSHD accepted key")
    record.update(changes)
    return normalize_event(record)


def rule(condition="selection", selection=None, **override):
    selectors = selection or "    User: root\n    Result: success\n"
    base = f"""title: Demo rule
id: argus-demo-test
logsource:
  product: argus
  category: authentication
detection:
  selection:
{selectors}  filter:
    SourceIp: '127.0.0.1'
  condition: {condition}
level: high
"""
    for old, new in override.items():
        base = base.replace(old, new)
    return base.encode()


class SigmaSubsetTests(unittest.TestCase):
    def test_sample_rule_maps_to_normalized_events(self):
        engine = SigmaSubsetEngine.from_directory(PROJECT_DIR / "sigma/rules")
        alert = engine.evaluate(event())
        self.assertEqual(len(alert), 1)
        self.assertEqual(alert[0].name, "sigma:argus-v04-privileged-ssh")
        self.assertEqual(alert[0].severity, "high")
        self.assertEqual(alert[0].score, 55)
        self.assertEqual(alert[0].details["engine"], "sigma_subset_v04")
        self.assertFalse(engine.evaluate(event(user="alice")))
        self.assertFalse(engine.evaluate(event(src_ip="127.0.0.1")))
        self.assertFalse(engine.evaluate(event(event="network_connection")))

    def test_exact_and_string_modifiers_with_boolean_condition(self):
        text = rule("selection and not filter").replace(
            b"    User: root\n    Result: success",
            b"    User|startswith: RO\n    Message|contains: ACCEPTED\n    Result|endswith: ccess",
        )
        parsed = parse_sigma_subset(text)
        self.assertTrue(parsed.matches(event()))
        self.assertFalse(parsed.matches(event(user="administrator")))
        self.assertFalse(parsed.matches(event(src_ip="127.0.0.1")))
        self.assertFalse(parsed.matches(event(message="Rejected key")))

    def test_selector_alternatives_and_condition_patterns(self):
        text = rule("1 of selection_* and not filter").replace(
            b"  selection:\n    User: root\n    Result: success\n",
            b"  selection_user:\n    User: root\n  selection_network:\n    SourceIp: '192.0.2.20'\n",
        )
        parsed = parse_sigma_subset(text)
        self.assertTrue(parsed.matches(event(user="root")))
        self.assertTrue(parsed.matches(event(user="x", src_ip="192.0.2.20")))
        self.assertFalse(parsed.matches(event(user="x", src_ip="192.0.2.30")))
        text2 = text.replace(b"1 of selection_*", b"all of selection_*")
        self.assertTrue(parse_sigma_subset(text2).matches(event(src_ip="192.0.2.20")))
        self.assertFalse(parse_sigma_subset(text2).matches(event(src_ip="192.0.2.21")))
        grouped = rule("(selection or filter) and not filter")
        self.assertTrue(parse_sigma_subset(grouped).matches(event()))

    def test_list_of_mappings_and_value_alternatives(self):
        text = rule().replace(
            b"  selection:\n    User: root\n    Result: success\n",
            b"  selection:\n    - User: [root, admin]\n      Result: success\n    - User: service\n      Result: failed\n",
        )
        parsed = parse_sigma_subset(text)
        self.assertTrue(parsed.matches(event(user="ADMIN")))
        self.assertTrue(parsed.matches(event(user="service", result="failed")))
        self.assertFalse(parsed.matches(event(user="guest")))

    def test_reject_unsupported_conditions_modifiers_and_fields(self):
        variations = (
            (b"condition: selection", b"condition: selection | eval(os.system('x'))"),
            (b"condition: selection", b"condition: 2 of them"),
            (b"condition: selection", b"condition: unknown"),
            (b"condition: selection", b"condition: 1 of nonexistent_*"),
            (b"condition: selection", b"condition: all of selection_*"),
            (b"User: root", b"CommandLine: root"),
            (b"User: root", b"User|re: root"),
            (b"User: root", b"User|contains|all: root"),
            (b"User: root", b"User: r*ot"),
            (b"User: root", b"User: null"),
            (b"User: root", b"User: {foo: bar}"),
            (b"category: authentication", b"category: process_creation"),
            (b"product: argus", b"product: windows"),
            (b"category: authentication", b"service: sshd"),
            (b"User: root", b"User: &a root"),
            (b"User: root", b"User: [root, *a]"),
            (b"User: root", b"User: root\n    User: admin"),
        )
        for old, replacement in variations:
            with self.subTest(replacement=replacement), self.assertRaises(
                (SigmaSubsetError, ValueError)
            ):
                parse_sigma_subset(rule().replace(old, replacement))

    def test_multidocument_and_oversized_rule_rejected(self):
        for payload in (rule() + b"---\ntitle: Other\n", b"x" * 32769,
                        b"[]", b"title: hello\n"):
            with self.assertRaises(SigmaSubsetError):
                parse_sigma_subset(payload)

    def test_rules_directory_limits_and_duplicate_ids(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with self.assertRaises(SigmaSubsetError):
                SigmaSubsetEngine.from_directory(root)
            (root / "one.yml").write_bytes(rule())
            self.assertEqual(len(SigmaSubsetEngine.from_directory(root).rules), 1)
            (root / "two.yml").write_bytes(rule().replace(b"Demo rule", b"Other"))
            with self.assertRaisesRegex(SigmaSubsetError, "duplicate Sigma rule ID"):
                SigmaSubsetEngine.from_directory(root)
            (root / "two.yml").unlink()
            (root / "one.yml").unlink()
            link = root / "one.yml"
            link.symlink_to(PROJECT_DIR / "sigma/rules/lnx_argus_privileged_auth.yml")
            with self.assertRaisesRegex(SigmaSubsetError, "symlinks"):
                SigmaSubsetEngine.from_directory(root)

    def test_opt_in_pipeline_preserves_existing_yaml(self):
        config = {"enabled": True, "rules_dir": str(PROJECT_DIR / "sigma/rules")}
        engine = build_engine(PROJECT_DIR / "rules/default.yaml",
                              {"window_seconds": 30, "failure_threshold": 15}, {},
                              config)
        result = engine.process(event())
        self.assertIsNotNone(result)
        names = {d.name for d in result.detections}
        self.assertIn("sigma:argus-v04-privileged-ssh", names)
        self.assertIn("privileged_successful_authentication", names)
        disabled = build_engine(PROJECT_DIR / "rules/default.yaml", {}, {}, {})
        result_without = disabled.process(event())
        self.assertFalse(any(d.name.startswith("sigma:") for d in result_without.detections))
        with self.assertRaises(SigmaSubsetError):
            build_engine(PROJECT_DIR / "rules/default.yaml", {}, {},
                         {"enabled": True, "rules_dir": "/missing/sigma"})

    def test_numeric_network_fields_not_coerced(self):
        data = rule().replace(b"category: authentication", b"category: network_connection").replace(
            b"    User: root\n    Result: success",
            b"    OrigBytes: 512\n    Protocol: tcp",
        )
        parsed = parse_sigma_subset(data)
        self.assertTrue(parsed.matches(event(event="network_connection",
                                              orig_bytes=512, protocol="TCP")))
        self.assertFalse(parsed.matches(event(event="network_connection",
                                               orig_bytes="512", protocol="tcp")))


if __name__ == "__main__":
    unittest.main()
