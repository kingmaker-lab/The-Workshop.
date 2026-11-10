#!/usr/bin/env python3
"""Ensure Flutter's included Gradle build resolves Kotlin plugins from Maven Central.

Flutter 3.47.9's bundled Gradle included-build settings declare dependency
repositories, but not pluginManagement repositories. The Gradle Plugin Portal
may fail to proxy Kotlin artifacts needed by the kotlin-dsl plugin.
This changes only the disposable CI Flutter SDK checkout, never app sources.
"""
import os
from pathlib import Path

root = os.environ.get("FLUTTER_ROOT")
if not root:
    raise SystemExit("FLUTTER_ROOT missing; run after installing Flutter")

file = Path(root) / "packages/flutter_tools/gradle/settings.gradle.kts"
if not file.is_file():
    raise SystemExit("Missing Flutter Gradle settings file")

original = file.read_text(encoding="utf-8")
if original.startswith("pluginManagement {"):
    if "mavenCentral()" not in original.split("dependencyResolutionManagement", 1)[0]:
        raise SystemExit("Plugin repositories already customized; inspect manually")
    print("Flutter plugin repositories already configured")
elif original.startswith("dependencyResolutionManagement {"):
    prefix = """pluginManagement {
    repositories {
        google()
        mavenCentral()
        gradlePluginPortal()
    }
}

"""
    file.write_text(prefix + original, encoding="utf-8")
    print("Enabled Maven Central for Flutter included-build plugin resolution")
else:
    raise SystemExit("Unexpected Flutter settings template; no changes made")
