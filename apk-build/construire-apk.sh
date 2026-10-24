#!/usr/bin/env bash
# ============================================================
# ÉcoleMax — construction de l'APK sans Gradle
# (aapt2 → javac → d8 → zipalign → apksigner)
# Usage : bash construire-apk.sh
# ============================================================
set -euo pipefail

RACINE="$(cd "$(dirname "$0")" && pwd)"
SDK="${ANDROID_HOME:-/home/user/android-sdk}"
JAVA_BIN="${JAVA_HOME:-/tmp/jdk-17.0.21+9}/bin"
BUILD_TOOLS="$(ls -d "$SDK"/build-tools/* | sort -V | tail -1)"
PLATEFORME="$(ls -d "$SDK"/platforms/android-* | sort -V | tail -1)"
ANDROID_JAR="$PLATEFORME/android.jar"

AAPT2="$BUILD_TOOLS/aapt2"
D8="$BUILD_TOOLS/d8"
ZIPALIGN="$BUILD_TOOLS/zipalign"
APKSIGNER="$BUILD_TOOLS/apksigner"
KEYTOOL="$JAVA_BIN/keytool"

SORTIE="$RACINE/sortie"
NOM="EcoleMax-1.0.0"

echo "📦 ÉcoleMax — build APK"
echo "   build-tools : $(basename "$BUILD_TOOLS")"
echo "   plateforme  : $(basename "$PLATEFORME")"
echo ""

rm -rf "$SORTIE"
mkdir -p "$SORTIE"/{res-compile,classes,dex,gen,apk}

# ---- 1. Ressources ----
echo "1/7 Compilation des ressources…"
"$AAPT2" compile --dir "$RACINE/res" -o "$SORTIE/res-compile/" >/dev/null

echo "2/7 Édition des liens…"
"$AAPT2" link \
  -o "$SORTIE/base.ap_" \
  -I "$ANDROID_JAR" \
  --manifest "$RACINE/AndroidManifest.xml" \
  --java "$SORTIE/gen" \
  --min-sdk-version 23 \
  --target-sdk-version 34 \
  --version-code 1 \
  --version-name 1.0.0 \
  -A "$RACINE/assets" \
  "$SORTIE"/res-compile/*.flat

# ---- 2. Java ----
echo "3/7 Compilation Java…"
find "$RACINE/src" "$SORTIE/gen" -name "*.java" > "$SORTIE/sources.txt"
"$JAVA_BIN/javac" -encoding UTF-8 -source 8 -target 8 \
  -bootclasspath "$ANDROID_JAR" \
  -classpath "$ANDROID_JAR" \
  -d "$SORTIE/classes" \
  @"$SORTIE/sources.txt" 2>&1 | grep -v "bootstrap class path" || true

# ---- 3. DEX ----
echo "4/7 Conversion en DEX…"
find "$SORTIE/classes" -name "*.class" > "$SORTIE/classes.txt"
"$D8" --lib "$ANDROID_JAR" --min-api 23 --output "$SORTIE/dex" @"$SORTIE/classes.txt"

# ---- 4. Assemblage ----
echo "5/7 Assemblage de l'APK…"
cp "$SORTIE/base.ap_" "$SORTIE/apk/app.apk"
cd "$SORTIE/dex"
zip -q "$SORTIE/apk/app.apk" classes.dex
cd "$RACINE"

# ---- 5. Alignement (optionnel si libc++ absent) ----
echo "6/7 Alignement…"
if "$ZIPALIGN" -f 4 "$SORTIE/apk/app.apk" "$SORTIE/apk/$NOM-non-signe.apk" 2>/dev/null; then
    : # alignement réussi
else
    echo "   ⚠️ zipalign indisponible (libc++ absent) → alignement sauté"
    cp "$SORTIE/apk/app.apk" "$SORTIE/apk/$NOM-non-signe.apk"
fi

# ---- 6. Signature ----
echo "7/7 Signature…"
KEYSTORE="$RACINE/ecolemax.keystore"
if [ ! -f "$KEYSTORE" ]; then
  echo "   création de la clé de signature…"
  "$KEYTOOL" -genkeypair -v \
    -keystore "$KEYSTORE" \
    -storetype JKS \
    -alias ecolemax \
    -keyalg RSA -keysize 2048 -validity 10000 \
    -storepass ecolemax2026 -keypass ecolemax2026 \
    -dname "CN=EcoleMax, OU=Mobile, O=EcoleMax, L=Dakar, C=SN" >/dev/null 2>&1
fi

"$APKSIGNER" sign \
  --ks "$KEYSTORE" --ks-type JKS --ks-key-alias ecolemax \
  --ks-pass pass:ecolemax2026 --key-pass pass:ecolemax2026 \
  --out "$SORTIE/$NOM.apk" \
  "$SORTIE/apk/$NOM-non-signe.apk"

"$APKSIGNER" verify --print-certs "$SORTIE/$NOM.apk" | head -3

echo ""
echo "✅ APK prêt : $SORTIE/$NOM.apk"
ls -lh "$SORTIE/$NOM.apk"
"$BUILD_TOOLS/aapt2" dump badging "$SORTIE/$NOM.apk" 2>/dev/null | head -3

# ---- 8. Bundle Play Store (AAB) ----
# Le format AAB exige les ressources au format "proto" (aapt2 --proto-format).
BUNDLETOOL="/tmp/bundletool.jar"
if [ -f "$BUNDLETOOL" ]; then
  echo ""
  echo "8/8 Bundle Play Store (AAB)…"
  MOD="$SORTIE/module"
  rm -rf "$MOD" && mkdir -p "$MOD"
  aapt2_link() {
    "$AAPT2" link -o "$MOD/base.apk" -I "$ANDROID_JAR" \
      --manifest "$RACINE/AndroidManifest.xml" --proto-format \
      --min-sdk-version 23 --target-sdk-version 34 \
      --version-code 1 --version-name 1.0.0 \
      -A "$RACINE/assets" \
      "$SORTIE"/res-compile/*.flat
  }
  rm -rf "$SORTIE/res-proto" && mkdir -p "$SORTIE/res-proto"
  "$AAPT2" compile --dir "$RACINE/res" -o "$SORTIE/res-proto/" >/dev/null
  "$AAPT2" link -o "$MOD/base.apk" -I "$ANDROID_JAR" \
    --manifest "$RACINE/AndroidManifest.xml" --proto-format \
    --min-sdk-version 23 --target-sdk-version 34 \
    --version-code 1 --version-name 1.0.0 \
    -A "$RACINE/assets" \
    "$SORTIE"/res-proto/*.flat
  cd "$MOD" && unzip -q base.apk -d tmp && cd tmp
  mkdir -p manifest res dex assets
  mv AndroidManifest.xml manifest/ 2>/dev/null || true
  mv resources.pb . 2>/dev/null || true
  [ -f classes.dex ] && mv classes.dex dex/ || true
  cd "$MOD/tmp" && rm -f classes.dex && zip -qr "$SORTIE/module.zip" . && cd "$RACINE"
  cp "$SORTIE/dex/classes.dex" "$MOD/tmp/dex/classes.dex"
  cd "$MOD/tmp" && rm -f "$SORTIE/module.zip" && zip -qr "$SORTIE/module.zip" . && cd "$RACINE"
  "$JAVA_BIN/java" -jar "$BUNDLETOOL" build-bundle \
    --output="$SORTIE/$NOM.aab" --modules="$SORTIE/module.zip" --overwrite
  # Signature JAR de l'AAB
  "$JAVA_BIN/jarsigner" -keystore "$KEYSTORE" -storepass ecolemax2026 -keypass ecolemax2026 \
    -sigalg SHA256withRSA -digestalg SHA-256 "$SORTIE/$NOM.aab" ecolemax
  echo "   ✅ AAB : $SORTIE/$NOM.aab"
  ls -lh "$SORTIE/$NOM.aab"
else
  echo ""
  echo "8/8 bundletool absent → AAB non construit"
fi
