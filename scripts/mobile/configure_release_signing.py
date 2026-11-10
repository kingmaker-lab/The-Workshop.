#!/usr/bin/env python3
"""Configure signing in Flutter-generated Android Kotlin Gradle without storing secrets."""
from pathlib import Path
import os

required = (
    "ACADEMY_KEYSTORE_PATH",
    "ACADEMY_STORE_PASSWORD",
    "ACADEMY_KEY_PASSWORD",
    "ACADEMY_KEY_ALIAS",
)
for name in required:
    if not os.environ.get(name):
        raise SystemExit(f"Required signing environment variable is missing: {name}")

gradle_path = Path("android/app/build.gradle.kts")
if not gradle_path.is_file():
    raise SystemExit("Flutter Android project was not generated")
text = gradle_path.read_text(encoding="utf-8")
for marker in (
    'signingConfig = signingConfigs.getByName("debug")',
    "    buildTypes {",
    "targetSdk = flutter.targetSdkVersion",
    "compileSdk = flutter.compileSdkVersion",
    "ndkVersion = flutter.ndkVersion",
):
    if text.count(marker) != 1:
        raise SystemExit("Unexpected generated Android Gradle template; aborting")

text = text.replace("targetSdk = flutter.targetSdkVersion", "targetSdk = 36")
text = text.replace("compileSdk = flutter.compileSdkVersion", "compileSdk = 36")
text = text.replace("ndkVersion = flutter.ndkVersion", 'ndkVersion = "29.0.14206865"')
text = text.replace(
    "    buildTypes {",
    """
    signingConfigs {
        create("release") {
            storeFile = file(System.getenv("ACADEMY_KEYSTORE_PATH"))
            storePassword = System.getenv("ACADEMY_STORE_PASSWORD")
            keyAlias = System.getenv("ACADEMY_KEY_ALIAS")
            keyPassword = System.getenv("ACADEMY_KEY_PASSWORD")
        }
    }

    buildTypes {""",
    1,
)
text = text.replace(
    'signingConfig = signingConfigs.getByName("debug")',
    'signingConfig = signingConfigs.getByName("release")',
    1,
)
gradle_path.write_text(text, encoding="utf-8")
print("Release signing configured; targetSdk=36; compileSdk=36; NDK=29")
