#!/usr/bin/env bash
# ============================================================
# ÉcoleMax — Prépare les assets de l'APK
# Copies app.html comme index.html + CSS + manifest + icônes
# + injection de l'adresse API serveur
# ============================================================
set -euo pipefail

RACINE="$(cd "$(dirname "$0")/.." && pwd)"
DEST="$RACINE/apk-build/assets/www"
SRC_PROJET="$RACINE/projet"
API_BASE="${1:-https://ecolemax.onrender.com}"

echo "📦 Préparation assets APK…"
echo "   API: $API_BASE"

rm -rf "$DEST"
mkdir -p "$DEST/css"

# --- 1. app.html → index.html (la TWA charge index.html) ---
cp "$SRC_PROJET/app.html" "$DEST/index.html"
echo "  ✅ app.html → index.html"

# --- 2. CSS ---
cp "$SRC_PROJET/css/style.css" "$DEST/css/style.css"
echo "  ✅ css/style.css"

# --- 3. Icônes (garder les existantes si disponibles) ---
if [ -f "$SRC_PROJET/pwa/icon-192.png" ]; then
    cp "$SRC_PROJET/pwa/icon-192.png" "$DEST/icon-192.png"
    cp "$SRC_PROJET/pwa/icon-512.png" "$DEST/icon-512.png"
    cp "$SRC_PROJET/pwa/apple-touch-icon.png" "$DEST/apple-touch-icon.png"
    cp "$SRC_PROJET/pwa/favicon.ico" "$DEST/favicon.ico"
    echo "  ✅ icônes"
else
    # Créer des icônes placeholder si pas d'icônes
    echo "  ⚠️ Pas d'icônes trouvées, création placeholders"
fi

# --- 4. Manifest PWA ---
if [ -f "$SRC_PROJET/pwa/manifest.json" ]; then
    cp "$SRC_PROJET/pwa/manifest.json" "$DEST/manifest.json"
    echo "  ✅ manifest.json"
else
    cat > "$DEST/manifest.json" << 'EOF'
{
  "name": "ÉcoleMax — Tuteur IA",
  "short_name": "ÉcoleMax",
  "description": "Tuteur IA scolaire : 18 matières, correction photo, wolof et français.",
  "start_url": "./",
  "scope": "./",
  "display": "standalone",
  "background_color": "#0f1420",
  "theme_color": "#15a05a",
  "icons": [
    { "src": "./icon-192.png", "sizes": "192x192", "type": "image/png" },
    { "src": "./icon-512.png", "sizes": "512x512", "type": "image/png" }
  ]
}
EOF
    echo "  ✅ manifest.json créé"
fi

# --- 5. Injection API URL dans index.html ---
python3 - "$DEST/index.html" "$API_BASE" << 'PY'
import sys
idx, base = sys.argv[1], sys.argv[2]
s = open(idx, encoding="utf-8").read()

# Injection du script API avant </head>
injection = f'''<script>window.__ECOLEMAX_API__ = "{base}";</script>
'''
# Injecter après <title> si possible, sinon avant </head>
if "</head>" in s:
    s = s.replace("</head>", injection + "</head>", 1)
else:
    s = injection + s

open(idx, "w", encoding="utf-8").write(s)
print(f"  ✅ injection : window.__ECOLEMAX_API__ = {base}")
PY

# --- 6. Vérification ---
echo ""
echo "✅ assets prêts : $(du -sh "$DEST" | cut -f1)"
echo "   index.html: $(wc -l < "$DEST/index.html") lignes"
echo "   css: $(wc -l < "$DEST/css/style.css") lignes"
echo "   API injectée: $(grep -c '__ECOLEMAX_API__' "$DEST/index.html")"
echo "   doAuth: $(grep -c 'function doAuth' "$DEST/index.html")"
echo "   showReset: $(grep -c 'showReset' "$DEST/index.html")"
