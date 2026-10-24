#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ÉcoleMax — Module de paiements (Wave + Orange Money Sénégal)
- Mode sandbox automatique sans clés (simulation)
- Mode réel avec clés marchand (env vars)
- Webhooks + vérification
"""
import base64
import hashlib
import hmac
import json
import os
import secrets
import urllib.request

# ---------------------------------------------------------------- config
def cfg(name, default=""):
    return os.environ.get(name, default)

WAVE_API_KEY = cfg("WAVE_API_KEY")
WAVE_BASE = cfg("WAVE_BASE_URL", "https://api.wave.com")
ORANGE_CLIENT_ID = cfg("ORANGE_CLIENT_ID")
ORANGE_CLIENT_SECRET = cfg("ORANGE_CLIENT_SECRET")
ORANGE_MERCHANT_KEY = cfg("ORANGE_MERCHANT_KEY")
ORANGE_BASE = cfg("ORANGE_BASE_URL", "https://api.orange-sonatel.com")
PUBLIC_BASE_URL = cfg("PUBLIC_BASE_URL", "http://localhost:8000")
WAVE_WEBHOOK_SECRET = cfg("WAVE_WEBHOOK_SECRET", "ecolemax-webhook-secret")

def _post(url, data, headers=None):
    req = urllib.request.Request(url, data=json.dumps(data).encode(),
                                 headers={"Content-Type": "application/json", **(headers or {})})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode())

def _post_form(url, data, headers=None):
    req = urllib.request.Request(url, data=urllib.parse.urlencode(data).encode(),
                                 headers={"Content-Type": "application/x-www-form-urlencoded", **(headers or {})})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode())

# ---------------------------------------------------------------- Wave
def creer_checkout_wave(montant, reference):
    """Crée une session de paiement Wave. Retourne l'URL de checkout."""
    if WAVE_API_KEY:
        try:
            data = {
                "amount": str(int(montant)),
                "currency": "XOF",
                "client_reference": reference,
                "success_url": f"{PUBLIC_BASE_URL}/paiement-reussi?ref={reference}",
                "error_url": f"{PUBLIC_BASE_URL}/paiement-echoue?ref={reference}",
            }
            r = _post(WAVE_BASE + "/v1/checkout/sessions", data,
                      headers={"Authorization": "Bearer " + WAVE_API_KEY})
            url = r.get("checkout_url") or r.get("wave_launch_url") or r.get("url") or ""
            if url:
                return {"canal": "Wave", "url": url, "statut": "en_attente", "reel": True}
        except Exception as e:
            return {"canal": "Wave", "url": "", "statut": "erreur", "erreur": str(e)[:80], "reel": True}
    # Sandbox : lien simulé
    return {"canal": "Wave", "url": f"https://send.wave.sn/ecolemax/{reference}", "statut": "en_attente", "reel": False}

def verifier_paiement_wave(reference):
    """Interroge le statut de la session Wave."""
    if not WAVE_API_KEY or not reference:
        return None
    try:
        req = urllib.request.Request(
            WAVE_BASE + f"/v1/checkout/sessions/{reference}",
            headers={"Authorization": "Bearer " + WAVE_API_KEY})
        with urllib.request.urlopen(req, timeout=20) as r:
            d = json.loads(r.read().decode())
        return d.get("status")
    except Exception:
        return None

def webhook_wave_valide(payload, signature):
    """Vérifie la signature HMAC-SHA256 du webhook Wave."""
    if not signature:
        return False
    message = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()
    expected = hmac.new(WAVE_WEBHOOK_SECRET.encode(), message, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)

# ---------------------------------------------------------------- Orange Money
def _token_orange():
    if not (ORANGE_CLIENT_ID and ORANGE_CLIENT_SECRET):
        return None
    try:
        auth = base64.b64encode((ORANGE_CLIENT_ID + ":" + ORANGE_CLIENT_SECRET).encode()).decode()
        r = _post_form(ORANGE_BASE + "/oauth/v3/token",
                       {"grant_type": "client_credentials"},
                       headers={"Authorization": "Basic " + auth})
        return r.get("access_token")
    except Exception:
        return None

def creer_checkout_orange(montant, order_id):
    """Crée un paiement Orange Money. Retourne l'URL de paiement."""
    token = _token_orange()
    if token:
        try:
            data = {
                "merchant_key": ORANGE_MERCHANT_KEY,
                "currency": "XOF",
                "order_id": order_id,
                "amount": int(montant),
                "return_url": f"{PUBLIC_BASE_URL}/paiement-reussi?ref={order_id}",
                "cancel_url": f"{PUBLIC_BASE_URL}/paiement-echoue?ref={order_id}",
                "notif_url": f"{PUBLIC_BASE_URL}/api/payments/orange/notif",
                "lang": "fr",
            }
            r = _post(ORANGE_BASE + "/webpayment", data,
                      headers={"Authorization": "Bearer " + token})
            url = r.get("payment_url") or r.get("redirectUrl") or ""
            if url:
                return {"canal": "Orange Money", "url": url, "statut": "en_attente", "reel": True}
        except Exception as e:
            return {"canal": "Orange Money", "url": "", "statut": "erreur", "erreur": str(e)[:80], "reel": True}
    # Sandbox : lien simulé
    return {"canal": "Orange Money", "url": f"https://pay.orange.sn/ecolemax/{order_id}", "statut": "en_attente", "reel": False}

def status_paiements():
    return {
        "wave": {"reel": bool(WAVE_API_KEY), "base": WAVE_BASE},
        "orange": {"reel": bool(ORANGE_CLIENT_ID), "base": ORANGE_BASE},
        "public_base": PUBLIC_BASE_URL,
    }

def generer_reference():
    return "EM-" + secrets.token_hex(6).upper()
