#!/usr/bin/env bash
# ============================================================
# ÉcoleMax — Build APK Android (gratuit)
# Usage :
#   1) bash build-apk.sh            (vérifie l'environnement)
#   2) bash build-apk.sh --eas       → build EAS (clique/cloud)
#   3) bash build-apk.sh --capacitor → build local Capacitor + Android Studio
# ============================================================
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
APP="$ROOT/app-expo"
OUT="$ROOT"

echo "📦 ÉcoleMax — Build APK"
echo "======================"

# ---- 0. Vérifications ----
command -v python3 >/dev/null || { echo "❌ python3 requis"; exit 1; }
python3 -c "import ast; ast.parse(open('$ROOT/backend/serveur.py').read())" || { echo "❌ serveur.py syntaxe invalide"; exit 1; }
echo "✅ serveur.py syntaxe OK"

for f in "$APP"/App.js "$APP"/api.js "$APP"/screens/*.js; do
  [ -f "$f" ] && node --check "$f" || true
done
command -v node >/dev/null || { echo "⚠️ node non trouvé — installer Node.js pour build EAS/Capacitor"; }
echo "✅ app Expo syntaxe vérifiée"

# ---- 1. Point vers la version en ligne ----
echo "🌐 Vérification de l'API en ligne..."
LINE=$(grep -o "API_BASE = '[^']*'" "$APP/api.js" | head -1 | sed "s/API_BASE = '//;s/'//")
echo "   API_BASE = $LINE"
case "$LINE" in
  *localhost*|*127.0.0.1*)
     echo "⚠️ API_BASE pointe encore vers localhost — changer pour l'URL de déploiement avant le build !"
     read -r -p "   URL de l'API (oui/non pour continuer) : " URL
     if [ -n "$URL" ]; then
       sed -i "s|API_BASE = '[^']*'|API_BASE = '$URL'|" "$APP/api.js"
       echo "   → API_BASE = $URL"
     fi ;;
esac

# ---- 2. Build EAS ----
if [ "${1:-}" = "--eas" ]; then
  echo "☁️  Build EAS (gratuit pour les builds internes)..."
  cd "$APP"
  [ -f package.json ] || { echo "❌ pas de package.json"; exit 1; }
  command -v eas >/dev/null || { echo "Installer : npm i -g @expo/eas-cli && eas login"; exit 1; }
  eas build --platform android --profile production --output-dir "$OUT"
  echo "✅ APK généré dans $OUT"
  exit 0
fi

# ---- 3. Build Capacitor ----
if [ "${1:-}" = "--capacitor" ]; then
  echo "🛠️  Build Capacitor (local, Android Studio)..."
  cd "$APP"
  [ -f package.json ] || { echo "❌ pas de package.json"; exit 1; }
  npm install
  npm install @capacitor/core @capacitor/cli
  npx cap init ÉcoleMax app.ecolemax --web-dir=dist || true
  npx expo export --platform android
  npx cap add android || true
  npx cap copy
  echo "✅ Ouvrir Android Studio : npx cap open android"
  echo "   APK → android/app/build/outputs/apk/debug/app-debug.apk"
  exit 0
fi

echo ""
echo "Options : --eas | --capacitor"
echo "Étapes : héberger backend → mettre API_BASE en ligne → build APK → héberger l'APK sur le site"
