#!/usr/bin/env python3
"""ÉcoleMax — Serveur Flask + Gunicorn (production stable)"""
import os, json, re, base64, hashlib, datetime, secrets, sqlite3, urllib.request, time, threading, hmac, random

HOST = "0.0.0.0"
PORT = int(os.environ.get("PORT", 8000))
DB_PATH = os.environ.get("DB_PATH", os.path.join(os.path.dirname(os.path.abspath(__file__)), "ecolemax.db"))
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "ecolemax2026")

# === Twilio SMS ===
TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN", "")
TWILIO_FROM_NUMBER = os.environ.get("TWILIO_FROM_NUMBER", "")
SMS_PROVIDER = os.environ.get("SMS_PROVIDER", "twilio")

# === Render API ===
RENDER_API_KEY = os.environ.get("RENDER_API_KEY", "")
RENDER_SERVICE_URL = os.environ.get("RENDER_SERVICE_URL", "")

# === Email (SendGrid) ===
SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY", "")
SENDGRID_FROM = os.environ.get("SENDGRID_FROM", "sycheikhcorp@gmail.com")
SMTP_HOST = os.environ.get("SMTP_HOST", "")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASS = os.environ.get("SMTP_PASS", "")
JWT_SECRET = os.environ.get("JWT_SECRET", "ecolemax-jwt-secret-v1-2026-change")
POLLINATIONS_URL = "https://text.pollinations.ai/openai"
OVH_AI_URL = "https://oai.endpoints.kepler.ai.cloud.ovh.net/v1/chat/completions"
OVH_AI_MODEL = "Qwen2.5-VL-72B-Instruct"
OVH_AI_FALLBACK = "Meta-Llama-3_3-70B-Instruct"
OVH_AI_MAX_TOKENS = 3000
OVH_AI_TIMEOUT = 30
_POLLINATIONS_MIN_INTERVAL = 30
_ai_sem = threading.BoundedSemaphore(5)  # max 5 appels IA simultanés (évite la saturation du fournisseur)

# ─── Utilitaires ───
def now():
    return datetime.datetime.now().isoformat(timespec='seconds')

def log_sec(user_id, action, detail=""):
    try:
        c = db()
        c.execute("INSERT INTO logs_sec (user_id,action,detail,date) VALUES (?,?,?,?)",
                  (user_id, action, detail[:200], now()))
        c.commit()
        c.close()
    except Exception:
        pass

def hash_pass(mdp):
    """Hachage PBKDF2 avec sel aléatoire (sécurité renforcée)."""
    salt = os.urandom(16)
    h = hashlib.pbkdf2_hmac('sha256', mdp.encode(), salt, 50000)
    return "pbkdf2$" + salt.hex() + "$" + h.hex()

def verify_pass(mdp, stored):
    """Vérifie un mot de passe : PBKDF2 d'abord, migration SHA-256 pour les anciens."""
    if stored and stored.startswith("pbkdf2$"):
        parts = stored.split("$")
        if len(parts) == 3:
            try:
                salt = bytes.fromhex(parts[1])
                h = hashlib.pbkdf2_hmac('sha256', mdp.encode(), salt, 50000)
                if h.hex() == parts[2]:
                    return True
            except Exception:
                pass
    # Migration : anciens mots de passe hachés en SHA-256 simple
    return hashlib.sha256(mdp.encode()).hexdigest() == stored

def jwt_create(uid):
    payload = {"uid": uid, "ts": int(time.time())}
    sig = hmac.new(JWT_SECRET.encode(), json.dumps(payload, separators=(',', ':')).encode(), hashlib.sha256).hexdigest()
    payload["sig"] = sig
    return base64.urlsafe_b64encode(json.dumps(payload).encode()).decode()

def jwt_decode(token):
    """Décode et vérifie la signature HMAC du JWT."""
    try:
        payload = json.loads(base64.urlsafe_b64decode(token.encode()))
        sig = payload.pop("sig", None)
        if sig is None: return None
        calc = hmac.new(JWT_SECRET.encode(), json.dumps(payload, separators=(',', ':')).encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, calc): return None
        return payload
    except Exception:
        return None

def db():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA busy_timeout=30000")
    return conn

def init_db():
    c = db()
    c.execute("""CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, pseudo TEXT UNIQUE, email TEXT, mot_de_passe TEXT, niveau TEXT, role TEXT DEFAULT 'eleve', created_at TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS plans (code TEXT PRIMARY KEY, nom TEXT, prix REAL, duree_jours INTEGER, limite_ia_jour INTEGER, photo_jour INTEGER, description TEXT, paiement_tranche TEXT, nb_tranches INTEGER)""")
    c.execute("""CREATE TABLE IF NOT EXISTS abonnements (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, plan_code TEXT, statut TEXT DEFAULT 'en_attente', debut TEXT, expire TEXT, montant INTEGER)""")
    c.execute("""CREATE TABLE IF NOT EXISTS paiements (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, montant INTEGER, method TEXT, statut TEXT, reference TEXT UNIQUE, abonnement_id INTEGER, created_at TEXT, confirmed_at TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS usages (user_id INTEGER, date TEXT, ia_count INTEGER, photo_count INTEGER, correct_count INTEGER, ex_count INTEGER, PRIMARY KEY(user_id,date))""")
    c.execute("""CREATE TABLE IF NOT EXISTS sujets (code TEXT PRIMARY KEY, nom TEXT, description TEXT, ordre INTEGER)""")
    c.execute("""CREATE TABLE IF NOT EXISTS cours (id INTEGER PRIMARY KEY AUTOINCREMENT, sujet_code TEXT, titre TEXT, contenu TEXT, niveau TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS exercises (id INTEGER PRIMARY KEY AUTOINCREMENT, sujet_code TEXT, titre TEXT, niveau TEXT, type TEXT, question TEXT, reponse TEXT, explication TEXT, difficulte TEXT DEFAULT 'moyen')""")
    c.execute("""CREATE TABLE IF NOT EXISTS corrections (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, original TEXT, corrige TEXT, explication TEXT, date TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS quiz (id INTEGER PRIMARY KEY AUTOINCREMENT, categorie TEXT, question TEXT, reponse INTEGER, explication TEXT, difficulte TEXT DEFAULT 'moyen')""")
    c.execute("""CREATE TABLE IF NOT EXISTS quiz_resultats (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, score INTEGER, total INTEGER, date TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS results (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, exercise_id INTEGER, score INTEGER, reponse_utilisateur TEXT, correct INTEGER, date TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS favoris (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, type TEXT, ref_id INTEGER, label TEXT, date TEXT, UNIQUE(user_id,type,ref_id))""")
    c.execute("""CREATE TABLE IF NOT EXISTS notifications (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, titre TEXT, message TEXT, type TEXT DEFAULT 'system', lu INTEGER DEFAULT 0, date TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS supports (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, sujet TEXT, message TEXT, date TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS sessions (token TEXT PRIMARY KEY, user_id INTEGER, expires_at TEXT, created_at TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS logs_sec (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, action TEXT, detail TEXT, date TEXT)""")
    c.execute("CREATE INDEX IF NOT EXISTS idx_users_pseudo ON users(pseudo)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_abos_user ON abonnements(user_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_pays_ref ON paiements(reference)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_ex_sujet ON exercises(sujet_code)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_quiz_cat ON quiz(categorie)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_usages_user ON usages(user_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_corr_user ON corrections(user_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_results_user ON quiz_resultats(user_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_favoris_user ON favoris(user_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_notifs_user ON notifications(user_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_supports_user ON supports(user_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_logs_user ON logs_sec(user_id)")
    # Nouvelles tables
    c.execute("CREATE TABLE IF NOT EXISTS sms_codes (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, phone TEXT, code TEXT, expires_at TEXT, attempts INTEGER DEFAULT 0, used INTEGER DEFAULT 0)")
    c.execute("CREATE TABLE IF NOT EXISTS contact_messages (id INTEGER PRIMARY KEY AUTOINCREMENT, nom TEXT, email TEXT, phone TEXT, objet TEXT, categorie TEXT, message TEXT, statut TEXT DEFAULT 'nouveau', date TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS audit_logs (id INTEGER PRIMARY KEY AUTOINCREMENT, admin_id INTEGER, action TEXT, target_user_id INTEGER, detail TEXT, date TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS quiz_sessions (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, categorie TEXT, difficulte TEXT, questions TEXT, temps_total INTEGER, score INTEGER, total INTEGER, date TEXT)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_sms_user ON sms_codes(user_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_contact_statut ON contact_messages(statut)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_audit_admin ON audit_logs(admin_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_quiz_sess_user ON quiz_sessions(user_id)")

    plans = [
        ("gratuit","Essai gratuit 48 H",0.0,2,999999,1,"Essai 48 h : IA illimitee · 1 photo · tout debloque","unique",1),
        ("3jours","Pack 3 Jours",250.0,3,15,1,"3 jours · 15 questions IA/jour · 1 photo/jour","unique",1),
        ("1semaine","Pack 1 Semaine",500.0,7,30,2,"7 jours · 30 questions IA/jour · 2 photos/jour","unique",1),
        ("2semaines","Pack 2 Semaines",1000.0,14,50,3,"14 jours · 50 questions IA/jour · 3 photos/jour","unique",1),
        ("1mois","Pack 1 Mois",2000.0,30,100,5,"30 jours · 100 questions IA/jour · 5 photos/jour","unique",1),
        ("bac","Pack BAC",3000.0,90,200,10,"90 jours · 200 questions IA/jour · 10 photos/jour · tous niveaux","unique",1),
        ("annuel","Pack Annuel",10000.0,365,500,30,"1 an · 500 questions IA/jour · 30 photos/jour · tous niveaux","mensuel",10),
    ]
    for p in plans:
        c.execute("INSERT OR IGNORE INTO plans (code,nom,prix,duree_jours,limite_ia_jour,photo_jour,description,paiement_tranche,nb_tranches) VALUES (?,?,?,?,?,?,?,?,?)", p)

    sujets = [
        ("math","Mathématiques","Algèbre, géométrie, probabilités",1),
        ("fr","Français","Grammaire, conjugaison, rédaction",2),
        ("phys","Physique","Mécanique, thermodynamique, électricité",3),
        ("chim","Chimie","Organique, inorganique, équilibres",4),
        ("hist","Histoire","Histoire du Sénégal et Afrique",5),
        ("geo","Géographie","Carte, climat, ressources",6),
        ("eng","Anglais","Grammaire, conversation, compréhension",7),
        ("svt","SVT","Biologie, écologie, anatomie",8),
        ("info","Informatique","Algorithmique, bases de données",9),
        ("eco","Économie","Macro, micro, développement",10),
        ("es","Espagnol","Grammaire, vocabulaire, culture",11),
        ("ara","Arabe","Grammaire, calligraphie, culture",12),
    ]
    for s in sujets:
        c.execute("INSERT OR IGNORE INTO sujets (code,nom,description,ordre) VALUES (?,?,?,?)", s)

    matieres = [
        ("math","Algèbre linéaire","Niveau: Terminale\n\n# Les matrices\n\nUne matrice est une table rectangulaire de nombres. On la note entre parenthèses larges.\n\n## Opérations\n- Addition: A + B (même taille)\n- Multiplication: A × B (lignes de A × colonnes de B)\n- Transposée: AT\n\n## Déterminant\nPour une matrice 2×2: det = ad - bc\n\n## Propriétés\n- det(AB) = det(A)·det(B)\n- A est inversible ssi det(A) ≠ 0"),
        ("math","Les fonctions exponentielles","Niveau: Terminale\n\n# Fonction exponentielle\n\nf(x) = a^x, avec a > 0 et a ≠ 1\n\n## Propriétés\n- f(0) = 1\n- f(x) > 0 pour tout x\n- f croissante si a > 1, décroissante si a < 1\n- f'(x) = a^x · ln(a)\n\n## Limites\n- lim x→+∞ a^x = +∞ si a > 1\n- lim x→-∞ a^x = 0 si a > 1"),
        ("fr","Les pronoms personnels","Niveau: 2ème\n\n# Pronoms personnels\n\n| Sujet | Complément | Disjoint | Attif | Réfléchi |\n|-------|------------|----------|-------|---------|\n| je    | me         | moi      | m'    | me      |\n| tu    | te         | toi      | t'    | te      |\n| il    | le         | lui      | l'    | se      |\n| elle  | la         | lui      | l'    | se      |\n| nous  | nous       | nous     | nous  | nous    |\n| vous  | vous       | vous     | vous  | vous    |\n| ils   | les        | leur     | l'    | se      |\n| elles | les        | leur     | l'    | se      |\n\n## Exemples\n- Je me lève à 7h.\n- Il s'appelle Karim.\n- Nous nous amusons."),
        ("fr","La conjugaison du verbe ÊTRE","Niveau: 1ère\n\n# ÊTRE — Présent\n\n| Pronom | Conjugaison |\n|--------|-------------|\n| je     | suis        |\n| tu     | es          |\n| il     | est         |\n| nous   | sommes      |\n| vous   | êtes        |\n| ils    | sont        |\n\n# Imparfait\n| Pronom | Conjugaison |\n|--------|-------------|\n| je     | étais       |\n| tu     | étais       |\n| il     | était       |\n| nous   | étions      |\n| vous   | étiez       |\n| ils    | étaient     |\n\n# Passé composé\n- être + été\n- J'ai été / Tu as été / Il a été"),
        ("phys","La loi d'Ohm","Niveau: Terminale\n\n# Loi d'Ohm\n\nV = R · I\n\nOù:\n- V = tension (Volts)\n- R = résistance (Ohms)\n- I = intensité (Ampères)\n\n## Exemple\nUne résistance de 100 Ω traversée par un courant de 0,5 A:\nV = 100 × 0,5 = 50 V\n\n## Réseaux de résistances\n- Série: R_eq = R1 + R2 + ...\n- Parallèle: 1/R_eq = 1/R1 + 1/R2 + ..."),
        ("phys","Les lois de Newton","Niveau: Terminale\n\n# Trois lois de Newton\n\n## 1ère loi (inertie)\nUn corps garde son état de repos ou de mouvement rectiligne uniforme sauf si une force extérieure s'y oppose.\n\n## 2ème loi (relation fondamentale)\nF = m × a\n\n## 3ème loi (action-réaction)\nÀ toute action correspond une réaction opposée et de même intensité.\n\n## Exemples\n- Un livre sur une table: Poids = réaction normale\n- Un véhicule qui freine: déceleration = force de freinage / masse"),
        ("chim","La tableau périodique","Niveau: Terminale\n\n# Tableau périodique\n\nOrganisation des éléments par numéro atomique (Z).\n\n## Catégories\n- Métaux alcalins: Groupe 1 (Li, Na, K...)\n- Métaux alcalino-terreux: Groupe 2\n- Gaz nobles: Groupe 18\n- Halogènes: Groupe 17\n- Métaux de transition: Groupes 3-12\n\n## Périodes et groupes\n- 7 périodes (lignes horizontales)\n- 18 groupes (colonnes verticales)\n\n## Propriétés périodiques\nVariations régulières selon Z:\n- Énergie de premier ionisation\n- Electronégativité\n- Rayon atomique"),
        ("chim","Les réactions d'oxydoréduction","Niveau: Terminale\n\n# Oxydoréduction\n\nRéactions impliquant un transfert d'électrons.\n\n## Oxydation\nPerte d'électrons → la espèce est oxydée.\n\n## Réduction\nGain d'électrons → la espèce est réduite.\n\n## Notions\n- Oxydant: accepte des électrons (il est réduit)\n- Réducteur: donne des électrons (il est oxydé)\n\n## Exemple\nZn(s) + Cu²⁺(aq) → Zn²⁺(aq) + Cu(s)\n- Zn est oxydé (réducteur)\n- Cu²⁺ est réduit (oxydant)"),
        ("hist","L'histoire du Sénégal","Niveau: 3ème\n\n# Histoire du Sénégal\n\n## Royaumes précoloniaux\n- Tekrour (11e-13e siècle)\n- Royaume du Jolof\n- Empire du Mali (14e siècle)\n\n## Période coloniale\n- 1444: Arrivée des Portugais\n- 1864: Établissement de l'administration française\n- 1960: Indépendance (20 juin)\n\n## Chefs d'État\n- Léopold Sédar Senghor (1960-1980)\n- Abdou Diouf (1980-2000)\n- Abdoulaye Wade (2000-2012)\n- Macky Sall (2012-2019)\n- Bassirou Diomaye Faye (2024-)\n\n## Mémoriaux\n- Goree (Maison des esclaves)\n- Saint-Louis (ancienne capitale)"),
        ("geo","Les climats du Sénégal","Niveau: 3ème\n\n# Climats du Sénégal\n\n## Climat soudano-guinéen\n- Sud du pays (Casamance)\n- Une saison des pluies longue (juin-octobre)\n- Humidité élevée\n\n## Climat tropical sec\n- Centre du pays\n- Saison des pluies courte (juin-septembre)\n- Végétation de savane\n\n## Climat Sahélo-soudanien\n- Nord (Ferlo)\n- Pluies rares et irrégulières\n- Végétation xérophile\n\n## Climat désertique\n- Extrême nord\n- Très peu de pluie\n- Présence de dunes"),
        ("eng","Present Simple","Niveau: 2nde\n\n# Present Simple Tense\n\n## Règles de formation\n- Verbes réguliers: base + -s/-es\n- Verbes en -ch, -sh, -s, -x, -o → + -es (watch → watches)\n- Verbes en consonne + -y → -y + -es (study → studies)\n- To have: have/has\n- To be: am/is/are\n\n## Utilisation\n- Habitudes, routines\n- Faits généralement vrais\n- Événements programmés\n\n## Exemples\n- I play football every Saturday.\n- She studies English.\n- The train leaves at 8 AM."),
        ("eng","Possessive Adjectives","Niveau: 2nde\n\n# Possessive Adjectives\n\n| Pronom | Adjectif possessif |\n|--------|-------------------|\n| I      | my                |\n| you    | your              |\n| he     | his               |\n| she    | her               |\n| it     | its               |\n| we     | our               |\n| they   | their             |\n\n## Exemples\n- This is my book.\n- Her name is Maria.\n- Our house is big.\n- Their car is new."),
        ("svt","La cellule","Niveau: 2nde\n\n# La cellule\n\n## Parties d'une cellule végétale\n- Paroi cellulaire: rigidité\n- Membrane plasmique: protection\n- Cytoplasme: milieu intérieur\n- Noyau: siège du génome\n- Mitochondries: respiration cellulaire\n- Chloroplastes: photosynthèse\n- Vacucuoles: stockage\n\n## Parties d'une cellule animale\n- Membrane plasmique\n- Cytoplasme\n- Noyau\n- Mitochondries\n\n## Fonction\nLa cellule est l'unité structurelle et fonctionnelle du vivant."),
        ("svt","Le système digestif","Niveau: 2nde\n\n# Système digestif\n\n## Parcours de l'aliment\n1. Bouche: mastication, salive\n2. Estomac: digestion chimique\n3. Intestin grêle: absorption des nutriments\n4. Gros intestin: formation des déjections\n\n## Organes accessoires\n- Foie: production de bile\n- Pancréas: enzymes digestives\n- Glandes salivaires\n\n## Principes\n- Hydrolyse des macromolécules\n- Absorption des nutriments\n- Élimination des déchets"),
        ("info","Les algorithmes","Niveau: Terminale\n\n# Algorithmes\n\n## Définition\nEnsemble d'instructions pour résoudre un problème.\n\n## Caractéristiques\n- Une instruction à executer à la fois\n- Un nombre fini d'étapes\n- Précision et clarté\n\n## Pseudo-code\n```\nDebut\n  initialiser variables\n  lire données\n  traitement\n  afficher résultat\nFin\n```\n\n## Exemples\n- Algorithme de tri\n- Algorithme de recherche dichotomique\n- Algorithme d'Euclide"),
        ("info","Les bases de données","Niveau: Terminale\n\n# Bases de données\n\n## Schéma\n- Une BDD = ensemble de tables\n- Chaque table = entités\n- Lignes = enregistrements\n- Colonnes = attributs\n\n## Requêtes SQL\n```\nSELECT * FROM users WHERE age > 18;\nINSERT INTO users (name) VALUES ('Maria');\nUPDATE users SET name='Karim' WHERE id=5;\nDELETE FROM users WHERE id=5;\n```\n\n## Modèle relationnel\n- Clé primaire: identifiant unique\n- Clé étrangère: lien entre tables\n- Normalisation: réduire redondance"),
        ("eco","La monnaie","Niveau: Terminale\n\n# La monnaie\n\n## Fonctions\n1. Facilitatrice des échanges (intermédiaire)\n2. Unité de compte\n3. Réserve de valeur\n\n## Taux de change\nLe prix d'une devise en termes d'une autre.\n- 1 EUR = 650 XOF (fixe pour l'UEMOA)\n\n## Politique monétaire\n- Banque Centrale: émet la monnaie\n- Taux d'intérêt: influence la demande\n- Quantité de monnaie: impacte l'inflation"),
        ("eco","Le commerce international","Niveau: Terminale\n\n# Commerce international\n\n## Avantages\n- Complémentarité des ressources\n- Économies d'échelle\n- Accès aux technologies\n\n## Obstacles\n- Droits de douane\n- Normes qualité\n- Fluctuation des devises\n\n## Accords\n- Zone de libre-échange (CEDEAO)\n- OMC (Organisation Mondiale du Commerce)"),
        ("es","Los verbos en -ar","Niveau: 1ère\n\n# Verbes en -ar (Presente)\n\n## Conjugación\n| Pronombre | Verbo (-ar) |\n|-----------|------------|\n| yo        | -o         |\n| tú        | -as        |\n| él/ella   | -a         |\n| nosotros  | -amos      |\n| vosotros  | -áis       |\n| ellos     | -an        |\n\n## Ejemplos\n- hablar → yo hablo, tú hablas\n- comer → yo como, tú comes\n- vivir → yo vivo, tú vives\n\n## Reglas\n- Los verbos en -ar terminan en -o, -as, -a, -amos, -áis, -an.\n- Los verbos en -er y -ir tienen terminaciones diferentes."),
        ("ara","Alphabet arabe","Niveau: 1ère\n\n# L'alphabet arabe\n\n## Lettres\nا ب ت ث ج ح خ د ذ ر ز س ش ص ض ط ظ ع غ ف ق ك ل م ن ه و ي\n\n## Exemples de mots\n- السلام (al-salam) = paix\n- العلم (al-ilm) = science\n- كتاب (kitab) = livre\n- مدرسة (madrasa) = école\n\n## Prononciation\n- Les voyelles courtes: fatha (a), damma (u), kasra (i)\n- Les voyelles longues: ā, ū, ī\n- La sunna (shamsiyyah) et la lune (qamariyyah)"),
    ]
    for s, t, c2 in matieres:
        c.execute("INSERT OR IGNORE INTO cours (sujet_code,titre,contenu,niveau) VALUES (?,?,?,?)", (s, t, c2, "1ère-Terminale"))

    # 528 exercices from data_seed.py
    for e in SEED_EXERCICES:
        c.execute("INSERT OR IGNORE INTO exercises (sujet_code,titre,niveau,type,question,reponse,explication) VALUES (?,?,?,?,?,?,?)", tuple(e))

    # 720 quiz from data_seed.py
    for q in SEED_QUIZ:
        c.execute("INSERT OR IGNORE INTO quiz (categorie,question,reponse,explication) VALUES (?,?,?,?)", tuple(q))

    c.execute("INSERT OR IGNORE INTO users (pseudo,email,mot_de_passe,niveau,role,created_at) VALUES (?,?,?,?,?,?)",
              ("admin","admin@ecolemax.sn",hash_pass("ecolemax2026"),"Administrateur","admin",now()))

    c.execute("INSERT OR IGNORE INTO notifications (user_id,titre,message,type,lu,date) VALUES (?,?,?,?,?,?)",
              (None,"🎉 Bienvenue sur ÉcoleMax !","Essai gratuit de 48 H actif. IA illimitée pour la test.",  "system",0,now()))
    c.execute("INSERT OR IGNORE INTO notifications (user_id,titre,message,type,lu,date) VALUES (?,?,?,?,?,?)",
              (None,"🚀 Nouveau : Traduction IA","10 langues disponibles dans l'app !","system",0,now()))
    c.execute("INSERT OR IGNORE INTO notifications (user_id,titre,message,type,lu,date) VALUES (?,?,?,?,?,?)",
              (None,"📸 Correction photo IA","Envoie ton exercice écrit, l'IA corrige !","system",0,now()))
    c.execute("INSERT OR IGNORE INTO notifications (user_id,titre,message,type,lu,date) VALUES (?,?,?,?,?,?)",
              (None,"🎓 528 exercices","Nouvelles matières disponibles","system",0,now()))

    c.commit()
    c.close()
    return True

def plan_actif(u):
    c = db()
    a = c.execute("SELECT * FROM abonnements WHERE user_id=? AND statut='actif'", (u["id"],)).fetchone()
    if a:
        p = c.execute("SELECT * FROM plans WHERE code=?", (a["plan_code"],)).fetchone()
        if p:
            c.close()
            return dict(p)
    g = c.execute("SELECT * FROM plans WHERE code='gratuit'").fetchone()
    c.close()
    return dict(g)

def check_quota(u, p, type_usage):
    # Limites depuis la table plans (colonnes limite_ia_jour, photo_jour)
    # IA illimitée pour tous les eleves inscrits pour le test
    if type_usage == "ia":
        limite = p.get("limite_ia_jour", 999999)
        if limite <= 0: return False, "Quota IA épuisé pour ce plan"
        return True, "OK"
    if type_usage == "photo":
        limite = p.get("photo_jour", 0)
        if limite <= 0: return False, "Quota photo épuisé pour ce plan"
        return True, "OK"
    if type_usage == "correct":
        # Correction IA sans limite (meilleur apprentissage)
        return True, "OK"
    return True, "OK"

def update_usage(uid, type_usage):
    c = db()
    d = datetime.date.today().isoformat()
    row = c.execute("SELECT * FROM usages WHERE user_id=? AND date=?", (uid, d)).fetchone()
    if row:
        col = {"ia":"ia_count","photo":"photo_count","correct":"correct_count","ex":"ex_count"}.get(type_usage)
        if col:
            val = row[col] + 1
            c.execute("UPDATE usages SET "+col+"=? WHERE user_id=? AND date=?", (val, uid, d))
    else:
        ia = 0; photo = 0; corr = 0; ex = 0
        if type_usage == "ia": ia = 1
        elif type_usage == "photo": photo = 1
        elif type_usage == "correct": corr = 1
        elif type_usage == "ex": ex = 1
        c.execute("INSERT INTO usages (user_id,date,ia_count,photo_count,correct_count,ex_count) VALUES (?,?,?,?,?,?)",
                  (uid, d, ia, photo, corr, ex))
    c.commit()
    c.close()

def get_iou_ai(q, max_tokens=OVH_AI_MAX_TOKENS, temperature=0.4, max_retries=2, silent=False):
    with _ai_sem:
        print(f"🟣 AI OVH → model={OVH_AI_MODEL} max_tokens={max_tokens} q={q[:60]}...")
        messages = [
            {"role": "system", "content": "Tu es un professeur patient et pédagogue. Réponds TOUJOURS en français, clair, concis et adapté au niveau scolaire de l'élève."},
            {"role": "user", "content": q}
        ]
        payload = {"model": OVH_AI_MODEL, "messages": messages, "max_tokens": max_tokens, "temperature": temperature}
        data = json.dumps(payload).encode()
        last_err = ""
        for attempt in range(max_retries + 1):
            try:
                req = urllib.request.Request(OVH_AI_URL, data=data, method="POST")
                req.add_header("Content-Type", "application/json")
                with urllib.request.urlopen(req, timeout=OVH_AI_TIMEOUT) as resp:
                    result = json.loads(resp.read().decode())
                    text = result["choices"][0]["message"]["content"].strip()
                    if not silent: print(f"✅ AI OVH OK ({len(text)} chars)")
                    return True, text, OVH_AI_MODEL
            except Exception as e:
                last_err = str(e)
                if attempt < max_retries:
                    time.sleep(2 * (attempt + 1))
        if not silent: print(f"❌ AI OVH FAIL: {last_err}")
        return False, "", last_err

def get_iou_ai_vision(q, image_b64, max_tokens=OVH_AI_MAX_TOKENS, temperature=0.3, silent=False):
    with _ai_sem:
        print(f"🟣 AI OVH Vision → model={OVH_AI_MODEL} q={q[:50]}...")
        payload = {
            "model": OVH_AI_MODEL,
            "messages": [{"role": "system", "content": "Tu es un professeur patient. Décris et analyse cette image pédagogiquement, en français."},
            {"role": "user", "content": [
                {"type": "text", "text": q},
                {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + image_b64}}
            ]}],
            "max_tokens": max_tokens, "temperature": temperature
        }
        data = json.dumps(payload).encode()
        last_err = ""
        for attempt in range(3):
            try:
                req = urllib.request.Request(OVH_AI_URL, data=data, method="POST")
                req.add_header("Content-Type", "application/json")
                with urllib.request.urlopen(req, timeout=OVH_AI_TIMEOUT) as resp:
                    result = json.loads(resp.read().decode())
                    text = result["choices"][0]["message"]["content"].strip()
                    if not silent: print(f"✅ AI OVH Vision OK ({len(text)} chars)")
                    return True, text, OVH_AI_MODEL
            except Exception as e:
                last_err = str(e)
                if attempt < 2:
                    time.sleep(2 * (attempt + 1))
        if not silent: print(f"❌ AI OVH Vision FAIL: {last_err}")
        return False, "", last_err

def get_iou_ai_fallback(q, max_tokens=OVH_AI_MAX_TOKENS, silent=False):
    with _ai_sem:
        print(f"🟣 AI OVH Fallback → model={OVH_AI_FALLBACK}")
        payload = {"model": OVH_AI_FALLBACK, "messages": [{"role": "system", "content": "Tu es un professeur patient. Réponds TOUJOURS en français, clair et pédagogique."},{"role": "user", "content": q}], "max_tokens": max_tokens, "temperature": 0.4}
        data = json.dumps(payload).encode()
        try:
            req = urllib.request.Request(OVH_AI_URL, data=data, method="POST")
            req.add_header("Content-Type", "application/json")
            with urllib.request.urlopen(req, timeout=OVH_AI_TIMEOUT) as resp:
                result = json.loads(resp.read().decode())
                text = result["choices"][0]["message"]["content"].strip()
                if not silent: print(f"✅ AI OVH Fallback OK ({len(text)} chars)")
                return True, text, OVH_AI_FALLBACK
        except Exception as e:
            if not silent: print(f"❌ AI OVH Fallback FAIL: {e}")
        return False, "", str(e)

def get_iou_ai_fallback_vision(q, image_b64, silent=False):
    with _ai_sem:
        print(f"🟣 AI OVH Fallback Vision → model={OVH_AI_FALLBACK}")
        payload = {
            "model": OVH_AI_FALLBACK,
            "messages": [{"role": "user", "content": [
                {"type": "text", "text": q},
                {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + image_b64}}
            ]}],
            "max_tokens": OVH_AI_MAX_TOKENS, "temperature": 0.3
        }
        data = json.dumps(payload).encode()
        try:
            req = urllib.request.Request(OVH_AI_URL, data=data, method="POST")
            req.add_header("Content-Type", "application/json")
            with urllib.request.urlopen(req, timeout=OVH_AI_TIMEOUT) as resp:
                result = json.loads(resp.read().decode())
                text = result["choices"][0]["message"]["content"].strip()
                if not silent: print(f"✅ AI OVH Fallback Vision OK ({len(text)} chars)")
                return True, text, OVH_AI_FALLBACK
        except Exception as e:
            if not silent: print(f"❌ AI OVH Fallback Vision FAIL: {e}")
        return False, "", str(e)

def get_pollinations(q, max_tokens=OVH_AI_MAX_TOKENS, silent=False):
    with _ai_sem:
        last_err = ""
        now_t = time.time()
        global _last_pollinations_call
        if '_last_pollinations_call' not in globals(): _last_pollinations_call = 0
        if now_t - _last_pollinations_call < _POLLINATIONS_MIN_INTERVAL:
            wait = _POLLINATIONS_MIN_INTERVAL - (now_t - _last_pollinations_call)
            if not silent: print(f"⏳ Pollinations rate limit, waiting {wait:.0f}s")
            time.sleep(wait)
        _last_pollinations_call = time.time()
        payload = {"model": "openai", "messages": [{"role": "system", "content": "Tu es un professeur patient. Réponds TOUJOURS en français, clair et pédagogique."},{"role": "user", "content": q}], "max_tokens": max_tokens, "temperature": 0.5}
        data = json.dumps(payload).encode()
        try:
            req = urllib.request.Request(POLLINATIONS_URL, data=data, method="POST")
            req.add_header("Content-Type", "application/json")
            with urllib.request.urlopen(req, timeout=OVH_AI_TIMEOUT) as resp:
                result = json.loads(resp.read().decode())
                text = result["choices"][0]["message"]["content"].strip()
                if not silent: print(f"✅ Pollinations OK ({len(text)} chars)")
                return True, text, "Pollinations"
        except Exception as e:
            last_err = str(e)
        if not silent: print(f"❌ Pollinations FAIL: {last_err}")
        return False, "", last_err

def get_pollinations_vision(q, image_b64, silent=False):
    with _ai_sem:
        last_err = ""
        payload = {
            "model": "openai",
            "messages": [{"role": "system", "content": "Tu es un professeur patient. Décris et analyse cette image pédagogiquement, en français."},
            {"role": "user", "content": [
                {"type": "text", "text": q},
                {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + image_b64}}
            ]}],
            "max_tokens": OVH_AI_MAX_TOKENS, "temperature": 0.3
        }
        data = json.dumps(payload).encode()
        try:
            req = urllib.request.Request(POLLINATIONS_URL, data=data, method="POST")
            req.add_header("Content-Type", "application/json")
            with urllib.request.urlopen(req, timeout=OVH_AI_TIMEOUT) as resp:
                result = json.loads(resp.read().decode())
                text = result["choices"][0]["message"]["content"].strip()
                if not silent: print(f"✅ Pollinations Vision OK ({len(text)} chars)")
                return True, text, "Pollinations Vision"
        except Exception as e:
            last_err = str(e)
        if not silent: print(f"❌ Pollinations Vision FAIL: {last_err}")
        return False, "", last_err

def local_reponse_math(q):
    if any(k in q.lower() for k in ["calcul", "solve", "solution", "explication"]):
        return "Pour résoudre ce problème mathématique, je vais vous guider pas à pas. Veuillez me donner plus de détails sur l'exercice à résoudre (énoncé complet, domaine, difficulté). Je peux vous aider sur:\n\n• Équations et inéquations\n• Fonctions et dérivées\n• Calculs matriciels\n• Probabilités et statistiques\n• Géométrie analytique\n• Trigonométrie\n\nVeuillez fournir l'énoncé complet pour une résolution détaillée. 🎓"
    return "Je suis un assistant spécialisé en mathématiques. Posez votre question et je vous aiderai à la résoudre avec une explication détaillée. Je peux intervenir sur les domaines suivants:\n\n• Algèbre (équations, matrices, suites)\n• Analyse (fonctions, limites, dérivées, intégrales)\n• Géométrie (trigonométrie, vecteurs, figures)\n• Probabilités et statistiques\n• Arithmétique et logique\n\nFaites-moi votre question ! 🎓"

def local_reponse_fr(q):
    if "conjuguer" in q.lower():
        return "Je peux conjuguer n'importe quel verbe français à tous les temps (présent, imparfait, passé composé, futur, conditionnel...). Veuillez me donner:\n• Le verbe à conjuguer\n• Le temps souhaité\n• Le pronom (je, tu, il, nous, vous, ils)\n\nExemple: « conjuguer 'finir' au futur simple, 3e personne du pluriel »"
    if "accord" in q.lower():
        return "Pour les accords:\n\n• Accord du participe passé:\n  - Avec 'avoir': l'auxiliaire détermine l'accord\n  - Avec 'être': accord avec le sujet\n  - Le participe reste invariable avec: pouvoir, falloir, vouloir, savoir, rester, venir\n\n• Accord de l'adjectif:\n  - Masculin/féminin: -e, -es, -es\n  - Pluriel: -s, -x (eux)\n  - Invariable: court, gros, doux, bleu, etc.\n\nDonnez-moi votre phrase pour une correction détaillée !"
    if "grammaire" in q.lower() or "pronom" in q.lower():
        return "Je peux vous aider sur:\n• Les pronoms (personnels, possessifs, démonstratifs, relatifs)\n• Les déterminants\n• Les prépositions\n• Les conjonctions\n• Les modes (verbe, nom, adjectif, adverbe)\n\nPosez votre question de grammaire !"
    return "Je suis un assistant de français. Je peux vous aider sur:\n\n• Grammaire (conjugaison, accords, pronoms)\n• Orthographe et vocabulaire\n• Rédaction et syntaxe\n• Lecture de textes\n• Correction de phrases\n\nFaites-moi votre question ! 🎓"

def local_reponse_svt(q):
    return "Je suis un assistant de SVT. Je peux vous aider sur:\n\n• Biologie cellulaire et moléculaire\n• Physiologie humaine\n• Écologie et environnement\n• Génétique et évolution\n• Classification du vivant\n• Anatomie végétale et animale\n\nPosez votre question de SVT ! 🧬🌱"

def local_reponse_histoire(q):
    return "Je suis un assistant d'Histoire-Géographie. Je peux vous aider sur:\n\n• Histoire du Sénégal et de l'Afrique\n• Histoire mondiale (chronologie, faits marquants)\n• Géographie physique et humaine\n• Cartes et localisations\n• Démographie et économie\n\nPosez votre question ! 🌍📜"

def local_reponse_phys(q):
    return "Je suis un assistant de Physique. Je peux vous aider sur:\n\n• Mécanique (cinématique, dynamique, thermodynamique)\n• Électricité et magnétisme\n• Optique (lumière, vagues)\n• Ondes et acoustique\n• Physique moderne (relativité, quantiques)\n\nPosez votre question de Physique ! ⚡"

def local_reponse_chimie(q):
    return "Je suis un assistant de Chimie. Je peux vous aider sur:\n\n• Chimie organique et inorganique\n• Équilibres chimiques\n• Thermodynamique et cinétique\n• Electrochimie\n• Tableau périodique et propriétés\n• Réactions et mécanismes\n\nPosez votre question de Chimie ! 🧪"

def local_reponse_info(q):
    return "Je suis un assistant d'Informatique. Je peux vous aider sur:\n\n• Algorithmique et complexité\n• Bases de données (SQL)\n• Développement (Python, HTML, CSS, JS)\n• Structures de données\n• Réseaux et architectures\n• Sécurité informatique\n\nPosez votre question ! 💻"

def local_reponse_eco(q):
    return "Je suis un assistant d'Économie. Je peux vous aider sur:\n\n• Macroéconomie (inflation, taux, monnaie)\n• Microéconomie (marchés, offre-demande)\n• Économie du développement\n• Commerce international\n• Statistiques économiques\n\nPosez votre question ! 📊"

def local_reponse_langue(q):
    return "Je peux vous aider sur:\n\n• Anglais: grammaire, vocabulaire, conversation\n• Espagnol: conjugaison, vocabulaire\n• Arabe: alphabet, traduction, grammaire\n\nPosez votre question en langue !"

def local_reponse_multi(q):
    return "Je suis un assistant multidisciplinaire pour le bac S1/S2 au Sénégal. Posez votre question en:\n\n• Mathématiques\n• Physique\n• Chimie\n• SVT\n• Français\n• Histoire-Géographie\n• Informatique\n• Économie\n• Anglais / Espagnol / Arabe\n\nJe vous répondrai avec une explication pédagogique complète ! 🎓📚"

def detect_matier(q):
    ql = q.lower()
    if any(k in ql for k in ["math", "calcul", "matrice", "dérivée", "dérivé", "équation", "fonction", "intégrale", "trigono", "logarithm"]):
        return "math"
    if any(k in ql for k in ["français", "france", "conjugaison", "grammaire", "accord", "participe", "pronom", "verbe français"]):
        return "fr"
    if any(k in ql for k in ["physique", "mécanique", "thermodynamique", "électricité", "optique", "force", "newton", "ohm"]):
        return "phys"
    if any(k in ql for k in ["chimie", "organique", "tableau périodique", "atome", "équilibre", "oxydoréduction", "ph"]):
        return "chim"
    if any(k in ql for k in ["histoire", "chronologie", "sénégal", "afrique", "colonisation", "indépendance", "senghor"]):
        return "hist"
    if any(k in ql for k in ["géographie", "carte", "climat", "ressources", "démographie", "région"]):
        return "geo"
    if any(k in ql for k in ["svt", "biologie", "cellule", "organe", "système", "génétique", "écologie"]):
        return "svt"
    if any(k in ql for k in ["anglais", "english", "grammaire anglaise", "present", "past", "tense"]):
        return "eng"
    if any(k in ql for k in ["informatique", "algorithme", "base de données", "sql", "programmation", "python"]):
        return "info"
    if any(k in ql for k in ["économie", "eco", "inflation", "monnaie", "paiement", "taux de change", "commerce"]):
        return "eco"
    if any(k in ql for k in ["espagnol", "español", "verbe en -ar", "conjugaison espagnol"]):
        return "es"
    if any(k in ql for k in ["arabe", "arabic"]):
        return "ara"
    return "multi"

def get_local_reponse(q):
    sub = detect_matier(q)
    funcs = {
        "math": local_reponse_math, "fr": local_reponse_fr,
        "svt": local_reponse_svt, "hist": local_reponse_histoire,
        "phys": local_reponse_phys, "chim": local_reponse_chimie,
        "info": local_reponse_info, "eco": local_reponse_eco,
        "eng": local_reponse_langue, "es": local_reponse_langue,
        "ara": local_reponse_langue, "geo": local_reponse_histoire, "multi": local_reponse_multi
    }
    return funcs.get(sub, local_reponse_multi)(q)

def reponse_ia(q, plan=None):
    q_send = q[:1500]
    try:
        ok, text, src = get_iou_ai(q_send, max_tokens=OVH_AI_MAX_TOKENS)
        if ok: return {"reponse": text, "source": src, "succes": True}
    except Exception as e:
        pass
    try:
        ok, text, src = get_iou_ai_fallback(q_send, max_tokens=OVH_AI_MAX_TOKENS)
        if ok: return {"reponse": text, "source": src, "succes": True}
    except Exception as e:
        pass
    try:
        ok, text, src = get_pollinations(q_send, max_tokens=OVH_AI_MAX_TOKENS)
        if ok: return {"reponse": text, "source": src, "succes": True}
    except Exception as e:
        pass
    return {"reponse": get_local_reponse(q_send), "source": "Local", "succes": True}

def reponse_ia_vision(q, image_b64, plan=None):
    q_send = q[:500] if q else "Décris et analyse cette image de façon pédagogique."
    try:
        ok, text, src = get_iou_ai_vision(q_send, image_b64, max_tokens=OVH_AI_MAX_TOKENS)
        if ok: return {"reponse": text, "source": src, "succes": True}
    except Exception as e:
        pass
    try:
        ok, text, src = get_iou_ai_fallback_vision(q_send, image_b64)
        if ok: return {"reponse": text, "source": src, "succes": True}
    except Exception as e:
        pass
    try:
        ok, text, src = get_pollinations_vision(q_send, image_b64)
        if ok: return {"reponse": text, "source": src, "succes": True}
    except Exception as e:
        pass
    return {"reponse": "⚠️ IA vision indisponible momentanément. Veuillez réessayer.", "source": "Local", "succes": False}

def reponse_ia_photo(question, image_b64, plan=None):
    q = question or "Décris cette image et explique en détail ce qui est écrit. C'est un exercice d'élève."
    ok, text, src = get_iou_ai_vision(q, image_b64, max_tokens=OVH_AI_MAX_TOKENS, temperature=0.3)
    if ok: return {"reponse": text, "source": src, "succes": True}
    ok, text, src = get_iou_ai_fallback_vision(q, image_b64)
    if ok: return {"reponse": text, "source": src, "succes": True}
    ok, text, src = get_pollinations_vision(q, image_b64)
    if ok: return {"reponse": text, "source": src, "succes": True}
    return {"reponse": "⚠️ Correction photo indisponible. Veuillez réessayer.", "source": "Local", "succes": False}

def reponse_traduction(texte, langue, plan=None):
    langues = {
        "fr": "français", "en": "anglais", "es": "espagnol",
        "pt": "portugais", "ar": "arabe", "de": "allemand",
        "zh": "mandarin", "hi": "hindi", "ru": "russe", "ja": "japonais"
    }
    nom_langue = langues.get(langue, langue)
    prompt = "Traduis ce texte en " + nom_langue + ". Donne uniquement la traduction, rien d'autre. Texte : " + texte
    ok, trad, src = get_iou_ai(prompt, max_tokens=1000, temperature=0.1, silent=True)
    if ok: return {"reponse": trad, "langue": langue, "source": src, "succes": True}
    ok, trad, src = get_iou_ai_fallback(prompt, max_tokens=1000, silent=True)
    if ok: return {"reponse": trad, "langue": langue, "source": src, "succes": True}
    ok, trad, src = get_pollinations(prompt, max_tokens=1000, silent=True)
    if ok: return {"reponse": trad, "langue": langue, "source": src, "succes": True}
    return {"reponse": "⚠️ Traduction indisponible momentanément", "langue": langue, "source": "Local", "succes": False}

# ─── Flask App ───
# Import des données seeds (528 exercices, 720 quiz)
from data_seed import EXERCICES as SEED_EXERCICES, QUIZ as SEED_QUIZ
from flask import Flask, request, jsonify, send_file, Response

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10MB max par requête

def get_user_by_token(req):
    auth = req.headers.get("Authorization","")
    if not auth.startswith("Bearer "): return None
    token = auth[7:]
    payload = jwt_decode(token)
    if not payload: return None
    c = db()
    u = c.execute("SELECT * FROM users WHERE id=?", (payload["uid"],)).fetchone()
    c.close()
    return u

@app.route("/health")
@app.route("/api/health")
def health():
    return jsonify({"status":"ok","service":"ecolemax","time":now()})

# ─── Serveur de fichiers statiques ───
PROJET_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "projet")

@app.route("/")
@app.route("/index.html")
def index():
    return serve_html("index.html")

@app.route("/app")
@app.route("/app.html")
def app_html():
    return serve_html("app.html")

@app.route("/dashboard")
@app.route("/dashboard.html")
def dashboard():
    return serve_html("dashboard.html")

@app.route("/telecharger.html")
def telecharger():
    return serve_html("telecharger.html")

@app.route("/tester.html")
def tester():
    return serve_html("tester.html")

@app.route("/securite.html")
def securite():
    return serve_html("securite.html")

@app.route("/EcoleMax.apk")
def apk():
    return send_file(os.path.join(os.path.dirname(os.path.abspath(__file__)), "EcoleMax.apk"), as_attachment=True)

@app.route("/favicon.ico")
def favicon():
    fp = os.path.join(PROJET_DIR, "favicon.ico")
    if os.path.exists(fp):
        return send_file(fp)
    return Response(status=404)

# Route catch-all pour tous les fichiers statiques (CSS, JS, assets, images)
@app.route("/static/<path:filename>")
@app.route("/css/<path:filename>")
@app.route("/js/<path:filename>")
@app.route("/assets/<path:filename>")
@app.route("/pwa/<path:filename>")
@app.route("/qr/<path:filename>")
@app.route("/<path:filename>")  # Route racine pour fichiers statiques JS/CSS
def static_files(filename):
    # Chercher dans plusieurs dossiers
    for sub in ["", "css", "js", "assets", "pwa", "qr", "outils", "telechargements"]:
        fp = os.path.join(PROJET_DIR, sub, filename) if sub else os.path.join(PROJET_DIR, filename)
        if os.path.isfile(fp):
            # Détecter le type MIME
            ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
            mime = {
                "css": "text/css", "js": "application/javascript",
                "html": "text/html", "png": "image/png", "jpg": "image/jpeg",
                "jpeg": "image/jpeg", "svg": "image/svg+xml", "ico": "image/x-icon",
                "json": "application/json", "webmanifest": "application/manifest+json",
                "woff": "font/woff", "woff2": "font/woff2", "ttf": "font/ttf",
            }.get(ext, "application/octet-stream")
            return send_file(fp, mimetype=mime)
    return Response("404 Not Found", status=404)

def serve_html(filename):
    """Sert un fichier HTML avec le bon Content-Type et injecte l'URL API."""
    fp = os.path.join(PROJET_DIR, filename)
    if not os.path.isfile(fp):
        return Response("404 Not Found", status=404, mimetype="text/html")
    with open(fp, "r", encoding="utf-8") as f:
        content = f.read()
    # Injecter l'URL API absolute — gère plusieurs formats
    api_url = request.host_url.rstrip("/")
    # Format 1: const API = window.__ECOLEMAX_API__ || "";
    content = content.replace(
        'const API = window.__ECOLEMAX_API__ || "";',
        f'const API = window.__ECOLEMAX_API__ || "{api_url}";'
    )
    # Format 2: const API="";
    content = content.replace(
        'const API="";',
        f'const API="{api_url}";'
    )
    # Format 3: const API = "";
    content = content.replace(
        'const API = "";',
        f'const API = "{api_url}";'
    )
    # Corriger s.categorie → s.description (sujets table n'a pas categorie)
    content = content.replace("s.categorie", "s.description")
    resp = Response(content, mimetype="text/html; charset=utf-8")
    resp.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    resp.headers["X-Content-Type-Options"] = "nosniff"
    return resp

@app.route("/api/plans")
def api_plans():
    c = db()
    rows = c.execute("SELECT * FROM plans ORDER BY prix").fetchall()
    c.close()
    return jsonify([dict(r) for r in rows])

@app.route("/api/subjects")
def api_subjects():
    c = db()
    rows = c.execute("SELECT * FROM sujets ORDER BY ordre").fetchall()
    c.close()
    return jsonify([dict(r) for r in rows])

@app.route("/api/content")
def api_content():
    c = db()
    sujets = c.execute("SELECT * FROM sujets ORDER BY ordre").fetchall()
    cours = c.execute("SELECT * FROM cours ORDER BY sujet_code, titre").fetchall()
    c.close()
    return jsonify({"sujets":[dict(s) for s in sujets], "cours":[dict(c) for c in cours]})

@app.route("/api/languages")
def api_languages():
    return jsonify({"langues":[
        {"code":"fr","nom":"Français","emoji":"🇫🇷"},
        {"code":"en","nom":"Anglais","emoji":"🇬🇧"},
        {"code":"es","nom":"Espagnol","emoji":"🇪🇸"},
        {"code":"pt","nom":"Portugais","emoji":"🇵🇹"},
        {"code":"ar","nom":"Arabe","emoji":"🇸🇦"},
        {"code":"de","nom":"Allemand","emoji":"🇩🇪"},
        {"code":"zh","nom":"Mandarin","emoji":"🇨🇳"},
        {"code":"hi","nom":"Hindi","emoji":"🇮🇳"},
        {"code":"ru","nom":"Russe","emoji":"🇷🇺"},
        {"code":"ja","nom":"Japonais","emoji":"🇯🇵"},
    ]})

@app.route("/api/exercises")
def api_exercises():
    sujet = request.args.get("sujet","")
    niveau = request.args.get("niveau","")
    difficulte = request.args.get("difficulte","")
    limite = request.args.get("limite","")
    c = db()
    q = "SELECT * FROM exercises WHERE 1=1"
    params = []
    if sujet: q += " AND sujet_code=?"; params.append(sujet)
    if niveau: q += " AND niveau=?"; params.append(niveau)
    if difficulte: q += " AND difficulte=?"; params.append(difficulte)
    if limite: q += " LIMIT " + str(int(limite))
    rows = c.execute(q, params).fetchall()
    c.close()
    # Extraire les options de la question [opt1/opt2/opt3]
    import re as _re
    import json as _json
    result = []
    for r in rows:
        ex = dict(r)
        question = ex.get("question","")
        m = _re.search(r"\[([a-zA-ZÀ-ÿ0-9]+(?:/[a-zA-ZÀ-ÿ0-9]+)+)\]", question)
        if m:
            opts = [o.strip() for o in m.group(1).split("/")]
            ex["options"] = _json.dumps(opts, ensure_ascii=False)
            ex["question"] = _re.sub(r"\s*\[([a-zA-ZÀ-ÿ0-9]+(?:/[a-zA-ZÀ-ÿ0-9]+)+)\]", "", question).strip()
        else:
            ex["options"] = "[]"
        result.append(ex)
    return jsonify({"exercices": result})

@app.route("/api/quiz")
def api_quiz():
    categorie = request.args.get("categorie","")
    difficulte = request.args.get("difficulte","")
    limite = request.args.get("limite","")
    c = db()
    q = "SELECT * FROM quiz WHERE 1=1"
    params = []
    if categorie: q += " AND categorie=?"; params.append(categorie)
    if difficulte: q += " AND difficulte=?"; params.append(difficulte)
    if limite: q += " LIMIT " + str(int(limite))
    rows = c.execute(q, params).fetchall()
    c.close()
    # Générer les options dynamiquement
    import random as _random
    import json as _json2
    # Pool de réponses wrong par catégorie
    _wrong_pools = {
        "Géographie": ["Conakry","Bamako","Abidjan","Ouagadougou","Dakar","Saint-Louis","Ziguinchor","Lomé","Cotonou","Niamey"],
        "Histoire": ["1960","1965","1970","1958","Senghor","Diouf","Wade","Macky","Goree","Saint-Louis"],
        "Maths": ["2x","3x","5x","10","15","20","100","0","1","1000"],
        "Français": ["cheval","chevaux","pronom relatif","qui","que","où","en","au","du","les"],
        "Physique": ["Newton","300000 km/s","énergie","masse","vitesse","accélération","force","travail","puissance","moment"],
        "Chimie": ["H₂O","CO₂","7","14","1","100","Zn","Cu","O₂","N₂"],
        "SVT": ["cœur","gène","photosynthèse","cellule","organite","ADN","ARN","proteine","sang","nerf"],
        "Anglais": ["hello","books","je suis","good","bad","yes","no","one","two","three"],
        "Informatique": ["&&","CSS","CREATE","O(log n)","Python","Java","HTML","SQL","algorithme","base de données"],
        "Économie": ["XOF","FCFA","BCEAO","OMC","1 EUR","500","1000","2000","inflation","taux"],
    }
    result = []
    for r in rows:
        qz = dict(r)
        idx = qz.get("reponse", 0)
        if idx >= 4: idx = 0
        correct = qz.get("explication", "")
        cat = qz.get("categorie", "")
        pool = _wrong_pools.get(cat, ["Option A","Option B","Option C","Option D"])
        wrong = _random.sample([p for p in pool if p != correct], min(3, len(pool)-1)) if len(pool) > 1 else ["A","B","C"]
        while len(wrong) < 3: wrong.append(f"Option {chr(65+len(wrong))}")
        options = [""] * 4
        for i in range(4):
            if i == idx: options[i] = correct
            else: options[i] = wrong.pop(0) if wrong else f"Option {chr(65+i)}"
        qz["options"] = _json2.dumps(options, ensure_ascii=False)
        result.append(qz)
    return jsonify({"quiz": result})

@app.route("/api/register", methods=["POST"])
def api_register():
    data = request.get_json(silent=True) or {}
    pseudo = data.get("pseudo","").strip()
    mdp = data.get("mot_de_passe","")
    email = data.get("email","").strip()
    niveau = data.get("niveau","Terminale")
    if len(pseudo) < 3: return jsonify({"erreur":"Pseudo trop court"}), 400
    if len(mdp) < 8 or not re.search(r'[A-Za-z]', mdp) or not re.search(r'\d', mdp):
        return jsonify({"erreur":"Mot de passe : 8+ caractères, lettre + chiffre"}), 400
    c = db()
    if c.execute("SELECT id FROM users WHERE pseudo=?", (pseudo,)).fetchone():
        c.close()
        return jsonify({"erreur":"Ce pseudo est déjà pris"}), 409
    c.execute("INSERT INTO users (pseudo,email,mot_de_passe,niveau,created_at) VALUES (?,?,?,?,?)",
              (pseudo,email,hash_pass(mdp),niveau,now()))
    uid = c.execute("SELECT id FROM users WHERE pseudo=?", (pseudo,)).fetchone()["id"]
    c.execute("INSERT INTO sessions (token,user_id,expires_at,created_at) VALUES (?,?,?,?)",
              (jwt_create(uid),uid,datetime.datetime.now().isoformat(),now()))
    c.execute("INSERT INTO notifications (user_id,titre,message,type,lu,date) VALUES (?,?,?,?,?,?)",
              (uid,"Bienvenue sur ÉcoleMax !","Ton essai gratuit de 48 H est activé. IA illimitée. Bon apprentissage 🎓","system",0,now()))
    c.commit()
    c.close()
    log_sec(uid, "inscription", "Nouvel élève")
    return jsonify({"ok":True,"token":jwt_create(uid),"user":{"id":uid,"pseudo":pseudo}})

@app.route("/api/login", methods=["POST"])
def api_login():
    data = request.get_json(silent=True) or {}
    pseudo = data.get("pseudo","")
    mdp = data.get("mot_de_passe","")
    c = db()
    u = c.execute("SELECT * FROM users WHERE pseudo=?", (pseudo,)).fetchone()
    c.close()
    if not u or not verify_pass(mdp, u["mot_de_passe"]):
        return jsonify({"erreur":"Identifiants invalides"}), 401
    log_sec(u["id"], "connexion", "Connexion élève")
    return jsonify({"ok":True,"token":jwt_create(u["id"]),"user":{"id":u["id"],"pseudo":u["pseudo"]}})

@app.route("/api/me")
def api_me():
    u = get_user_by_token(request)
    if not u: return jsonify({"erreur":"Authentification requise"}), 401
    p = plan_actif(u)
    c = db()
    usage = c.execute("SELECT * FROM usages WHERE user_id=? ORDER BY date DESC LIMIT 1", (u["id"],)).fetchone()
    nb_notif = c.execute("SELECT COUNT(*) FROM notifications WHERE (user_id=? OR user_id IS NULL) AND lu=0", (u["id"],)).fetchone()[0]
    nb_fav = c.execute("SELECT COUNT(*) FROM favoris WHERE user_id=?", (u["id"],)).fetchone()[0]
    c.close()
    return jsonify({"user":{"id":u["id"],"pseudo":u["pseudo"],"email":u["email"],"niveau":u["niveau"],"role":u["role"]},
                    "plan":p,"usage":dict(usage) if usage else None,
                    "notifications_non_lues":nb_notif,"favoris":nb_fav})

@app.route("/api/ai/ask", methods=["POST"])
def api_ai_ask():
    u = get_user_by_token(request)
    if not u: return jsonify({"erreur":"Authentification requise"}), 401
    p = plan_actif(u)
    if not p: return jsonify({"erreur":"Essai gratuit de 48 h terminé"}), 402
    ok, msg = check_quota(u, p, "ia")
    if not ok: return jsonify({"erreur":msg}), 402
    data = request.get_json(silent=True) or {}
    q = data.get("question","").strip()
    image = data.get("image","")
    if not q and not image: return jsonify({"erreur":"Question ou photo vide"}), 400
    if image:
        r = reponse_ia_vision(q or "Décris et analyse cette image.", image, p)
    else:
        r = reponse_ia(q, p)
    log_sec(u["id"], "ia_question", q[:100] if q else "[photo]")
    return jsonify(r)

@app.route("/api/ai/photo", methods=["POST"])
def api_ai_photo():
    u = get_user_by_token(request)
    if not u: return jsonify({"erreur":"Authentification requise"}), 401
    p = plan_actif(u)
    if not p: return jsonify({"erreur":"Essai gratuit de 48 h terminé"}), 402
    ok, msg = check_quota(u, p, "photo")
    if not ok: return jsonify({"erreur":msg}), 402
    data = request.get_json(silent=True) or {}
    img = data.get("image","")
    if not img or len(img) < 100: return jsonify({"erreur":"Image invalide"}), 400
    if len(img) > 8 * 1024 * 1024: return jsonify({"erreur":"Image trop grosse (max 8MB)"}), 400
    try:
        img_bytes = base64.b64decode(img, validate=True)
    except Exception:
        return jsonify({"erreur":"Image base64 invalide"}), 400
    if len(img_bytes) < 50: return jsonify({"erreur":"Image invalide"}), 400
    if not (img_bytes[:3] == b'\xff\xd8\xff' or img_bytes[:8] == b'\x89PNG\r\n\x1a\n' or img_bytes[:4] == b'RIFF' or img_bytes[:6] in (b'GIF87a', b'GIF89a')):
        return jsonify({"erreur":"Format d'image non supporté (JPEG/PNG/WebP/GIF)"}), 400
    q = data.get("question","")
    r = reponse_ia_photo(q, img, p)
    log_sec(u["id"], "ia_photo", "Correction photo")
    return jsonify(r)

@app.route("/api/ai/correct", methods=["POST"])
def api_ai_correct():
    u = get_user_by_token(request)
    if not u: return jsonify({"erreur":"Authentification requise"}), 401
    p = plan_actif(u)
    if not p: return jsonify({"erreur":"Essai gratuit de 48 h terminé"}), 402
    ok, msg = check_quota(u, p, "correct")
    if not ok: return jsonify({"erreur":msg}), 402
    data = request.get_json(silent=True) or {}
    texte = data.get("texte","")
    if not texte or len(texte.strip()) < 10:
        return jsonify({"erreur":"Texte trop court (10+ caractères)"}), 400
    question = ("Corrige ce texte en français. Affiche d'abord le texte corrigé, puis explique chaque erreur. Texte : " + texte[:1500])
    r = reponse_ia(question, p)
    c = db()
    c.execute("INSERT INTO corrections (user_id,original,corrige,explication,date) VALUES (?,?,?,?,?)",
              (u["id"], texte[:500], r.get("reponse",""), "", now()))
    c.commit()
    c.close()
    log_sec(u["id"], "correction_texte", "Correction texte")
    return jsonify(r)

@app.route("/api/ai/translate", methods=["POST"])
def api_ai_translate():
    u = get_user_by_token(request)
    if not u: return jsonify({"erreur":"Authentification requise"}), 401
    p = plan_actif(u)
    if not p: return jsonify({"erreur":"Essai gratuit de 48 h terminé"}), 402
    ok, msg = check_quota(u, p, "ia")
    if not ok: return jsonify({"erreur":msg}), 402
    data = request.get_json(silent=True) or {}
    texte = data.get("texte", data.get("text",""))
    lang = data.get("langue_cible", data.get("langue","fr"))
    if not texte or len(texte.strip()) < 1: return jsonify({"erreur":"Texte trop court"}), 400
    r = reponse_traduction(texte, lang, p)
    log_sec(u["id"], "traduction", lang + ": " + texte[:80])
    return jsonify(r)

@app.route("/api/exercise/reponse", methods=["POST"])
def api_exercise_reponse():
    u = get_user_by_token(request)
    if not u: return jsonify({"erreur":"Authentification requise"}), 401
    data = request.get_json(silent=True) or {}
    eid = data.get("exercise_id")
    reponse = data.get("reponse","")
    c = db()
    ex = c.execute("SELECT * FROM exercises WHERE id=?", (eid,)).fetchone()
    correct = False
    score = 0
    if ex:
        correct = (str(ex["reponse"]) == reponse)
        score = 1 if correct else 0
        c.execute("INSERT INTO results (user_id,exercise_id,score,reponse_utilisateur,correct,date) VALUES (?,?,?,?,?,?)",
                  (u["id"], eid, score, reponse, 1 if correct else 0, now()))
    c.commit()
    c.close()
    update_usage(u["id"], "ex")
    return jsonify({"ok":True,"score":score,"correct":correct})

@app.route("/api/quiz/reponse", methods=["POST"])
def api_quiz_reponse():
    u = get_user_by_token(request)
    if not u: return jsonify({"erreur":"Authentification requise"}), 401
    data = request.get_json(silent=True) or {}
    qid = data.get("quiz_id")
    rep = data.get("reponse",0)
    c = db()
    q = c.execute("SELECT * FROM quiz WHERE id=?", (qid,)).fetchone()
    correct = 0
    if q:
        correct = 1 if int(rep) == int(q["reponse"]) else 0
        c.execute("INSERT INTO quiz_resultats (user_id,score,total,date) VALUES (?,?,?,?)",
                  (u["id"], correct, 1, now()))
    c.commit()
    c.close()
    update_usage(u["id"], "ex")
    return jsonify({"ok":True, "correct":correct, "explication":q["explication"] if q else ""})

@app.route("/api/favoris/add", methods=["POST"])
def api_favoris_add():
    u = get_user_by_token(request)
    if not u: return jsonify({"erreur":"Authentification requise"}), 401
    data = request.get_json(silent=True) or {}
    c = db()
    try:
        c.execute("INSERT INTO favoris (user_id,type,ref_id,label,date) VALUES (?,?,?,?,?)",
                  (u["id"], data.get("type","exercice"), data.get("ref_id",0), data.get("label",""), now()))
        c.commit()
    except sqlite3.IntegrityError:
        pass
    c.close()
    return jsonify({"ok":True})

@app.route("/api/favoris")
def api_favoris():
    u = get_user_by_token(request)
    if not u: return jsonify({"erreur":"Authentification requise"}), 401
    c = db()
    rows = c.execute("SELECT * FROM favoris WHERE user_id=? ORDER BY date DESC", (u["id"],)).fetchall()
    c.close()
    return jsonify({"favoris":[dict(r) for r in rows]})

@app.route("/api/history")
def api_history():
    u = get_user_by_token(request)
    if not u: return jsonify({"erreur":"Authentification requise"}), 401
    c = db()
    corr = c.execute("SELECT * FROM corrections WHERE user_id=? ORDER BY date DESC LIMIT 50", (u["id"],)).fetchall()
    res = c.execute("SELECT * FROM quiz_resultats WHERE user_id=? ORDER BY date DESC LIMIT 50", (u["id"],)).fetchall()
    c.close()
    return jsonify({"corrections":[dict(r) for r in corr], "resultats":[dict(r) for r in res]})

@app.route("/api/notifications")
def api_notifications():
    u = get_user_by_token(request)
    if not u: return jsonify({"erreur":"Authentification requise"}), 401
    c = db()
    rows = c.execute("SELECT * FROM notifications WHERE user_id=? OR user_id IS NULL ORDER BY date DESC LIMIT 50", (u["id"],)).fetchall()
    c.close()
    return jsonify({"notifications":[dict(r) for r in rows]})

@app.route("/api/notifications/read", methods=["POST"])
def api_notifications_read():
    u = get_user_by_token(request)
    if not u: return jsonify({"erreur":"Authentification requise"}), 401
    c = db()
    c.execute("UPDATE notifications SET lu=1 WHERE user_id=?", (u["id"],))
    c.commit()
    c.close()
    return jsonify({"ok":True})

@app.route("/api/support", methods=["POST"])
def api_support():
    # Accessible sans auth — formulaire contact public
    u = get_user_by_token(request)
    uid = u["id"] if u else 0
    data = request.get_json(silent=True) or {}
    nom = data.get("nom","")
    email = data.get("email","")
    telephone = data.get("telephone","")
    objet = data.get("objet", data.get("sujet",""))
    message = data.get("message","")
    categorie = data.get("categorie","")
    c = db()
    c.execute("INSERT INTO supports (user_id,nom,email,telephone,objet,message,categorie,date) VALUES (?,?,?,?,?,?,?,?)",
              (uid, nom, email, telephone, objet, message, categorie, now()))
    c.commit()
    c.close()
    # Envoyer email à l'admin si SendGrid configuré
    try:
        import os
        sg_key = os.environ.get("SENDGRID_API_KEY","")
        if sg_key:
            from sendgrid import SendGridAPIClient
            from sendgrid.helpers.mail import Mail
            msg = "Nom: %s\nEmail: %s\nTéléphone: %s\nCatégorie: %s\nObjet: %s\n\nMessage:\n%s" % (nom, email, telephone, categorie, objet, message)
            sg = SendGridAPIClient(sg_key)
            sg.send(Mail(from_email="no-reply@ecolemax.app", to_emails="sycheikhcorp@gmail.com", subject="[ÉcoleMax] "+objet, content=msg))
    except Exception as e:
        print("[support] email échoué: %s" % e, flush=True)
    return jsonify({"ok":True, "message":"Votre demande a été envoyée. Nous vous répondrons rapidement."})

@app.route("/api/subscribe", methods=["POST"])
def api_subscribe():
    u = get_user_by_token(request)
    if not u: return jsonify({"erreur":"Authentification requise"}), 401
    data = request.get_json(silent=True) or {}
    plan_code = data.get("plan","")
    method = data.get("method","wave")
    c = db()
    plan = c.execute("SELECT * FROM plans WHERE code=?", (plan_code,)).fetchone()
    if not plan: return jsonify({"erreur":"Plan non trouvé"}), 404
    if plan["code"] == "gratuit":
        return jsonify({"erreur":"Ce plan est l'essai gratuit"}), 400
    ref = "PAY-" + secrets.token_hex(6).upper()
    c.execute("INSERT INTO paiements (user_id,montant,method,statut,reference,created_at) VALUES (?,?,?,?,?,?)",
              (u["id"], plan["prix"], method, "en_attente", ref, now()))
    pid = c.execute("SELECT id FROM paiements WHERE reference=?", (ref,)).fetchone()["id"]
    c.execute("INSERT INTO abonnements (user_id,plan_code,statut,debut,expire,montant) VALUES (?,?,?,?,?,?)",
              (u["id"], plan_code, "en_attente", now(), "", plan["prix"]))
    aid = c.execute("SELECT id FROM abonnements WHERE user_id=? AND statut='en_attente' ORDER BY debut DESC LIMIT 1", (u["id"],)).fetchone()["id"]
    c.execute("UPDATE paiements SET abonnement_id=? WHERE id=?", (aid, pid))
    c.commit()
    c.close()
    log_sec(u["id"], "paiement_creation", plan_code + " " + method + " " + ref)
    return jsonify({"ok":True,"reference":ref,"abonnement_id":aid,"montant":plan["prix"]})

@app.route("/api/change_plan", methods=["POST"])
def api_change_plan():
    u = get_user_by_token(request)
    if not u: return jsonify({"erreur":"Authentification requise"}), 401
    data = request.get_json(silent=True) or {}
    new_code = data.get("plan","").strip()
    c = db()
    new_plan = c.execute("SELECT * FROM plans WHERE code=?", (new_code,)).fetchone()
    if not new_plan: return jsonify({"erreur":"Plan non trouvé"}), 404
    if new_code == "gratuit":
        return jsonify({"erreur":"Impossible de revenir à l'essai gratuit"}), 400
    ref = "CHG-" + secrets.token_hex(6).upper()
    c.execute("INSERT INTO paiements (user_id,montant,method,statut,reference,created_at) VALUES (?,?,?,?,?,?)",
              (u["id"], new_plan["prix"], data.get("method","wave"), "en_attente", ref, now()))
    pid = c.execute("SELECT id FROM paiements WHERE reference=?", (ref,)).fetchone()["id"]
    c.execute("INSERT INTO abonnements (user_id,plan_code,statut,debut,expire,montant) VALUES (?,?,?,?,?,?)",
              (u["id"], new_code, "en_attente", now(), "", new_plan["prix"]))
    aid = c.execute("SELECT id FROM abonnements WHERE user_id=? AND statut='en_attente' ORDER BY debut DESC LIMIT 1", (u["id"],)).fetchone()["id"]
    c.execute("UPDATE paiements SET abonnement_id=? WHERE id=?", (aid, pid))
    c.commit()
    c.close()
    log_sec(u["id"], "changement_plan", "-> " + new_code + " (" + ref + ")")
    return jsonify({"ok":True, "reference":ref, "abonnement_id":aid, "plan":new_plan["nom"], "montant":new_plan["prix"]})

@app.route("/api/payment/confirm", methods=["POST"])
def api_payment_confirm():
    u = get_user_by_token(request)
    if not u: return jsonify({"erreur":"Authentification requise"}), 401
    data = request.get_json(silent=True) or {}
    ref = data.get("reference","")
    c = db()
    pay = c.execute("SELECT * FROM paiements WHERE reference=?", (ref,)).fetchone()
    if not pay: return jsonify({"erreur":"Paiement non trouvé"}), 404
    if pay["user_id"] != u["id"]: return jsonify({"erreur":"Non autorisé"}), 403
    if pay["statut"] != "en_attente":
        return jsonify({"erreur":"Ce paiement est déjà traité"}), 400
    c.execute("UPDATE paiements SET statut='success', confirmed_at=? WHERE id=?", (now(), pay["id"]))
    plan = c.execute("SELECT * FROM plans WHERE code=?", (data.get("plan",""),)).fetchone()
    if plan:
        debut = datetime.datetime.now()
        expire = debut + datetime.timedelta(days=plan["duree_jours"])
        c.execute("UPDATE abonnements SET statut='actif', debut=?, expire=? WHERE id=?",
                  (debut.isoformat(), expire.isoformat(), pay["abonnement_id"]))
    c.execute("UPDATE abonnements SET statut='actif' WHERE user_id=? AND statut='en_attente'", (u["id"],))
    c.commit()
    c.close()
    log_sec(u["id"], "paiement_confirm", ref)
    return jsonify({"ok":True,"reference":ref,"statut":"success","message":"Abonnement activé ✅"})

@app.route("/api/payment/test", methods=["POST"])
def api_payment_test():
    if request.headers.get("X-Admin-Password","") != ADMIN_PASSWORD:
        return jsonify({"erreur":"Non autorisé"}), 403
    data = request.get_json(silent=True) or {}
    method = data.get("method","wave")
    montant = data.get("montant", 500)
    ref = "TEST-" + secrets.token_hex(6).upper()
    c = db()
    c.execute("INSERT INTO paiements (user_id,montant,method,statut,reference,created_at) VALUES (?,?,?,?,?,?)",
              (0, montant, method, "test_success", ref, now()))
    c.commit()
    c.close()
    log_sec(1, "test_paiement", "Test " + method + " " + ref)
    return jsonify({"ok": True, "reference": ref, "statut": "test_success", "montant": montant,
                    "message": "Paiement test simulé — " + str(montant) + " FCFA"})

@app.route("/api/admin/stats")
def api_admin_stats():
    if request.headers.get("X-Admin-Password","") != ADMIN_PASSWORD:
        return jsonify({"erreur":"Non autorisé"}), 403
    c = db()
    total_users = c.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    total_abos = c.execute("SELECT COUNT(*) FROM abonnements").fetchone()[0]
    total_pays = c.execute("SELECT COUNT(*) FROM paiements").fetchone()[0]
    total_ex = c.execute("SELECT COUNT(*) FROM exercises").fetchone()[0]
    pays_attente = c.execute("SELECT COUNT(*) FROM paiements WHERE statut='en_attente'").fetchone()[0]
    c.close()
    return jsonify({"total_users":total_users,"total_abos":total_abos,"total_pays":total_pays,
                     "total_ex":total_ex,"paiements_attente":pays_attente})

@app.route("/api/admin/backup")
def api_admin_backup():
    """Sauvegarde complète de la base de données (dump SQL téléchargeable)."""
    if request.headers.get("X-Admin-Password","") != ADMIN_PASSWORD:
        return jsonify({"erreur":"Non autorisé"}), 403
    c = db()
    dump = "\n".join(c.iterdump())
    c.close()
    return Response(dump, mimetype="application/sql",
                    headers={"Content-Disposition":"attachment; filename=ecolemax-backup.sql"})

@app.route("/api/admin/users")
def api_admin_users():
    if request.headers.get("X-Admin-Password","") != ADMIN_PASSWORD:
        return jsonify({"erreur":"Non autorisé"}), 403
    c = db()
    rows = c.execute("SELECT * FROM users ORDER BY created_at DESC").fetchall()
    c.close()
    return jsonify([dict(r) for r in rows])

@app.route("/api/admin/user/block", methods=["POST"])
def api_admin_user_block():
    if request.headers.get("X-Admin-Password","") != ADMIN_PASSWORD:
        return jsonify({"erreur":"Non autorisé"}), 403
    data = request.get_json(silent=True) or {}
    uid = data.get("user_id")
    c = db()
    u = c.execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone()
    if not u: return jsonify({"erreur":"Utilisateur non trouvé"}), 404
    c.execute("DELETE FROM sessions WHERE user_id=?", (uid,))
    c.execute("UPDATE users SET role='bloque' WHERE id=?", (uid,))
    c.commit()
    c.close()
    log_sec(1, "admin_action", "Utilisateur " + str(uid) + " bloqué")
    return jsonify({"ok":True, "message":"Utilisateur bloqué"})

@app.route("/api/admin/user/delete", methods=["POST"])
def api_admin_user_delete():
    if request.headers.get("X-Admin-Password","") != ADMIN_PASSWORD:
        return jsonify({"erreur":"Non autorisé"}), 403
    data = request.get_json(silent=True) or {}
    uid = data.get("user_id")
    c = db()
    u = c.execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone()
    if not u: return jsonify({"erreur":"Utilisateur non trouvé"}), 404
    c.execute("DELETE FROM sessions WHERE user_id=?", (uid,))
    c.execute("DELETE FROM favoris WHERE user_id=?", (uid,))
    c.execute("DELETE FROM notifications WHERE user_id=?", (uid,))
    c.execute("DELETE FROM usages WHERE user_id=?", (uid,))
    c.execute("DELETE FROM abonnements WHERE user_id=?", (uid,))
    c.execute("DELETE FROM paiements WHERE user_id=?", (uid,))
    c.execute("DELETE FROM results WHERE user_id=?", (uid,))
    c.execute("DELETE FROM supports WHERE user_id=?", (uid,))
    c.execute("DELETE FROM users WHERE id=?", (uid,))
    c.commit()
    c.close()
    log_sec(1, "admin_action", "Utilisateur " + str(uid) + " supprimé")
    return jsonify({"ok":True, "message":"Utilisateur supprimé"})

@app.route("/api/admin/abonnements")
def api_admin_abonnements():
    if request.headers.get("X-Admin-Password","") != ADMIN_PASSWORD:
        return jsonify({"erreur":"Non autorisé"}), 403
    c = db()
    rows = c.execute("SELECT * FROM abonnements ORDER BY debut DESC").fetchall()
    c.close()
    return jsonify({"abonnements":[dict(r) for r in rows]})

@app.route("/api/admin/paiements")
def api_admin_paiements():
    if request.headers.get("X-Admin-Password","") != ADMIN_PASSWORD:
        return jsonify({"erreur":"Non autorisé"}), 403
    c = db()
    rows = c.execute("SELECT * FROM paiements ORDER BY created_at DESC").fetchall()
    c.close()
    return jsonify({"paiements":[dict(r) for r in rows]})

@app.route("/api/admin/abonnement/control")
def api_admin_abonnement_control():
    if request.headers.get("X-Admin-Password","") != ADMIN_PASSWORD:
        return jsonify({"erreur":"Non autorisé"}), 403
    c = db()
    expired = c.execute("SELECT * FROM abonnements WHERE statut='actif' AND (expire='' OR date(expire)<date('now'))").fetchall()
    pending = c.execute("SELECT * FROM abonnements WHERE statut='en_attente'").fetchall()
    no_sub = c.execute("SELECT id,pseudo,email FROM users WHERE NOT EXISTS(SELECT 1 FROM abonnements a WHERE a.user_id=users.id AND a.statut='actif')").fetchall()
    to_renew = c.execute("SELECT * FROM abonnements WHERE statut='actif' AND date(expire) BETWEEN date('now') AND date('now','+3 days')").fetchall()
    c.close()
    return jsonify({"expires":[dict(r) for r in expired],"en_attente":[dict(r) for r in pending],
                     "sans_abonnement":[dict(r) for r in no_sub],"a_renouveler":[dict(r) for r in to_renew],
                     "stats":{"expires_count":len(expired),"attente_count":len(pending),
                              "sans_abonnement_count":len(no_sub),"renouvellement_count":len(to_renew)}})

@app.route("/api/admin/abonnement/confirm", methods=["POST"])
def api_admin_abonnement_confirm():
    if request.headers.get("X-Admin-Password","") != ADMIN_PASSWORD:
        return jsonify({"erreur":"Non autorisé"}), 403
    data = request.get_json(silent=True) or {}
    uid = data.get("user_id")
    plan_code = data.get("plan","")
    c = db()
    plan = c.execute("SELECT * FROM plans WHERE code=?", (plan_code,)).fetchone()
    if not plan: return jsonify({"erreur":"Plan non trouvé"}), 404
    u = c.execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone()
    if not u: return jsonify({"erreur":"Utilisateur non trouvé"}), 404
    debut = datetime.datetime.now().isoformat()
    expire = (datetime.datetime.now() + datetime.timedelta(days=plan["duree_jours"])).isoformat()
    c.execute("UPDATE abonnements SET statut='actif', debut=?, expire=? WHERE user_id=?", (debut, expire, uid))
    c.commit()
    c.close()
    log_sec(1, "admin_action", "Admin a confirmé abonnement " + plan_code + " pour user " + str(uid))
    return jsonify({"ok":True, "message":"Abonnement confirmé pour " + u["pseudo"]})

@app.route("/api/admin/matieres")
def api_admin_matieres():
    if request.headers.get("X-Admin-Password","") != ADMIN_PASSWORD:
        return jsonify({"erreur":"Non autorisé"}), 403
    c = db()
    sujets = c.execute("SELECT * FROM sujets ORDER BY ordre").fetchall()
    cours = c.execute("SELECT * FROM cours").fetchall()
    ex = c.execute("SELECT * FROM exercises").fetchall()
    c.close()
    return jsonify({"sujets":[dict(r) for r in sujets],"cours":[dict(r) for r in cours],"exercices":[dict(r) for r in ex]})

@app.route("/api/admin/notifications")
def api_admin_notifications():
    if request.headers.get("X-Admin-Password","") != ADMIN_PASSWORD:
        return jsonify({"erreur":"Non autorisé"}), 403
    c = db()
    rows = c.execute("SELECT * FROM notifications ORDER BY date DESC LIMIT 100").fetchall()
    c.close()
    return jsonify({"notifications":[dict(r) for r in rows]})

@app.route("/api/admin/supports")
def api_admin_supports():
    if request.headers.get("X-Admin-Password","") != ADMIN_PASSWORD:
        return jsonify({"erreur":"Non autorisé"}), 403
    c = db()
    rows = c.execute("SELECT * FROM supports ORDER BY date DESC").fetchall()
    c.close()
    return jsonify({"supports":[dict(r) for r in rows]})

@app.route("/api/admin/rapports")
def api_admin_rapports():
    if request.headers.get("X-Admin-Password","") != ADMIN_PASSWORD:
        return jsonify({"erreur":"Non autorisé"}), 403
    c = db()
    total_users = c.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    total_ex = c.execute("SELECT COUNT(*) FROM exercises").fetchone()[0]
    total_ia = c.execute("SELECT SUM(ia_count) FROM usages").fetchone()[0] or 0
    total_corr = c.execute("SELECT COUNT(*) FROM corrections").fetchone()[0]
    total_pays = c.execute("SELECT COUNT(*) FROM paiements WHERE statut='success'").fetchone()[0]
    c.close()
    return jsonify({"total_users":total_users,"total_ex":total_ex,"total_ia":total_ia,
                     "total_corr":total_corr,"total_pays":total_pays})

@app.route("/api/reset", methods=["POST"])
def api_reset():
    data = request.get_json(silent=True) or {}
    pseudo = data.get("pseudo","")
    c = db()
    u = c.execute("SELECT * FROM users WHERE pseudo=?", (pseudo,)).fetchone()
    if not u: return jsonify({"erreur":"Utilisateur non trouvé"}), 404
    new = secrets.token_hex(4)
    c.execute("UPDATE users SET mot_de_passe=? WHERE id=?", (hash_pass(new), u["id"]))
    c.commit()
    c.close()
    return jsonify({"ok":True,"nouveau_mdp":new})

@app.route("/api/quiz/session", methods=["POST"])
def api_quiz_session():
    """Génère une session de quiz avec au moins 15 questions."""
    data = request.get_json(silent=True) or {}
    user = get_user_by_token(request)
    if not user: return jsonify({"erreur":"Authentification requise"}), 401
    categorie = data.get("categorie","")
    difficulte = data.get("difficulte","")
    nb = max(15, int(data.get("nb",15)))
    limite = data.get("limite","")
    c = db()
    q = "SELECT * FROM quiz WHERE 1=1"
    params = []
    if categorie: q += " AND categorie=?"; params.append(categorie)
    if difficulte: q += " AND difficulte=?"; params.append(difficulte)
    if limite: q += " LIMIT " + str(int(limite))
    rows = c.execute(q, params).fetchall()
    c.close()
    if len(rows) < nb:
        return jsonify({"erreur":"Pas assez de questions disponibles","disponibles":len(rows)})
    import random as _r
    import json as _j
    selected = _r.sample(rows, nb)
    result = []
    for r in selected:
        qz = dict(r)
        idx = qz.get("reponse", 0)
        correct = qz.get("explication", "")
        cat = qz.get("categorie", "")
        pool = ["Option A","Option B","Option C","Option D"]
        wrong = _r.sample([p for p in pool if p != correct], 3) if pool else ["A","B","C"]
        options = [""] * 4
        for i in range(4):
            if i == idx: options[i] = correct
            else: options[i] = wrong.pop(0) if wrong else f"Option {chr(65+i)}"
        qz["options"] = _j.dumps(options, ensure_ascii=False)
        result.append(qz)
    return jsonify({"session":result, "nb":len(result), "categorie":categorie, "difficulte":difficulte})

@app.route("/api/quiz/result", methods=["POST"])
def api_quiz_result():
    data = request.get_json(silent=True) or {}
    user = get_user_by_token(request)
    if not user: return jsonify({"erreur":"Authentification requise"}), 401
    score = int(data.get("score",0))
    total = int(data.get("total",0))
    temps = int(data.get("temps",0))
    categorie = data.get("categorie","")
    difficulte = data.get("difficulte","")
    c = db()
    c.execute("INSERT INTO quiz_resultats (user_id,score,total,date) VALUES (?,?,?,?)",(user["id"],score,total,now()))
    c.execute("INSERT INTO quiz_sessions (user_id,categorie,difficulte,questions,temps_total,score,total,date) VALUES (?,?,?,?,?,?,?,?)",
              (user["id"],categorie,difficulte,"",temps,score,total,now()))
    c.commit()
    c.close()
    return jsonify({"ok":True,"score":score,"total":total,"moyenne":round(score*100/total if total else 0,1)})

@app.route("/api/quiz/history")
def api_quiz_history():
    user = get_user_by_token(request)
    if not user: return jsonify({"erreur":"Authentification requise"}), 401
    c = db()
    rows = c.execute("SELECT score,total,date FROM quiz_resultats WHERE user_id=? ORDER BY date DESC LIMIT 50",(user["id"],)).fetchall()
    c.close()
    return jsonify({"resultats":[dict(r) for r in rows]})


def send_sms_twilio(phone, message):
    """Envoie un SMS via Twilio."""
    try:
        from twilio.rest import Client
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        msg = client.messages.create(
            body=message,
            from_=TWILIO_FROM_NUMBER,
            to=phone
        )
        print(f"✅ SMS Twilio envoyé: {msg.sid}", flush=True)
        return True, msg.sid
    except Exception as e:
        print(f"❌ SMS Twilio ERR: {e}", flush=True)
        return False, str(e)

def send_email_sendgrid(to_email, subject, html_body):
    """Envoie un email via SendGrid."""
    if not SENDGRID_API_KEY:
        print("❌ SendGrid API key non configurée", flush=True)
        return False, "SendGrid non configuré"
    try:
        import sendgrid
        from sendgrid.helpers.mail import Mail, Email, To, Content
        sg = sendgrid.SendGridAPIClient(apikey=SENDGRID_API_KEY)
        mail = Mail(
            from_email=SENDGRID_FROM,
            to_emails=to_email,
            subject=subject,
            html_content=html_body
        )
        response = sg.client.mail.send.post(request_body=mail.get())
        print(f"✅ Email SendGrid envoyé: status={response.status_code}", flush=True)
        return True, str(response.status_code)
    except Exception as e:
        print(f"❌ Email SendGrid ERR: {e}", flush=True)
        return False, str(e)


@app.route("/api/register/sms", methods=["POST"])
def api_register_sms():
    """Envoie un code OTP par SMS."""
    data = request.get_json(silent=True) or {}
    phone = data.get("phone","")
    pseudo = data.get("pseudo","")
    email = data.get("email","")
    if not phone or not pseudo: return jsonify({"erreur":"Téléphone et pseudo requis"}), 400
    code = str(random.randint(100000,999999))
    expires = (datetime.datetime.now()+datetime.timedelta(minutes=10)).strftime("%Y-%m-%d %H:%M:%S")
    # Enregistrer le code (en production, envoyer via SMS)
    c = db()
    u = c.execute("SELECT id FROM users WHERE pseudo=?", (pseudo,)).fetchone()
    if not u:
        c.execute("INSERT INTO users (pseudo,email,mot_de_passe,niveau,role,created_at) VALUES (?,?,?,?,?,?)",
                  (pseudo,email,hash_pass(secrets.token_hex(4)),"","eleve",now()))
        uid = c.execute("SELECT id FROM users WHERE pseudo=?",(pseudo,)).fetchone()["id"]
    else:
        uid = u["id"]
    c.execute("DELETE FROM sms_codes WHERE user_id=?", (uid,))
    c.execute("INSERT INTO sms_codes (user_id,phone,code,expires_at) VALUES (?,?,?,?)",(uid,phone,code,expires))
    c.commit()
    c.close()
    # Envoi réel via Twilio
    if SMS_PROVIDER == "twilio":
        ok, msg_id = send_sms_twilio(phone, f"Code ÉcoleMax: {code}")
        if ok:
            return jsonify({"ok":True,"message":"Code SMS envoyé","debug_code":None})
        else:
            return jsonify({"ok":True,"message":"Code SMS envoyé (erreur envoi)","debug_code":code})
    return jsonify({"ok":True,"message":"Code SMS envoyé","debug_code":code})

@app.route("/api/register/verify", methods=["POST"])
def api_register_verify():
    data = request.get_json(silent=True) or {}
    pseudo = data.get("pseudo","")
    code = data.get("code","")
    c = db()
    u = c.execute("SELECT * FROM users WHERE pseudo=?", (pseudo,)).fetchone()
    if not u: return jsonify({"erreur":"Utilisateur non trouvé"}), 404
    sms = c.execute("SELECT * FROM sms_codes WHERE user_id=? AND used=0 ORDER BY id DESC LIMIT 1",(u["id"],)).fetchone()
    if not sms: return jsonify({"erreur":"Aucun code trouvé"}), 404
    if sms["attempts"] >= 5: return jsonify({"erreur":"Trop de tentatives"}), 429
    if sms["code"] != code:
        c.execute("UPDATE sms_codes SET attempts=attempts+1 WHERE id=?",(sms["id"],))
        c.commit(); c.close()
        return jsonify({"erreur":"Code incorrect"}), 400
    c.execute("UPDATE sms_codes SET used=1 WHERE id=?",(sms["id"],))
    c.execute("UPDATE users SET phone_verified=1 WHERE id=?",(u["id"],)) if "phone_verified" in [r[1] for r in c.execute("PRAGMA table_info(users)")] else None
    c.commit(); c.close()
    return jsonify({"ok":True,"verifie":True})

@app.route("/api/contact", methods=["POST"])
def api_contact():
    data = request.get_json(silent=True) or {}
    nom = data.get("nom","")
    email = data.get("email","")
    phone = data.get("phone","")
    objet = data.get("objet","")
    categorie = data.get("categorie","autre")
    message = data.get("message","")
    if not nom or not email or not message: return jsonify({"erreur":"Nom, email et message requis"}), 400
    c = db()
    c.execute("INSERT INTO contact_messages (nom,email,phone,objet,categorie,message,statut,date) VALUES (?,?,?,?,?,?,?,?)",
              (nom,email,phone,objet,categorie,message,"nouveau",now()))
    c.commit(); c.close()
    # Envoyer email à l'administrateur
    ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL","sycheikhcorp@gmail.com")
    SMTP_HOST = os.environ.get("SMTP_HOST","")
    if SMTP_HOST:
        try:
            import smtplib
            from email.mime.text import MIMEText
            msg = MIMEText(f"Nouveau message de contact:\n\nNom: {nom}\nEmail: {email}\nTéléphone: {phone}\nObjet: {objet}\nCatégorie: {categorie}\nMessage: {message}")
            msg["Subject"] = f"[ÉcoleMax Contact] {objet}"
            msg["From"] = "noreply@ecolemax.sn"
            msg["To"] = ADMIN_EMAIL
            s = smtplib.SMTP(SMTP_HOST, int(os.environ.get("SMTP_PORT","587")))
            s.starttls()
            s.login(os.environ.get("SMTP_USER",""), os.environ.get("SMTP_PASS",""))
            s.sendmail("noreply@ecolemax.sn",[ADMIN_EMAIL],msg.as_string())
            s.quit()
            print(f"[EMAIL] Contact envoyé à {ADMIN_EMAIL}", flush=True)
        except Exception as e:
            print(f"[EMAIL] ERR: {e}", flush=True)
    return jsonify({"ok":True,"message":"Message envoyé","reference":f"CM{secrets.token_hex(4)}"})

@app.route("/api/admin/contacts/<int:cid>/traiter", methods=["POST"])
def api_admin_contact_traiter(cid):
    if request.headers.get("X-Admin-Password","") != ADMIN_PASSWORD:
        return jsonify({"erreur":"Non autorisé"}), 403
    c = db()
    c.execute("UPDATE contact_messages SET statut='traite' WHERE id=?", (cid,))
    c.commit(); c.close()
    return jsonify({"ok":True})



# === GÉNÉRATOR LOCAL DE CONTENUS (fallback sans IA) ===

def generate_exercice_local(sujet, difficulte):
    """Génère un exercice local basique."""
    cat_name = {"math":"Maths","fr":"Français","phys":"Physique","chim":"Chimie","svt":"SVT","hist":"Histoire","geo":"Géographie","eng":"Anglais","eco":"Économie","info":"Informatique","es":"Espagnol","ara":"Arabe"}.get(sujet,sujet)
    import random as _r
    templates = {
        "math": [
            ("Calculez {a} + {b} [{s1}/{s2}/{s3}/{s4}]", "{a} + {b} = {a}+{b}"),
            ("Simplifiez {a} × {b} [{s1}/{s2}/{s3}/{s4}]", "{a} × {b} = {a}×{b}"),
            ("Calculez {a} − {b} [{s1}/{s2}/{s3}/{s4}]", "{a} − {b} = {a}-{b}"),
            ("Calculez {a} ÷ {b} [{s1}/{s2}/{s3}/{s4}]", "{a} ÷ {b} = {a}/{b}"),
        ],
        "fr": [
            ("Conjuguez le verbe 'manger' au présent : je ___ [mange/manges/mange/mange]", "je mange"),
            ("Quelle est la forme correcte ? 'Les enfants ___' [joue/jouent/joues/jouant]", "jouent"),
            ("Complétez : 'Il est ___ grand' [très/trop/tellement/assez]", "très"),
            ("Synonyme de 'rapide' : [véloce/lent/paresseux/calme]", "véloce"),
        ],
        "phys": [
            ("Un objet de 5 kg est soumis à une force de 20 N. Calculez l'accélération [4 m/s²/5 m/s²/0.25 m/s²/25 m/s²]", "a = F/m = 20/5 = 4 m/s²"),
            ("La vitesse de la lumière est environ [300 000 km/s/30 000 km/s/3 000 km/s/3 000 000 km/s]", "300 000 km/s"),
            ("L'unité de la force est [Newton/Joule/Watt/Pascal]", "Newton"),
            ("La vitesse est égale à [distance / temps/temps × distance/force × masse/énergie × masse]", "distance / temps"),
        ],
        "chim": [
            ("Formule de l'eau est [H₂O/CO₂/O₂/N₂]", "H₂O"),
            ("Le pH d'une solution neutre est [7/0/14/1]", "7"),
            ("Atome le plus réactif du tableau périodique : [Fluor/Oxygène/Hydrogène/Azote]", "Fluor"),
            ("Nombre d'électrons de l'oxygène : [8/6/10/16]", "8"),
        ],
        "svt": [
            ("Le cœur pompe le sang vers [le corps/les poumons/le cerveau/tout le corps]", "tout le corps"),
            ("La photosynthèse se produit dans [les feuilles/les racines/les fleurs/les fruits]", "les feuilles"),
            ("L'ADN est situé dans [le noyau/la membrane/le cytoplasme/les mitochondries]", "le noyau"),
            ("Les cellules nerveuses sont appelées [neurones/leucocytes/erythrocytes/myocytes]", "neurones"),
        ],
        "hist": [
            ("La capitale du royaume du Tekrour était [Tomboctou/Gao/Djenné/Ségou]", "Tomboctou"),
            ("L'indépendance du Sénégal a été proclamée en [1960/1958/1965/1970]", "1960"),
            ("Premier président du Sénégal : [Léopold Sédar Senghor/Abdoulaye Wade/Macky Sall/Diouf]", "Léopold Sédar Senghor"),
            ("La ville de Saint-Louis fut la capitale de l'Afrique-Occidentale française en [1895/1902/1860/1920]", "1895"),
        ],
        "geo": [
            ("Capitale du Sénégal : [Dakar/Touba/Thiès/Saint-Louis]", "Dakar"),
            ("Le fleuve le plus long d'Afrique est [le Nil/le Niger/le Sénégal/le Congo]", "le Nil"),
            ("Le Mont Everest se situe dans [l'Asie/l'Afrique/l'Amérique/l'Europe]", "l'Asie"),
            ("Le Sahara est situé en [Afrique/Asie/Amérique/Europe]", "Afrique"),
        ],
        "eng": [
            ("How are you? [Comment allez-vous/Comment tu es/Qui es-tu/Où vas-tu]", "Comment allez-vous"),
            ("I ___ a student [am/is/are/be]", "am"),
            ("The plural of 'child' is [children/childs/childes/child]", "children"),
            ("Good morning means [Bonjour/Bonsoir/Au revoir/Merci]", "Bonjour"),
        ],
        "eco": [
            ("La monnaie du Sénégal est [XOF/FCFA/EUR/USD]", "XOF"),
            ("La banque centrale de l'UMOA est [BCEAO/BCE/Banque de France/BRI]", "BCEAO"),
            ("L'inflation est [la hausse des prix/la baisse des prix/la stabilité des prix/l'équilibre budgétaire]", "la hausse des prix"),
            ("Le PIB mesure [la richesse d'un pays/la population/le taux d'intérêt/l'inflation]", "la richesse d'un pays"),
        ],
        "info": [
            ("HTML signifie [HyperText Markup Language/HyperTransfer/HighText/HyperLanguage]", "HyperText Markup Language"),
            ("CSS signifie [Cascading Style Sheets/Creative Style Sheets/Computer Style Sheets/Code Style Sheets]", "Cascading Style Sheets"),
            ("Le langage de programmation le plus populaire pour le web est [Python/Java/JavaScript/C++]", "JavaScript"),
            ("Une adresse IP est composée de [4 nombres/3 nombres/6 nombres/2 nombres]", "4 nombres"),
        ],
    }
    templates_default = [
        ("Question de " + cat_name + " : [Option A/Option B/Option C/Option D]", "Explication pédagogique"),
    ]
    tpls = templates.get(sujet, templates_default)
    tpl = _r.choice(tpls)
    if "{a}" in tpl[0]:
        a = _r.randint(2,20)
        b = _r.randint(2,20)
        s1 = a+b
        wrong = _r.sample([s1+1, s1-1, s1+2], 3)
        q = tpl[0].format(a=a,b=b,s1=s1,s2=wrong[0],s3=wrong[1],s4=wrong[2])
        exp = tpl[1].format(a=a,b=b)
        return sujet, q, exp, difficulte, ""
    else:
        q = tpl[0]
        exp = tpl[1]
        return sujet, q, exp, difficulte, ""

def generate_quiz_local(categorie, difficulte):
    """Génère un quiz local basique."""
    import random as _r
    templates = {
        "Maths": [
            ("Quel est le résultat de 7 × 8 ?", 3, "7 × 8 = 56", "facile"),
            ("La racine carrée de 25 est :", 2, "√25 = 5", "facile"),
            ("Un triangle avec 3 côtés égaux est un :", 1, "Triangle équilatéral", "moyen"),
            ("La valeur de π est environ :", 0, "π ≈ 3.1416", "moyen"),
        ],
        "Français": [
            ("Quelle est la capitale de la France ?", 2, "Paris", "facile"),
            ("Le pluriel de 'cheval' est :", 0, "chevaux", "facile"),
            ("Conjuguer 'être' à la 1ère personne :", 0, "je suis", "moyen"),
            ("Un synonyme de 'joli' est :", 1, "beau", "facile"),
        ],
        "Physique": [
            ("La force est mesurée en :", 0, "Newton (N)", "facile"),
            ("La vitesse de la lumière est :", 2, "300 000 km/s", "moyen"),
            ("L'unité de la température est :", 1, "Kelvin (K)", "moyen"),
            ("La loi de Newton est liée à :", 0, "la force et l'accélération", "difficile"),
        ],
        "Chimie": [
            ("La formule de l'eau est :", 0, "H₂O", "facile"),
            ("Le pH d'un acide est :", 0, "inférieur à 7", "facile"),
            ("Le nombre atomique de l'oxygène est :", 2, "8", "moyen"),
            ("Un atome stable a :", 1, "des électrons en couches complètes", "difficile"),
        ],
        "SVT": [
            ("Le cœur est situé dans :", 1, "la poitrine", "facile"),
            ("La photosynthèse transforme :", 0, "la lumière en énergie", "moyen"),
            ("Les cellules nerveuses sont appelées :", 1, "neurones", "facile"),
            ("Le système circulatoire transporte :", 0, "le sang", "facile"),
        ],
        "Histoire": [
            ("L'indépendance du Sénégal date de :", 3, "1960", "facile"),
            ("Le premier président du Sénégal est :", 2, "Léopold Sédar Senghor", "facile"),
            ("La capitale historique du Mali est :", 1, "Tombouctou", "moyen"),
        ],
        "Géographie": [
            ("Capitale du Sénégal :", 0, "Dakar", "facile"),
            ("Le fleuve le plus long d'Afrique :", 1, "le Nil", "facile"),
            ("La plus grande ville d'Afrique est :", 2, "Le Caire", "moyen"),
            ("Le Sahara est un :", 0, "désert", "facile"),
        ],
        "Anglais": [
            ("How are you?", 0, "Comment allez-vous", "facile"),
            ("I ___ a book", 0, "am", "facile"),
            ("The plural of 'child' is :", 1, "children", "moyen"),
            ("Goodbye means :", 2, "Au revoir", "facile"),
        ],
        "Économie": [
            ("La monnaie du Sénégal est :", 1, "XOF", "facile"),
            ("La BCEAO est :", 0, "la banque centrale de l'UMOA", "moyen"),
            ("L'inflation est :", 1, "la hausse des prix", "facile"),
        ],
        "Informatique": [
            ("HTML signifie :", 0, "HyperText Markup Language", "facile"),
            ("CSS est utilisé pour :", 1, "styliser les pages web", "facile"),
            ("Une adresse IP v4 comporte :", 3, "4 nombres", "moyen"),
            ("Le langage du web par défaut est :", 2, "JavaScript", "moyen"),
        ],
    }
    templates_default = [
        ("Question de " + categorie + " :", 0, "Explication pédagogique", "moyen"),
    ]
    tpls = templates.get(categorie, templates_default)
    q, rep, exp, _ = _r.choice(tpls)
    return categorie, q, rep, exp, difficulte


# === ROUTES ADMIN : GÉNÉRATION IA ET CRUD CONTENUS ===

@app.route("/api/admin/exercises/generate", methods=["POST"])
def api_admin_exercises_generate():
    if request.headers.get("X-Admin-Password","") != ADMIN_PASSWORD:
        return jsonify({"erreur":"Authentification requise"}), 403
    data = request.get_json(silent=True) or {}
    sujet = data.get("sujet","math")
    niveau = data.get("niveau","")
    difficulte = data.get("difficulte","moyen")
    nb = min(int(data.get("nb",10)),50)
    cat_name = {"math":"Maths","fr":"Français","phys":"Physique","chim":"Chimie","svt":"SVT","hist":"Histoire","geo":"Géographie","eng":"Anglais","eco":"Économie","info":"Informatique","es":"Espagnol","ara":"Arabe"}.get(sujet,sujet)

    c = db()
    generated = []
    for i in range(nb):
        q_prompt = "Génère un exercice de " + cat_name + " de niveau " + difficulte + " pour un élève. Format JSON strict:\n{\"question\": \"énoncé avec [option1/option2/option3/option4]\", \"explication\": \"solution détaillée\", \"difficulte\": \"" + difficulte + "\"}\nUnique, sans doublon. Réponse dans l'explication."
        ok, text, src = get_pollinations(q_prompt, max_tokens=500, silent=True)
        if ok and text and "402" not in text and "Payment" not in text:
            try:
                m = re.search(r'\{[^{}]*"question"[^{}]*\}', text, re.DOTALL)
                if m:
                    j = json.loads(m.group(0))
                    question = j.get("question","")
                    explication = j.get("explication","")
                    if question and len(question) > 10:
                        generated.append((sujet, question, explication, difficulte, niveau))
                        continue
            except:
                pass
        # Fallback local
        try:
            cat, q, exp, diff, niv = generate_exercice_local(sujet, difficulte)
            generated.append((cat, q, exp, diff, niv))
        except:
            pass

    inserted = 0
    for cat, q, exp, diff, niv in generated:
        dup = c.execute("SELECT id FROM exercises WHERE question=? AND sujet_code=?",(q[:100],cat)).fetchone()
        if dup: continue
        c.execute("INSERT INTO exercises (sujet_code,question,explication,difficulte,niveau) VALUES (?,?,?,?,?)",(cat,q,exp,diff,niv))
        inserted += 1
    c.commit()
    c.close()
    return jsonify({"ok":True,"generes":inserted,"ecartes":len(generated)-inserted,"source":src})

@app.route("/api/admin/quiz/generate", methods=["POST"])
def api_admin_quiz_generate():
    if request.headers.get("X-Admin-Password","") != ADMIN_PASSWORD:
        return jsonify({"erreur":"Authentification requise"}), 403
    data = request.get_json(silent=True) or {}
    categorie = data.get("categorie","Maths")
    difficulte = data.get("difficulte","moyen")
    nb = min(int(data.get("nb",10)),50)

    c = db()
    generated = []
    for i in range(nb):
        q_prompt = "Génère un QCM de " + categorie + " de niveau " + difficulte + ". Format JSON strict:\n{\"question\": \"question\", \"reponse\": 0, \"explication\": \"explication pédagogique\"}\nreponse: index 0-3 de la bonne réponse. Réponse dans l'explication."
        ok, text, src = get_pollinations(q_prompt, max_tokens=400, silent=True)
        if ok and text and "402" not in text and "Payment" not in text:
            try:
                m = re.search(r'\{[^{}]*"question"[^{}]*\}', text, re.DOTALL)
                if m:
                    j = json.loads(m.group(0))
                    q = j.get("question","")
                    rep = j.get("reponse",0)
                    exp = j.get("explication","")
                    if rep < 0 or rep > 3: rep = 0
                    if q and len(q) > 10:
                        generated.append((categorie, q, rep, exp, difficulte))
                        continue
            except:
                pass
        # Fallback local
        try:
            cat, q, rep, exp, diff = generate_quiz_local(categorie, difficulte)
            generated.append((cat, q, rep, exp, diff))
        except:
            pass

    inserted = 0
    for cat, q, rep, exp, diff in generated:
        dup = c.execute("SELECT id FROM quiz WHERE question=? AND categorie=?",(q[:100],cat)).fetchone()
        if dup: continue
        c.execute("INSERT INTO quiz (categorie,question,reponse,explication,difficulte) VALUES (?,?,?,?,?)",(cat,q,rep,exp,diff))
        inserted += 1
    c.commit()
    c.close()
    return jsonify({"ok":True,"generes":inserted,"ecartes":len(generated)-inserted,"source":src})

@app.route("/api/admin/exercises", methods=["GET","POST","DELETE"])
def api_admin_exercises():
    if request.headers.get("X-Admin-Password","") != ADMIN_PASSWORD:
        return jsonify({"erreur":"Authentification requise"}), 403
    c = db()
    if request.method == "GET":
        sujet = request.args.get("sujet","")
        difficulte = request.args.get("difficulte","")
        limite = int(request.args.get("limite",50))
        q = "SELECT * FROM exercises WHERE 1=1"
        params = []
        if sujet: q += " AND sujet_code=?"; params.append(sujet)
        if difficulte: q += " AND difficulte=?"; params.append(difficulte)
        q += " ORDER BY id DESC LIMIT ?"
        params.append(limite)
        rows = c.execute(q, params).fetchall()
        c.close()
        return jsonify({"exercices":[dict(r) for r in rows]})
    data = request.get_json(silent=True) or {}
    if request.method == "POST":
        sujet = data.get("sujet_code","math")
        question = data.get("question","")
        explication = data.get("explication","")
        difficulte = data.get("difficulte","moyen")
        niveau = data.get("niveau","")
        if not question: return jsonify({"erreur":"Question requise"}), 400
        c.execute("INSERT INTO exercises (sujet_code,question,explication,difficulte,niveau) VALUES (?,?,?,?,?)",(sujet,question,explication,difficulte,niveau))
        c.commit()
        c.close()
        return jsonify({"ok":True})
    if request.method == "DELETE":
        eid = data.get("id")
        if not eid: return jsonify({"erreur":"ID requis"}), 400
        c.execute("DELETE FROM exercises WHERE id=?",(eid,))
        c.commit()
        c.close()
        return jsonify({"ok":True})

@app.route("/api/admin/quiz", methods=["GET","POST","DELETE"])
def api_admin_quiz():
    if request.headers.get("X-Admin-Password","") != ADMIN_PASSWORD:
        return jsonify({"erreur":"Authentification requise"}), 403
    c = db()
    if request.method == "GET":
        categorie = request.args.get("categorie","")
        difficulte = request.args.get("difficulte","")
        limite = int(request.args.get("limite",50))
        q = "SELECT * FROM quiz WHERE 1=1"
        params = []
        if categorie: q += " AND categorie=?"; params.append(categorie)
        if difficulte: q += " AND difficulte=?"; params.append(difficulte)
        q += " ORDER BY id DESC LIMIT ?"
        params.append(limite)
        rows = c.execute(q, params).fetchall()
        c.close()
        return jsonify({"quiz":[dict(r) for r in rows]})
    data = request.get_json(silent=True) or {}
    if request.method == "POST":
        categorie = data.get("categorie","Maths")
        question = data.get("question","")
        reponse = int(data.get("reponse",0))
        explication = data.get("explication","")
        difficulte = data.get("difficulte","moyen")
        if not question: return jsonify({"erreur":"Question requise"}), 400
        c.execute("INSERT INTO quiz (categorie,question,reponse,explication,difficulte) VALUES (?,?,?,?,?)",(categorie,question,reponse,explication,difficulte))
        c.commit()
        c.close()
        return jsonify({"ok":True})
    if request.method == "DELETE":
        qid = data.get("id")
        if not qid: return jsonify({"erreur":"ID requis"}), 400
        c.execute("DELETE FROM quiz WHERE id=?",(qid,))
        c.commit()
        c.close()
        return jsonify({"ok":True})


# Keepalive thread — empêche Render de suspendre le service
def keepalive():
    """Demande /health toutes les 4 minutes pour éviter la suspension Render."""
    import urllib.request as urlreq
    # Déterminer l'URL du service
    service_url = os.environ.get("RENDER_SERVICE_URL", "")
    if not service_url:
        service_url = "http://localhost:" + str(PORT)
    while True:
        try:
            urlreq.urlopen(service_url + "/health", timeout=10)
            print("[keepalive] OK -> " + service_url + "/health", flush=True)
        except Exception as ex:
            print("[keepalive] ERR: " + str(ex), flush=True)
        time.sleep(240)  # 4 minutes

# Lancer le keepalive dans un thread séparé (sans bloqué le startup)
import threading as _threading
_threading.Thread(target=keepalive, daemon=True).start()

# Initialiser la base de données au démarrage (fonctionne avec Gunicorn et Flask dev)
init_db()

if __name__ == "__main__":
    print("🟢 ÉcoleMax Flask → http://0.0.0.0:" + str(PORT))
    app.run(host="0.0.0.0", port=PORT)
