"""Structural test: the core may not import adapters, database drivers, transport or filesystem."""
from pathlib import Path
import ast
import unittest


SRC = Path(__file__).resolve().parents[1] / "src" / "cerberus02"
FORBIDDEN = {"sqlite3", "argparse", "json", "pathlib", "http", "os", "subprocess"}


class DependencyRuleTests(unittest.TestCase):
    def test_domain_ports_usecases_have_no_outside_dependencies(self):
        for filename in ("domain.py", "ports.py", "usecases.py"):
            with self.subTest(module=filename):
                tree = ast.parse((SRC / filename).read_text(encoding="utf-8"))
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            self.assertNotIn(alias.name.split(".")[0], FORBIDDEN)
                            self.assertFalse(alias.name.startswith("cerberus02.adapters"))
                    if isinstance(node, ast.ImportFrom):
                        self.assertNotIn((node.module or "").split(".")[0], FORBIDDEN)
                        self.assertFalse("adapters" in (node.module or "").split("."))


if __name__ == "__main__":
    unittest.main()
