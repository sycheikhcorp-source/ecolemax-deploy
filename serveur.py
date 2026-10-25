#!/usr/bin/env python3
"""ÉcoleMax — Lanceur gunicorn via serveur.py (compat Render)"""
import os, subprocess, sys

PORT = os.environ.get("PORT", "8000")
cmd = ["gunicorn", "-w", "4", "-b", f"0.0.0.0:{PORT}", "--timeout", "120", "app:app"]
print(f"[serveur.py] Lancement gunicorn sur port {PORT}...")
print(f"[serveur.py] Commande: {' '.join(cmd)}")
subprocess.run(cmd, check=True)
