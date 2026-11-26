#!/usr/bin/env bash
set -euo pipefail
umask 077
cd "$(dirname "$0")/.."
: "${ANDROID_SDK_ROOT:?Set ANDROID_SDK_ROOT}"
: "${BUILD_TOOLS_VERSION:?Set BUILD_TOOLS_VERSION, e.g. 35.0.0}"
BT="$ANDROID_SDK_ROOT/build-tools/$BUILD_TOOLS_VERSION"
JAR="$ANDROID_SDK_ROOT/platforms/android-35/android.jar"
OUT="$(mktemp -d "$PWD/.pulse-build.XXXXXX")"
echo "Build directory: $OUT" >&2
mkdir "$OUT/classes" "$OUT/dex"
"$BT/aapt2" link -I "$JAR" --manifest fixtures/AndroidManifest.xml -o "$OUT/base.apk"
javac -source 8 -target 8 -classpath "$JAR" -d "$OUT/classes" fixtures/MainActivity.java
"$BT/d8" --min-api 23 --lib "$JAR" --output "$OUT/dex" "$OUT/classes/lab/workshop/pulsefixture/MainActivity.class"
if [[ -n "${NDK_CLANG_DIR:-}" ]]; then
    mkdir -p "$OUT/native/arm64-v8a" "$OUT/native/x86_64"
    "$NDK_CLANG_DIR/aarch64-linux-android23-clang" -shared -fPIC fixtures/native.c -o "$OUT/native/arm64-v8a/libpulsefixture.so"
    "$NDK_CLANG_DIR/x86_64-linux-android23-clang" -shared -fPIC fixtures/native.c -o "$OUT/native/x86_64/libpulsefixture.so"
fi
python3 - "$OUT" <<'PY'
import sys, zipfile
from pathlib import Path
out = Path(sys.argv[1])
with zipfile.ZipFile(out / "base.apk", "a") as z:
    z.write(out / "dex/classes.dex", "classes.dex", compress_type=zipfile.ZIP_STORED)
    for lib in sorted((out / "native").glob("*/*.so")):
        z.write(lib, "lib/" + lib.relative_to(out / "native").as_posix(), compress_type=zipfile.ZIP_STORED)
PY
"$BT/zipalign" -f 4 "$OUT/base.apk" "$OUT/aligned.apk"
keytool -genkeypair -alias pulse-test -keyalg RSA -keysize 2048 -validity 365 -dname "CN=Pulse Local Fixture" -keystore "$OUT/test.p12" -storetype PKCS12 -storepass pulse-test-only -keypass pulse-test-only >/dev/null
"$BT/apksigner" sign --ks "$OUT/test.p12" --ks-pass pass:pulse-test-only --out "$OUT/pulse-fixture.apk" "$OUT/aligned.apk"
"$BT/apksigner" verify "$OUT/pulse-fixture.apk"
echo "APK: $OUT/pulse-fixture.apk"
