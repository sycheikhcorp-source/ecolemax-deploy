#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ÉcoleMax — Backend API (Python standard, sans dépendances)
Serveur : API REST + static (dashboard) sur le même port.
Base de données : SQLite.
Sécurité : hachage mots de passe, tokens, limites par plan, contenu protégé, logs.
"""
import json
import os
import re
import secrets
import sqlite3
import sys
import hashlib
import random
import time
import urllib.request
import urllib.parse
from datetime import datetime, timedelta
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(os.path.dirname(BASE_DIR), "projet")
if not os.path.isdir(STATIC_DIR):
    STATIC_DIR = os.path.join(BASE_DIR, "projet")  # Fallback pour déploiement Render
if not os.path.isdir(STATIC_DIR):
    STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(BASE_DIR))), "projet")
DB_PATH = os.path.join(BASE_DIR, "ecolemax.db")
HOST = "0.0.0.0"
PORT = int(os.environ.get("PORT", 8000))  # Render/Koyeb fournissent $PORT
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "ecolemax2026")

def is_admin(handler):
    """Vérifie le mot de passe admin via header X-Admin-Password."""
    return handler.headers.get("X-Admin-Password", "") == ADMIN_PASSWORD

# Optional real AI (OpenAI-compatible). Set OPENAI_API_KEY to enable.
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_BASE = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
POLLINATIONS_KEY = os.environ.get("POLLINATIONS_KEY", "")
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY", "")

# Paiements (clés marchand en production)
import reponses_locales
from paiements import (creer_checkout_wave, creer_checkout_orange,
                       verifier_paiement_wave, webhook_wave_valide,
                       generer_reference, status_paiements, WAVE_WEBHOOK_SECRET)

PROMPT_SYSTEME = (
    "Tu es « Mon Tuteur », l'assistant IA d'ÉcoleMax pour les élèves du Sénégal (primaire, collège, lycée).\n"
    "LANGUE : réponds en français. Si l'élève demande le wolof (ou si la notion est difficile), "
    "explique aussi en wolof (traduction idiomatique, pas mot à mot).\n"
    "DISCIPLINE :\n"
    "1. Reste dans le cadre du programme sénégalais/français et du niveau demandé.\n"
    "2. Réponds toujours étape par étape ; aucune étape ne doit être sautée.\n"
    "3. MATHS/PHYSIQUE : calcule, puis VERIFIE ton résultat (recalcule à l'envers ou autre méthode) et affiche la vérification.\n"
    "4. LANGUES : traduction fidèle + explication des termes difficiles.\n"
    "5. RECHERCHE (faits, dates, biographies, définitions) : réponds avec précision et termine par « Source : [domaine] » ; si tu n'es pas sûr, dis « Je vérifie » et propose une recherche.\n"
    "6. RÉDACTION/DISSERTATION : structure (intro/développement/conclusion), plan, idées, reformulation, anti-plagiat.\n"
    "7. Sois bref, clair, pédagogique ; utilise des listes/étapes ; jamais d'invention.\n"
    "FORMAT : réponse directe d'abord, puis « Explication » puis « Étapes » si nécessaire."
)

# ------------------------------------------------------------------
# Base de données
# ------------------------------------------------------------------
def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    c = db()
    # Migration: ajouter colonnes email/telephone/bloque si elles n'existent pas
    cols = [r["name"] for r in c.execute("PRAGMA table_info(users)").fetchall()]
    if "email" not in cols:
        c.execute("ALTER TABLE users ADD COLUMN email TEXT")
    if "telephone" not in cols:
        c.execute("ALTER TABLE users ADD COLUMN telephone TEXT")
    if "bloque" not in cols:
        c.execute("ALTER TABLE users ADD COLUMN bloque INTEGER DEFAULT 0")
    c.commit()
    c.executescript("""
    CREATE TABLE IF NOT EXISTS plans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT UNIQUE NOT NULL,
        nom TEXT NOT NULL,
        prix REAL NOT NULL,
        duree_jours INTEGER NOT NULL,
        limite_ia_jour INTEGER NOT NULL,
        photo_jour INTEGER NOT NULL,
        telechargement INTEGER NOT NULL,
        download_quota INTEGER NOT NULL DEFAULT 0,
        description TEXT
    );
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pseudo TEXT UNIQUE NOT NULL,
        mot_de_passe TEXT NOT NULL,
        niveau TEXT, ville TEXT, langue TEXT DEFAULT 'fr',
        plan_id INTEGER, date_expiration TEXT,
        token TEXT UNIQUE, date_creation TEXT,
        parrain_id INTEGER,
        email TEXT,
        telephone TEXT,
        bloque INTEGER DEFAULT 0
    );
    CREATE TABLE IF NOT EXISTS password_reset (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pseudo TEXT NOT NULL,
        code TEXT NOT NULL,
        date_creation TEXT,
        date_expiration TEXT
    );
    CREATE TABLE IF NOT EXISTS payment_links (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        plan_id INTEGER NOT NULL,
        canal TEXT NOT NULL,
        url TEXT NOT NULL,
        montant REAL NOT NULL,
        statut TEXT DEFAULT 'en_attente',
        reference TEXT,
        date_creation TEXT, date_activation TEXT
    );
    CREATE TABLE IF NOT EXISTS sujets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nom TEXT NOT NULL, icone TEXT
    );
    CREATE TABLE IF NOT EXISTS chapitres (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sujet_id INTEGER NOT NULL,
        nom TEXT NOT NULL,
        contenu TEXT
    );
    CREATE TABLE IF NOT EXISTS exercices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chapitre_id INTEGER NOT NULL,
        type TEXT, question TEXT, reponse TEXT, explication TEXT
    );
    CREATE TABLE IF NOT EXISTS ai_usage (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER, action TEXT, tokens INTEGER, cout REAL, date TEXT
    );
    CREATE TABLE IF NOT EXISTS security_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER, type TEXT, detail TEXT, date TEXT
    );
    CREATE TABLE IF NOT EXISTS usage_journaliere (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER, date TEXT, count INTEGER DEFAULT 0
    );
    CREATE UNIQUE INDEX IF NOT EXISTS idx_usage_unique ON usage_journaliere(user_id, date);
    CREATE TABLE IF NOT EXISTS admin_config (
        key TEXT PRIMARY KEY, value TEXT
    );
    """)
    c.executescript("""
    INSERT OR IGNORE INTO plans (code, nom, prix, duree_jours, limite_ia_jour, photo_jour, telechargement, download_quota, description) VALUES
    ('gratuit',    'Essai gratuit 24 h', 0,     1,   24,   1, 1, 5, 'Essai 24 h : 24 questions IA/jour · 1 photo/jour · tout débloqué'),
    ('15jours',    '15 jours',          250,    15,  30,   0, 0, 0, '30 questions IA/jour · correction texte · pas de téléchargement hors ligne'),
    ('mensuel',    'Mensuel',           500,    30,  150,  5, 0, 5, '150 questions IA/jour · photo 5/jour · téléchargement limité (5 chap/mois)'),
    ('illimité',   'Illimité',         1500,    30,  1000, 100, 1, 100, 'Tout illimité · IA · photo · téléchargement · rédactions'),
    ('pack3mois',  'Pack 3 mois',      1200,    90,  1000, 100, 1, 100, 'Tout illimité · 90 jours'),
    ('packbac',    'Pack Bac',         3000,   180,  1000, 100, 1, 100, 'Tout illimité · 6 mois + annales');
    """)
    # Démo : un abonné actif
    if c.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0:
        c.execute("""INSERT INTO users (pseudo, mot_de_passe, niveau, ville, langue, plan_id, date_expiration, token, date_creation)
                     VALUES (?,?,?,?,?,?,?,?,?)""",
                  ("fatimatou", hash_mdp("fatimatou"), "Lycée", "Dakar", "fr", 3,
                   (datetime.now()+timedelta(days=20)).strftime("%Y-%m-%d"),
                   secrets.token_hex(16), datetime.now().strftime("%Y-%m-%d")))
        c.execute("""INSERT INTO payment_links (user_id, plan_id, canal, url, montant, statut, reference, date_creation, date_activation)
                     VALUES (1, 3, 'Wave', 'https://send.wave.sn/ecolemax/500fcfa-fatimatou', 500, 'valide', 'EM-DEMO1', datetime('now'), datetime('now'))""")
    c.execute("""INSERT OR IGNORE INTO sujets (id, nom, icone) VALUES
                (1,'Mathématiques','🧮'),(2,'Français','🇫🇷'),(3,'Physique-Chimie','🔬'),
                (4,'SVT','🧬'),(5,'Histoire-Géographie','🌍'),(6,'Anglais','🇬🇧'),
                (7,'Espagnol','🇳🇪'),(8,'Arabe','🕌'),(9,'Wolof','🗣️'),
                (10,'Philosophie','🎓'),(11,'Latin','📜'),(12,'Économie','💰'),
                (13,'Technologie','💻'),(14,'Arts','🎨'),(15,'EPS','⚽'),
                (16,'Éducation morale et civique','⚖️'),(17,'Peul','🐄'),(18,'Sèrer','🌾')""")
    c.execute("""INSERT OR IGNORE INTO chapitres (id, sujet_id, nom, contenu) VALUES
                (1,1,'Fonction exponentielle','f(x)=a·bˣ · propriétés · équations'),
                (2,1,'Fonction logarithme','Logarithme décimal et népérien · propriétés'),
                (3,1,'Équations et inéquations','Méthodes de résolution'),
                (4,1,'Géométrie : le triangle','Angles · théorèmes · calculs'),
                (5,1,'Statistiques','Diagrammes · moyenne · médiane'),
                (6,2,'Le genre','Nom, adjectif, pronom'),
                (7,2,'Le verbe','Conjugaison · temps · modes'),
                (8,2,'La phrase','Syntaxe · accords · ponctuation'),
                (9,2,'Le vocabulaire','Thèmes · dictionnaire'),
                (10,3,'Optique','Réflexion · réfraction'),
                (11,3,'Électricité','Loi d''Ohm · circuits'),
                (12,3,'Mécanique','Forces · mouvement'),
                (13,4,'La cellule','Structure · fonctions'),
                (14,4,'Sang et circulation','Cœur · vaisseaux'),
                (15,4,'Système nerveux','Neurones · réflexes'),
                (16,5,'Le Sénégal','Histoire · géographie · institutions'),
                (17,5,'L''Afrique indépendante','Décolonisation · Etats'),
                (18,5,'Les climats','Types · facteurs'),
                (19,6,'Verbes irréguliers','Be, have, do, go'),
                (20,6,'Present perfect','Forme · usage'),
                (21,6,'Vocabulaire scolaire','Lecture · expression'),
                (22,7,'Ser et estar','Conjugaison · usage'),
                (23,7,'Vocabulaire','Thèmes courants'),
                (24,7,'Le présent','Conjugaison'),
                (25,8,'L''alphabet','Lettres · sons'),
                (26,8,'Salutations','Expressions'),
                (27,8,'Vocabulaire','Mots utiles'),
                (28,9,'Salutations','Expressions courantes'),
                (29,9,'L''alphabet','Lettres'),
                (30,9,'Vocabulaire','Thèmes'),
                (31,10,'La liberté','Définition · responsabilité'),
                (32,10,'La justice','Concepts · débat'),
                (33,10,'Le pouvoir','Formes · légitimité'),
                (34,11,'L''alphabet','Lettres · prononciation'),
                (35,11,'Les déclinaisons','Cas · rôles'),
                (36,11,'Vocabulaire','Mots latins courants'),
                (37,12,'Offre et demande','Concepts · marché'),
                (38,12,'La monnaie','Fonction · inflation'),
                (39,12,'Le budget familial','Revenus · dépenses'),
                (40,13,'Informatique','Matériel · logiciel'),
                (41,13,'Réseaux','Internet · sécurité'),
                (42,13,'Traitement de texte','Word processor'),
                (43,14,'Histoire de l''art','Périodes · mouvements'),
                (44,14,'Le dessin','Techniques · esquisse'),
                (45,15,'Règles du sport','Sports · arbitrage'),
                (46,15,'Santé et hygiene','Alimentation · hygiene'),
                (47,16,'La citoyenneté','Devoirs · droits'),
                (48,16,'Les droits de l''homme','Déclaration · applications'),
                (49,17,'Salutations','Expressions peules'),
                (50,17,'Vocabulaire','Thèmes peules'),
                (51,18,'Salutations','Expressions sèreres'),
                (52,18,'Vocabulaire','Thèmes sèreres')""")
    c.execute("""INSERT OR IGNORE INTO exercices (id, chapitre_id, type, question, reponse, explication) VALUES
                (1,1,'qcm','Soit f(x)=2·3ˣ. Calculer f(2).','18','f(2)=2·3²=2·9=18'),
                (2,1,'qcm','Résoudre 3ˣ=81.','x=4','3⁴=81 → x=4'),
                (3,1,'vf','La fonction 3ˣ est croissante.','Vrai','Base 3>1 → croissante'),
                (4,2,'qcm','Résoudre log(x)=2 (base 10).','x=100','10²=100'),
                (5,3,'qcm','Résoudre 2x+3=11.','x=4','2x=8 → x=4'),
                (6,3,'vf','La solution de x²=9 est x=3.','Vrai et Faux','x=3 ou x=-3'),
                (7,4,'qcm','Somme des angles d''un triangle ?','180°','Théorème de la somme'),
                (8,5,'qcm','Quelle est la moyenne de 4, 8, 12 ?','8','(4+8+12)/3=8'),
                (9,6,'qcm','Le mot « cheval » est masculin.','Vrai','Genre masculin'),
                (10,6,'qcm','« Les enfants » est :','pluriel','pluriel de enfant'),
                (11,7,'qcm','Conjuguer : je mangeais (imparfait).','Verbe manger à l''imparfait','radical mang- + ais'),
                (12,7,'qcm','« J''ai mangé » est au :','passé composé','auxiliaire + participe'),
                (13,8,'qcm','Quelle phrase est correcte ?','« Le livre du professeur. »','accords et place des compléments'),
                (14,10,'qcm','Réflexion : un rayon frappe un miroir plan. L''angle de réflexion est :','égal à l''angle d''incidence','loi de la réflexion'),
                (15,11,'qcm','Loi d''Ohm : V = ?','R·I','U=R×I'),
                (16,12,'qcm','Si la force et la masse doublent, l''accélération :','doit doubler','F=ma'),
                (17,13,'qcm','Que contient un neurone ?','Dendrites, axone','structure du neurone'),
                (18,16,'qcm','La capitale du Sénégal ?','Dakar','capitale'),
                (19,17,'qcm','La plupart des pays africains sont indépendants depuis :','1960','années 1960'),
                (20,19,'qcm','Conjuguer : I have eaten (present perfect).','J''ai mangé','have + participe passé'),
                (21,20,'qcm','« I have lived here » signifie :','J''ai habité ici','present perfect'),
                (22,22,'qcm','Conjuguer ser : yo ____.','soy','ser au présent'),
                (23,25,'qcm','L''arabe s''écrit :','de droite à gauche','écriture arabe'),
                (24,28,'qcm','« Sutub » en wolof signifie :','salut','salutation wolof'),
                (25,31,'qcm','Qui a dit « Je pense donc je suis » ?','Descartes','philosophie'),
                (26,34,'qcm','En latin, « amor » signifie :','l''amour','latin'),
                (27,37,'qcm','Quand la demande augmente, le prix :','augmente','loi de l''offre et demande'),
                (28,38,'qcm','La fonction de la monnaie sert à :','acheter, stocker, mesurer','fonctions de la monnaie'),
                (29,40,'qcm','Le CPU est le :','cerveau de l''ordinateur','informatique'),
                (30,43,'qcm','Qui a peint la Joconde ?','Léonard de Vinci','histoire de l''art'),
                (31,45,'qcm','Un match de football dure :','90 minutes','règles du sport'),
                (32,47,'qcm','Un citoyen a des droits et :','des devoirs','citoyenneté'),
                (33,48,'qcm','La Déclaration des droits de l''homme date de :','1789','histoire')""")

    c.commit()
    c.close()

def hash_mdp(m):
    salt = "ecolemax-salt-2026"
    return hashlib.sha256((salt + m).encode()).hexdigest()

def user_by_token(token):
    if not token: return None
    c = db()
    row = c.execute("SELECT * FROM users WHERE token=?", (token,)).fetchone()
    c.close()
    return row

def plan_valide(user):
    """Renvoie le plan actif de l'utilisateur (non expiré)."""
    if not user or not user["plan_id"]: return None
    if not user["date_expiration"]: return None
    try:
        if datetime.strptime(user["date_expiration"], "%Y-%m-%d") < datetime.now():
            return None
    except ValueError:
        return None
    c = db()
    p = c.execute("SELECT * FROM plans WHERE id=?", (user["plan_id"],)).fetchone()
    c.close()
    return p

def plan_actif(user):
    """Plan applicable : gratuit sans abonnement, ou abonnement payant actif."""
    if not user:
        return None
    c = db()
    if user["plan_id"]:
        p = c.execute("SELECT * FROM plans WHERE id=?", (user["plan_id"],)).fetchone()
        if p and p["code"] == "gratuit":
            # Essai gratuit de 24 h : expiré => plus d'accès
            if user["date_expiration"]:
                fin = datetime.strptime(user["date_expiration"][:10], "%Y-%m-%d")
                if fin < datetime.now():
                    c.close()
                    return None
            c.close()
            return p
        if p and user["date_expiration"] and datetime.strptime(user["date_expiration"], "%Y-%m-%d") >= datetime.now():
            c.close()
            return p
    else:
        p = c.execute("SELECT * FROM plans WHERE code='gratuit'").fetchone()
        c.close()
        return p
    c.close()
    return None

def ajout_usage_ia(user_id, action, tokens, cout):
    c = db()
    c.execute("INSERT INTO ai_usage (user_id, action, tokens, cout, date) VALUES (?,?,?,?,datetime('now'))",
              (user_id, action, tokens, cout))
    c.commit(); c.close()

def log_sec(user_id, type_, detail):
    c = db()
    c.execute("INSERT INTO security_logs (user_id, type, detail, date) VALUES (?,?,?,datetime('now'))",
              (user_id, type_, detail))
    c.commit(); c.close()

# ------------------------------------------------------------------
# Intelligence IA (multi-fournisseur + cache + repli)
# ------------------------------------------------------------------
_IA_CACHE = {}

def _repli_mock(question):
    """Repli hors ligne intelligent."""
    q = question.strip().lower()
    m = re.search(r"([0-9]+)\s*[·*]\s*([0-9]+)\s*\^\s*([0-9]+|x)", q)
    if m and ("calculer" in q or "f(" in q):
        a, b, e_str = float(m.group(1)), float(m.group(2)), m.group(3)
        if e_str == "x":
            fm = re.search(r"f\((\d+)\)", q)
            e = int(fm.group(1)) if fm else 2
        else:
            e = int(e_str)
        val = a * (b ** e)
        return {"reponse": f"✅ f = {int(val)}", "explication": f"{a}·{b}^{e} = {a}·{b**e} = {val}.",
                "etapes": [f"Calcul de {b} puissance {e} = {b**e}", f"Multiplication par {a}", f"Résultat = {val}"],
                "confiance": 0.99, "source": "IA hors ligne"}
    if "exclusif" in q or "inclusif" in q:
        return {"reponse": "Exclusif = éléments de A ou B sans les communs (A∪B − A∩B). Inclusif = A∪B avec tout.",
                "explication": "Exemple : A={1,2,3}, B={3,4,5} → inclusif=5, exclusif=4.",
                "etapes": ["Définition des ensembles", "Calcul de l'union", "Soustraction des communs"],
                "confiance": 0.98, "source": "IA hors ligne"}
    if "trad" in q:
        return {"reponse": "🌍 Traduction : « Le Sénégal est un pays d'Afrique de l'Ouest. »",
                "explication": "EN : « Senegal is a country in West Africa. » / ES : « Senegal es un país de África Occidental. »",
                "confiance": 0.97, "source": "IA hors ligne"}
    if "cheikh anta" in q:
        return {"reponse": "Cheikh Anta Diop (1923-1990) : historien, anthropologue et physicien sénégalais, figure du panafricanisme.",
                "explication": "Sources : biographies et sites académiques (recherche internet).",
                "confiance": 0.96, "source": "IA hors ligne"}
    return {"reponse": "Je peux t'aider : pose une question (maths, physique, français, explication, traduction, recherche, rédaction).",
            "explanation": "Essaie par exemple : « Explique la fonction exponentielle », « Qui était Cheikh Anta Diop ? », « Traduis cette phrase en espagnol ».",
            "confiance": 0.9, "source": "IA hors ligne"}
def _message_saturation():
    """Message utile quand aucun fournisseur ne répond et que la question est hors bibliothèque."""
    exemples = " · ".join(reponses_locales.suggestions()[:8])
    return {
        "reponse": (
            "🤖 Le service IA gratuit est momentanément saturé (beaucoup d'élèves en même temps).\n\n"
            "**En attendant, essaie ces sujets qui fonctionnent toujours hors connexion :**\n"
            f"{exemples}\n\n"
            "Réessaie dans 30 secondes pour ta question exacte."
        ),
        "confiance": 0, "source": "limite", "explication": "", "etapes": [],
    }

def _llm_messages(question):
    return [{"role": "system", "content": PROMPT_SYSTEME}, {"role": "user", "content": question}]

def _call_llm(messages, base, key, model, endpoint="/chat/completions", extra=None):
    body = {"model": model, "messages": messages, "max_tokens": 600}
    if extra:
        body.update(extra)
    req = urllib.request.Request(
        base + endpoint,
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json", "Authorization": "Bearer " + key})
    with urllib.request.urlopen(req, timeout=45) as r:
        return json.loads(r.read().decode())

def reponse_ia(question, plan):
    """Assistant IA réel : OpenAI -> Groq -> Gemini -> Pollinations (gratuit) -> repli."""
    # Cache (réduit les appels, limite les requêtes au service gratuit)
    cache_key = re.sub(r"\s+", " ", question.strip().lower())[:200]
    if cache_key in _IA_CACHE:
        cached = dict(_IA_CACHE[cache_key])
        cached["source"] = str(cached.get("source", "")) + " (cache)"
        return cached
    # 1. OpenAI / Groq (OpenAI-compatible)
    for key, base, model in ((OPENAI_API_KEY, OPENAI_BASE, OPENAI_MODEL),
                             (GROQ_API_KEY, "https://api.groq.com/openai/v1", GROQ_MODEL)):
        if key:
            try:
                data = _call_llm(_llm_messages(question), base, key, model)
                return {"reponse": data["choices"][0]["message"]["content"],
                        "confiance": 0.95, "source": "IA", "explication": "", "etapes": []}
            except Exception:
                pass
    # 2. Gemini
    if GEMINI_API_KEY:
        try:
            url = ("https://generativelanguage.googleapis.com/v1beta/models/"
                   "gemini-2.0-flash:generateContent?key=" + GEMINI_API_KEY)
            body = {"contents": [{"parts": [{"text": PROMPT_SYSTEME + "\n\nQuestion de l'élève : " + question}]}]}
            req = urllib.request.Request(url, data=json.dumps(body).encode(),
                                         headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=45) as r:
                data = json.loads(r.read().decode())
            txt = data["candidates"][0]["content"]["parts"][0]["text"]
            return {"reponse": txt, "confiance": 0.95, "source": "IA", "explication": "", "etapes": []}
        except Exception:
            pass
    # 3. Pollinations (gratuit, limite ~1/30s par IP sans clé)
    try:
        headers = {"Content-Type": "application/json"}
        if POLLINATIONS_KEY:
            headers["Authorization"] = "Bearer " + POLLINATIONS_KEY
        req = urllib.request.Request(
            "https://text.pollinations.ai/",
            data=json.dumps({"messages": _llm_messages(question), "model": "openai"}).encode(),
            headers=headers)
        with urllib.request.urlopen(req, timeout=45) as r:
            raw = r.read().decode()
        try:
            txt = json.loads(raw)["choices"][0]["message"]["content"]
        except Exception:
            txt = raw.strip()
        if "limit" in txt.lower() or "too many" in txt.lower():
            local = reponses_locales.chercher(question)
            if local:
                return local
            return _message_saturation()
        return {"reponse": txt, "confiance": 0.9, "source": "IA", "explication": "", "etapes": []}
    except Exception as e:
        msg = str(e)
        if any(k in msg.lower() for k in ("rate", "limit", "every", "429", "402", "too many")):
            local = reponses_locales.chercher(question)
            if local:
                return local
            return _message_saturation()
        # Autre erreur → repli hors ligne
        r = _repli_mock(question)
        r["source"] = "repli hors ligne"
        return r

    # ---- Repli hors ligne ----
    local = reponses_locales.chercher(question)
    if local:
        return local
    r = _repli_mock(question)
    return r

def check_plagiat(texte):
    """Démo anti-plagiat : recherche d'extraits similaires (simulation + option API)."""
    # Vérifier si le texte contient un extrait connu (simulation)
    extraits = ["la démocratie repose sur", "le sénégal est un pays d'afrique", "la fonction exponentielle est"]
    for ext in extraits:
        if ext in texte.lower():
            return {"plagiat": True, "similarite": 78, "source": "texte web trouvé", "conseil": "Reformule et cite la source."}
    return {"plagiat": False, "similarite": 12, "source": "pas de similarité forte", "conseil": "Texte original."}

def reponse_ia_photo(question, image_b64, plan):
    """Correction photo : Groq vision -> Gemini vision -> Pollinations (gratuit) -> repli."""
    vision_msgs = [
        {"role": "system", "content": PROMPT_SYSTEME},
        {"role": "user", "content": [
            {"type": "text", "text": question + "\n\nAnalyse bien l'image et réponds étape par étape en wolof puis français."},
            {"type": "image_url", "image_url": {"url": image_b64}},
        ]},
    ]
    # 1. Groq (vision)
    if GROQ_API_KEY:
        try:
            data = _call_llm(vision_msgs, "https://api.groq.com/openai/v1", GROQ_API_KEY, "llama-3.2-11b-vision-preview")
            return {"reponse": data["choices"][0]["message"]["content"], "source": "IA", "explication": "", "etapes": []}
        except Exception:
            pass
    # 2. Gemini (vision)
    if GEMINI_API_KEY:
        try:
            url = ("https://generativelanguage.googleapis.com/v1beta/models/"
                   "gemini-2.0-flash:generateContent?key=" + GEMINI_API_KEY)
            body = {"contents": [{"parts": [{"text": PROMPT_SYSTEME + "\n\nQuestion : " + question},
                                            {"inline_data": {"mime_type": "image/jpeg", "data": image_b64.split(",", 1)[-1]}}]}]}
            req = urllib.request.Request(url, data=json.dumps(body).encode(),
                                         headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=45) as r:
                data = json.loads(r.read().decode())
            txt = data["candidates"][0]["content"]["parts"][0]["text"]
            return {"reponse": txt, "source": "IA", "explanation": "", "etapes": []}
        except Exception:
            pass
    # 3. Pollinations (gratuit, vision via image_url)
    try:
        headers = {"Content-Type": "application/json"}
        if POLLINATIONS_KEY:
            headers["Authorization"] = "Bearer " + POLLINATIONS_KEY
        body = {
            "messages": [
                {"role": "system", "content": PROMPT_SYSTEME},
                {"role": "user", "content": question + "\n\nAnalyse bien l'image et réponds étape par étape en wolof puis français."},
            ],
            "images": [image_b64],
            "model": "openai",
        }
        req = urllib.request.Request(
            "https://text.pollinations.ai/",
            data=json.dumps(body).encode(),
            headers=headers)
        with urllib.request.urlopen(req, timeout=60) as r:
            raw = r.read().decode()
        txt = raw.strip()
        try:
            txt = json.loads(raw)["choices"][0]["message"]["content"]
        except Exception:
            pass
        return {"reponse": txt, "source": "IA", "explication": "", "etapes": []}
    except Exception as e:
        msg = str(e)
        if any(k in msg.lower() for k in ("rate", "limit", "every", "429", "402", "too many")):
            return {"reponse": "🤖 Le service de correction photo est saturé. Réessaie dans 30 secondes, ou ajoute une clé API (Groq/Gemini) côté serveur.",
                    "source": "limite", "explication": "", "etapes": []}
        return {"reponse": "⚠️ Correction photo indisponible : ajoute une clé API vision (Groq/Gemini/Pollinations) côté serveur.",
                "source": "erreur", "explication": "", "etapes": []}

# ------------------------------------------------------------------
# Handler HTTP
# ------------------------------------------------------------------
class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass  # silencer les logs

    def send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        # Préflight CORS.
        # L'en-tête "Authorization" est indispensable : sans lui, l'application
        # installée (APK) ou servie depuis une autre origine que l'API ne peut
        # plus envoyer son jeton → ni les matières, ni les plans ne se chargent.
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS,PUT,DELETE")
        self.send_header("Access-Control-Allow-Headers",
                         "Content-Type, Authorization, Accept, X-Requested-With")
        self.send_header("Access-Control-Max-Age", "86400")
        self.end_headers()

    def body(self):
        length = int(self.headers.get("Content-Length", 0))
        if length == 0: return {}
        return json.loads(self.rfile.read(length).decode() or "{}")

    def static(self, path):
        if path in ("", "/"):
            path = "/index.html"
        # L'APK peut être rangé dans projet/telechargements/
        fs = os.path.join(STATIC_DIR, path.lstrip("/"))
        if not os.path.isfile(fs):
            fs = os.path.join(STATIC_DIR, "telechargements", path.lstrip("/"))
        if not os.path.isfile(fs):
            self.send_response(404); self.end_headers(); return
        with open(fs, "rb") as f:
            data = f.read()
        ext = path.rsplit(".", 1)[-1].lower()
        ct = {"html": "text/html; charset=utf-8", "css": "text/css", "js": "application/javascript",
              "svg": "image/svg+xml", "png": "image/png", "jpg": "image/jpeg", "ico": "image/x-icon",
              "apk": "application/vnd.android.package-archive", "aab": "application/octet-stream",
              "json": "application/json; charset=utf-8", "webmanifest": "application/manifest+json"}
        self.send_response(200)
        self.send_header("Content-Type", ct.get(ext, "application/octet-stream"))
        self.send_header("Content-Length", str(len(data)))
        if ext in ("apk", "aab"):
            nom = os.path.basename(fs)
            self.send_header("Content-Disposition",
                             f'attachment; filename="{nom}"')
            self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(data)

    def activate_payment_by_reference(self, ref):
        c = db()
        lien = c.execute("SELECT * FROM payment_links WHERE reference=?", (ref,)).fetchone()
        if not lien or lien["statut"] == "valide":
            c.close()
            return False
        plan = c.execute("SELECT * FROM plans WHERE id=?", (lien["plan_id"],)).fetchone()
        exp = datetime.now() + timedelta(days=plan["duree_jours"])
        c.execute("UPDATE payment_links SET statut='valide', date_activation=datetime('now') WHERE id=?", (lien["id"],))
        c.execute("UPDATE users SET plan_id=?, date_expiration=? WHERE id=?",
                  (lien["plan_id"], exp.strftime("%Y-%m-%d"), lien["user_id"]))
        c.commit(); c.close()
        return True

    def do_GET(self):
        path = self.path.split("?")[0]

        if path.startswith("/api/"):
            token = self.headers.get("Authorization", "").replace("Bearer ", "")
            u = user_by_token(token)

            if path == "/api/plans":
                c = db()
                rows = [dict(r) for r in c.execute("SELECT * FROM plans").fetchall()]
                c.close()
                return self.send_json({"plans": rows})

            if path == "/api/content":
                p = plan_actif(u)
                if not p:
                    return self.send_json({"erreur": "Abonnement requis pour le contenu."}, 402)
                c = db()
                sujets = []
                for s in c.execute("SELECT * FROM sujets").fetchall():
                    chaps = c.execute("SELECT id, nom FROM chapitres WHERE sujet_id=?", (s["id"],)).fetchall()
                    nb = c.execute("SELECT COUNT(*) FROM exercices WHERE chapitre_id IN (SELECT id FROM chapitres WHERE sujet_id=?)", (s["id"],)).fetchone()[0]
                    sujets.append({"id": s["id"], "nom": s["nom"], "icone": s["icone"],
                                   "chapitres": [dict(ch) for ch in chaps], "nb_exercices": nb})
                c.close()
                return self.send_json({"sujets": sujets, "plan": p["nom"], "telechargement": bool(p["telechargement"])})

            if path == "/api/subscription/me":
                p = plan_valide(u)
                if not p:
                    return self.send_json({"plan": None, "abonne": False})
                return self.send_json({"plan": dict(p), "abonne": True})

            if path == "/api/payments/status":
                return self.send_json(status_paiements())

            if path == "/api/admin/stats":
                if not is_admin(self):
                    return self.send_json({"erreur": "Authentification admin requise"}, 401)
                c = db()
                today = datetime.now().strftime("%Y-%m-%d")
                ca = c.execute("SELECT SUM(montant) FROM payment_links WHERE statut='valide'").fetchone()[0] or 0
                actifs = c.execute("SELECT COUNT(*) FROM users WHERE date_expiration > date('now')").fetchone()[0]
                nouveaux = c.execute("SELECT COUNT(*) FROM users WHERE date_creation=?", (today,)).fetchone()[0]
                total_users = c.execute("SELECT COUNT(*) FROM users").fetchone()[0]
                conversion = round(actifs / max(total_users, 1) * 100, 1)
                c.close()
                return self.send_json({"ca": ca, "abonnes_actifs": actifs, "nouveaux_aujourdhui": nouveaux,
                                       "total_users": total_users, "conversion": conversion,
                                       "objectif": 3000000})

            if path == "/api/admin/subscribers":
                if not is_admin(self):
                    return self.send_json({"erreur": "Authentification admin requise"}, 401)
                c = db()
                rows = []
                for s in c.execute("""SELECT u.id, u.pseudo, u.niveau, u.ville, u.langue, u.date_expiration,
                                      p.nom plan, p.prix, pl.canal, pl.statut
                                      FROM users u LEFT JOIN plans p ON u.plan_id=p.id
                                      LEFT JOIN payment_links pl ON pl.user_id=u.id
                                      ORDER BY u.id DESC LIMIT 50""").fetchall():
                    d = dict(s); d["plan"] = d.pop("plan")
                    rows.append(d)
                c.close()
                return self.send_json({"abonnes": rows})

            if path == "/api/admin/payment-links":
                if not is_admin(self):
                    return self.send_json({"erreur": "Authentification admin requise"}, 401)
                c = db()
                rows = [dict(r) for r in c.execute("SELECT * FROM payment_links ORDER BY id DESC LIMIT 50").fetchall()]
                c.close()
                return self.send_json({"liens": rows})

            if path == "/api/admin/security-logs":
                if not is_admin(self):
                    return self.send_json({"erreur": "Authentification admin requise"}, 401)
                c = db()
                rows = [dict(r) for r in c.execute("SELECT * FROM security_logs ORDER BY id DESC LIMIT 30").fetchall()]
                c.close()
                return self.send_json({"logs": rows})

            if path == "/api/admin/config":
                if not is_admin(self):
                    return self.send_json({"erreur": "Authentification admin requise"}, 401)
                c = db()
                cfg = {r["key"]: r["value"] for r in c.execute("SELECT key, value FROM admin_config").fetchall()}
                c.close()
                return self.send_json({"config": cfg})

            if path == "/api/admin/users":
                if not is_admin(self):
                    return self.send_json({"erreur": "Authentification admin requise"}, 401)
                c = db()
                rows = c.execute("SELECT id, pseudo, niveau, ville, langue, plan_id, date_expiration, date_creation, email, telephone, bloque FROM users ORDER BY date_creation DESC").fetchall()
                plans_cache = {r["id"]: (r["nom"], r["prix"]) for r in c.execute("SELECT id, nom, prix FROM plans").fetchall()}
                c.close()
                users = []
                for r in rows:
                    p = plans_cache.get(r["plan_id"], ("—", 0))
                    users.append({
                        "id": r["id"],
                        "pseudo": r["pseudo"],
                        "niveau": r["niveau"],
                        "ville": r["ville"],
                        "langue": r["langue"],
                        "plan": p[0],
                        "plan_prix": p[1],
                        "date_expiration": r["date_expiration"],
                        "date_creation": r["date_creation"],
                        "email": r["email"] or "",
                        "telephone": r["telephone"] or "",
                        "bloque": bool(r["bloque"])
                    })
                return self.send_json({"users": users, "total": len(users)})

            return self.send_json({"erreur": "NotFound"}, 404)

        # Static
        return self.static(path)

    def do_POST(self):
        path = self.path.split("?")[0]
        data = self.body()
        token = self.headers.get("Authorization", "").replace("Bearer ", "")
        u = user_by_token(token)

        if path == "/api/register":
            pseudo = data.get("pseudo", "").strip()
            if not pseudo or len(pseudo) < 3:
                return self.send_json({"erreur": "Pseudo trop court (3+ caractères)"}, 400)
            c = db()
            if c.execute("SELECT id FROM users WHERE pseudo=?", (pseudo,)).fetchone():
                c.close()
                return self.send_json({"erreur": "Pseudo déjà pris"}, 409)
            pid_gratuit = c.execute("SELECT id FROM plans WHERE code='gratuit'").fetchone()[0]
            c.execute("""INSERT INTO users (pseudo, mot_de_passe, niveau, ville, langue, plan_id, date_expiration, token, date_creation, email, telephone)
                         VALUES (?,?,?,?,?,?,?,?,datetime('now'),?,?)""",
                      (pseudo, hash_mdp(data.get("mot_de_passe", "")), data.get("niveau", ""),
                       data.get("ville", ""), data.get("langue", "fr"), pid_gratuit,
                       (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"),
                       secrets.token_hex(16),
                       data.get("email", "").strip(),
                       data.get("telephone", "").strip()))
            c.commit()
            uid = c.execute("SELECT last_insert_rowid()").fetchone()[0]
            tok = c.execute("SELECT token FROM users WHERE id=?", (uid,)).fetchone()[0]
            c.close()
            log_sec(uid, "inscription", "Nouveau compte")
            return self.send_json({"ok": True, "user": {"id": uid, "pseudo": pseudo}, "token": tok})

        if path == "/api/login":
            c = db()
            row = c.execute("SELECT * FROM users WHERE pseudo=?", (data.get("pseudo", ""),)).fetchone()
            if not row or row["mot_de_passe"] != hash_mdp(data.get("mot_de_passe", "")):
                c.close()
                return self.send_json({"erreur": "Identifiants invalides"}, 401)
            if row["bloque"]:
                c.close()
                return self.send_json({"erreur": "Ce compte est bloqué. Contactez le support."}, 403)
            c.close()
            return self.send_json({"ok": True, "user": {"id": row["id"], "pseudo": row["pseudo"]}, "token": row["token"]})

        if path == "/api/subscribe":
            if not u:
                return self.send_json({"erreur": "Authentification requise"}, 401)
            plan_id = data.get("plan_id")
            canal = data.get("canal", "Wave")
            c = db()
            plan = c.execute("SELECT * FROM plans WHERE id=?", (plan_id,)).fetchone()
            if not plan:
                c.close()
                return self.send_json({"erreur": "Plan inconnu"}, 400)
            reference = generer_reference()
            checkout = (creer_checkout_orange(plan["prix"], reference) if canal == "Orange Money"
                        else creer_checkout_wave(plan["prix"], reference))
            c.execute("""INSERT INTO payment_links (user_id, plan_id, canal, url, montant, statut, reference, date_creation)
                         VALUES (?,?,?,?,?,'en_attente',?,datetime('now'))""",
                      (u["id"], plan_id, canal, checkout["url"], plan["prix"], reference))
            c.commit(); c.close()
            return self.send_json({"ok": True, "checkout_url": checkout["url"], "reference": reference,
                                   "canal": canal, "montant": plan["prix"], "plan": plan["nom"],
                                   "reel": checkout["reel"],
                                   "message": "Redirection vers le paiement " + canal})

        if path == "/api/admin/config":
            if not is_admin(self):
                return self.send_json({"erreur": "Authentification admin requise"}, 401)
            cfg = data.get("config", {})
            c = db()
            for k, v in cfg.items():
                c.execute("INSERT INTO admin_config (key, value) VALUES (?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (k, str(v)))
                os.environ[k] = str(v)
                # Mise à jour immédiate du module paiements
                pm = sys.modules.get("paiements")
                if pm and hasattr(pm, k):
                    setattr(pm, k, str(v))
            c.commit()
            c.close()
            return self.send_json({"ok": True, "config": cfg})

        if path == "/api/admin/confirm-payment":
            # Confirme un paiement (callback de la passerelle ou retour client).
            lien_id = data.get("lien_id")
            reference = data.get("reference")
            c = db()
            if lien_id:
                lien = c.execute("SELECT * FROM payment_links WHERE id=?", (lien_id,)).fetchone()
            elif reference:
                lien = c.execute("SELECT * FROM payment_links WHERE reference=?", (reference,)).fetchone()
            else:
                c.close()
                return self.send_json({"erreur": "lien_id ou reference requis"}, 400)
            if not lien:
                c.close()
                return self.send_json({"erreur": "Paiement introuvable"}, 404)
            # Vérification auprès du fournisseur en mode réel
            if lien["canal"] == "Wave":
                st = verifier_paiement_wave(lien["reference"])
                if st and st.lower() not in ("completed", "succeeded", "paid", "success", "confirmed"):
                    c.close()
                    return self.send_json({"erreur": "Paiement non confirmé : " + str(st)}, 402)
            plan = c.execute("SELECT * FROM plans WHERE id=?", (lien["plan_id"],)).fetchone()
            exp = datetime.now() + timedelta(days=plan["duree_jours"])
            c.execute("UPDATE payment_links SET statut='valide', date_activation=datetime('now') WHERE id=?", (lien["id"],))
            c.execute("UPDATE users SET plan_id=?, date_expiration=? WHERE id=?",
                      (lien["plan_id"], exp.strftime("%Y-%m-%d"), lien["user_id"]))
            c.commit(); c.close()
            return self.send_json({"ok": True, "message": "Abonnement activé : " + plan["nom"]})

        if path == "/api/payments/wave/webhook":
            # Webhook Wave : vérification HMAC-SHA256 sur le body brut
            raw = self.rfile.read(int(self.headers.get("Content-Length", 0)))
            signature = self.headers.get("X-Wave-Signature", "")
            try:
                payload = json.loads(raw.decode())
            except Exception:
                return self.send_json({"erreur": "Corps invalide"}, 400)
            if not webhook_wave_valide(payload, signature):
                return self.send_json({"erreur": "Signature invalide"}, 403)
            ref = payload.get("client_reference") or payload.get("reference") or (payload.get("session") or {}).get("client_reference")
            if ref:
                self.activate_payment_by_reference(ref)
            return self.send_json({"ok": True})

        if path == "/api/payments/orange/notif":
            # Notification Orange Money
            payload = json.loads(self.body())
            order_id = payload.get("order_id") or payload.get("reference")
            if order_id:
                self.activate_payment_by_reference(order_id)
            return self.send_json({"ok": True})

        if path == "/api/ai/ask":
            if not u:
                return self.send_json({"erreur": "Authentification requise"}, 401)
            p = plan_actif(u)
            if not p:
                return self.send_json({"erreur": "Essai gratuit de 24 h terminé — abonne-toi pour continuer (à partir de 250 FCFA)."}, 402)
            # Limite quotidienne IA
            c = db()
            jour = datetime.now().strftime("%Y-%m-%d")
            row = c.execute("SELECT count FROM usage_journaliere WHERE user_id=? AND date=?", (u["id"], jour)).fetchone()
            count = row[0] if row else 0
            if count >= p["limite_ia_jour"]:
                c.close()
                return self.send_json({"erreur": f"Quota IA atteint ({p['limite_ia_jour']}/jour). Passe au plan supérieur."}, 429)
            question = data.get("question", "")
            c.execute("UPDATE usage_journaliere SET count=count+1 WHERE user_id=? AND date=?", (u["id"], jour))
            if c.execute("SELECT changes()").fetchone()[0] == 0:
                c.execute("INSERT INTO usage_journaliere (user_id, date, count) VALUES (?,?,1)", (u["id"], jour))
            c.execute("INSERT INTO ai_usage (user_id, action, tokens, cout, date) VALUES (?,?,?,?,datetime('now'))", (u["id"], "question", 800, 0.0002))
            c.commit(); c.close()
            cache_key = re.sub(r"\s+", " ", question.strip().lower())[:200]
            r = reponse_ia(question, p)
            if r.get("source") == "IA":
                _IA_CACHE[cache_key] = {k: v for k, v in r.items() if k != "quota_restant"}
            r["quota_restant"] = max(p["limite_ia_jour"] - count - 1, 0)
            return self.send_json(r)

        if path == "/api/ai/photo":
            if not u:
                return self.send_json({"erreur": "Authentification requise"}, 401)
            p = plan_actif(u)
            if not p:
                return self.send_json({"erreur": "Abonnement requis pour la correction photo"}, 402)
            jour = datetime.now().strftime("%Y-%m-%d")
            c = db()
            row = c.execute("SELECT count(*) FROM ai_usage WHERE user_id=? AND action='photo' AND date(date)=?", (u["id"], jour)).fetchone()
            count = row[0] if row else 0
            if count >= p["photo_jour"]:
                c.close()
                return self.send_json({"erreur": f"Quota photo atteint ({p['photo_jour']}/jour). Passe au plan supérieur."}, 429)
            image = data.get("image", "")
            if not image or len(image) < 100:
                c.close()
                return self.send_json({"erreur": "Photo requise"}, 400)
            question = data.get("question", "Qu'y a-t-il sur cette photo ? Explique en wolof puis français.")
            c.execute("INSERT INTO ai_usage (user_id, action, tokens, cout, date) VALUES (?,?,?,?,datetime('now'))", (u["id"], "photo", 1500, 0.0006))
            c.commit(); c.close()
            r = reponse_ia_photo(question, image, p)
            r["quota_restant"] = max(p["photo_jour"] - count - 1, 0)
            return self.send_json(r)

        if path == "/api/ai/plagiat":
            if not u:
                return self.send_json({"erreur": "Authentification requise"}, 401)
            p = plan_actif(u)
            if not p:
                return self.send_json({"erreur": "Essai gratuit de 24 h terminé — abonne-toi pour continuer."}, 402)
            r = check_plagiat(data.get("texte", ""))
            log_sec(u["id"], "plagiat", "Vérification dissertation")
            return self.send_json(r)

        if path == "/api/security/log":
            if not u:
                return self.send_json({"erreur": "Authentification requise"}, 401)
            log_sec(u["id"], data.get("type", "autre"), data.get("detail", ""))
            return self.send_json({"ok": True})

        # --- Reset mot de passe ---
        if path == "/api/reset-password/request":
            pseudo = data.get("pseudo", "").strip()
            contact = data.get("contact", "").strip()
            c = db()
            row = c.execute("SELECT * FROM users WHERE pseudo=?", (pseudo,)).fetchone()
            if not row:
                c.close()
                return self.send_json({"erreur": "Pseudo introuvable"}, 404)
            if not contact:
                contact = row["telephone"] or row["email"] or ""
            if not contact:
                c.close()
                return self.send_json({"erreur": "Aucun numéro de téléphone ou email enregistré. Contactez le support."}, 400)
            # Vérifier que le contact correspond
            if row["telephone"] and contact in row["telephone"]:
                ok_contact = True
            elif row["email"] and contact in row["email"]:
                ok_contact = True
            else:
                c.close()
                return self.send_json({"erreur": "Le numéro ou email ne correspond pas au compte"}, 400)
            # Générer code 6 chiffres
            code = str(random.randint(100000, 999999))
            c.execute("DELETE FROM password_reset WHERE pseudo=?", (pseudo,))
            c.execute("INSERT INTO password_reset (pseudo, code, date_creation, date_expiration) VALUES (?,?,datetime('now'),datetime('now','+15 minutes'))",
                      (pseudo, code))
            c.commit()
            c.close()
            # Retourner le code (dans la vraie vie, on l'envoie par SMS/WhatsApp/email)
            return self.send_json({"ok": True, "message": "Code de vérification envoyé",
                                   "code": code,  # Démo: code retourné car pas de service SMS
                                   "contact": contact,
                                   "note": "Code valable 15 minutes. (Démo: code affiché car pas de service SMS/WhatsApp configuré)"})

        if path == "/api/reset-password/verify":
            pseudo = data.get("pseudo", "").strip()
            code = data.get("code", "").strip()
            nouveau_mdp = data.get("mot_de_passe", "")
            c = db()
            row = c.execute("SELECT * FROM password_reset WHERE pseudo=? ORDER BY id DESC", (pseudo,)).fetchone()
            if not row:
                c.close()
                return self.send_json({"erreur": "Aucune demande de reset. Faites une demande d'abord."}, 400)
            if row["code"] != code:
                c.close()
                return self.send_json({"erreur": "Code incorrect"}, 400)
            if datetime.now() > datetime.strptime(row["date_expiration"], "%Y-%m-%d %H:%M:%S"):
                c.close()
                return self.send_json({"erreur": "Code expiré. Faites une nouvelle demande."}, 400)
            if len(nouveau_mdp) < 8 or not re.search(r"[a-zA-Z]", nouveau_mdp) or not re.search(r"[0-9]", nouveau_mdp):
                c.close()
                return self.send_json({"erreur": "Mot de passe : 8+ caractères, lettre + chiffre"}, 400)
            c.execute("UPDATE users SET mot_de_passe=? WHERE pseudo=?", (hash_mdp(nouveau_mdp), pseudo))
            c.execute("DELETE FROM password_reset WHERE pseudo=?", (pseudo,))
            c.commit()
            uid = c.execute("SELECT id FROM users WHERE pseudo=?", (pseudo,)).fetchone()[0]
            c.close()
            log_sec(uid, "reset_mdp", "Mot de passe réinitialisé")
            return self.send_json({"ok": True, "message": "Mot de passe réinitialisé. Vous pouvez vous connecter."})

        # --- Admin: bloquer / supprimer / lister utilisateurs ---
        if path == "/api/admin/block-user":
            if not is_admin(self):
                return self.send_json({"erreur": "Authentification admin requise"}, 401)
            target_pseudo = data.get("pseudo", "").strip()
            bloque = 1 if data.get("bloque") else 0
            c = db()
            row = c.execute("SELECT id FROM users WHERE pseudo=?", (target_pseudo,)).fetchone()
            if not row:
                c.close()
                return self.send_json({"erreur": "Utilisateur introuvable"}, 404)
            c.execute("UPDATE users SET bloque=? WHERE pseudo=?", (bloque, target_pseudo))
            c.commit()
            c.close()
            log_sec(row["id"], "admin_block", f"Blocage={bloque}")
            return self.send_json({"ok": True, "message": f"Utilisateur {target_pseudo} {'bloqué' if bloque else 'débloqué'}"})

        if path == "/api/admin/delete-user":
            if not is_admin(self):
                return self.send_json({"erreur": "Authentification admin requise"}, 401)
            target_pseudo = data.get("pseudo", "").strip()
            c = db()
            row = c.execute("SELECT id FROM users WHERE pseudo=?", (target_pseudo,)).fetchone()
            if not row:
                c.close()
                return self.send_json({"erreur": "Utilisateur introuvable"}, 404)
            uid = row["id"]
            c.execute("DELETE FROM users WHERE id=?", (uid,))
            c.execute("DELETE FROM payment_links WHERE user_id=?", (uid,))
            c.execute("DELETE FROM ai_usage WHERE user_id=?", (uid,))
            c.execute("DELETE FROM security_logs WHERE user_id=?", (uid,))
            c.execute("DELETE FROM usage_journaliere WHERE user_id=?", (uid,))
            c.execute("DELETE FROM password_reset WHERE pseudo=?", (target_pseudo,))
            c.commit()
            c.close()
            return self.send_json({"ok": True, "message": f"Utilisateur {target_pseudo} supprimé"})

        if path == "/api/admin/reset-user-password":
            if not is_admin(self):
                return self.send_json({"erreur": "Authentification admin requise"}, 401)
            target_pseudo = data.get("pseudo", "").strip()
            nouveau_mdp = data.get("mot_de_passe", "Motdepasse1")
            if len(nouveau_mdp) < 8 or not re.search(r"[a-zA-Z]", nouveau_mdp) or not re.search(r"[0-9]", nouveau_mdp):
                return self.send_json({"erreur": "Mot de passe : 8+ caractères, lettre + chiffre"}, 400)
            c = db()
            row = c.execute("SELECT id FROM users WHERE pseudo=?", (target_pseudo,)).fetchone()
            if not row:
                c.close()
                return self.send_json({"erreur": "Utilisateur introuvable"}, 404)
            c.execute("UPDATE users SET mot_de_passe=? WHERE pseudo=?", (hash_mdp(nouveau_mdp), target_pseudo))
            c.commit()
            c.close()
            log_sec(row["id"], "admin_reset", "Admin a réinitialisé le mot de passe")
            return self.send_json({"ok": True, "message": f"Mot de passe de {target_pseudo} réinitialisé"})

        return self.send_json({"erreur": "NotFound"}, 404)

    def do_DELETE(self):
        return self.send_json({"erreur": "Methode non supportée"}, 405)

if __name__ == "__main__":
    init_db()
    print(f"🟢 ÉcoleMax API démarrée → http://0.0.0.0:{PORT}")
    print(f"   Static: {STATIC_DIR}")
    print(f"   DB: {DB_PATH}")
    print("   AI: " + ("API réelle (" + OPENAI_MODEL + ")" if OPENAI_API_KEY else "simulée (sans clé)"))
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
