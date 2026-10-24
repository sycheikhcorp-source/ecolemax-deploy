#!/usr/bin/env python3
"""Génère les QR codes ÉcoleMax.

Usage :
    python3 qr.py https://votre-url.trycloudflare.com
    python3 qr.py https://... --sortie /chemin/mon-qr.svg
"""
import sys, os, qrcode, qrcode.image.svg

ICI = os.path.dirname(os.path.abspath(__file__))
PROJET = os.path.abspath(os.path.join(ICI, ".."))

BASE = "http://localhost:8000"
SORTIE = None
CIBLE = None

args = sys.argv[1:]
i = 0
while i < len(args):
    a = args[i]
    if a == "--sortie" and i + 1 < len(args):
        SORTIE = args[i + 1]
        i += 2
    elif a == "--url" and i + 1 < len(args):
        CIBLE = args[i + 1]
        i += 2
    else:
        BASE = a.rstrip("/")
        i += 1

CIBLES = {
    "qr-app.svg":          f"{BASE}/pwa/index.html",   # application élève (PWA installable)
    "qr-site.svg":         f"{BASE}/",                 # site vitrine
    "qr-dashboard.svg":    f"{BASE}/dashboard.html",   # tableau de bord
    "qr-telecharger.svg":  f"{BASE}/telecharger.html", # page de téléchargement
    "qr-apk.svg":          f"{BASE}/EcoleMax-1.0.0.apk",  # téléchargement direct de l'APK
}

if CIBLE:
    CIBLES = {"qr-apk.svg": CIBLE}

for nom, url in CIBLES.items():
    img = qrcode.make(url, image_factory=qrcode.image.svg.SvgPathImage,
                      box_size=12, border=2)
    chemin = SORTIE if SORTIE else os.path.join(PROJET, nom)
    with open(chemin, "wb") as f:
        img.save(f)
    print(f"✅ {os.path.basename(chemin):22s} → {url}")
