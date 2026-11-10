import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).with_name("prepare_flutter_gradle_repos.py").resolve()


class FlutterGradleRepoPatchTests(unittest.TestCase):
    def test_adds_plugin_repositories_once(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "packages/flutter_tools/gradle/settings.gradle.kts"
            path.parent.mkdir(parents=True)
            original = "dependencyResolutionManagement {\\n repositories { mavenCentral() }\\n}\\n".replace("\\n", "\n")
            path.write_text(original)
            env = {**os.environ, "FLUTTER_ROOT": td}
            for _ in range(2):
                subprocess.run([sys.executable, str(SCRIPT)], env=env, check=True,
                               capture_output=True, text=True)
            data = path.read_text()
            self.assertEqual(data.count("pluginManagement {"), 1)
            self.assertEqual(data.count("dependencyResolutionManagement {"), 1)
            self.assertIn("gradlePluginPortal()", data.split("dependencyResolutionManagement", 1)[0])

    def test_unknown_template_is_not_modified(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "packages/flutter_tools/gradle/settings.gradle.kts"
            path.parent.mkdir(parents=True)
            path.write_text("unexpected template")
            env = {**os.environ, "FLUTTER_ROOT": td}
            res = subprocess.run([sys.executable, str(SCRIPT)], env=env,
                                 capture_output=True, text=True)
            self.assertNotEqual(res.returncode, 0)
            self.assertEqual(path.read_text(), "unexpected template")


if __name__ == "__main__":
    unittest.main()
