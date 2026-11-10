import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).with_name("configure_release_signing.py").resolve()
TEMPLATE = '''plugins {}
android {
    compileSdk = flutter.compileSdkVersion
    defaultConfig {
        targetSdk = flutter.targetSdkVersion
    }
    buildTypes {
        release {
            signingConfig = signingConfigs.getByName("debug")
        }
    }
}
'''

class ReleaseSigningTest(unittest.TestCase):
    def test_injects_release_signing_without_leaking_secrets(self):
        with tempfile.TemporaryDirectory() as td:
            gradle = Path(td, "android", "app", "build.gradle.kts")
            gradle.parent.mkdir(parents=True)
            gradle.write_text(TEMPLATE)
            env = {**os.environ,
                "ACADEMY_KEYSTORE_PATH": "/tmp/placeholder-keystore.p12",
                "ACADEMY_STORE_PASSWORD": "not-a-real-store-secret",
                "ACADEMY_KEY_PASSWORD": "not-a-real-key-secret",
                "ACADEMY_KEY_ALIAS": "academy"}
            p = subprocess.run([sys.executable, str(SCRIPT)],
                cwd=td, env=env, capture_output=True, text=True, check=True)
            out = gradle.read_text()
            self.assertIn('targetSdk = 36', out)
            self.assertIn('compileSdk = 36', out)
            self.assertIn('signingConfigs.getByName("release")', out)
            for secret in ["not-a-real-store-secret","not-a-real-key-secret"]:
                self.assertNotIn(secret, out)
                self.assertNotIn(secret, p.stdout)

    def test_refuses_incomplete_signing_environment(self):
        with tempfile.TemporaryDirectory() as td:
            gradle = Path(td, "android", "app", "build.gradle.kts")
            gradle.parent.mkdir(parents=True)
            gradle.write_text(TEMPLATE)
            env = os.environ.copy()
            for name in ("ACADEMY_KEYSTORE_PATH", "ACADEMY_STORE_PASSWORD",
                         "ACADEMY_KEY_PASSWORD", "ACADEMY_KEY_ALIAS"):
                env.pop(name, None)
            p = subprocess.run([sys.executable, str(SCRIPT)],
                cwd=td, env=env, capture_output=True, text=True)
            self.assertNotEqual(p.returncode, 0)
            self.assertEqual(gradle.read_text(), TEMPLATE)

if __name__ == "__main__":
    unittest.main()
