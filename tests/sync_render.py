#!/usr/bin/env python3
"""Synchroniser ecolemax.db vers Render"""
import os
import sys

REPO = "/home/user/deploy"
REMOTE_DB = os.path.join(REPO, "app.db")
LOCAL_DB = os.path.join(REPO, "ecolemax.db")

if not os.path.exists(LOCAL_DB):
    print(f"❌ Base locale non trouvée: {LOCAL_DB}")
    sys.exit(1)

if os.path.exists(REMOTE_DB):
    os.remove(REMOTE_DB)
    print(f"🗑️  Base Render supprimée")

import shutil
shutil.copy2(LOCAL_DB, REMOTE_DB)
print(f"✅ Base copiée: {LOCAL_DB} -> {REMOTE_DB}")

size_mb = os.path.getsize(REMOTE_DB) / 1024 / 1024
print(f"📦 Taille: {size_mb:.1f} MB")

print("\n⚠️  Pousser vers GitHub pour déployer sur Render...")
print("  git add app.db && git commit -m 'sync base' && git push")
