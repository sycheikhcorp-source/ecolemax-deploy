#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ÉcoleMax — Plateforme éducative complète
Backend : auth, IA (Professeur/Scanner/Correcteur), exercices, abonnements,
          paiements (Wave/Orange Money/cartes), dashboard admin temps réel.
Stack : Python 3 / SQLite (WAL) / Pollinations AI (gratuit) + calculateur local.
Par SYCHEIKHCORP
"""
import os, json, sqlite3, hashlib, hmac, secrets, re, base64, datetime, urllib.request, urllib.error, threading, time
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

HOST = "0.0.0.0"
PORT = int(os.environ.get("PORT", 8000))
DB_PATH = os.environ.get("DB_PATH", os.path.join(os.path.dirname(os.path.abspath(__file__)), "ecolemax.db"))
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "ecolemax2026")
POLLINATIONS_URL = "https://text.pollinations.ai/openai"
OVH_AI_URL = "https://oai.endpoints.kepler.ai.cloud.ovh.net/v1/chat/completions"
OVH_AI_MODEL = "meta-llama/Llama-3.3-70B-Instruct"
POLLINATIONS_REFERER = "https://ecolemax.onrender.com"

# ─────────────────────────────────────────────
# Base de données
# ─────────────────────────────────────────────
def db():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    c = db()
    c.execute("PRAGMA journal_mode=WAL")
    c.execute("PRAGMA busy_timeout=30000")
    # Recrée les tables pour une structure cohérente (migration complète)
    tables = ["journaux","supports","notifications","favoris","results","corrections",
              "exercices_favoris","exercises","cours","sujets","usages","paiements",
              "abonnements","plans","sessions","users","admins"]
    for t in tables:
        c.execute(f"DROP TABLE IF EXISTS {t}")
    c.executescript("""
    CREATE TABLE users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pseudo TEXT UNIQUE NOT NULL,
        email TEXT,
        mot_de_passe TEXT NOT NULL,
        niveau TEXT DEFAULT 'Terminale',
        created_at TEXT,
        role TEXT DEFAULT 'eleve'
    );
    CREATE TABLE IF NOT EXISTS sessions(
        token TEXT PRIMARY KEY,
        user_id INTEGER NOT NULL,
        expires_at TEXT,
        created_at TEXT
    );
    CREATE TABLE IF NOT EXISTS plans(
        code TEXT PRIMARY KEY,
        nom TEXT,
        prix REAL,
        duree_jours INTEGER,
        limite_ia_jour INTEGER,
        photo_jour INTEGER,
        description TEXT,
        paiement_tranche TEXT DEFAULT 'unique',
        nb_tranches INTEGER DEFAULT 1
    );
    CREATE TABLE IF NOT EXISTS abonnements(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        plan_code TEXT NOT NULL,
        statut TEXT DEFAULT 'actif',
        debut TEXT,
        expire TEXT,
        montant REAL DEFAULT 0
    );
    CREATE TABLE IF NOT EXISTS paiements(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        abonnement_id INTEGER,
        montant REAL,
        method TEXT,
        statut TEXT DEFAULT 'en_attente',
        reference TEXT,
        created_at TEXT,
        confirmed_at TEXT
    );
    CREATE TABLE IF NOT EXISTS usages(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        date TEXT,
        ia_count INTEGER DEFAULT 0,
        photo_count INTEGER DEFAULT 0,
        correct_count INTEGER DEFAULT 0,
        ex_count INTEGER DEFAULT 0
    );
    CREATE TABLE IF NOT EXISTS sujets(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT,
        nom TEXT,
        categorie TEXT,
        ordre INTEGER DEFAULT 0
    );
    CREATE TABLE IF NOT EXISTS cours(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sujet_code TEXT,
        titre TEXT,
        contenu TEXT,
        niveau TEXT,
        chapitre TEXT
    );
    CREATE TABLE IF NOT EXISTS exercises(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sujet_code TEXT,
        titre TEXT,
        type TEXT DEFAULT 'qcm',
        qtext TEXT,
        options TEXT,
        reponse TEXT,
        explication TEXT,
        niveau TEXT,
        chapitre TEXT,
        difficulte INTEGER DEFAULT 1,
        created_at TEXT
    );
    CREATE TABLE IF NOT EXISTS results(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        exercise_id INTEGER,
        score INTEGER,
        reponse_utilisateur TEXT,
        correct INTEGER,
        date TEXT
    );
    CREATE TABLE IF NOT EXISTS corrections(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        original TEXT,
        corrige TEXT,
        explication TEXT,
        date TEXT
    );
    CREATE TABLE IF NOT EXISTS favoris(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        type TEXT,
        ref_id INTEGER,
        label TEXT,
        date TEXT,
        UNIQUE(user_id,type,ref_id)
    );
    CREATE TABLE IF NOT EXISTS notifications(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        titre TEXT,
        message TEXT,
        type TEXT,
        lu INTEGER DEFAULT 0,
        date TEXT
    );
    CREATE TABLE IF NOT EXISTS supports(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        sujet TEXT,
        message TEXT,
        statut TEXT DEFAULT 'ouvert',
        reponse TEXT,
        date TEXT
    );
    CREATE TABLE IF NOT EXISTS admins(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pseudo TEXT UNIQUE,
        mot_de_passe TEXT,
        role TEXT DEFAULT 'admin',
        created_at TEXT
    );
    CREATE TABLE IF NOT EXISTS journaux(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        action TEXT,
        detail TEXT,
        date TEXT
    );
    CREATE TABLE IF NOT EXISTS exercices_favoris(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        exercice_id INTEGER NOT NULL,
        date TEXT,
        UNIQUE(user_id,exercice_id)
    );
    """)
    # Plans — 7 offres : gratuit 48H + 6 abonnements (3 jours → annuel avec tranches)
    plans = [
        ('gratuit',   'Essai gratuit 48 H',   0,    2,    30,   1, 'Essai 48 h : 30 questions IA · 1 photo · tout débloqué', 'unique', 1),
        ('3jours',    'Pack 3 Jours',         250,  3,    15,   1, '3 jours · 15 questions IA/jour · 1 photo/jour', 'unique', 1),
        ('1semaine',  'Pack 1 Semaine',       500,  7,    30,   2, '7 jours · 30 questions IA/jour · 2 photos/jour', 'unique', 1),
        ('2semaines', 'Pack 2 Semaines',     1000,  14,   50,   3, '14 jours · 50 questions IA/jour · 3 photos/jour', 'unique', 1),
        ('1mois',     'Pack 1 Mois',         2000,  30,   100,  5, '30 jours · 100 questions IA/jour · 5 photos/jour', 'unique', 1),
        ('bac',       'Pack BAC',            3000,  90,   200,  10, '90 jours · 200 questions IA/jour · 10 photos/jour · tous niveaux', 'unique', 1),
        ('annuel',    'Pack Annuel',        10000,  365,  500,  30, '1 an · 500 questions IA/jour · 30 photos/jour · tous niveaux', 'mensuel', 10),
    ]
    for p in plans:
        c.execute("INSERT OR IGNORE INTO plans (code,nom,prix,duree_jours,limite_ia_jour,photo_jour,description,paiement_tranche,nb_tranches) VALUES (?,?,?,?,?,?,?,?,?)", p)
    sujets = [
        ('maths','Mathématiques','sciences',1),('fr','Français','langues',2),('phys','Physique','sciences',3),
        ('chim','Chimie','sciences',4),('hist','Histoire','sociales',5),('geo','Géographie','sociales',6),
        ('svt','SVT','sciences',7),('ang','Anglais','langues',8),('es','Espagnol','langues',9),
        ('ara','Arabe','langues',10),('ed_na','Éducation nationale','sociales',11),('info','Informatique','sciences',12),
        ('ec',  'Économie','sociales',13),('philo','Philosophie','sociales',14),('arts','Arts plastiques','culture',15),
        ('mus', 'Musique','culture',16),('sport','EPS','culture',17),('tec', 'Technologie','sciences',18),
    ]
    for s in sujets:
        c.execute("INSERT OR IGNORE INTO sujets (code,nom,categorie,ordre) VALUES (?,?,?,?)", s)
    # Cours
    cours_list = [
        ('maths','Algèbre','x²+2x+1=0 → (x+1)²=0 → x=-1','Terminale','Algèbre'),
        ('maths','Géométrie','Aire triangle = base×hauteur/2','3ème','Géométrie'),
        ('fr','Conjugaison','Passé composé de « faire » → j\'ai fait','2nde','Conjugaison'),
        ('fr','Orthographe','« a » préposition vs « à » verbe','2nde','Orthographe'),
        ('phys','Loi de Newton','F = m × a','Terminale','Mécanique'),
        ('hist','Histoire Sénégal','Dakar capitale depuis 1866','3ème','Sénégal moderne'),
        ('geo','Géographie','Le Sénégal est en Afrique de l\'Ouest','3ème','Afrique'),
        ('svt','Photosynthèse','6CO₂ + 6H₂O → C₆H₁₂O₆ + 6O₂','3ème','Biologie'),
        ('ang','Vocabulaire','Hello = Bonjour','2nde','Vocabulaire'),
        ('info','Algorithme','Une suite d\'instructions','2nde','Algorithmes'),
    ]
    for c_ in cours_list:
        c.execute("INSERT OR IGNORE INTO cours (sujet_code,titre,contenu,niveau,chapitre) VALUES (?,?,?,?,?)", c_)
    # Exercices bibliothèque — CM1 → Université, 12 matières
    exercices = [
        # ── CM1 ──
        ('maths','Addition','qcm','2+3=?',json.dumps(['4','5','6','7']),'1','2+3=5','CM1','Arithmétique',1),
        ('maths','Soustraction','qcm','7-4=?',json.dumps(['2','3','4','5']),'1','7-4=3','CM1','Arithmétique',1),
        ('fr','Alphabet','qcm','Quelle lettre suit « D »?',json.dumps(['C','E','F','G']),'1','E','CM1','Alphabet',1),
        ('fr','Mot de passe','qcm','Comment dit-on « maison »?',json.dumps(['maison','maisonne','mison','mayon']),'0','maison','CM1','Vocabulaire',1),
        ('svt','Animaux','qcm','Qu\'appelle-t-on un baby-carriage?',json.dumps(['Un animal','Un vélo','Un jouet','Une maison']),'1','Un animal','CM1','Animaux',1),
        # ── CM2 ──
        ('maths','Multiplication','qcm','3×4=?',json.dumps(['7','10','12','14']),'2','3×4=12','CM2','Produit',1),
        ('maths','Division','qcm','12/3=?',json.dumps(['2','3','4','6']),'2','12/3=4','CM2','Division',1),
        ('fr','Conjugaison','qcm','« Je ___ à l\'école »?',json.dumps(['vais','vas','va','vont']),'0','vais','CM2','Conjugaison',1),
        ('hist','Drapeau','qcm','Combien de couleurs a le drapeau sénégalais?',json.dumps(['2','3','4','5']),'1','3','CM2','Sénégal',1),
        ('geo','Continent','qcm','Le Sénégal est en?',json.dumps(['Afrique','Europe','Asie','Amérique']),'0','Afrique','CM2','Géographie',1),
        # ── 6ème ──
        ('maths','Division longue','qcm','100/4=?',json.dumps(['20','25','30','40']),'1','100/4=25','6ème','Division',1),
        ('maths','Fractions','qcm','1/2 + 1/2 = ?',json.dumps(['1','1/2','2','1/4']),'0','1','6ème','Fractions',2),
        ('fr','Accord','qcm','« Les garçons ___ content »?',json.dumps(['est','sont','été','être']),'1','sont','6ème','Accord',2),
        ('svt','Corps humain','qcm','Où se trouve le cœur?',json.dumps(['Tête','Poitrine','Dos','Bras']),'1','Poitrine','6ème','Anatomie',2),
        ('ang','Salutation','qcm','« Hello » signifie?',json.dumps(['Au revoir','Bonjour','Merci','Oui']),'1','Bonjour','6ème','Vocabulaire',1),
        # ── 5ème ──
        ('maths','Puissance','qcm','2³=?',json.dumps(['6','8','9','12']),'1','2³=8','5ème','Puissances',2),
        ('maths','Opposé','qcm','Opposé de -5?',json.dumps(['-5','0','5','10']),'2','+5','5ème','Nombres relatifs',2),
        ('fr','Temps','qcm','« Hier, je ___ à l\'école »?',json.dumps(['vais','allais','suis allé','irai']),'2','suis allé','5ème','Temps',2),
        ('phys','Unités','qcm','L\'unité de mesure de la force est?',json.dumps(['kg','N','J','W']),'1','N (Newton)','5ème','Unités',2),
        ('info','Algorithme','qcm','Une suite d\'instructions s\'appelle?',json.dumps(['Un algorithme','Un programme','Un code','Un site']),'0','Un algorithme','5ème','Algorithmes',2),
        # ── 4ème ──
        ('maths','Problème ouvert','ouvert','Combien font 7×8 ?','','56','7×8=56','4ème','Produit',2),
        ('maths','Problème ouvert','ouvert','Résous : x+5=12','','x=7','x=7','4ème','Équations',3),
        ('maths','PGCD','qcm','PGCD de 12 et 18?',json.dumps(['2','3','6','9']),'2','6','4ème','PGCD/PCM',3),
        ('fr','Orthographe','qcm','« aller ___ l\'école »?',json.dumps(['à','a','en','au']),'0','à','4ème','Orthographe',2),
        ('svt','Cellule','qcm','La cellule se divise en?',json.dumps(['Mitose','Métamorphose','Évolution','Photosynthèse']),'0','Mitose','4ème','Biologie',3),
        # ── 3ème ──
        ('maths','Fonction','qcm','Pour f(x)=2x+1, f(3)=?',json.dumps(['5','6','7','8']),'2','7','3ème','Fonctions',3),
        ('maths','Théorème','qcm','Dans un triangle rectangle, a²+b²=?',json.dumps(['c','c²','2c','a×b']),'1','c²','3ème','Pythagore',3),
        ('fr','Part du passé','qcm','« Il ___ hier »?',json.dumps(['vient','venait','est venu','viendra']),'2','est venu','3ème','Temps',3),
        ('hist','Capitale','qcm','Capitale du Sénégal?',json.dumps(['Dakar','Saint-Louis','Thiès','Kaolack']),'0','Dakar','3ème','Sénégal',1),
        ('geo','Climat','qcm','Quel climat a le Sénégal?',json.dumps(['Tempéré','Tropical','Polaire','Désertique']),'1','Tropical','3ème','Géographie',2),
        ('svt','Photosynthèse','qcm','La photosynthèse produit?',json.dumps(['O₂','CO₂','N₂','H₂O']),'0','O₂','3ème','Biologie',2),
        # ── 2nde ──
        ('maths','Dérivée','qcm','Dérivée de x²?',json.dumps(['x','2x','2','x²']),'1','2x','2nde','Calcul',4),
        ('fr','Conjugaison','qcm','Passé composé de « faire »?',json.dumps(['fais','fait','ai fait','feras']),'2','j\'ai fait','2nde','Conjugaison',2),
        ('fr','Participe passé','qcm','Participe passé de « finir »?',json.dumps(['fini','finit','finissant','finira']),'0','fini','2nde','Conjugaison',2),
        ('fr','Rédaction','ouvert','Écris une phrase avec « cependant ».','','Cependant, il pleuvait.','La conjonction « cependant » introduit une opposition.','2nde','Rédaction',2),
        ('phys','Newton','qcm','F = ?',json.dumps(['m+a','m×a','m/a','m-a']),'1','m×a','2nde','Mécanique',3),
        ('chim','Eau','qcm','Formule de l\'eau est?',json.dumps(['CO₂','H₂O','O₂','H₂'],),'1','H₂O','2nde','Chimie',2),
        ('ang','Grammar','qcm','« I ___ a book »?',json.dumps(['read','reads','reading','have read']),'0','read','2nde','Grammar',2),
        ('es','Saludos','qcm','« Hola » signifie?',json.dumps(['Au revoir','Bonjour','Merci','Oui']),'1','Bonjour','2nde','Vocabulaire',1),
        # ── Première ──
        ('maths','Inégalité','qcm','Résous : 2x-3 > 7',json.dumps(['x>2','x>5','x>7','x>10']),'1','x>5','Première','Inéquations',4),
        ('maths','Probabilités','qcm','P(obtenir 6 avec un dé)?',json.dumps(['1/3','1/6','1/2','1/12']),'1','1/6','Première','Probabilités',4),
        ('phys','Énergie','qcm','Formule de l\'énergie cinétique?',json.dumps(['mv','½mv²','mgh','Fd']),'1','½mv²','Première','Énergie',4),
        ('chim','Tableau','qcm','Dans le tableau périodique, H a numéro?',json.dumps(['1','2','8','18']),'0','1','Première','Chimie',3),
        ('philo','Question','ouvert','Que signifie « penser »?','','Penser = exercer son esprit, raisonner, comprendre.','Penser est l\'acte de réfléchir et de raisonner.','Première','Philosophie',3),
        ('info','Python','qcm','En Python, comment déclarer une variable?',json.dumps(['var x=5','x=5','x:5','set x=5']),'1','x=5','Première','Informatique',3),
        ('ec','Définition','qcm','Qu\'est-ce que l\'inflation?',json.dumps(['Baisse des prix','Hausse générale des prix','Stagnation','Croissance',''] if False else ['Baisse des prix','Hausse générale des prix','Stagnation','Croissance']),'1','Hausse générale des prix','Première','Économie',3),
        # ── Terminale ──
        ('maths','Dérivée 2','qcm','Dérivée de sin(x)?',json.dumps(['cos(x)','-cos(x)','sin(x)','-sin(x)']),'0','cos(x)','Terminale','Calcul',5),
        ('maths','Intégrale','qcm','∫ 2x dx = ?',json.dumps(['x²+C','2+C','x²+2','2x²+C']),'0','x²+C','Terminale','Calcul',5),
        ('phys','Rélativité','qcm','Formule d\'énergie E=mc² est de?',json.dumps(['Newton','Einstein','Planck','Bohr']),'1','Einstein','Terminale','Physique',5),
        ('fr','Argument','ouvert','Écris un argument sur la liberté d\'expression.','','La liberté d\'expression est un droit fondamental...','Argumenter = fournir des raisons pour défendre une position.','Terminale','Rédaction',4),
        ('ara','Alif','qcm','Quelle lettre est la première de l\'alphabet arabe?',json.dumps(['Alif','Ba','Dal','Sad']),'0','Alif','Terminale','Arabe',2),
        # ── Université ──
        ('maths','Limite','qcm','lim(x→0) sin(x)/x = ?',json.dumps(['0','1','∞','x'],),'1','1','Université','Analyse',5),
        ('maths','Dérivée partielle','qcm','∂/∂x (x²y) = ?',json.dumps(['2xy','x²y','2y','xy²']),'0','2xy','Université','Analyse',5),
        ('info','Algorithme','qcm','La complexité de tri rapide est?',json.dumps(['O(n)','O(n log n)','O(n²)','O(log n)'],),'1','O(n log n)','Université','Algorithmes',5),
        ('chim','Orbitale','qcm','Nombre d\'orbitales dans la couche n=2?',json.dumps(['1','2','4','8'],),'2','4','Université','Chimie',5),
        ('ec','Monnaie','qcm','Qu\'est-ce que le Bitcoin?',json.dumps(['Monnaie numérique','Action','Obligation','Matière'],),'0','Monnaie numérique','Université','Économie',4),
        ('maths','Dérivée','qcm','d/dx (3x²+2x) = ?',json.dumps(['6x','3x+2','6x+2','3x²']),'2','6x+2','Université S1','Calcul',5),
        ('info','Structure','qcm','Quelle structure de données est FIFO?',json.dumps(['Stack','Queue','Tree','Graph']),'1','Queue','Université S1','Algorithmes',4),
        ('phys','Thermo','qcm','La loi de Fourier concerne?',json.dumps(['Convection','Conduction','Radiation','Évaporation']),'1','Conduction','Université S1','Thermodynamique',5),
        ('chim','Cinétique','qcm','La vitesse de réaction dépend de?',json.dumps(['Température','Pression','Volume','Masse']),'0','Température','Université S1','Chimie',4),
        ('fr','Analyse','ouvert','Analyse le registre d un texte scientifique.','','Un texte scientifique utilise un registre formel, impersonnel, précis.','Analyser un registre = identifier le niveau de langue, le ton, le style.','Université S1','Analyse',4),
        ('ec','Théorie','qcm','Qu est-ce que la monnaie fiduciaire?',json.dumps(['Monnaie électronique','Monnaie scripturale','Monnaie basée sur la confiance','Monnaie collante']),'2','Monnaie basée sur la confiance','Université S1','Économie',4),
        ('maths','Statistique','qcm','La variance de X est Var(X)=?',json.dumps(['E(X)','E(X²)','E(X²)-E(X)²','E(X)-E(X²)']),'2','E(X²)-E(X)²','Université S2','Statistiques',5),
        ('info','Base de données','qcm','Quel langage pour gérer une base SQL?',json.dumps(['HTML','Python','SQL','CSS']),'2','SQL','Université S2','Bases de données',4),
        ('phys','Électromag','qcm','La loi d Ohm est V = ?',json.dumps(['R/I','I×R','I/R','R×I²']),'1','I×R','Université S2','Électricité',5),
        ('chim','Organique','qcm','Quel groupe fonctionnel contient le méthane?',json.dumps(['Aldéhyde','Alcool','Alcan','Acide']),'2','Alcan','Université S2','Chimie organique',5),
        ('fr','Argument','ouvert','Rédige un plan de dissertation (intro-dév-concl).','','Introduction : définition + problématique. Développement : arguments + exemples. Conclusion : synthèse + ouverture.','Un plan de dissertation suit une structure tripartite.','Université S2','Rédaction',4),
        ('ec','Étude','qcm','Qu est-ce que le PIB nominal?',json.dumps(['PIB à prix constants','PIB à prix courants','PIB réel','PIB en volume']),'1','PIB à prix courants','Université S2','Économie',4),
    ]
    for e in exercices:
        c.execute("INSERT OR IGNORE INTO exercises (sujet_code,titre,type,qtext,options,reponse,explication,niveau,chapitre,difficulte) VALUES (?,?,?,?,?,?,?,?,?,?)", e)
    # Notifications par défaut pour nouveaux utilisateurs (créées à l'inscription)
    c.execute("INSERT OR IGNORE INTO admins (pseudo,mot_de_passe,role,created_at) VALUES ('admin',?,'superadmin',?)",
              (hashlib.sha256(ADMIN_PASSWORD.encode()).hexdigest(), datetime.datetime.now().isoformat()))
    c.commit()
    c.close()

# ─────────────────────────────────────────────
# Utilitaires
# ─────────────────────────────────────────────
def hash_pass(m):
    return hashlib.sha256(m.encode()).hexdigest()

def now():
    return datetime.datetime.now().isoformat()

def jwt_create(uid, role='eleve'):
    payload = {"uid":uid,"role":role,"exp":int(datetime.datetime.now().timestamp())+86400*30}
    return base64.urlsafe_b64encode(json.dumps(payload).encode()).decode()

def jwt_decode(token):
    try:
        payload = json.loads(base64.urlsafe_b64decode(token.encode()).decode())
        if int(payload.get("exp",0)) < datetime.datetime.now().timestamp():
            return None
        return payload
    except Exception:
        return None

def log_sec(uid, action, detail=""):
    c = db()
    c.execute("INSERT INTO journaux (user_id,action,detail,date) VALUES (?,?,?,?)", (uid,action,detail,now()))
    c.commit()
    c.close()

def get_user_by_token(handler):
    auth = handler.headers.get("Authorization","")
    if not auth.startswith("Bearer "):
        return None
    payload = jwt_decode(auth[7:])
    if not payload:
        return None
    c = db()
    u = c.execute("SELECT * FROM users WHERE id=?", (payload["uid"],)).fetchone()
    c.close()
    return u

def plan_actif(u):
    """Plan applicable : gratuit (48h) sans abonnement, ou abonnement payant actif."""
    if not u: return None
    c = db()
    sub = c.execute("SELECT * FROM abonnements WHERE user_id=? AND statut='actif' ORDER BY debut DESC LIMIT 1", (u["id"],)).fetchone()
    if sub:
        p = c.execute("SELECT * FROM plans WHERE code=?", (sub["plan_code"],)).fetchone()
        if p:
            return dict(p) | {"abonnement_id": sub["id"], "expire": sub["expire"]}
    p = c.execute("SELECT * FROM plans WHERE code='gratuit'").fetchone()
    if p:
        debut = u["created_at"]
        limite = debut[:10] + "T00:00:00"
        d = datetime.datetime.fromisoformat(debut) + datetime.timedelta(hours=48)
        limite = d.isoformat()
        if d > datetime.datetime.now():
            return dict(p)
    return None

def update_usage(uid, field):
    c = db()
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    row = c.execute("SELECT * FROM usages WHERE user_id=? AND date=?", (uid, today)).fetchone()
    if not row:
        col = {"ia":"ia_count","photo":"photo_count","correct":"correct_count","ex":"ex_count"}[field]
        c.execute("INSERT INTO usages (user_id,date,ia_count,photo_count,correct_count,ex_count) VALUES (?,?,0,0,0,0)", (uid, today))
        c.execute(f"UPDATE usages SET {col}=1 WHERE user_id=? AND date=?", (uid, today))
    else:
        col = {"ia":"ia_count","photo":"photo_count","correct":"correct_count","ex":"ex_count"}[field]
        c.execute(f"UPDATE usages SET {col}={col}+1 WHERE user_id=? AND date=?", (uid, today))
    c.commit()
    c.close()

def check_quota(u, plan, field):
    if not plan: return False, "Essai gratuit de 48 h terminé — abonne-toi pour continuer."
    update_usage(u["id"], field)
    c = db()
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    row = c.execute("SELECT * FROM usages WHERE user_id=? AND date=?", (u["id"], today)).fetchone()
    c.close()
    if not row: return True, ""
    col = {"ia":"ia_count","photo":"photo_count","correct":"correct_count","ex":"ex_count"}[field]
    limite = plan["limite_ia_jour"] if field in ("ia","correct") else plan["photo_jour"]
    if field == "ex": limite = 50
    if row[col] > limite:
        return False, f"Quota atteint pour aujourd'hui ({limite}). Réessaille demain ou passe à un abonnement."
    return True, ""

# ─────────────────────────────────────────────
# Calculateur local + bibliothèque de réponses
# ─────────────────────────────────────────────
def _calculer(question):
    """Calcul mathématique local instantané."""
    q = question.lower()
    m = re.search(r'(\d+(?:[.,]\d+)?)\s*([+\-*/×÷x])\s*(\d+(?:[.,]\d+)?)', q)
    if not m: return None
    a = float(m.group(1).replace(',','.'))
    op = m.group(2)
    b = float(m.group(3).replace(',','.'))
    try:
        if op in ('+','＋'): r = a + b
        elif op in ('-','－'): r = a - b
        elif op in ('*','×','x','X','x'): r = a * b
        elif op in ('/','÷'):
            if b == 0: return None
            r = a / b
        else: return None
        if isinstance(r,float) and r.is_integer(): r = int(r)
        return {"reponse": str(r), "explication": f"{a:g} {op if op not in ('*','x') else '×'} {b:g} = {r:g}",
                "confiance": 0.99, "source": "Calcul local",
                "etapes": [f"Identifier l'opération {a:g} {op} {b:g}", f"Effectuer le calcul = {r:g}"]}
    except Exception:
        return None

REPONSES_LOCALES = {
    "photosynthèse": ("La photosynthèse est le processus par lequel les végétaux verts transforment la lumière du soleil, le CO₂ et l'eau en glucose (énergie) et en dioxygène (O₂). Équation : 6CO₂ + 6H₂O → C₆H₁₂O₆ + 6O₂. Elle se déroule dans les chloroplastes.", "SVT"),
    "democratie": ("La démocratie est un régime politique où le pouvoir est exercé par le peuple. Au Sénégal, c'est une république démocratique sécularisée. Le peuple élit le président et les députés.", "Éducation nationale"),
    "sénégal": ("Le Sénégal est un pays d'Afrique de l'Ouest. Capitale : Dakar. Langue officielle : français. Langues nationales : wolof, sérère, mandingue, soninké, peule. Population : ~17 millions.", "Géographie"),
    "dakar": ("Dakar est la capitale du Sénégal, sur la côte atlantique, presqu'île du Cap-Vert. Centre économique et culturel. ~3 millions d'habitants.", "Géographie"),
    "sutu rekk": ("« Sutu rekk » en wolof signifie « cinquante » (50).", "Mathématiques"),
    "newton": ("La loi de Newton (F=ma) : la force F = masse m × accélération a. Unité : Newton (N).", "Physique"),
    "pythagore": ("Théorème de Pythagore : dans un triangle rectangle, a² + b² = c² où c est l'hypoténuse.", "Mathématiques"),
    "einstein": ("Albert Einstein (1879-1955), physicien. Théorie de la relativité, E=mc². Prix Nobel 1921.", "Physique"),
    "hydrocarbure": ("Hydrocarbures : composés de C et H. Méthane CH₄, éthane C₂H₆, pétrole, gaz naturel.", "Chimie"),
    "colonisation": ("La colonisation : domination d'un pays sur un autre. Sénégal colonisé par la France (1854-1960). Indépendance le 20 juin 1960.", "Histoire"),
    "lumières": ("Les Lumières (18e s.) : mouvement intellectuel valorisant raison, liberté, égalité. Voltaire, Rousseau, Montesquieu, Diderot.", "Histoire"),
    "bac": ("Le Baccalauréat : diplôme de fin de lycée. Séries : A (philosophie), B (sciences), C (littéraire).", "Éducation nationale"),
    "informatique": ("L'informatique : science du traitement de l'information par ordinateurs. Algorithmique, programmation, réseaux, cybersécurité.", "Informatique"),
    "économie": ("L'économie : science de production, distribution et consommation de biens. Microéconomie et macroéconomie.", "Économie"),
    "philosophie": ("La philosophie : discipline étudiant existence, connaissance, valeurs, raison. Platon, Aristote, Descartes, Kant, Sartre.", "Philosophie"),
    "anglais": ("L'anglais : langue germanique, internationale des affaires et de la science. Hello=Bonjour, Thank you=Merci.", "Anglais"),
    "wolof": ("Le wolof : langue nigéro-congolaise du Sénégal. Suli=Bonjour, Wahaa=Oui, Degg=Médiocre.", "Wolof"),
    "espagnol": ("L'espagnol : langue romane d'Espagne et d'Amérique latine. Hola=Bonjour, Gracias=Merci.", "Espagnol"),
    "arabe": ("L'arabe : langue sémitique du monde arabe. Écrit de droite à gauche. مرحبا=Bienvenue, شكرا=Merci.", "Arabe"),
    "portugais": ("Le portugais : langue romane du Portugal, Brésil, Angola. Olá=Bonjour, Obrigado=Merci.", "Portugais"),
    "allemand": ("L'allemand : langue germanique d'Allemagne, Autriche, Suisse. Guten Tag=Bonjour, Danke=Merci.", "Allemand"),
    "sine": ("Le sinus (sin) : fonction trigonométrique, rapport entre côté opposé et hypoténuse dans un triangle rectangle.", "Mathématiques"),
    "cosine": ("Le cosinus (cos) : fonction trigonométrique, rapport entre côté adjacent et hypoténuse.", "Mathématiques"),
    "intelligence": ("L'IA : domaine de l'informatique visant à créer des machines intelligentes : raisonnement, apprentissage, décision.", "Informatique"),
    "volcan": ("Un volcan : rupture dans la croûte terrestre laissant sortir magma, lave, cendres. Placé sur plaques tectoniques.", "Géographie"),
    "solaire": ("Le système solaire : Soleil + 8 planètes (Mercure à Neptune), lunes, astéroïdes, comètes.", "Géographie"),
    "monde": ("Le monde : 7 continents, 195 pays. Afrique, Antarctique, Asie, Australie, Europe, Amérique N., Amérique S.", "Géographie"),
}

# File d'attente simple pour contourner le rate-limit Pollinations (1 réq/30s par IP)
_pollinations_lock = threading.Lock()
_last_pollinations_call = 0
_POLLINATIONS_MIN_INTERVAL = 5  # secondes entre deux appels (contourne rate-limit sans bloquer)

def _ai_call(messages, max_tokens=600, timeout=25):
    """Appel IA : OVH AI (rapide, gratuit) → Pollinations /openai → repli."""
    # ── 1. OVH AI (Llama 3.3 70B, gratuit, sans clé) ──
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                OVH_AI_URL,
                data=json.dumps({"model": OVH_AI_MODEL, "messages": messages, "max_tokens": max_tokens}).encode(),
                headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                data = json.loads(r.read().decode())
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            if attempt < 2: time.sleep(1.5 * (attempt + 1))
    # ── 2. Pollinations /openai (fallback) ──
    global _last_pollinations_call
    for attempt in range(3):
        try:
            with _pollinations_lock:
                now_ts = time.time()
                if now_ts - _last_pollinations_call < _POLLINATIONS_MIN_INTERVAL:
                    wait = _POLLINATIONS_MIN_INTERVAL - (now_ts - _last_pollinations_call)
                    time.sleep(min(wait, 10))
                _last_pollinations_call = time.time()
            req = urllib.request.Request(
                POLLINATIONS_URL,
                data=json.dumps({"messages": messages, "model": "openai", "max_tokens": max_tokens}).encode(),
                headers={"Content-Type": "application/json", "Referer": POLLINATIONS_REFERER})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                data = json.loads(r.read().decode())
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            if attempt < 2: time.sleep(2 * (attempt + 1))
    return None

def reponse_ia(question, plan=None):
    """Assistant IA réel : calculateur local → bibliothèque → Pollinations /openai → repli."""
    # 1. Calcul local
    calc = _calculer(question)
    if calc: return calc
    # 2. Bibliothèque locale
    ql = question.lower()
    for key,(rep,sujet) in REPONSES_LOCALES.items():
        if key in ql:
            return {"reponse": rep, "explication": rep, "confiance": 0.85, "source": "Bibliothèque locale",
                    "etapes": ["Recherche dans la bibliothèque de cours ÉcoleMax"]}
    # 3. Pollinations IA avec retry
    messages = [{"role":"system","content":"Tu es Professeur IA d'ÉcoleMax. Tu réponds en français, pédagogique, bref et clair. Adapte ton niveau à l'élève (CM1 à Université). Structure : 1) Réponse directe, 2) Explication, 3) Étapes ou exemple si nécessaire. Pour les maths : donne la méthode. Pour les langues : donne la traduction + usage. Pour les sciences : donne la définition + exemple concret. Sois concis (max 150 mots)."},
                {"role":"user","content":question}]
    content = _ai_call(messages, max_tokens=600, timeout=25)
    if content:
        return {"reponse": content, "source": "IA"}
    return {"reponse": "⚠️ IA momentanément saturée (trop d'élèves en même temps). Essaye un calcul (2+2), ou demande un sujet du cours. Réessaille dans 30 secondes.",
                "source": "hors ligne"}

def reponse_ia_photo(question, image_b64, plan=None):
    """Correction photo : OCR + résolution via Pollinations vision."""
    question = question or "Lis cet énoncé, reconnais-le et résous-le étape par étape en français."
    messages = [{"role":"system","content":"Tu es Professeur IA d'ÉcoleMax. Reconnaît l'énoncé dans l'image, résous-le, explique chaque étape en français pédagogique. Si l'image est illisible, dis-le et demande une nouvelle photo."},
                {"role":"user","content":[
                    {"type":"text","text":question},
                    {"type":"image_url","image_url":{"url":f"data:image/jpeg;base64,{image_b64}"}}
                ]}]
    content = _ai_call(messages, max_tokens=700, timeout=30)
    if content:
        return {"reponse": content, "source": "IA Vision"}
    return {"reponse": "⚠️ IA Vision momentanément saturée. Vérifie la luminosité et reprends une photo claire, ou envoie l'énoncé en texte. Réessaille dans 30 secondes.", "source": "hors ligne"}

# ─────────────────────────────────────────────
# HTTP Handler
# ─────────────────────────────────────────────
class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a): pass

    def send_json(self, data, code=200):
        body = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type","application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin","*")
        self.send_header("Access-Control-Allow-Headers","*")
        self.send_header("Content-Length",str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_html(self, path, code=200):
        if not os.path.isfile(path):
            self.send_error(404, "Fichier non trouvé")
            return
        with open(path,"rb") as f:
            body = f.read()
        self.send_response(code)
        ext = path.lower().split(".")[-1]
        ct = {"html":"text/html; charset=utf-8","js":"application/javascript","css":"text/css",
              "json":"application/json","apk":"application/vnd.android.package-archive","png":"image/png","ico":"image/x-icon"}.get(ext,"application/octet-stream")
        self.send_header("Content-Type", ct)
        self.send_header("Access-Control-Allow-Origin","*")
        self.send_header("Content-Length",str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def body(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            if length == 0: return {}
            raw = self.rfile.read(length)
            return json.loads(raw.decode("utf-8", "replace") or "{}")
        except (json.JSONDecodeError, ValueError, UnicodeDecodeError):
            return {}

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin","*")
        self.send_header("Access-Control-Allow-Headers","*")
        self.end_headers()

    def do_GET(self):
        try:
            self._do_GET()
        except Exception as e:
            self.send_json({"erreur":"Erreur interne: "+str(e), "trace": str(e)[:200]}, 500)

    def _do_GET(self):
        path = self.path.split("?")[0]
        if path == "/health":
            return self.send_json({"status":"ok","service":"ecolemax","time":now()})
        if path == "/api/plans":
            c = db()
            rows = c.execute("SELECT * FROM plans ORDER BY prix").fetchall()
            c.close()
            return self.send_json([dict(r) for r in rows])
        if path == "/api/subjects":
            c = db()
            rows = c.execute("SELECT * FROM sujets ORDER BY ordre").fetchall()
            c.close()
            return self.send_json([dict(r) for r in rows])
        if path == "/api/content":
            u = get_user_by_token(self)
            c = db()
            sujets = c.execute("SELECT * FROM sujets ORDER BY ordre").fetchall()
            cours = c.execute("SELECT * FROM cours ORDER BY sujet_code,titre").fetchall()
            c.close()
            return self.send_json({"sujets":[dict(r) for r in sujets], "cours":[dict(r) for r in cours], "plan": plan_actif(u)})
        if path == "/api/admin/stats":
            if self.headers.get("X-Admin-Password","") != ADMIN_PASSWORD:
                return self.send_json({"erreur":"Non autorisé"}, 403)
            c = db()
            total = c.execute("SELECT COUNT(*) as n FROM users").fetchone()["n"]
            actifs = c.execute("SELECT COUNT(*) as n FROM users WHERE created_at > ?", (datetime.datetime.now().strftime("%Y-%m-%d"),)).fetchone()["n"]
            abonnes = c.execute("SELECT COUNT(*) as n FROM abonnements WHERE statut='actif'").fetchone()["n"]
            pays = c.execute("SELECT COUNT(*) as n FROM abonnements WHERE statut='actif' AND plan_code != 'gratuit'").fetchone()["n"]
            rev = c.execute("SELECT COALESCE(SUM(montant),0) as s FROM paiements WHERE statut='success'").fetchone()["s"]
            pend = c.execute("SELECT COUNT(*) as n FROM paiements WHERE statut='en_attente'").fetchone()["n"]
            ia_count = c.execute("SELECT COALESCE(SUM(ia_count),0) as s FROM usages").fetchone()["s"]
            c.close()
            return self.send_json({"total_users":total,"nouveaux_aujourdhui":actifs,"abonnes_actifs":abonnes,
                                   "payants":pays,"revenu_encaisse":rev,"paiements_attente":pend,
                                   "requetes_ia":ia_count,"objectif":3000000})
        if path == "/api/admin/users":
            if self.headers.get("X-Admin-Password","") != ADMIN_PASSWORD:
                return self.send_json({"erreur":"Non autorisé"}, 403)
            c = db()
            rows = c.execute("SELECT id,pseudo,email,niveau,role,created_at FROM users ORDER BY created_at DESC").fetchall()
            c.close()
            return self.send_json({"users":[dict(r) for r in rows]})
        if path == "/api/admin/abonnements":
            if self.headers.get("X-Admin-Password","") != ADMIN_PASSWORD:
                return self.send_json({"erreur":"Non autorisé"}, 403)
            c = db()
            rows = c.execute("SELECT a.*, u.pseudo FROM abonnements a JOIN users u ON a.user_id=u.id ORDER BY a.debut DESC").fetchall()
            c.close()
            return self.send_json({"abonnements":[dict(r) for r in rows]})
        if path == "/api/admin/paiements":
            if self.headers.get("X-Admin-Password","") != ADMIN_PASSWORD:
                return self.send_json({"erreur":"Non autorisé"}, 403)
            c = db()
            rows = c.execute("SELECT p.*, u.pseudo FROM paiements p JOIN users u ON p.user_id=u.id ORDER BY p.created_at DESC").fetchall()
            c.close()
            return self.send_json({"paiements":[dict(r) for r in rows]})
        if path == "/api/admin/matieres":
            if self.headers.get("X-Admin-Password","") != ADMIN_PASSWORD:
                return self.send_json({"erreur":"Non autorisé"}, 403)
            c = db()
            sujets = c.execute("SELECT * FROM sujets ORDER BY ordre").fetchall()
            cours = c.execute("SELECT * FROM cours").fetchall()
            ex = c.execute("SELECT * FROM exercises").fetchall()
            c.close()
            return self.send_json({"sujets":[dict(r) for r in sujets], "cours":[dict(r) for r in cours], "exercices":[dict(r) for r in ex]})
        if path == "/api/admin/supports":
            if self.headers.get("X-Admin-Password","") != ADMIN_PASSWORD:
                return self.send_json({"erreur":"Non autorisé"}, 403)
            c = db()
            rows = c.execute("SELECT s.*, u.pseudo FROM supports s JOIN users u ON s.user_id=u.id ORDER BY s.date DESC").fetchall()
            c.close()
            return self.send_json({"supports":[dict(r) for r in rows]})
        if path == "/api/admin/journaux":
            if self.headers.get("X-Admin-Password","") != ADMIN_PASSWORD:
                return self.send_json({"erreur":"Non autorisé"}, 403)
            c = db()
            rows = c.execute("SELECT * FROM journaux ORDER BY date DESC LIMIT 100").fetchall()
            c.close()
            return self.send_json({"journaux":[dict(r) for r in rows]})
        if path == "/api/admin/notifications":
            if self.headers.get("X-Admin-Password","") != ADMIN_PASSWORD:
                return self.send_json({"erreur":"Non autorisé"}, 403)
            c = db()
            rows = c.execute("SELECT * FROM notifications ORDER BY date DESC LIMIT 100").fetchall()
            c.close()
            return self.send_json({"notifications":[dict(r) for r in rows]})
        if path == "/api/me":
            u = get_user_by_token(self)
            if not u: return self.send_json({"erreur":"Authentification requise"}, 401)
            p = plan_actif(u)
            c = db()
            usage = c.execute("SELECT * FROM usages WHERE user_id=? AND date=?", (u["id"], datetime.datetime.now().strftime("%Y-%m-%d"))).fetchone()
            nb_notif = c.execute("SELECT COUNT(*) as n FROM notifications WHERE user_id=? AND lu=0", (u["id"],)).fetchone()["n"]
            nb_fav = c.execute("SELECT COUNT(*) as n FROM favoris WHERE user_id=?", (u["id"],)).fetchone()["n"]
            c.close()
            return self.send_json({"user":{"id":u["id"],"pseudo":u["pseudo"],"email":u["email"],"niveau":u["niveau"],"role":u["role"]},
                                   "plan":p,"usage":dict(usage) if usage else None,
                                   "notifications_non_lues":nb_notif,"favoris":nb_fav})
        if path == "/api/exercises":
            import urllib.parse as _up
            raw_qs = self.path.split("?", 1)[1] if "?" in self.path else ""
            qs = _up.parse_qs(_up.unquote(raw_qs, encoding="utf-8", errors="replace"))
            sujet = qs.get("sujet", qs.get("matiere", [""]))[0].lower()
            niveau = qs.get("niveau", [""])[0]
            chapitre = qs.get("chapitre", [""])[0]
            diff = qs.get("difficulte", [""])[0]
            c = db()
            q = "SELECT * FROM exercises WHERE 1=1"
            params = []
            if sujet: q += " AND sujet_code=?"; params.append(sujet)
            if niveau: q += " AND niveau=?"; params.append(niveau)
            if chapitre: q += " AND chapitre=?"; params.append(chapitre)
            if diff: q += " AND difficulte=?"; params.append(diff)
            rows = c.execute(q, params).fetchall()
            c.close()
            return self.send_json({"exercices":[dict(r) for r in rows]})
        if path.startswith("/api/"):
            return self.send_json({"erreur":"Méthode non autorisée"}, 405)
        # Fichiers statiques
        projet = os.path.join(os.path.dirname(os.path.abspath(__file__)), "projet")
        mapping = {"/":"index.html","/index.html":"index.html","/app.html":"app.html",
                   "/dashboard.html":"dashboard.html","/favicon.ico":"favicon.ico"}
        if path in mapping:
            return self.send_html(os.path.join(projet, mapping[path]))
        if path.startswith("/EcoleMax") or path.startswith("/apk"):
            tele = os.path.join(projet, "telechargements")
            for f in os.listdir(tele):
                if f.lower().startswith("ecolemax") and f.endswith(".apk"):
                    return self.send_html(os.path.join(tele, f))
        return self.send_json({"erreur":"Non trouvé"}, 404)

    def do_POST(self):
        try:
            self._do_POST()
        except Exception as e:
            self.send_json({"erreur":"Erreur interne: "+str(e), "trace": str(e)[:200]}, 500)

    def _do_POST(self):
        path = self.path.split("?")[0]
        data = self.body()
        u = get_user_by_token(self)

        if path == "/api/admin/user/block":
            if self.headers.get("X-Admin-Password","") != ADMIN_PASSWORD:
                return self.send_json({"erreur":"Non autorisé"}, 403)
            uid = data.get("user_id")
            c = db()
            u = c.execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone()
            if not u: c.close(); return self.send_json({"erreur":"Utilisateur non trouvé"}, 404)
            c.execute("DELETE FROM sessions WHERE user_id=?", (uid,))
            c.execute("UPDATE users SET role='bloque' WHERE id=?", (uid,))
            c.commit(); c.close()
            log_sec(1, "admin_action", f"Utilisateur {uid} bloqué")
            return self.send_json({"ok":True, "message":"Utilisateur bloqué"})

        if path == "/api/admin/user/delete":
            if self.headers.get("X-Admin-Password","") != ADMIN_PASSWORD:
                return self.send_json({"erreur":"Non autorisé"}, 403)
            uid = data.get("user_id")
            c = db()
            u = c.execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone()
            if not u: c.close(); return self.send_json({"erreur":"Utilisateur non trouvé"}, 404)
            c.execute("DELETE FROM sessions WHERE user_id=?", (uid,))
            c.execute("DELETE FROM favoris WHERE user_id=?", (uid,))
            c.execute("DELETE FROM notifications WHERE user_id=?", (uid,))
            c.execute("DELETE FROM usages WHERE user_id=?", (uid,))
            c.execute("DELETE FROM abonnements WHERE user_id=?", (uid,))
            c.execute("DELETE FROM paiements WHERE user_id=?", (uid,))
            c.execute("DELETE FROM results WHERE user_id=?", (uid,))
            c.execute("DELETE FROM supports WHERE user_id=?", (uid,))
            c.execute("DELETE FROM users WHERE id=?", (uid,))
            c.commit(); c.close()
            log_sec(1, "admin_action", f"Utilisateur {uid} supprimé")
            return self.send_json({"ok":True, "message":"Utilisateur supprimé"})

        if path == "/api/admin/abonnement/control":
            if self.headers.get("X-Admin-Password","") != ADMIN_PASSWORD:
                return self.send_json({"erreur":"Non autorisé"}, 403)
            c = db()
            expired = c.execute("SELECT * FROM abonnements WHERE statut='actif' AND (expire='' OR date(expire)<date('now'))").fetchall()
            pending = c.execute("SELECT * FROM abonnements WHERE statut='en_attente'").fetchall()
            no_sub = c.execute("SELECT id,pseudo,email FROM users WHERE NOT EXISTS(SELECT 1 FROM abonnements a WHERE a.user_id=users.id AND a.statut='actif')").fetchall()
            to_renew = c.execute("SELECT * FROM abonnements WHERE statut='actif' AND date(expire) BETWEEN date('now') AND date('now','+3 days')").fetchall()
            c.close()
            return self.send_json({
                "expires":[dict(r) for r in expired],
                "en_attente":[dict(r) for r in pending],
                "sans_abonnement":[dict(r) for r in no_sub],
                "a_renouveler":[dict(r) for r in to_renew],
                "stats":{
                    "expires_count":len(expired),
                    "attente_count":len(pending),
                    "sans_abonnement_count":len(no_sub),
                    "renouvellement_count":len(to_renew)
                }
            })

        
        if path == "/api/admin/abonnement/confirm":
            if self.headers.get("X-Admin-Password","") != ADMIN_PASSWORD:
                return self.send_json({"erreur":"Non autorisé"}, 403)
            uid = data.get("user_id")
            plan_code = data.get("plan","")
            c = db()
            plan = c.execute("SELECT * FROM plans WHERE code=?", (plan_code,)).fetchone()
            if not plan: c.close(); return self.send_json({"erreur":"Plan non trouvé"}, 404)
            u = c.execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone()
            if not u: c.close(); return self.send_json({"erreur":"Utilisateur non trouvé"}, 404)
            debut = datetime.datetime.now().isoformat()
            expire = (datetime.datetime.now() + datetime.timedelta(days=plan["duree_jours"])).isoformat()
            c.execute("UPDATE abonnements SET statut='actif', debut=?, expire=? WHERE user_id=?", (debut, expire, uid))
            c.commit(); c.close()
            log_sec(1, "admin_action", f"Admin a confirmé abonnement {plan_code} pour user {uid}")
            return self.send_json({"ok":True, "message":f"Abonnement {plan['nom']} confirmé pour {u['pseudo']}"})


        # ── Auth ──
        if path == "/api/register":
            pseudo = data.get("pseudo","").strip()
            mdp = data.get("mot_de_passe","")
            email = data.get("email","").strip()
            niveau = data.get("niveau","Terminale")
            if len(pseudo) < 3: return self.send_json({"erreur":"Pseudo trop court (3+ caractères)"}, 400)
            if len(mdp) < 8 or not re.search(r'[A-Za-z]', mdp) or not re.search(r'\d', mdp):
                return self.send_json({"erreur":"Mot de passe : 8+ caractères, lettre + chiffre"}, 400)
            c = db()
            if c.execute("SELECT id FROM users WHERE pseudo=?", (pseudo,)).fetchone():
                c.close()
                return self.send_json({"erreur":"Ce pseudo est déjà pris"}, 409)
            c.execute("INSERT INTO users (pseudo,email,mot_de_passe,niveau,created_at) VALUES (?,?,?,?,?)",
                      (pseudo,email,hash_pass(mdp),niveau,now()))
            uid = c.execute("SELECT id FROM users WHERE pseudo=?", (pseudo,)).fetchone()["id"]
            c.execute("INSERT INTO sessions (token,user_id,expires_at,created_at) VALUES (?,?,?,?)",
                      (jwt_create(uid),uid,datetime.datetime.now().isoformat(),now()))
            # Notification de bienvenue
            c.execute("INSERT INTO notifications (user_id,titre,message,type,lu,date) VALUES (?,?,?,?,?,?)",
                      (uid,"Bienvenue sur ÉcoleMax !","Ton essai gratuit de 48 H est activé. 30 questions IA, 1 photo par jour, tout débloqué. Bon apprentissage 🎓","system",0,now()))
            c.commit()
            c.close()
            log_sec(uid, "inscription", "Nouvel élève")
            return self.send_json({"ok":True,"token":jwt_create(uid),"user":{"id":uid,"pseudo":pseudo}})

        if path == "/api/login":
            pseudo = data.get("pseudo","")
            mdp = data.get("mot_de_passe","")
            c = db()
            u = c.execute("SELECT * FROM users WHERE pseudo=?", (pseudo,)).fetchone()
            c.close()
            if not u or u["mot_de_passe"] != hash_pass(mdp):
                return self.send_json({"erreur":"Identifiants invalides"}, 401)
            log_sec(u["id"], "connexion", "Connexion élève")
            return self.send_json({"ok":True,"token":jwt_create(u["id"]),"user":{"id":u["id"],"pseudo":u["pseudo"]}})

        if path == "/api/reset":
            pseudo = data.get("pseudo","")
            c = db()
            u = c.execute("SELECT * FROM users WHERE pseudo=?", (pseudo,)).fetchone()
            c.close()
            if not u: return self.send_json({"erreur":"Utilisateur non trouvé"}, 404)
            new = secrets.token_hex(4)
            c.execute("UPDATE users SET mot_de_passe=? WHERE id=?", (hash_pass(new), u["id"]))
            c.commit()
            c.close()
            return self.send_json({"ok":True,"nouveau_mdp":new})

        # ── IA — Professeur ──
        if path == "/api/ai/ask":
            if not u: return self.send_json({"erreur":"Authentification requise"}, 401)
            p = plan_actif(u)
            if not p: return self.send_json({"erreur":"Essai gratuit de 48 h terminé — abonne-toi pour continuer."}, 402)
            ok, msg = check_quota(u, p, "ia")
            if not ok: return self.send_json({"erreur":msg}, 402)
            q = data.get("question","").strip()
            if not q: return self.send_json({"erreur":"Question vide"}, 400)
            r = reponse_ia(q, p)
            log_sec(u["id"], "ia_question", q[:100])
            return self.send_json(r)

        # ── IA — Scanner photo ──
        if path == "/api/ai/photo":
            if not u: return self.send_json({"erreur":"Authentification requise"}, 401)
            p = plan_actif(u)
            if not p: return self.send_json({"erreur":"Essai gratuit de 48 h terminé — abonne-toi pour continuer."}, 402)
            ok, msg = check_quota(u, p, "photo")
            if not ok: return self.send_json({"erreur":msg}, 402)
            img = data.get("image","")
            if not img or len(img) < 100: return self.send_json({"erreur":"Image invalide"}, 400)
            q = data.get("question","")
            r = reponse_ia_photo(q, img, p)
            log_sec(u["id"], "ia_photo", "Correction photo")
            return self.send_json(r)

        # ── IA — Correcteur de texte ──
        if path == "/api/ai/correct":
            if not u: return self.send_json({"erreur":"Authentification requise"}, 401)
            p = plan_actif(u)
            if not p: return self.send_json({"erreur":"Essai gratuit de 48 h terminé — abonne-toi pour continuer."}, 402)
            ok, msg = check_quota(u, p, "correct")
            if not ok: return self.send_json({"erreur":msg}, 402)
            texte = data.get("texte","")
            if not texte or len(texte.strip()) < 10:
                return self.send_json({"erreur":"Texte trop court (10+ caractères)"}, 400)
            question = ("Corrige ce texte en français. Affiche d'abord le texte corrigé, puis explique chaque erreur "
                        "(orthographe, grammaire, conjugaison, ponctuation). Texte à corriger : " + texte[:1500])
            r = reponse_ia(question, p)
            c = db()
            c.execute("INSERT INTO corrections (user_id,original,corrige,explication,date) VALUES (?,?,?,?,?)",
                      (u["id"], texte[:500], r.get("reponse",""), "", now()))
            c.commit()
            c.close()
            log_sec(u["id"], "correction_texte", "Correction texte")
            return self.send_json(r)

        # ── Exercices ──
        if path == "/api/exercises":
            c = db()
            sujet = data.get("sujet","")
            niveau = data.get("niveau","")
            chapitre = data.get("chapitre","")
            diff = data.get("difficulte","")
            q = "SELECT * FROM exercises WHERE 1=1"
            params = []
            if sujet: q += " AND sujet_code=?"; params.append(sujet)
            if niveau: q += " AND niveau=?"; params.append(niveau)
            if chapitre: q += " AND chapitre=?"; params.append(chapitre)
            if diff: q += " AND difficulte=?"; params.append(diff)
            rows = c.execute(q, params).fetchall()
            c.close()
            return self.send_json({"exercices":[dict(r) for r in rows]})

        if path == "/api/exercise/reponse":
            if not u: return self.send_json({"erreur":"Authentification requise"}, 401)
            eid = data.get("exercise_id")
            reponse = data.get("reponse","")
            score = 1 if reponse else 0
            c = db()
            ex = c.execute("SELECT * FROM exercises WHERE id=?", (eid,)).fetchone()
            if ex:
                correct = (str(ex["reponse"]) == reponse)
                score = 1 if correct else 0
                c.execute("INSERT INTO results (user_id,exercise_id,score,reponse_utilisateur,correct,date) VALUES (?,?,?,?,?,?)",
                          (u["id"], eid, score, reponse, 1 if correct else 0, now()))
            c.commit()
            c.close()
            update_usage(u["id"], "ex")
            return self.send_json({"ok":True,"score":score,"correct":correct if ex else False})

        # ── Favoris ──
        if path == "/api/favoris/add":
            if not u: return self.send_json({"erreur":"Authentification requise"}, 401)
            c = db()
            try:
                c.execute("INSERT INTO favoris (user_id,type,ref_id,label,date) VALUES (?,?,?,?,?)",
                          (u["id"], data.get("type","exercice"), data.get("ref_id",0), data.get("label",""), now()))
                c.commit()
            except sqlite3.IntegrityError:
                pass
            c.close()
            return self.send_json({"ok":True})

        if path == "/api/favoris":
            if not u: return self.send_json({"erreur":"Authentification requise"}, 401)
            c = db()
            rows = c.execute("SELECT * FROM favoris WHERE user_id=? ORDER BY date DESC", (u["id"],)).fetchall()
            c.close()
            return self.send_json({"favoris":[dict(r) for r in rows]})

        # ── Historique ──
        if path == "/api/history":
            if not u: return self.send_json({"erreur":"Authentification requise"}, 401)
            c = db()
            corr = c.execute("SELECT * FROM corrections WHERE user_id=? ORDER BY date DESC LIMIT 50", (u["id"],)).fetchall()
            res = c.execute("SELECT * FROM results WHERE user_id=? ORDER BY date DESC LIMIT 50", (u["id"],)).fetchall()
            c.close()
            return self.send_json({"corrections":[dict(r) for r in corr], "resultats":[dict(r) for r in res]})

        # ── Notifications ──
        if path == "/api/notifications":
            if not u: return self.send_json({"erreur":"Authentification requise"}, 401)
            c = db()
            rows = c.execute("SELECT * FROM notifications WHERE user_id=? OR user_id IS NULL ORDER BY date DESC LIMIT 50", (u["id"],)).fetchall()
            c.close()
            return self.send_json({"notifications":[dict(r) for r in rows]})

        if path == "/api/notifications/read":
            if not u: return self.send_json({"erreur":"Authentification requise"}, 401)
            c = db()
            c.execute("UPDATE notifications SET lu=1 WHERE user_id=?", (u["id"],))
            c.commit()
            c.close()
            return self.send_json({"ok":True})

        # ── Support ──
        if path == "/api/support":
            if not u: return self.send_json({"erreur":"Authentification requise"}, 401)
            c = db()
            c.execute("INSERT INTO supports (user_id,sujet,message,date) VALUES (?,?,?,?)",
                      (u["id"], data.get("sujet",""), data.get("message",""), now()))
            c.commit()
            c.close()
            return self.send_json({"ok":True})

        # ── Abonnements / Paiements ──
        if path == "/api/subscribe":
            if not u: return self.send_json({"erreur":"Authentification requise"}, 401)
            plan_code = data.get("plan","")
            method = data.get("method","wave")
            c = db()
            plan = c.execute("SELECT * FROM plans WHERE code=?", (plan_code,)).fetchone()
            if not plan: return self.send_json({"erreur":"Plan non trouvé"}, 404)
            if plan["code"] == "gratuit":
                return self.send_json({"erreur":"Ce plan est l'essai gratuit"}, 400)
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
            log_sec(u["id"], "paiement_creation", f"{plan_code} {method} {ref}")
            return self.send_json({"ok":True,"reference":ref,"abonnement_id":aid,"montant":plan["prix"]})

        if path == "/api/payment/confirm":
            """Confirmation sécurisée du paiement — activée seulement après vérification."""
            if not u: return self.send_json({"erreur":"Authentification requise"}, 401)
            ref = data.get("reference","")
            c = db()
            pay = c.execute("SELECT * FROM paiements WHERE reference=?", (ref,)).fetchone()
            if not pay: return self.send_json({"erreur":"Paiement non trouvé"}, 404)
            if pay["user_id"] != u["id"]: return self.send_json({"erreur":"Non autorisé"}, 403)
            if pay["statut"] != "en_attente":
                return self.send_json({"erreur":"Ce paiement est déjà traité"}, 400)
            # Simulation de vérification du prestataire (dans production : Webhook Wave/Orange Money)
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
            return self.send_json({"ok":True,"reference":ref,"statut":"success","message":"Abonnement activé ✅"})

        if path == "/api/payment/webhook":
            """Webhook des prestataires (Wave/Orange Money) — confirmation serveur."""
            ref = data.get("reference","")
            statut = data.get("statut","success")
            c = db()
            pay = c.execute("SELECT * FROM paiements WHERE reference=?", (ref,)).fetchone()
            if not pay: return self.send_json({"erreur":"Paiement non trouvé"}, 404)
            c.execute("UPDATE paiements SET statut=?, confirmed_at=? WHERE id=?", (statut, now(), pay["id"]))
            if statut == "success":
                plan = c.execute("SELECT * FROM plans WHERE prix=?", (pay["montant"],)).fetchone()
                if plan:
                    debut = datetime.datetime.now()
                    expire = debut + datetime.timedelta(days=plan["duree_jours"])
                    c.execute("UPDATE abonnements SET statut='actif', debut=?, expire=? WHERE user_id=? AND plan_code=?",
                              (debut.isoformat(), expire.isoformat(), pay["user_id"], plan["code"]))
            c.commit()
            c.close()
            return self.send_json({"ok":True})

        if path.startswith("/api/"):
            return self.send_json({"erreur":"Route non trouvée"}, 404)

        return self.send_json({"erreur":"Non trouvé"}, 404)

    # NOTE: do_GET unique ci-dessus — routes admin incluses.

if __name__ == "__main__":
    init_db()
    print(f"🟢 ÉcoleMax API démarrée → http://0.0.0.0:{PORT}")
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
