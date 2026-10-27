# -*- coding: utf-8 -*-
"""
ÉcoleMax — générateur de contenu pédagogique
=============================================
Produit des exercices et des quiz **vérifiés** (réponse calculée ou issue
d'une table de faits), répartis de façon **identique sur tous les niveaux**.

Principes :
  • Aucune question inventée au hasard : chaque réponse est calculée
    (maths, physique, chimie) ou provient d'une table de faits contrôlée.
  • Même nombre d'exercices par niveau, même nombre de quiz par catégorie.
  • Options de réponse stockées en JSON, index de la bonne réponse explicite.
"""
import json
import random
import re

LEVELS = ["CM1", "CM2", "6ème", "5ème", "4ème", "3ème", "2nde", "1ère", "Terminale",
          "Université L1", "Université L2", "Université L3", "Université S1", "Université S2"]

SUBJECTS = [
    ("math", "Mathématiques"), ("fr", "Français"), ("phys", "Physique"),
    ("chim", "Chimie"), ("svt", "SVT"), ("hist", "Histoire"),
    ("geo", "Géographie"), ("eng", "Anglais"), ("info", "Informatique"),
    ("eco", "Économie"), ("es", "Espagnol"), ("ara", "Arabe"),
]

# Niveau → indice de difficulté (0 = primaire, 8 = terminale / université)
LVL_IDX = {"CM1": 0, "CM2": 1, "6ème": 2, "5ème": 3, "4ème": 4, "3ème": 5,
           "2nde": 6, "1ère": 7, "Terminale": 8,
           "Université L1": 8, "Université L2": 8, "Université L3": 8,
           "Université S1": 8, "Université S2": 8}
UNIV = ["Université L1", "Université L2", "Université L3", "Université S1", "Université S2"]
DIFFS = ["facile", "moyen", "difficile"]


# ─────────────────────────────────────────────────────────────
#  Utilitaires
# ─────────────────────────────────────────────────────────────
def _fmt(x):
    """Formate un nombre : entier sans décimale, sinon 2 décimales max."""
    if isinstance(x, float):
        if abs(x - round(x)) < 1e-9:
            return str(int(round(x)))
        return ("%.2f" % x).rstrip("0").rstrip(".")
    return str(x)


def mkq(question, correct, distractors, explication=""):
    """Construit une question à 4 options mélangées."""
    correct = str(correct)
    opts = [correct]
    for d in distractors:
        d = str(d)
        if d != correct and d not in opts:
            opts.append(d)
        if len(opts) == 4:
            break
    n = 1
    while len(opts) < 4:
        filler = "Aucune de ces réponses" if n == 1 else ("Toutes ces réponses" if n == 2 else "Ne sait pas")
        if filler not in opts:
            opts.append(filler)
        n += 1
    rnd.shuffle(opts)
    return {
        "q": question,
        "o": opts,
        "i": opts.index(correct),
        "e": explication or ("La bonne réponse est : " + correct),
    }


def num_distractors(val, count=3, spread=None):
    """Génère des valeurs numériques fausses plausibles, distinctes de val."""
    out = []
    v = float(val)
    if spread is None:
        spread = max(1.0, abs(v) * 0.25)
    tries = 0
    while len(out) < count and tries < 60:
        tries += 1
        d = v + rnd.choice([-1, 1]) * rnd.uniform(0.1, 1.0) * spread
        d = round(d, 2) if isinstance(val, float) else int(round(d))
        if d != val and _fmt(d) not in [_fmt(x) for x in out] and (
                not isinstance(val, int) or isinstance(d, int)):
            out.append(d)
    while len(out) < count:
        out.append(v + len(out) + 1)
    return out


rnd = random.Random(20261027)


# ─────────────────────────────────────────────────────────────
#  MATHÉMATIQUES — générateurs procéduraux (réponses calculées)
# ─────────────────────────────────────────────────────────────
def gen_math(level, count):
    li = LVL_IDX[level]
    items = []
    guard = 0
    while len(items) < count and guard < count * 60:
        guard += 1
        kind = rnd.randrange(10)
        try:
            if li <= 1:          # CM1 / CM2
                if kind < 3:
                    a, b = rnd.randint(12, 99), rnd.randint(12, 99)
                    op = rnd.choice(["+", "-", "×"])
                    if op == "+": r = a + b
                    elif op == "-": r = a - b
                    else: a, b = rnd.randint(3, 12), rnd.randint(3, 12); r = a * b
                    items.append(mkq(f"Calcule : {a} {op} {b} = ?", _fmt(r),
                                     [_fmt(r + rnd.choice([-11, -10, 10, 11, 1, -1, 9])),
                                      _fmt(r + rnd.choice([-21, 21, 20, -20])), _fmt(r * 2 if r else 7)],
                                     f"{a} {op} {b} = {_fmt(r)}"))
                elif kind < 5:
                    b = rnd.randint(2, 9); q = rnd.randint(2, 12); r = b * q
                    a = r
                    items.append(mkq(f"{a} ÷ {b} = ?", _fmt(q),
                                     [_fmt(q + 1), _fmt(q - 1), _fmt(q * 2)],
                                     f"{a} ÷ {b} = {q} car {b} × {q} = {a}"))
                elif kind < 7:
                    n = rnd.randint(2, 6); d = rnd.randint(n + 1, 12)
                    items.append(mkq(f"Quelle fraction représente {n} parts sur {d} ?", f"{n}/{d}",
                                     [f"{d}/{n}", f"{n}/{d+1}", f"{n+1}/{d}"],
                                     f"On écrit {n}/{d}."))
                else:
                    a = rnd.randint(2, 12) * 10
                    items.append(mkq(f"Combien font {a} + {rnd.randint(1,9)*10} ?",
                                     _fmt(a + rnd.randint(1, 9) * 0) if False else None, []))
                    items.pop()
                    x, y = a, rnd.randint(1, 9) * 10
                    items.append(mkq(f"Combien font {x} + {y} ?", _fmt(x + y),
                                     [_fmt(x + y + 10), _fmt(x + y - 10), _fmt(x * 2)],
                                     f"{x} + {y} = {x+y}"))
            elif li <= 3:        # 6ème / 5ème / 4ème
                if kind < 2:
                    a, b = rnd.randint(2, 15), rnd.randint(2, 15)
                    items.append(mkq(f"Développe et réduis : {a}(x + {b})",
                                     f"{a}x + {a*b}",
                                     [f"{a}x + {b}", f"{a+b}x", f"{a}x + {a+b}"],
                                     f"{a}(x + {b}) = {a}x + {a}×{b} = {a}x + {a*b}"))
                elif kind < 4:
                    p = rnd.choice([10, 20, 25, 50])
                    n = rnd.randrange(10, 90, 10)
                    if n * p % 100: continue
                    r = n * p // 100
                    items.append(mkq(f"Combien font {p} % de {n} ?", _fmt(r),
                                     [_fmt(r + 2), _fmt(r - 2), _fmt(n - r)],
                                     f"{p} % de {n} = {n} × {p}/100 = {_fmt(r)}"))
                elif kind < 6:
                    a, b = rnd.randint(2, 9), rnd.randint(2, 9)
                    items.append(mkq(f"Quel est le PGCD de {a*4} et {a*6} ?", _fmt(a*2),
                                     [_fmt(a), _fmt(a*3), _fmt(a*4)],
                                     f"PGCD({a*4}, {a*6}) = {a*2}"))
                elif kind < 8:
                    c1, c2 = rnd.randint(3, 12), rnd.randint(3, 12)
                    items.append(mkq(f"Un rectangle mesure {c1} cm sur {c2} cm. Quelle est son aire ?",
                                     f"{c1*c2} cm²", [f"{2*(c1+c2)} cm²", f"{c1+c2} cm²", f"{c1*c2*2} cm²"],
                                     f"Aire = {c1} × {c2} = {c1*c2} cm²"))
                else:
                    x = rnd.randint(2, 12)
                    a = rnd.randint(2, 9); b = rnd.randint(1, 20)
                    items.append(mkq(f"Résous : {a}x + {b} = {a*x+b}", f"x = {x}",
                                     [f"x = {x+1}", f"x = {x-1}", f"x = {b}"],
                                     f"{a}x = {a*x+b} − {b} = {a*x}, donc x = {x}"))
            elif li <= 5:        # 3ème admis ci-dessus
                pass
            else:
                pass
        except Exception:
            continue
    # niveaux 3ème → Terminale
    if li >= 4:
        items = []
        guard = 0
        while len(items) < count and guard < count * 80:
            guard += 1
            k = rnd.randrange(12)
            try:
                if k < 2:      # équation du 1er degré
                    a = rnd.randint(2, 9); x = rnd.randint(-8, 9); b = rnd.randint(-15, 15)
                    c = a * x + b
                    items.append(mkq(f"Résous l'équation : {a}x {b:+d} = {c}", f"x = {x}",
                                     [f"x = {x+1}", f"x = {x-1}", f"x = {-x if x else 2}"],
                                     f"{a}x = {c} {(-b):+d} = {a*x}, donc x = {a*x}/{a} = {x}"))
                elif k < 4:    # identités remarquables
                    a = rnd.randint(2, 9); b = rnd.randint(1, 9)
                    items.append(mkq(f"Développe : (x + {a})(x + {b})",
                                     f"x² + {a+b}x + {a*b}",
                                     [f"x² + {a*b}x + {a+b}", f"x² + {a+b}", f"x² + {a+b}x + {a+b}"],
                                     f"(x+{a})(x+{b}) = x² + ({a}+{b})x + {a}×{b} = x² + {a+b}x + {a*b}"))
                elif k < 6:    # Pythagore
                    t = rnd.choice([(3, 4, 5), (6, 8, 10), (5, 12, 13), (9, 12, 15), (8, 15, 17), (7, 24, 25)])
                    items.append(mkq(
                        f"Un triangle rectangle a des côtés de l'angle droit {t[0]} cm et {t[1]} cm. "
                        f"Quelle est la longueur de l'hypoténuse ?",
                        f"{t[2]} cm", [f"{t[2]+1} cm", f"{t[0]+t[1]} cm", f"{t[2]-1} cm"],
                        f"√({t[0]}² + {t[1]}²) = √({t[0]**2}+{t[1]**2}) = √{t[0]**2+t[1]**2} = {t[2]} cm"))
                elif k < 8:    # dérivée
                    n = rnd.randint(2, 6); a = rnd.randint(2, 9)
                    items.append(mkq(f"Quelle est la dérivée de f(x) = {a}x^{n} ?",
                                     f"f'(x) = {a*n}x^{n-1}",
                                     [f"f'(x) = {a}x^{n-1}", f"f'(x) = {a*n}x^{n}", f"f'(x) = {n}x^{a}"],
                                     f"La dérivée de x^n est n·x^(n-1), donc f'(x) = {a}×{n}x^{n-1} = {a*n}x^{n-1}"))
                elif k < 9:    # suite arithmétique
                    u0 = rnd.randint(1, 10); r = rnd.randint(2, 9); n = rnd.randint(5, 20)
                    items.append(mkq(f"Suite arithmétique : u₀ = {u0}, raison r = {r}. Combien vaut uₙ pour n = {n} ?",
                                     _fmt(u0 + n * r), [_fmt(u0 + (n+1)*r), _fmt(u0 * r + n), _fmt(u0 + n)],
                                     f"uₙ = u₀ + n·r = {u0} + {n}×{r} = {u0 + n*r}"))
                elif k < 10:   # probabilité
                    a, b = rnd.randint(2, 7), rnd.randint(8, 16)
                    r = round(a / b * 100, 1)
                    items.append(mkq(f"Une urne contient {b} boules dont {a} rouges. Quelle est la probabilité de tirer une boule rouge ?",
                                     f"{a}/{b}", [f"{b}/{a}", f"{a}/{b-a}", f"{a+1}/{b}"],
                                     f"P = nombre de cas favorables / nombre de cas possibles = {a}/{b}"))
                else:          # statistiques
                    vals = [rnd.randint(1, 20) for _ in range(5)]
                    m = sum(vals) / len(vals)
                    items.append(mkq(f"Quelle est la moyenne de la série {', '.join(map(str, vals))} ?",
                                     _fmt(round(m, 2)), [_fmt(round(m + 2, 2)), _fmt(round(m - 1.5, 2)), _fmt(max(vals))],
                                     f"Moyenne = ({' + '.join(map(str, vals))}) / 5 = {_fmt(round(m, 2))}"))
            except Exception:
                continue
    return items[:count]


# ─────────────────────────────────────────────────────────────
#  FRANÇAIS — conjugaison procédurale + grammaire
# ─────────────────────────────────────────────────────────────
VERBES_FR = {
    "être":   {"présent": ["suis", "es", "est", "sommes", "êtes", "sont"],
               "imparfait": ["étais", "étais", "était", "étions", "étiez", "étaient"],
               "futur": ["serai", "seras", "sera", "serons", "serez", "seront"],
               "conditionnel": ["serais", "serais", "serait", "serions", "seriez", "seraient"],
               "subjonctif": ["sois", "sois", "soit", "soyons", "soyez", "soient"]},
    "avoir":  {"présent": ["ai", "as", "a", "avons", "avez", "ont"],
               "imparfait": ["avais", "avais", "avait", "avions", "aviez", "avaient"],
               "futur": ["aurai", "auras", "aura", "aurons", "aurez", "auront"],
               "conditionnel": ["aurais", "aurais", "aurait", "aurions", "auriez", "auraient"],
               "subjonctif": ["aie", "aies", "ait", "ayons", "ayez", "aient"]},
    "aller":  {"présent": ["vais", "vas", "va", "allons", "allez", "vont"],
               "imparfait": ["allais", "allais", "allait", "allions", "alliez", "allaient"],
               "futur": ["irai", "iras", "ira", "irons", "irez", "iront"],
               "conditionnel": ["irais", "irais", "irait", "irions", "iriez", "iraient"],
               "subjonctif": ["aille", "ailles", "aille", "allions", "alliez", "aillent"]},
    "faire":  {"présent": ["fais", "fais", "fait", "faisons", "faites", "font"],
               "imparfait": ["faisais", "faisais", "faisait", "faisions", "faisiez", "faisaient"],
               "futur": ["ferai", "feras", "fera", "ferons", "ferez", "feront"],
               "conditionnel": ["ferais", "ferais", "ferait", "ferions", "feriez", "feraient"],
               "subjonctif": ["fasse", "fasses", "fasse", "fassions", "fassiez", "fassent"]},
    "dire":   {"présent": ["dis", "dis", "dit", "disons", "dites", "disent"],
               "imparfait": ["disais", "disais", "disait", "disions", "disiez", "disaient"],
               "futur": ["dirai", "diras", "dira", "dirons", "direz", "diront"],
               "conditionnel": ["dirais", "dirais", "dirait", "dirions", "diriez", "diraient"],
               "subjonctif": ["dise", "dises", "dise", "disions", "disiez", "disent"]},
    "prendre": {"présent": ["prends", "prends", "prend", "prenons", "prenez", "prennent"],
                "imparfait": ["prenais", "prenais", "prenait", "prenions", "preniez", "prenaient"],
                "futur": ["prendrai", "prendras", "prendra", "prendrons", "prendrez", "prendront"],
                "conditionnel": ["prendrais", "prendrais", "prendrait", "prendrions", "prendriez", "prendraient"],
                "subjonctif": ["prenne", "prennes", "prenne", "prenions", "preniez", "prennent"]},
    "venir":  {"présent": ["viens", "viens", "vient", "venons", "venez", "viennent"],
               "imparfait": ["venais", "venais", "venait", "venions", "veniez", "venaient"],
               "futur": ["viendrai", "viendras", "viendra", "viendrons", "viendrez", "viendront"],
               "conditionnel": ["viendrais", "viendrais", "viendrait", "viendrions", "viendriez", "viendraient"],
               "subjonctif": ["vienne", "viennes", "vienne", "venions", "veniez", "viennent"]},
    "voir":   {"présent": ["vois", "vois", "voit", "voyons", "voyez", "voient"],
               "imparfait": ["voyais", "voyais", "voyait", "voyions", "voyiez", "voyaient"],
               "futur": ["verrai", "verras", "verra", "verrons", "verrez", "verront"],
               "conditionnel": ["verrais", "verrais", "verrait", "verrions", "verriez", "verraient"],
               "subjonctif": ["voie", "voies", "voie", "voyions", "voyiez", "voient"]},
    "pouvoir": {"présent": ["peux", "peux", "peut", "pouvons", "pouvez", "peuvent"],
                "imparfait": ["pouvais", "pouvais", "pouvait", "pouvions", "pouviez", "pouvaient"],
                "futur": ["pourrai", "pourras", "pourra", "pourrons", "pourrez", "pourront"],
                "conditionnel": ["pourrais", "pourrais", "pourrait", "pourrions", "pourriez", "pourraient"],
                "subjonctif": ["puisse", "puisses", "puisse", "puissions", "puissiez", "puissent"]},
    "vouloir": {"présent": ["veux", "veux", "veut", "voulons", "voulez", "veulent"],
                "imparfait": ["voulais", "voulais", "voulait", "voulions", "vouliez", "voulaient"],
                "futur": ["voudrai", "voudras", "voudra", "voudrons", "voudrez", "voudront"],
                "conditionnel": ["voudrais", "voudrais", "voudrait", "voudrions", "voudriez", "voudraient"],
                "subjonctif": ["veuille", "veuilles", "veuille", "voulions", "vouliez", "veuillent"]},
    "savoir": {"présent": ["sais", "sais", "sait", "savons", "savez", "savent"],
               "imparfait": ["savais", "savais", "savait", "savions", "saviez", "savaient"],
               "futur": ["saurai", "sauras", "saura", "saurons", "saurez", "sauront"],
               "conditionnel": ["saurais", "saurais", "saurait", "saurions", "sauriez", "sauraient"],
               "subjonctif": ["sache", "saches", "sache", "sachions", "sachiez", "sachent"]},
    "parler": {"présent": ["parle", "parles", "parle", "parlons", "parlez", "parlent"],
               "imparfait": ["parlais", "parlais", "parlait", "parlions", "parliez", "parlaient"],
               "futur": ["parlerai", "parleras", "parlera", "parlerons", "parlerez", "parleront"],
               "conditionnel": ["parlerais", "parlerais", "parlerait", "parlerions", "parleriez", "parleraient"],
               "subjonctif": ["parle", "parles", "parle", "parlions", "parliez", "parlent"]},
    "finir":  {"présent": ["finis", "finis", "finit", "finissons", "finissez", "finissent"],
               "imparfait": ["finissais", "finissais", "finissait", "finissions", "finissiez", "finissaient"],
               "futur": ["finirai", "finiras", "finira", "finirons", "finirez", "finiront"],
               "conditionnel": ["finirais", "finirais", "finirait", "finirions", "finiriez", "finiraient"],
               "subjonctif": ["finisse", "finisses", "finisse", "finissions", "finissiez", "finissent"]},
    "partir": {"présent": ["pars", "pars", "part", "partons", "partez", "partent"],
               "imparfait": ["partais", "partais", "partait", "partions", "partiez", "partaient"],
               "futur": ["partirai", "partiras", "partira", "partirons", "partirez", "partiront"],
               "conditionnel": ["partirais", "partirais", "partirait", "partirions", "partiriez", "partiraient"],
               "subjonctif": ["parte", "partes", "parte", "partions", "partiez", "partent"]},
    "chanter": {"présent": ["chante", "chantes", "chante", "chantons", "chantez", "chantent"]},
    "jouer":  {"présent": ["joue", "joues", "joue", "jouons", "jouez", "jouent"]},
    "aimer":  {"présent": ["aime", "aimes", "aime", "aimons", "aimez", "aiment"]},
    "regarder": {"présent": ["regarde", "regardes", "regarde", "regardons", "regardez", "regardent"]},
    "écouter": {"présent": ["écoute", "écoutes", "écoute", "écoutons", "écoutez", "écoutent"]},
    "travailler": {"présent": ["travaille", "travailles", "travaille", "travaillons", "travaillez", "travaillent"]},
    "étudier": {"présent": ["étudie", "étudies", "étudie", "étudions", "étudiez", "étudient"]},
    "marcher": {"présent": ["marche", "marches", "marche", "marchons", "marchez", "marchent"]},
    "donner": {"présent": ["donne", "donnes", "donne", "donnons", "donnez", "donnent"]},
    "trouver": {"présent": ["trouve", "trouves", "trouve", "trouvons", "trouvez", "trouvent"]},
    "fermer": {"présent": ["ferme", "fermes", "ferme", "fermons", "fermez", "ferment"]},
    "ouvrir": {"présent": ["ouvre", "ouvres", "ouvre", "ouvrons", "ouvrez", "ouvrent"]},
    "manger": {"présent": ["mange", "manges", "mange", "mangeons", "mangez", "mangent"],
               "imparfait": ["mangeais", "mangeais", "mangeait", "mangions", "mangiez", "mangeaient"],
               "futur": ["mangerai", "mangeras", "mangera", "mangerons", "mangerez", "mangeront"],
               "conditionnel": ["mangerais", "mangerais", "mangerait", "mangerions", "mangeriez", "mangeraient"],
               "subjonctif": ["mange", "manges", "mange", "mangions", "mangiez", "mangent"]},
}
TEMPS_FR = {"présent": "au présent", "imparfait": "à l'imparfait", "futur": "au futur simple",
            "conditionnel": "au conditionnel présent", "subjonctif": "au subjonctif présent"}
TEMPS_PAR_NIVEAU = {
    0: ["présent"], 1: ["présent"], 2: ["présent"], 3: ["présent", "imparfait"],
    4: ["présent", "imparfait", "futur"], 5: ["imparfait", "futur", "conditionnel"],
    6: ["futur", "conditionnel"], 7: ["futur", "conditionnel", "subjonctif"],
    8: ["futur", "conditionnel", "subjonctif"],
}
PRONOMS = ["je", "tu", "il", "nous", "vous", "ils"]
ACCORD_FR = [
    ("Les élèves ___ arrivés en retard.", "sont", ["est", "es", "sommes"], "« Les élèves » = 3e pers. du pluriel."),
    ("Ma sœur et moi ___ allés au marché.", "sommes", ["sont", "êtes", "est"], "« Ma sœur et moi » = nous."),
    ("Vous ___ très gentils.", "êtes", ["est", "sont", "sommes"], "« Vous » = 2e pers. du pluriel."),
    ("Le chat ___ sur le canapé.", "est", ["es", "sont", "êtes"], "« Le chat » = 3e pers. du singulier."),
    ("Nous ___ contents de vous voir.", "sommes", ["sont", "êtes", "est"], "« Nous » = 1re pers. du pluriel."),
    ("Elles ___ parties hier soir.", "sont", ["est", "es", "êtes"], "« Elles » = 3e pers. du pluriel."),
]


def gen_fr(level, count):
    li = LVL_IDX[level]
    items = []
    temps = TEMPS_PAR_NIVEAU.get(li, ["présent"])
    combos = []
    for v in VERBES_FR:
        for t in temps:
            if t not in VERBES_FR[v]:
                continue
            for p in range(6):
                combos.append((v, t, p))
    rnd.shuffle(combos)
    for (v, t, p) in combos:
        if len(items) >= count:
            break
        bon = VERBES_FR[v][t][p]
        faux = [x for x in VERBES_FR[v][t] if x != bon]
        # compléter avec des formes d'autres temps
        for ot in VERBES_FR[v]:
            if ot != t:
                faux.extend([x for x in VERBES_FR[v][ot] if x != bon])
        faux = list(dict.fromkeys(faux))
        rnd.shuffle(faux)
        items.append(mkq(f"Conjugue le verbe « {v} » {TEMPS_FR[t]} : {PRONOMS[p]} ___",
                         bon, faux[:3],
                         f"« {v} » {TEMPS_FR[t]} → {PRONOMS[p]} {bon}"))
    if len(items) < count:
        for (ph, bon, faux, expl) in ACCORD_FR:
            if len(items) >= count:
                break
            items.append(mkq(ph, bon, faux, expl))
    return items[:count]


# ─────────────────────────────────────────────────────────────
#  PHYSIQUE — formules, réponses calculées
# ─────────────────────────────────────────────────────────────
def gen_phys(level, count):
    li = LVL_IDX[level]
    items, guard = [], 0
    while len(items) < count and guard < count * 80:
        guard += 1
        k = rnd.randrange(8)
        try:
            if k < 2:      # loi d'Ohm
                R = rnd.choice([10, 20, 25, 50, 100, 200, 250])
                I = rnd.choice([0.1, 0.2, 0.25, 0.5, 1, 2])
                U = round(R * I, 2)
                items.append(mkq(f"Une résistance de {_fmt(R)} Ω est traversée par un courant de {_fmt(I)} A. Quelle est la tension ?",
                                 f"{_fmt(U)} V", [f"{_fmt(U*2)} V", f"{_fmt(R+I)} V", f"{_fmt(round(R/I,2))} V"],
                                 f"U = R × I = {_fmt(R)} × {_fmt(I)} = {_fmt(U)} V"))
            elif k < 4:    # F = m a
                m = rnd.randint(2, 20); a = rnd.randint(2, 10)
                items.append(mkq(f"Une force de {m*a} N s'exerce sur un objet de {m} kg. Quelle est son accélération ?",
                                 f"{a} m/s²", [f"{m*a} m/s²", f"{round(m/a,2)} m/s²", f"{a*2} m/s²"],
                                 f"a = F / m = {m*a} / {m} = {a} m/s²"))
            elif k < 5:    # vitesse
                d = rnd.randint(2, 30) * 10; t = rnd.randint(1, 10)
                v = round(d / t, 2)
                items.append(mkq(f"Un véhicule parcourt {d} km en {t} h. Quelle est sa vitesse moyenne ?",
                                 f"{_fmt(v)} km/h", [f"{_fmt(round(d*t,2))} km/h", f"{_fmt(round(t/d,2))} km/h", f"{_fmt(v*2)} km/h"],
                                 f"v = d / t = {d} / {t} = {_fmt(v)} km/h"))
            elif k < 6:    # énergie
                m = rnd.randint(1, 10); c = 4.18
                items.append(mkq(f"Quelle est l'énergie nécessaire pour chauffer {m} kg d'eau de 1 °C ? (c = 4 180 J/kg·°C)",
                                 f"{int(m*4180)} J", [f"{int(m*418)} J", f"{int(m*41800)} J", f"{int(4180)} J"],
                                 f"Q = m × c × ΔT = {m} × 4180 × 1 = {int(m*4180)} J"))
            elif k < 7:    # poids
                m = rnd.randint(1, 20)
                p = round(m * 9.81, 2)
                items.append(mkq(f"Quel est le poids d'un objet de masse {m} kg sur Terre ? (g = 9,81 N/kg)",
                                 f"{_fmt(p)} N", [f"{m} N", f"{_fmt(round(m*9.81/2,2))} N", f"{_fmt(round(m/9.81,2))} N"],
                                 f"P = m × g = {m} × 9,81 = {_fmt(p)} N"))
            else:          # fréquence/période
                f = rnd.choice([2, 4, 5, 10, 20, 50])
                items.append(mkq(f"Un signal a une fréquence de {f} Hz. Quelle est sa période ?",
                                 f"{_fmt(round(1/f,3))} s", [f"{f} s", f"{_fmt(round(f/2,3))} s", f"{_fmt(round(2/f,3))} s"],
                                 f"T = 1 / f = 1 / {f} = {_fmt(round(1/f,3))} s"))
        except Exception:
            continue
    return items[:count]


# ─────────────────────────────────────────────────────────────
#  CHIMIE
# ─────────────────────────────────────────────────────────────
def gen_chim(level, count):
    items, guard = [], 0
    while len(items) < count and guard < count * 60:
        guard += 1
        k = rnd.randrange(11)
        try:
            if k < 2:      # moles
                M = rnd.choice([18, 44, 58.5, 98, 100])
                n = rnd.choice([0.5, 1, 2, 0.25])
                m = round(M * n, 2)
                items.append(mkq(f"Quelle est la masse de {_fmt(n)} mol d'un composé de masse molaire {_fmt(M)} g/mol ?",
                                 f"{_fmt(m)} g", [f"{_fmt(round(M/n,2))} g", f"{_fmt(M)} g", f"{_fmt(round(m*2,2))} g"],
                                 f"m = n × M = {_fmt(n)} × {_fmt(M)} = {_fmt(m)} g"))
            elif k < 3:    # concentration
                n = rnd.randint(1, 5); V = rnd.choice([0.5, 1, 2, 4])
                C = round(n / V, 2)
                items.append(mkq(f"On dissout {n} mol de sel dans {_fmt(V)} L d'eau. Quelle est la concentration ?",
                                 f"{_fmt(C)} mol/L", [f"{_fmt(round(n*V,2))} mol/L", f"{_fmt(round(V/n,2))} mol/L", f"{n} mol/L"],
                                 f"C = n / V = {n} / {_fmt(V)} = {_fmt(C)} mol/L"))
            elif k < 4:    # dilution
                C1 = rnd.choice([0.1, 0.5, 1, 2]); V1 = rnd.randint(1, 5); V2 = V1 * rnd.choice([2, 5, 10])
                items.append(mkq(f"On dilue {V1} mL d'une solution à {_fmt(C1)} mol/L dans {V2} mL. Quelle est la nouvelle concentration ?",
                                 f"{_fmt(round(C1*V1/V2,3))} mol/L",
                                 [f"{_fmt(round(C1*V2/V1,2))} mol/L", f"{_fmt(C1)} mol/L", f"{_fmt(round(C1/2,3))} mol/L"],
                                 f"C1V1 = C2V2 → C2 = {_fmt(C1)}×{V1}/{V2} = {_fmt(round(C1*V1/V2,3))} mol/L"))
            elif k < 5:    # pH
                h = rnd.choice([1e-2, 1e-3, 1e-4, 1e-5])
                ph = -round(__import__('math').log10(h))
                items.append(mkq(f"Une solution a une concentration en ions H⁺ de {h:.0e} mol/L. Quel est son pH ?",
                                 f"{ph}", [f"{ph+1}", f"{14-ph}", f"{ph-1}"],
                                 f"pH = −log[H⁺] = −log({h:.0e}) = {ph}"))
            elif k < 6:    # masse molaire
                items.append(mkq("Quelle est la masse molaire de H₂O ? (H = 1, O = 16)",
                                 "18 g/mol", ["16 g/mol", "17 g/mol", "20 g/mol"],
                                 "M(H₂O) = 2×1 + 16 = 18 g/mol"))
            elif k < 7:    # équilibrage
                items.append(mkq("Équilibre : __ H₂ + O₂ → __ H₂O",
                                 "2 H₂ + O₂ → 2 H₂O", ["H₂ + O₂ → H₂O", "2 H₂ + 2 O₂ → 2 H₂O", "H₂ + 2 O₂ → H₂O"],
                                 "Il faut 2 H₂ et 1 O₂ pour former 2 H₂O : conservation des atomes."))
            elif k < 8:    # masse molaire composée
                items.append(mkq("Quelle est la masse molaire de CO₂ ? (C = 12, O = 16)",
                                 "44 g/mol", ["28 g/mol", "32 g/mol", "56 g/mol"],
                                 "M(CO₂) = 12 + 2×16 = 44 g/mol."))
            elif k < 9:    # nombre d'Avogadro
                n = rnd.choice([0.5, 1, 2])
                N = n * 6.02e23
                items.append(mkq(f"Combien y a-t-il de molécules dans {_fmt(n)} mol ? (N_A = 6,02 × 10²³)",
                                 f"{n} × 6,02 × 10²³", ["6,02 × 10²³", f"{n} × 10²³", "1,2 × 10²³"],
                                 f"N = n × N_A = {_fmt(n)} × 6,02 × 10²³"))
            elif k < 10:   # pourcentage massique
                m_tot = rnd.choice([100, 200, 500]); m_sol = rnd.choice([5, 10, 20])
                pct = round(m_sol * 100 / m_tot, 2)
                items.append(mkq(f"On dissout {m_sol} g de sel dans {m_tot} g de solution. Quel est le pourcentage massique ?",
                                 f"{_fmt(pct)} %", [f"{_fmt(round(pct*2,2))} %", f"{m_sol} %", f"{_fmt(round(pct/2,2))} %"],
                                 f"% = {m_sol} / {m_tot} × 100 = {_fmt(pct)} %"))
            else:          # volume molaire
                n = rnd.choice([0.5, 1, 2, 3])
                V = round(n * 22.4, 1)
                items.append(mkq(f"Quel volume occupe {_fmt(n)} mol de gaz dans les conditions normales ? (Vm = 22,4 L/mol)",
                                 f"{_fmt(V)} L", [f"{_fmt(round(22.4,1))} L", f"{_fmt(round(n*11.2,1))} L", f"{_fmt(round(n*44.8,1))} L"],
                                 f"V = n × Vm = {_fmt(n)} × 22,4 = {_fmt(V)} L"))
        except Exception:
            continue
    return items[:count]


# ─────────────────────────────────────────────────────────────
#  TABLES DE FAITS (histoire, géographie, SVT, économie, info)
# ─────────────────────────────────────────────────────────────
PAYS = [
    # (pays, capitale, continent, monnaie)
    ("Sénégal", "Dakar", "Afrique", "Franc CFA"), ("Mali", "Bamako", "Afrique", "Franc CFA"),
    ("Guinée", "Conakry", "Afrique", "Franc guinéen"), ("Côte d'Ivoire", "Yamoussoukro", "Afrique", "Franc CFA"),
    ("Burkina Faso", "Ouagadougou", "Afrique", "Franc CFA"), ("Niger", "Niamey", "Afrique", "Franc CFA"),
    ("Mauritanie", "Nouakchott", "Afrique", "Ouguiya"), ("Maroc", "Rabat", "Afrique", "Dirham"),
    ("Algérie", "Alger", "Afrique", "Dinar algérien"), ("Tunisie", "Tunis", "Afrique", "Dinar tunisien"),
    ("Égypte", "Le Caire", "Afrique", "Livre égyptienne"), ("Nigeria", "Abuja", "Afrique", "Naira"),
    ("Ghana", "Accra", "Afrique", "Cedi"), ("Cameroun", "Yaoundé", "Afrique", "Franc CFA"),
    ("Kenya", "Nairobi", "Afrique", "Shilling kényan"), ("Éthiopie", "Addis-Abeba", "Afrique", "Birr"),
    ("Afrique du Sud", "Pretoria", "Afrique", "Rand"), ("Tanzanie", "Dodoma", "Afrique", "Shilling tanzanien"),
    ("France", "Paris", "Europe", "Euro"), ("Allemagne", "Berlin", "Europe", "Euro"),
    ("Espagne", "Madrid", "Europe", "Euro"), ("Italie", "Rome", "Europe", "Euro"),
    ("Portugal", "Lisbonne", "Europe", "Euro"), ("Belgique", "Bruxelles", "Europe", "Euro"),
    ("Royaume-Uni", "Londres", "Europe", "Livre sterling"), ("Suisse", "Berne", "Europe", "Franc suisse"),
    ("Maroc", "Rabat", "Afrique", "Dirham"), ("Grèce", "Athènes", "Europe", "Euro"),
    ("Turquie", "Ankara", "Asie", "Livre turque"), ("Russie", "Moscou", "Europe", "Rouble"),
    ("États-Unis", "Washington", "Amérique", "Dollar"), ("Canada", "Ottawa", "Amérique", "Dollar canadien"),
    ("Brésil", "Brasilia", "Amérique", "Real"), ("Argentine", "Buenos Aires", "Amérique", "Peso argentin"),
    ("Mexique", "Mexico", "Amérique", "Peso mexicain"), ("Chine", "Pékin", "Asie", "Yuan"),
    ("Japon", "Tokyo", "Asie", "Yen"), ("Inde", "New Delhi", "Asie", "Roupie indienne"),
    ("Australie", "Canberra", "Océanie", "Dollar australien"), ("Arabie saoudite", "Riyad", "Asie", "Riyal"),
]
PAYS_UNIK = list({p[0]: p for p in PAYS}.values())

FLEUVES = [("Nil", "Afrique", "Égypte"), ("Congo", "Afrique", "RDC"), ("Niger", "Afrique", "Nigeria"),
           ("Sénégal", "Afrique", "Sénégal"), ("Gambie", "Afrique", "Gambie"), ("Zambèze", "Afrique", "Zambie"),
           ("Amazone", "Amérique du Sud", "Brésil"), ("Mississippi", "Amérique du Nord", "États-Unis"),
           ("Danube", "Europe", "Roumanie"), ("Rhin", "Europe", "Allemagne"),
           ("Gange", "Asie", "Inde"), ("Mékong", "Asie", "Vietnam"), ("Ienisseï", "Asie", "Russie")]

MONTS = [("Kilimandjaro", "Tanzanie", "Afrique"), ("Mont Kenya", "Kenya", "Afrique"),
         ("Atlas", "Maroc", "Afrique"), ("Everest", "Népal", "Asie"), ("Mont Blanc", "France", "Europe"),
         ("Aconcagua", "Argentine", "Amérique du Sud"), ("Denali", "États-Unis", "Amérique du Nord"),
         ("Elbrouz", "Russie", "Europe")]

HIST_DATES = [
    ("Indépendance du Sénégal", "1960"), ("Indépendance du Mali", "1960"),
    ("Indépendance de la Guinée", "1958"), ("Indépendance de la Côte d'Ivoire", "1960"),
    ("Indépendance de l'Algérie", "1962"), ("Indépendance du Ghana", "1957"),
    ("Fin de la Seconde Guerre mondiale", "1945"), ("Début de la Première Guerre mondiale", "1914"),
    ("Révolution française", "1789"), ("Chute du mur de Berlin", "1989"),
    ("Création de l'OUA", "1963"), ("Création de l'Union africaine", "2002"),
    ("Création de la CEDEAO", "1975"), ("Création de l'ONU", "1945"),
    ("Indépendance de l'Inde", "1947"), ("Naissance de l'empire du Mali", "1235"),
    ("Abolition de l'esclavage en France", "1848"), ("Conférence de Berlin", "1884-1885"),
]
HIST_PERSONNES = [
    ("Premier président du Sénégal", "Léopold Sédar Senghor"),
    ("Premier président du Ghana", "Kwame Nkrumah"),
    ("Leader de l'indépendance de l'Inde", "Mahatma Gandhi"),
    ("Premier président de la Guinée", "Ahmed Sékou Touré"),
    ("Premier président du Mali", "Modibo Keïta"),
    ("Empereur du Mali au XIIIe siècle", "Soundiata Keïta"),
    ("Premier président de l'Afrique du Sud démocratique", "Nelson Mandela"),
    ("Pharaon célèbre d'Égypte", "Ramsès II"),
]

SVT_FACTS = [
    ("Quel organe pompe le sang dans le corps ?", "Le cœur", ["Le foie", "Les poumons", "L'estomac"], "Le cœur est une pompe musculaire."),
    ("Où se déroule la photosynthèse ?", "Dans les chloroplastes", ["Dans les mitochondries", "Dans le noyau", "Dans les vacuoles"], "Les chloroplastes contiennent la chlorophylle."),
    ("Quel est le gaz absorbé par les plantes ?", "Le dioxyde de carbone (CO₂)", ["Le dioxygène (O₂)", "L'azote (N₂)", "Le méthane (CH₄)"], "Les plantes absorbent le CO₂ pour la photosynthèse."),
    ("Combien de chromosomes possède l'être humain ?", "46", ["23", "44", "48"], "23 paires = 46 chromosomes."),
    ("Quel est le plus grand organe du corps humain ?", "La peau", ["Le foie", "Le cerveau", "Les intestins"], "La peau est le plus grand organe."),
    ("Comment appelle-t-on les cellules nerveuses ?", "Les neurones", ["Les leucocytes", "Les hématies", "Les myocytes"], "Les neurones transmettent l'influx nerveux."),
    ("Quel organe produit l'insuline ?", "Le pancréas", ["Le foie", "Le rein", "La rate"], "Le pancréas produit l'insuline."),
    ("Quel groupe sanguin est donneur universel ?", "O−", ["AB+", "A+", "B−"], "O− ne possède ni antigène A, B ni facteur Rh."),
    ("Qu'est-ce que l'ADN ?", "La molécule portant l'information génétique", ["Une protéine", "Un glucide", "Un lipide"], "L'ADN porte les gènes."),
    ("Quel est le rôle des globules rouges ?", "Transporter l'oxygène", ["Défendre l'organisme", "Digérer les aliments", "Produire des hormones"], "L'hémoglobine fixe l'oxygène."),
    ("Quel appareil mesure la respiration ?", "Le spiromètre", ["Le tensiomètre", "Le thermomètre", "L'oscilloscope"], "Le spiromètre mesure la capacité respiratoire."),
    ("Combien de dents a un adulte ?", "32", ["28", "30", "36"], "8 incisives, 4 canines, 8 prémolaires, 12 molaires."),
]

ECO_FACTS = [
    ("Quelle est la monnaie du Sénégal ?", "Le franc CFA (XOF)", ["Le naira", "Le cedi", "L'ouguiya"], "Le Sénégal utilise le franc CFA (XOF)."),
    ("Que signifie PIB ?", "Produit Intérieur Brut", ["Plan Intérieur de Base", "Produit Intérieur de Base", "Prix Intérieur Brut"], "Le PIB mesure la production nationale."),
    ("Quelle institution émet le franc CFA ?", "La BCEAO", ["La Banque mondiale", "Le FMI", "L'OMC"], "La BCEAO est la banque centrale des États de l'Afrique de l'Ouest."),
    ("Qu'est-ce que l'inflation ?", "La hausse générale des prix", ["La baisse des prix", "La hausse du chômage", "La baisse de la production"], "C'est la perte du pouvoir d'achat."),
    ("Quel organisme prête aux États en difficulté ?", "Le FMI", ["La BCEAO", "L'OMC", "L'UNESCO"], "Le Fonds monétaire international."),
    ("Qu'est-ce que l'offre ?", "La quantité de biens proposés à la vente", ["La quantité demandée", "Le prix fixé", "La quantité produite gratuitement"], "L'offre dépend du prix."),
    ("Qu'est-ce que la rareté en économie ?", "Des ressources limitées face à des besoins illimités", ["Un manque de magasins", "Une pénurie de vendeurs", "Un prix trop bas"], "C'est le fondement de l'économie."),
    ("Que mesure le taux de chômage ?", "La part des actifs sans emploi", ["La part des inactifs", "Le nombre d'entreprises", "Le niveau des salaires"], "Chômeurs / population active."),
]

INFO_FACTS = [
    ("Que signifie HTML ?", "HyperText Markup Language", ["High Tech Modern Language", "Hyper Transfer Markup Link", "Home Tool Markup Language"], "Langage de balisage des pages web."),
    ("Quel langage sert à styliser une page web ?", "CSS", ["HTML", "SQL", "PHP"], "CSS = Cascading Style Sheets."),
    ("Que signifie SQL ?", "Structured Query Language", ["Simple Query Logic", "Standard Query Link", "System Query Language"], "Langage d'interrogation des bases de données."),
    ("En base de données, que fait SELECT ?", "Lire des données", ["Supprimer des données", "Créer une table", "Modifier la structure"], "SELECT sert à interroger."),
    ("Quelle est la complexité d'une recherche dichotomique ?", "O(log n)", ["O(n)", "O(n²)", "O(1)"], "On divise l'espace de recherche par 2 à chaque étape."),
    ("Qu'est-ce qu'un algorithme ?", "Une suite finie d'instructions pour résoudre un problème", ["Un langage de programmation", "Un type de câble", "Un système d'exploitation"], "Un algorithme décrit une méthode."),
    ("Quel symbole signifie ET logique ?", "&&", ["||", "!=", "=="], "&& est le ET logique."),
    ("Qu'est-ce qu'une boucle ?", "Une structure qui répète des instructions", ["Une condition", "Une variable", "Un commentaire"], "for / while sont des boucles."),
    ("Que signifie CPU ?", "Central Processing Unit", ["Computer Power Unit", "Central Program Utility", "Control Processing Utility"], "Le processeur."),
    ("Quelle base représente le binaire ?", "2", ["8", "10", "16"], "Le binaire utilise 0 et 1."),
]


SVT_EXTRA = [
    ('Quel organe filtre le sang ?', 'Les reins', ['Le foie', 'La rate', "L'estomac"], "Les reins filtrent le sang et produisent l'urine."),
    ('Quel est le rôle des poumons ?', 'Assurer les échanges gazeux', ['Filtrer le sang', 'Digérer les aliments', 'Produire des hormones'], 'Les poumons échangent O₂ et CO₂.'),
    ('Quelle est la plus petite unité du vivant ?', 'La cellule', ["L'atome", "L'organe", 'Le tissu'], "La cellule est l'unité de base du vivant."),
    ("Quel est le symbole chimique de l'oxygène ?", 'O', ['O₂', 'Ox', 'Og'], "L'élément oxygène a pour symbole O."),
    ('Quel est le rôle des plaquettes ?', 'La coagulation du sang', ["Transporter l'oxygène", "Défendre l'organisme", 'Digérer'], 'Les plaquettes forment les caillots.'),
    ('Combien de cavités a le cœur humain ?', '4', ['2', '3', '6'], 'Deux oreillettes et deux ventricules.'),
    ('Quel organe produit la bile ?', 'Le foie', ['Le pancréas', "L'estomac", "L'intestin"], 'La bile aide à digérer les lipides.'),
    ("Quel est le rôle de l'intestin grêle ?", 'Absorber les nutriments', ['Broyer les aliments', 'Stocker les déchets', "Produire l'urine"], "L'absorption se fait dans l'intestin grêle."),
    ('Que produit la photosynthèse ?', 'Du glucose et du dioxygène', ["Du CO₂ et de l'eau", "De l'azote", 'Du méthane'], '6CO₂ + 6H₂O → C₆H₁₂O₆ + 6O₂.'),
    ('Quel pigment rend les feuilles vertes ?', 'La chlorophylle', ['La mélanine', "L'hémoglobine", 'La kératine'], 'La chlorophylle capte la lumière.'),
    ('Comment appelle-t-on un être qui fabrique sa matière organique ?', 'Un autotrophe', ['Un hétérotrophe', 'Un parasite', 'Un virus'], 'Les plantes sont autotrophes.'),
    ("Quelle partie de la plante absorbe l'eau ?", 'Les racines', ['Les feuilles', 'Les fleurs', 'Les fruits'], "Les racines puisent l'eau du sol."),
    ('Quel est le rôle des fleurs ?', 'La reproduction', ['La nutrition', 'La photosynthèse', "Le transport de l'eau"], 'Les fleurs portent les organes reproducteurs.'),
    ("Quel est le nom du transport de l'eau dans la plante ?", 'La sève brute', ['La sève élaborée', 'La transpiration', 'La respiration'], 'La sève brute monte des racines vers les feuilles.'),
    ("Qu'est-ce qu'un écosystème ?", "Un milieu et l'ensemble des êtres vivants qui l'habitent", ['Une seule espèce', 'Un animal', 'Un climat'], 'Biotope + biocénose.'),
    ("Quel est le premier maillon d'une chaîne alimentaire ?", 'Le producteur (végétal)', ['Le prédateur', 'Le décomposeur', "L'herbivore"], 'Les végétaux produisent la matière organique.'),
    ('Que sont les décomposeurs ?', 'Des êtres qui recyclent la matière morte', ['Des prédateurs', 'Des producteurs', 'Des parasites'], 'Champignons et bactéries décomposent.'),
    ("Quelle molécule transporte l'oxygène dans le sang ?", "L'hémoglobine", ["L'insuline", 'La kératine', 'Le collagène'], "L'hémoglobine fixe l'O₂."),
    ('Quel est le rôle du système nerveux ?', 'Transmettre et traiter les messages', ['Digérer', 'Filtrer le sang', 'Produire de la chaleur'], "Il coordonne l'organisme."),
    ('Quel organe est le centre de commande du corps ?', 'Le cerveau', ['Le cœur', 'Le foie', "L'estomac"], 'Le cerveau est le centre du système nerveux.'),
    ("Qu'est-ce qu'une hormone ?", "Une substance qui régule l'organisme", ['Un aliment', 'Une bactérie', 'Un os'], 'Les hormones agissent via le sang.'),
    ('Quel organe produit les globules rouges ?', 'La moelle osseuse', ['Le foie', 'Le cœur', 'La peau'], 'La moelle osseuse produit les cellules sanguines.'),
    ('Quel est le rôle des globules blancs ?', "Défendre l'organisme", ["Transporter l'oxygène", 'Coaguler le sang', 'Digérer'], 'Ce sont les cellules immunitaires.'),
    ("Comment appelle-t-on l'ensemble des gènes d'un individu ?", 'Le génome', ['Le génotype', 'Le phénotype', "L'ADN"], "Le génome est l'ensemble du matériel génétique."),
    ("Qu'est-ce qu'un allèle ?", "Une version d'un gène", ['Un chromosome', 'Une cellule', 'Une protéine'], 'Un gène peut avoir plusieurs allèles.'),
    ("Qui a découvert les lois de l'hérédité ?", 'Gregor Mendel', ['Charles Darwin', 'Louis Pasteur', 'Lamarck'], "Mendel a établi les lois de l'hérédité."),
    ("Quelle est la théorie de l'évolution ?", 'Les espèces évoluent par sélection naturelle', ['Les espèces sont fixes', 'Les espèces sont créées', 'Les espèces ne changent jamais'], 'Darwin, 1859.'),
    ("Qu'est-ce qu'une mutation ?", "Une modification de la séquence de l'ADN", ['Une maladie', 'Un organe', 'Une cellule'], 'Les mutations créent la diversité génétique.'),
    ('Quel est le rôle de la vaccination ?', 'Protéger contre une maladie infectieuse', ['Guérir une fracture', "Nourrir l'organisme", 'Remplacer un organe'], 'Elle stimule les défenses immunitaires.'),
    ('Quel micro-organisme cause le paludisme ?', 'Le plasmodium', ['Le virus grippal', 'La bactérie E. coli', 'Le champignon'], 'Transmis par le moustique anophèle.'),
    ('Quel organisme transmet le paludisme ?', 'Le moustique anophèle', ['La mouche', 'Le moustique Aedes', 'La punaise'], "L'anophèle femelle transmet le plasmodium."),
    ('Quelle maladie est causée par le VIH ?', 'Le SIDA', ['Le paludisme', 'La grippe', 'Le diabète'], 'Le VIH détruit le système immunitaire.'),
    ("Qu'est-ce que la digestion ?", 'La transformation des aliments en nutriments', ['La respiration', 'La circulation', "L'excrétion"], 'La digestion libère les nutriments.'),
    ('Où commence la digestion ?', 'Dans la bouche', ["Dans l'estomac", "Dans l'intestin", "Dans l'œsophage"], "La mastication et l'amylase salivaires commencent."),
    ('Quel est le rôle des dents ?', 'Broyer les aliments', ["Filtrer l'eau", 'Produire la salive', 'Respirer'], 'Les dents assurent la mastication.'),
    ('Quel est le pH du sang humain ?', 'Environ 7,4', ['Environ 7', 'Environ 2', 'Environ 12'], 'Le sang est légèrement basique.'),
    ('Quel organe stocke le glycogène ?', 'Le foie', ['Le cœur', 'Les poumons', 'Les reins'], 'Le foie stocke le glycogène.'),
    ("Qu'est-ce que la puberté ?", 'La période de maturation sexuelle', ['Une maladie', "Un âge d'or", 'Une digestion'], 'Elle entraîne des transformations physiques.'),
    ('Quel est le rôle des testicules ?', 'Produire les spermatozoïdes', ['Filtrer le sang', "Produire l'urine", 'Digérer'], 'Ce sont les organes reproducteurs masculins.'),
    ('Quel est le rôle des ovaires ?', 'Produire les ovules', ["Produire l'urine", 'Filtrer le sang', 'Digérer'], 'Ce sont les organes reproducteurs féminins.'),
    ('Combien de temps dure une grossesse humaine ?', 'Environ 9 mois', ['Environ 3 mois', 'Environ 6 mois', 'Environ 12 mois'], 'Environ 39 semaines.'),
    ("Qu'est-ce que la mitose ?", 'Une division cellulaire produisant 2 cellules identiques', ['La fusion de cellules', 'La mort cellulaire', 'La digestion'], 'Elle assure la croissance.'),
    ("Qu'est-ce que la méiose ?", 'Une division produisant des cellules reproductrices', ['La croissance', 'La digestion', 'La respiration'], 'Elle produit des cellules haploïdes.'),
    ('Quel gaz les plantes rejettent-elles la nuit ?', 'Du CO₂', ["De l'O₂", "De l'azote", "De l'hydrogène"], 'La nuit, seule la respiration agit.'),
    ('Quel est le plus grand organe interne ?', 'Le foie', ['Le cœur', 'Le cerveau', "L'estomac"], 'Le foie pèse environ 1,5 kg.'),
    ("Quelle est l'unité de base du rein ?", 'Le néphron', ['Le neurone', "L'alvéole", 'Le villosité'], 'Le néphron filtre le sang.'),
    ('Que mesure un électrocardiogramme ?', "L'activité électrique du cœur", ['La glycémie', 'La tension', 'Le rythme respiratoire'], "L'ECG enregistre le cœur."),
    ('Quelle est la principale cause de déforestation ?', "L'expansion agricole", ['La pluie', 'Le vent', 'Les animaux'], 'Les terres agricoles remplacent les forêts.'),
    ("Quel gaz est principalement responsable de l'effet de serre anthropique ?", 'Le CO₂', ["L'O₂", "L'azote", "L'hélium"], 'Le CO₂ issu des combustibles fossiles.'),
    ('Quelle énergie est renouvelable ?', "L'énergie solaire", ['Le charbon', 'Le pétrole', 'Le gaz naturel'], 'Le soleil se renouvelle en continu.'),
    ("Qu'est-ce que la biodiversité ?", 'La diversité des êtres vivants', ['La diversité des climats', 'La diversité des roches', 'La diversité des langues'], 'Espèces, gènes et écosystèmes.'),
]

ECO_EXTRA = [
    ("Quel est le secteur qui regroupe l'agriculture ?", 'Le secteur primaire', ['Le secteur secondaire', 'Le secteur tertiaire', 'Le secteur quaternaire'], 'Le primaire exploite les ressources naturelles.'),
    ("Quel secteur regroupe l'industrie ?", 'Le secteur secondaire', ['Le secteur primaire', 'Le secteur tertiaire', 'Le secteur informel'], 'Le secondaire transforme les matières premières.'),
    ('Quel secteur regroupe les services ?', 'Le secteur tertiaire', ['Le secteur primaire', 'Le secteur secondaire', 'Le secteur public'], 'Le tertiaire = commerce, transport, banque.'),
    ("Qu'est-ce que la demande ?", 'La quantité de biens que les consommateurs veulent acheter', ['La quantité offerte', 'Le prix de vente', 'Le stock disponible'], 'La demande dépend du prix et du revenu.'),
    ("Que se passe-t-il si l'offre augmente et la demande reste stable ?", 'Le prix baisse', ['Le prix monte', 'Le prix ne change pas', "L'offre baisse"], "Loi de l'offre et de la demande."),
    ("Qu'est-ce que le coût de production ?", 'La dépense nécessaire pour produire un bien', ['Le prix de vente', 'Le bénéfice', 'La taxe'], 'Coût = matières + travail + charges.'),
    ("Qu'est-ce que le bénéfice ?", 'Recette moins coût', ['Recette plus coût', "Le chiffre d'affaires", 'La taxe'], 'Bénéfice = recettes − coûts.'),
    ("Qu'est-ce que le chiffre d'affaires ?", 'Le total des ventes', ['Le total des coûts', 'Le bénéfice net', 'Le capital'], 'CA = prix × quantités vendues.'),
    ('Quelle institution finance des projets de développement ?', 'La Banque mondiale', ["L'OMC", 'La BCEAO', "L'UNESCO"], 'Elle lutte contre la pauvreté.'),
    ('Que signifie FMI ?', 'Fonds Monétaire International', ['Fonds des Marchés Intérieurs', 'Finance des Monnaies Interafricaines', 'Fonds Mondial des Investissements'], 'Institution de Washington.'),
    ('Que signifie OMC ?', 'Organisation Mondiale du Commerce', ['Organisation des Marchés Communs', 'Ordre Mondial du Commerce', 'Office Mondial des Changes'], 'Elle régule le commerce mondial.'),
    ("Qu'est-ce que la balance commerciale ?", 'Exportations moins importations', ['Recettes moins dépenses publiques', 'Le PIB moins les impôts', 'La dette extérieure'], 'Un solde positif = excédent.'),
    ("Qu'est-ce qu'un impôt ?", "Un prélèvement obligatoire de l'État", ['Un crédit bancaire', 'Une subvention', 'Un salaire'], 'Il finance les dépenses publiques.'),
    ("Quel est le rôle du budget de l'État ?", 'Prévoir les recettes et dépenses publiques', ['Fixer les salaires privés', 'Décider des prix', 'Créer la monnaie'], 'Loi de finances annuelle.'),
    ("Qu'est-ce que le chômage technique ?", 'La suspension temporaire du travail', ['Un emploi à temps partiel', 'Une formation', 'Un licenciement définitif'], "Liée à un manque d'activité temporaire."),
    ("Qu'est-ce que la croissance économique ?", "L'augmentation du PIB sur une période", ['La hausse des prix', 'La baisse du chômage', 'La hausse de la population'], 'Elle se mesure en % du PIB.'),
    ("Qu'est-ce que la déflation ?", 'La baisse générale des prix', ['La hausse des prix', 'La hausse du PIB', 'La baisse du chômage'], "Opposé de l'inflation."),
    ("Qu'est-ce que le pouvoir d'achat ?", "La quantité de biens qu'on peut acheter avec un revenu", ['Le revenu brut', 'Le salaire minimum', 'Le prix moyen'], 'Il dépend du revenu et des prix.'),
    ('Quelle est la monnaie de la zone UEMOA ?', 'Le franc CFA', ['Le naira', 'Le cedi', 'Le dirham'], "UEMOA : 8 pays d'Afrique de l'Ouest."),
    ("Combien de pays composent l'UEMOA ?", '8', ['4', '12', '15'], "Bénin, Burkina, Côte d'Ivoire, Guinée-Bissau, Mali, Niger, Sénégal, Togo."),
    ("Qu'est-ce qu'une PME ?", 'Petite et Moyenne Entreprise', ['Produit Marchand Exporté', 'Plan Monétaire Européen', 'Prix Moyen Estimé'], 'Moins de 250 salariés selon les critères.'),
    ("Quel est le principal secteur d'activité au Sénégal ?", 'Les services', ["L'industrie minière", 'La construction', "L'automobile"], 'Le tertiaire domine le PIB sénégalais.'),
    ("Quelle est la principale ressource d'exportation du Sénégal ?", "La pêche et l'arachide", ['Le pétrole', 'Le café', 'Le cacao'], "Avec l'or et les phosphates."),
    ("Qu'est-ce que l'épargne ?", 'La partie du revenu non consommée', ['Un crédit', 'Une taxe', 'Un salaire'], "Elle finance l'investissement."),
    ("Qu'est-ce qu'un investissement ?", 'Une dépense pour produire davantage plus tard', ['Une consommation immédiate', 'Un impôt', 'Une épargne'], 'Formation brute de capital fixe.'),
    ('Que fait une banque commerciale ?', 'Reçoit des dépôts et accorde des crédits', ['Émet la monnaie nationale', 'Fixe les impôts', 'Contrôle les prix'], "Elle collecte l'épargne."),
    ("Qu'est-ce qu'un taux d'intérêt ?", "Le prix de l'argent emprunté", ["Le prix d'un bien", 'Le montant des impôts', 'Le taux de change'], 'Exprimé en % par an.'),
    ("Qu'est-ce que le taux de change ?", "Le prix d'une monnaie exprimé dans une autre", ["Le taux d'imposition", 'Le taux de chômage', "Le taux d'inflation"], 'Il fluctue selon le marché.'),
    ("Qu'est-ce que l'économie informelle ?", 'Les activités non déclarées', ['Les entreprises publiques', 'Le commerce international', "L'agriculture moderne"], 'Sans enregistrement ni protection sociale.'),
    ("Quel est l'objectif principal de la BCEAO ?", 'Maintenir la stabilité des prix', ['Augmenter les impôts', 'Créer des emplois', 'Construire des routes'], 'Elle conduit la politique monétaire.'),
    ("Qu'est-ce que la dette publique ?", "L'ensemble des emprunts de l'État", ['Les impôts futurs', 'Le budget annuel', "Les réserves d'or"], 'Elle est à rembourser avec intérêts.'),
    ("Que mesure le taux d'inflation ?", 'La variation des prix à la consommation', ['La variation du PIB', "Le taux d'épargne", 'Le taux de change'], 'Calculé sur un panier de biens.'),
    ("Qu'est-ce qu'une subvention ?", 'Une aide financière publique', ['Une taxe', 'Un crédit privé', 'Un salaire'], 'Elle soutient un secteur ou produit.'),
    ("Qu'est-ce qu'un monopole ?", 'Une seule entreprise contrôle un marché', ['Deux entreprises', 'Cent entreprises', 'Un marché libre'], 'Il réduit la concurrence.'),
    ("Qu'est-ce que la concurrence ?", 'La rivalité entre entreprises sur un marché', ["L'entente entre entreprises", 'Le monopole', 'Une taxation'], 'Elle fait baisser les prix.'),
    ('Quel indicateur mesure le développement humain ?', "L'IDH", ['Le PIB', 'Le taux de change', 'La balance commerciale'], 'Espérance de vie, éducation, revenu.'),
    ("Qu'est-ce que l'agriculture de subsistance ?", 'Produire pour se nourrir soi-même', ['Produire pour exporter', 'Produire pour vendre en ville', "L'élevage industriel"], 'Faible surplus commercialisable.'),
    ("Qu'est-ce que la traçabilité ?", "Suivre le parcours d'un produit", ['Mesurer son poids', 'Calculer son prix', 'Compter les stocks'], 'Utile en agriculture et alimentation.'),
    ('Quel est le rôle du microcrédit ?', 'Financer les petits entrepreneurs', ['Financer les États', 'Créer la monnaie', 'Fixer les prix'], 'Il cible les exclus du système bancaire.'),
    ("Qu'est-ce qu'un marché ?", "Le lieu de rencontre de l'offre et de la demande", ["Un magasin d'État", 'Une banque', 'Un impôt'], 'Il peut être physique ou virtuel.'),
    ('Que signifie TIC ?', "Technologies de l'Information et de la Communication", ['Taxes sur les Importations et Consommations', 'Transferts Internationaux de Capitaux', "Taux d'Intérêt et de Change"], 'Internet, téléphonie, informatique.'),
    ("Qu'est-ce que le mobile money ?", 'Un service de paiement par téléphone', ['Une carte bancaire', 'Un chèque', 'Un virement postal'], 'Très développé en Afrique.'),
]

INFO_EXTRA = [
    ('Que signifie RAM ?', 'Random Access Memory', ['Read Access Memory', 'Rapid Access Module', 'Run All Memory'], 'Mémoire vive temporaire.'),
    ('Que signifie ROM ?', 'Read Only Memory', ['Random Output Memory', 'Run Only Mode', 'Read Order Memory'], 'Mémoire en lecture seule.'),
    ('Quel composant effectue les calculs ?', 'Le processeur', ['La RAM', 'Le disque dur', "L'écran"], 'Le CPU exécute les instructions.'),
    ('Que signifie SSD ?', 'Solid State Drive', ['Super Storage Disk', 'System Start Drive', 'Secure Storage Data'], 'Disque flash.'),
    ("Quelle est l'unité de la mémoire la plus petite ?", 'Le bit', ["L'octet", 'Le kilo-octet', 'Le mégaoctet'], '1 octet = 8 bits.'),
    ('Combien de bits dans un octet ?', '8', ['4', '16', '32'], '1 o = 8 bits.'),
    ("Combien d'octets dans un kilooctet (norme SI) ?", '1000', ['1024', '100', '10000'], 'En informatique, on utilise souvent 1024.'),
    ('Que signifie OS ?', 'Operating System', ['Open Source', 'Output System', 'Online Storage'], 'Windows, Linux, Android sont des OS.'),
    ("Quel est un système d'exploitation mobile ?", 'Android', ['Photoshop', 'Word', 'Excel'], 'Android est un OS mobile.'),
    ('Que fait un compilateur ?', 'Traduit le code source en code machine', ['Exécute le programme', 'Écrit du code', 'Débogue du code'], 'Il produit un exécutable.'),
    ('Quelle structure teste une condition ?', 'if', ['for', 'while', 'print'], 'if exécute si la condition est vraie.'),
    ("Qu'est-ce qu'une variable ?", 'Un emplacement mémoire nommé qui stocke une valeur', ['Une fonction', 'Une boucle', 'Un fichier'], 'Elle peut changer de valeur.'),
    ("Qu'est-ce qu'une fonction ?", 'Un bloc de code réutilisable', ['Une variable', 'Une boucle', 'Un fichier'], 'Elle a un nom et des paramètres.'),
    ("Quel opérateur teste l'égalité en Python ?", '==', ['=', '!=', '<>'], '== compare, = affecte.'),
    ('Que fait INSERT en SQL ?', 'Ajoute une ligne', ['Lit des lignes', 'Supprime des lignes', 'Modifie une table'], 'INSERT INTO ... VALUES.'),
    ('Que fait UPDATE en SQL ?', 'Modifie des lignes existantes', ['Ajoute des lignes', 'Supprime des lignes', 'Crée une table'], 'UPDATE ... SET.'),
    ('Que fait DELETE en SQL ?', 'Supprime des lignes', ['Ajoute des lignes', 'Lit des lignes', 'Crée une table'], 'DELETE FROM ... WHERE.'),
    ('Quelle clé identifie de façon unique une ligne ?', 'La clé primaire', ['La clé étrangère', "L'index", 'Le trigger'], 'PRIMARY KEY.'),
    ('Que fait une clé étrangère ?', 'Relie deux tables', ['Identifie une ligne', 'Trie les données', 'Chiffre les données'], 'FOREIGN KEY.'),
    ("Qu'est-ce qu'une adresse IP ?", "Un identifiant unique d'un appareil sur un réseau", ['Un mot de passe', 'Un nom de domaine', 'Un protocole'], 'IPv4 ou IPv6.'),
    ('Que signifie DNS ?', 'Domain Name System', ['Data Network Service', 'Digital Name Server', 'Direct Node System'], 'Il traduit les noms en adresses IP.'),
    ('Que signifie HTTP ?', 'HyperText Transfer Protocol', ['High Transfer Text Protocol', 'Hyper Terminal Transfer Process', 'Home Text Transport Protocol'], 'Protocole du web.'),
    ('Que protège HTTPS par rapport à HTTP ?', 'Le chiffrement des échanges', ['La vitesse', 'La taille', 'La couleur'], 'HTTPS chiffre avec TLS.'),
    ('Que signifie URL ?', 'Uniform Resource Locator', ['Universal Reference Link', 'Uniform Routing Line', 'User Resource Location'], "L'adresse d'une ressource web."),
    ("Qu'est-ce qu'un serveur ?", 'Un ordinateur qui fournit des services à des clients', ['Un écran', 'Un câble', 'Un logiciel antivirus'], 'Il répond aux requêtes.'),
    ("Qu'est-ce qu'un algorithme de tri ?", 'Une méthode pour ordonner des données', ['Une méthode pour chiffrer', 'Une méthode pour compresser', 'Une méthode pour imprimer'], 'Tri par insertion, fusion, etc.'),
    ('Quelle est la complexité du tri par insertion (pire cas) ?', 'O(n²)', ['O(n)', 'O(log n)', 'O(1)'], 'Deux boucles imbriquées.'),
    ("Qu'est-ce qu'une boucle infinie ?", 'Une boucle dont la condition est toujours vraie', ["Une boucle qui s'arrête vite", 'Un if', 'Une variable'], 'Elle bloque le programme.'),
    ("Que fait l'instruction return ?", 'Renvoie une valeur et sort de la fonction', ['Répète le code', 'Déclare une variable', 'Importe un module'], 'Elle termine la fonction.'),
    ("Qu'est-ce qu'un bug ?", 'Une erreur dans le programme', ['Une fonctionnalité', 'Un virus', 'Un mot de passe'], 'Il faut le corriger.'),
    ('Que signifie BDD en informatique ?', 'Base de données', ['Boîtier de disque', 'Bureau de développement', 'Bloc de données'], "Stockage structuré de l'information."),
    ("Qu'est-ce que le cloud computing ?", 'Utiliser des ressources informatiques à distance', ['Un disque local', 'Un logiciel de dessin', "Un type d'écran"], 'Serveurs distants via Internet.'),
    ('Que fait un pare-feu (firewall) ?', 'Filtre le trafic réseau', ['Accélère Internet', 'Compresse les fichiers', 'Affiche les sites'], 'Il bloque les connexions non autorisées.'),
    ("Qu'est-ce qu'un antivirus ?", 'Un logiciel qui détecte les programmes malveillants', ['Un accélérateur', 'Un compilateur', 'Un navigateur'], 'Il protège contre les virus.'),
    ("Qu'est-ce que le phishing ?", "Une tentative d'obtenir des informations par tromperie", ['Une accélération réseau', 'Un type de sauvegarde', 'Un langage de programmation'], 'Hameçonnage par faux messages.'),
    ('Quel est un mot de passe robuste ?', 'Long avec majuscules, minuscules, chiffres et symboles', ['Son prénom', '123456', 'azerty'], 'Il doit être complexe et unique.'),
    ('Que signifie PDF ?', 'Portable Document Format', ['Personal Data File', 'Public Document Form', 'Printed Digital File'], 'Format de document.'),
    ('Quel logiciel sert à faire des tableaux de calcul ?', 'Un tableur', ['Un traitement de texte', 'Un navigateur', 'Un lecteur vidéo'], 'Excel, LibreOffice Calc.'),
    ('Que signifie CPU en français ?', 'Unité centrale de traitement', ['Mémoire vive', 'Carte graphique', 'Disque dur'], 'Le processeur.'),
    ("Que fait la mémoire RAM quand on éteint l'ordinateur ?", 'Les données sont effacées', ['Elles sont conservées', 'Elles sont imprimées', 'Elles sont copiées'], 'La RAM est volatile.'),
    ('Quelle base utilise le système hexadécimal ?', '16', ['2', '8', '10'], '0-9 et A-F.'),
    ('Combien vaut le binaire 1010 en décimal ?', '10', ['8', '12', '16'], '1×8 + 0×4 + 1×2 + 0×1 = 10.'),
    ("Qu'est-ce que le Wi-Fi ?", 'Un réseau local sans fil', ['Un câble réseau', 'Un type de disque', 'Un logiciel'], 'Norme IEEE 802.11.'),
    ('Quel appareil relie un réseau local à Internet ?', 'Le routeur', ["L'écran", 'Le clavier', "L'imprimante"], 'Il route les paquets.'),
    ("Qu'est-ce qu'une sauvegarde ?", 'Une copie des données pour les récupérer en cas de perte', ['Une suppression', 'Un formatage', 'Un partage'], 'Backup régulier recommandé.'),
    ('Que signifie IA ?', 'Intelligence Artificielle', ['Interface Automatique', 'Information Avancée', 'Intégration Algorithmique'], "Simulation de l'intelligence par la machine."),
    ("Qu'est-ce qu'un modèle d'apprentissage automatique ?", 'Un programme qui apprend à partir de données', ['Un tableur', 'Un antivirus', 'Un navigateur'], 'Machine learning.'),
    ('Que fait un moteur de recherche ?', 'Trouve des pages correspondant à une requête', ['Crée des sites', 'Héberge des fichiers', 'Envoie des e-mails'], 'Google, Bing.'),
    ('Que signifie @ dans une adresse e-mail ?', "Il sépare le nom de l'utilisateur du domaine", ['Il signifie urgent', 'Il indique le pays', 'Il remplace le point'], 'utilisateur@domaine.'),
    ('Que fait Ctrl+C ?', 'Copier', ['Coller', 'Couper', 'Enregistrer'], 'Raccourci clavier de copie.'),
    ('Que fait Ctrl+V ?', 'Coller', ['Copier', 'Couper', 'Annuler'], 'Raccourci clavier de collage.'),
    ('Quelle extension correspond à un fichier image ?', '.png', ['.docx', '.mp3', '.exe'], 'png, jpg, gif sont des images.'),
    ('Quelle extension correspond à un document Word ?', '.docx', ['.jpg', '.mp3', '.html'], 'Format Microsoft Word.'),
    ("Qu'est-ce que le code source ?", 'Le texte du programme écrit par le développeur', ['Le fichier exécutable', 'Un mot de passe', 'Un pilote'], 'Il est écrit en langage de programmation.'),
    ('Que signifie API ?', 'Application Programming Interface', ['Automatic Program Input', 'Applied Process Interface', 'Advanced Program Install'], 'Interface de programmation.'),
    ("Qu'est-ce que Git ?", 'Un système de gestion de versions', ['Un langage de programmation', 'Un antivirus', 'Un navigateur'], 'Il suit les modifications du code.'),
]

def _cycle(bank, level, count, template):
    """Produit `count` variantes en tournant sur une banque de faits."""
    li = LVL_IDX[level]
    out = []
    rnd.shuffle(bank)
    for i in range(count):
        fact = bank[i % len(bank)]
        out.append(template(fact, i))
    return out


HIST_EXTRA2 = [
    ('La traite transatlantique a duré principalement du', 'XVIe au XIXe siècle', ['Xe au XIIe siècle', 'XXe siècle', 'Ve siècle'], 'Du XVIe au XIXe siècle.'),
    ('Qui a conduit la conférence de Berlin ?', 'Otto von Bismarck', ['Napoléon', 'Léopold II', 'Cecil Rhodes'], 'Chancelier allemand, 1884-1885.'),
    ("Quel empire a dominé l'Afrique de l'Ouest au XIIIe siècle ?", "L'empire du Mali", ["L'empire du Ghana moderne", "L'empire romain", "L'empire ottoman"], 'Fondé par Soundiata Keïta.'),
    ("Quelle est la date de l'indépendance de la Gambie ?", '1965', ['1960', '1970', '1958'], '18 février 1965.'),
    ('Quel pays a colonisé le Sénégal ?', 'La France', ['Le Portugal', 'Le Royaume-Uni', "L'Espagne"], "Colonie française jusqu'en 1960."),
    ('Quelle île a été un grand centre de la traite négrière ?', 'Gorée', ['Zanzibar', 'Madagascar', 'Malte'], 'Au large de Dakar.'),
    ('Quel roi a résisté à la colonisation au Sénégal ?', 'Lat Dior', ['Soundiata Keïta', 'Mansa Moussa', 'Samory Touré'], 'Damél du Cayor.'),
    ('Qui a résisté à la colonisation en Guinée ?', 'Samory Touré', ['Lat Dior', 'Behanzin', 'Soundiata Keïta'], "Fondateur de l'empire Wassoulou."),
    ("En quelle année l'ONU a-t-elle été créée ?", '1945', ['1919', '1950', '1960'], 'Après la Seconde Guerre mondiale.'),
    ('Quel mur a été détruit en 1989 ?', 'Le mur de Berlin', ["Le mur d'Hadrien", 'La Grande Muraille', 'Le mur de Chine'], 'Symbole de la fin de la Guerre froide.'),
    ('Quelle guerre a opposé le Nord et le Sud des États-Unis ?', 'La guerre de Sécession', ['La guerre de Cent Ans', 'La guerre froide', 'La guerre de 1914'], '1861-1865.'),
    ('Quel événement a déclenché la Première Guerre mondiale ?', "L'assassinat de l'archiduc François-Ferdinand", ['La Révolution russe', 'La chute de Berlin', 'La guerre de Sécession'], 'Sarajevo, 1914.'),
    ('Quel pays a lancé la première bombe atomique en 1945 ?', 'Les États-Unis', ["L'URSS", 'Le Japon', "L'Allemagne"], 'Hiroshima et Nagasaki.'),
    ('Quelle civilisation a construit les pyramides de Gizeh ?', "L'Égypte antique", ['La Grèce', 'Rome', 'Le Mali'], 'Vers 2560 av. J.-C.'),
    ('Quel empire a construit le Colisée ?', "L'Empire romain", ['La Grèce', "L'Égypte", 'Carthage'], 'Rome, 80 ap. J.-C.'),
    ('Qui était Cléopâtre ?', "Une reine d'Égypte", ['Une reine de France', 'Une impératrice romaine', 'Une reine du Mali'], 'Dernière reine ptolémaïque.'),
    ('Quelle révolution a commencé en 1789 ?', 'La Révolution française', ['La révolution industrielle', 'La révolution russe', 'La révolution américaine'], 'Prise de la Bastille.'),
    ('Quel roi français a été guillotiné en 1793 ?', 'Louis XVI', ['Louis XIV', 'Henri IV', 'François Ier'], 'Révolution française.'),
    ('Qui a mené la Révolution russe de 1917 ?', 'Lénine', ['Staline', 'Trotski', 'Khrouchtchev'], 'Bolcheviks.'),
    ("Quelle organisation a succédé à l'OUA en 2002 ?", "L'Union africaine", ['La CEDEAO', "L'ONU", 'La Ligue arabe'], 'Union africaine.'),
    ('Quel traité a mis fin à la Première Guerre mondiale ?', 'Le traité de Versailles', ['Le traité de Paris', 'Le traité de Rome', 'Le traité de Berlin'], '1919.'),
    ('Quel pays a obtenu son indépendance en 1957 ?', 'Le Ghana', ['Le Sénégal', 'Le Mali', "L'Algérie"], "Premier pays d'Afrique subsaharienne indépendant."),
    ("Quelle année marque la fin de l'apartheid ?", '1994', ['1976', '1985', '2000'], 'Élections multiraciales en Afrique du Sud.'),
    ('Qui était Nelson Mandela ?', 'Un président sud-africain et prix Nobel de la paix', ['Un roi du Mali', 'Un général français', 'Un empereur éthiopien'], '1993 prix Nobel, président en 1994.'),
    ('Quelle bataille marque la fin de Napoléon en 1815 ?', 'Waterloo', ['Austerlitz', 'Iéna', 'Trafalgar'], 'Défaite finale.'),
    ("Quel peuple a créé l'écriture cunéiforme ?", 'Les Sumériens', ['Les Égyptiens', 'Les Grecs', 'Les Romains'], 'Mésopotamie.'),
    ('Quelle cité antique était célèbre pour sa démocratie ?', 'Athènes', ['Rome', 'Sparte', 'Carthage'], 'Ve siècle av. J.-C.'),
    ('Quel empire a été dirigé par Mansa Moussa ?', "L'empire du Mali", ["L'empire du Ghana", "L'empire Songhaï", "L'empire du Kanem"], 'Roi du Mali, XIVe siècle.'),
    ("Quelle est la capitale de l'empire Songhaï ?", 'Gao', ['Tombouctou', 'Djenné', 'Ségou'], 'Gao était la capitale politique.'),
    ("Quel explorateur a atteint l'Amérique en 1492 ?", 'Christophe Colomb', ['Vasco de Gama', 'Magellan', 'Marco Polo'], "Au service de l'Espagne."),
    ('Qui a fait le tour du monde en premier (expédition) ?', 'Magellan et Elcano', ['Colomb', 'Vasco de Gama', 'Marco Polo'], '1519-1522.'),
    ("Quel pays africain n'a jamais été colonisé ?", "L'Éthiopie", ['Le Sénégal', 'Le Ghana', 'Le Mali'], 'Sauf brève occupation italienne.'),
    ("Quelle guerre a opposé l'Est et l'Ouest de 1947 à 1991 ?", 'La guerre froide', ['La guerre de Cent Ans', 'La guerre de Sécession', 'La Grande Guerre'], 'Sans affrontement direct.'),
    ('Quel mur séparait la Chine des invasions ?', 'La Grande Muraille', ['Le mur de Berlin', "Le mur d'Hadrien", 'Le mur de Babylone'], 'Construite sur des siècles.'),
    ('Quelle dynastie a régné en France de 987 à 1328 ?', 'Les Capétiens', ['Les Bourbons', 'Les Mérovingiens', 'Les Carolingiens'], 'Hugues Capet en 987.'),
    ("Quel roi a créé l'empire du Ghana antique ?", 'Les Soninkés', ['Les Peuls', 'Les Wolofs', 'Les Sérères'], 'Empire du Wagadou.'),
    ('Quel pays a été le premier à abolir la traite en 1807 ?', 'Le Royaume-Uni', ['La France', 'Les États-Unis', 'Le Portugal'], 'Abolition de la traite.'),
]

GEO_EXTRA2 = [
    ('Quel est le plus grand désert chaud du monde ?', 'Le Sahara', ['Le Gobi', "L'Atacama", 'Le Kalahari'], 'Environ 9 millions de km².'),
    ('Quel est le plus long fleuve du monde ?', 'Le Nil', ["L'Amazone", 'Le Niger', 'Le Congo'], 'Environ 6 700 km.'),
    ("Quelle est la plus haute montagne d'Afrique ?", 'Le Kilimandjaro', ['Le mont Kenya', "L'Atlas", 'Le Ruwenzori'], '5 895 m, Tanzanie.'),
    ('Quel océan borde le Sénégal ?', "L'océan Atlantique", ["L'océan Indien", "L'océan Pacifique", "L'océan Arctique"], "À l'ouest du pays."),
    ('Quel pays entoure presque entièrement la Gambie ?', 'Le Sénégal', ['Le Mali', 'La Guinée', 'La Mauritanie'], 'Enclave dans le Sénégal.'),
    ('Quelle est la capitale de la Mauritanie ?', 'Nouakchott', ['Nouadhibou', 'Rosso', 'Atar'], 'Depuis 1960.'),
    ("Quel est le plus grand pays d'Afrique en superficie ?", "L'Algérie", ['Le Soudan', 'La RDC', 'Le Mali'], '2,38 millions de km².'),
    ("Quel pays d'Afrique compte le plus d'habitants ?", 'Le Nigeria', ["L'Égypte", "L'Éthiopie", "L'Afrique du Sud"], 'Plus de 220 millions.'),
    ("Quel est le plus grand lac d'Afrique ?", 'Le lac Victoria', ['Le lac Tanganyika', 'Le lac Tchad', 'Le lac Malawi'], 'Environ 68 000 km².'),
    ("Quelle chaîne de montagnes sépare l'Europe de l'Asie ?", "L'Oural", ['Les Alpes', 'Les Pyrénées', 'Le Caucase'], 'Frontière naturelle.'),
    ("Quel détroit sépare l'Afrique de l'Europe ?", 'Le détroit de Gibraltar', ['Le Bosphore', 'Le détroit de Malacca', 'Le canal de Suez'], '14 km de large.'),
    ('Quel canal relie la Méditerranée et la mer Rouge ?', 'Le canal de Suez', ['Le canal de Panama', 'Le canal de Corinthe', 'Le canal de Kiel'], 'Égypte, 1869.'),
    ("Quelle est la capitale de la Côte d'Ivoire ?", 'Yamoussoukro', ['Abidjan', 'Bouaké', 'Daloa'], 'Capitale politique, Abidjan économique.'),
    ('Quel est le plus grand pays du monde ?', 'La Russie', ['Le Canada', 'La Chine', 'Les États-Unis'], '17 millions de km².'),
    ('Quelle est la plus grande forêt tropicale ?', 'La forêt amazonienne', ['La forêt du Congo', 'La forêt de Bornéo', 'La forêt indienne'], 'Amérique du Sud.'),
    ('Quelle mer est la plus salée ?', 'La mer Morte', ['La Méditerranée', 'La mer Rouge', 'La mer Noire'], 'Environ 34 % de sel.'),
    ("Quel pays a la forme d'une botte ?", "L'Italie", ['La Grèce', "L'Espagne", 'Le Portugal'], 'Péninsule italienne.'),
    ("Quelle est la capitale de l'Espagne ?", 'Madrid', ['Barcelone', 'Séville', 'Valence'], 'Capitale depuis 1561.'),
    ('Quel est le plus petit pays du monde ?', 'Le Vatican', ['Monaco', 'Saint-Marin', 'Le Liechtenstein'], '0,44 km².'),
    ('Quelle région du Sénégal est la plus arrosée ?', 'La Casamance', ['Le Ferlo', 'La Petite Côte', 'Le Siné-Saloum'], 'Climat soudano-guinéen.'),
    ('Quel fleuve forme la frontière nord du Sénégal ?', 'Le fleuve Sénégal', ['La Gambie', 'Le Sine', 'Le Saloum'], 'Frontière avec la Mauritanie.'),
    ("Quelle est la plus grande ville d'Afrique ?", 'Le Caire', ['Lagos', 'Kinshasa', 'Johannesburg'], 'Agglomération la plus peuplée.'),
    ('Quel pays possède le plus de fuseaux horaires ?', 'La France', ['La Russie', 'Les États-Unis', 'La Chine'], "Grâce à ses territoires d'outre-mer."),
    ("Quelle île est le plus grand État d'Afrique ?", 'Madagascar', ['Maurice', 'Zanzibar', 'Le Cap-Vert'], '592 000 km².'),
    ('Quel océan est le plus vaste ?', "L'océan Pacifique", ["L'Atlantique", "L'Indien", "L'Arctique"], 'Un tiers de la surface du globe.'),
]



HIST_ADD2 = [
    ('Quel empire africain a été dirigé par Soundiata Keïta ?', "L'empire du Mali", ["L'empire du Ghana", "L'empire Songhaï", 'Le Kanem-Bornou'], 'Fondé au XIIIe siècle.'),
    ("Quelle conférence a partagé l'Afrique en 1884-1885 ?", 'La conférence de Berlin', ['Le congrès de Vienne', 'La conférence de Yalta', 'Le traité de Versailles'], 'Organisée par Bismarck.'),
    ('En quelle année le Sénégal a-t-il obtenu son indépendance ?', '1960', ['1958', '1962', '1957'], 'Le 4 avril 1960.'),
    ('Qui fut le premier président du Sénégal ?', 'Léopold Sédar Senghor', ['Abdou Diouf', 'Mamadou Dia', 'Abdoulaye Wade'], '1960-1980.'),
    ('Quelle grande guerre a eu lieu de 1914 à 1918 ?', 'La Première Guerre mondiale', ['La Seconde Guerre mondiale', 'La guerre de Cent Ans', 'La guerre de Crimée'], '1914-1918.'),
    ('Quelle organisation a été créée en 1945 après la Seconde Guerre mondiale ?', "L'ONU", ['La SDN', "L'OTAN", "L'UE"], 'Organisation des Nations unies.'),
    ('Quel mur est tombé en 1989 ?', 'Le mur de Berlin', ["Le mur d'Hadrien", 'La Grande Muraille', 'Le mur de Chine'], 'Symbole de la fin de la Guerre froide.'),
    ('Quelle révolution a commencé en 1789 ?', 'La Révolution française', ['La Révolution russe', 'La révolution industrielle', 'La Révolution américaine'], 'Prise de la Bastille.'),
    ("Qui a mené la lutte contre l'apartheid en Afrique du Sud ?", 'Nelson Mandela', ['Desmond Tutu', 'Thabo Mbeki', 'Julius Nyerere'], 'Prix Nobel de la paix 1993.'),
    ('Quel pays a colonisé le Sénégal ?', 'La France', ['Le Portugal', 'Le Royaume-Uni', "L'Espagne"], "Jusqu'en 1960."),
    ('Quelle île au large de Dakar fut un lieu de traite négrière ?', 'Gorée', ['Zanzibar', 'Madagascar', 'Malte'], 'Mémorial de la traite atlantique.'),
    ('Quel roi du Cayor a résisté à la colonisation française ?', 'Lat Dior', ['Samory Touré', 'Behanzin', 'Mansa Moussa'], 'Damél du Cayor.'),
    ('Quelle civilisation a construit les pyramides de Gizeh ?', "L'Égypte antique", ['La Grèce', 'Rome', 'Carthage'], 'Vers 2560 av. J.-C.'),
    ('Quel empire a construit le Colisée ?', "L'Empire romain", ['La Grèce', "L'Égypte", 'Les Perses'], 'Rome, 80 ap. J.-C.'),
    ('Quel événement a déclenché la Première Guerre mondiale ?', "L'attentat de Sarajevo", ['La Révolution russe', 'La chute du mur de Berlin', 'La guerre de Sécession'], 'Assassinat de François-Ferdinand.'),
    ("En quelle année l'ONU a-t-elle adopté la Déclaration universelle des droits de l'homme ?", '1948', ['1945', '1950', '1960'], '10 décembre 1948.'),
    ('Quel traité met fin à la Première Guerre mondiale ?', 'Le traité de Versailles', ['Le traité de Rome', 'Le traité de Paris', 'Le traité de Berlin'], 'Signé en 1919.'),
    ('Qui était Cléopâtre ?', "Une reine d'Égypte", ['Une impératrice romaine', 'Une reine de France', 'Une reine du Mali'], 'Dernière reine ptolémaïque.'),
    ("Quel explorateur a atteint l'Amérique en 1492 ?", 'Christophe Colomb', ['Vasco de Gama', 'Magellan', 'Marco Polo'], "Au service de l'Espagne."),
    ("Quel peuple a inventé l'écriture cunéiforme ?", 'Les Sumériens', ['Les Égyptiens', 'Les Grecs', 'Les Romains'], 'Mésopotamie.'),
    ('Quelle cité grecque a inventé la démocratie ?', 'Athènes', ['Sparte', 'Rome', 'Carthage'], 'Ve siècle av. J.-C.'),
    ('Quel empire ouest-africain avait pour capitale Gao ?', "L'empire Songhaï", ["L'empire du Mali", "L'empire du Ghana", 'Le Kanem'], 'Gao, capitale politique.'),
    ("Quel pays africain n'a jamais été colonisé durablement ?", "L'Éthiopie", ['Le Sénégal', 'Le Ghana', 'Le Mali'], "Victoire d'Adoua en 1896."),
    ("Quelle guerre a opposé l'Est et l'Ouest de 1947 à 1991 ?", 'La guerre froide', ['La guerre de Cent Ans', 'La guerre de Sécession', 'La Grande Guerre'], 'Sans affrontement direct.'),
    ('Quel roi de France a été guillotiné en 1793 ?', 'Louis XVI', ['Louis XIV', 'Henri IV', 'Charles X'], 'Révolution française.'),
    ('Quelle bataille marque la chute définitive de Napoléon en 1815 ?', 'Waterloo', ['Austerlitz', 'Iéna', 'Trafalgar'], '18 juin 1815.'),
    ('Quel pays a obtenu son indépendance en 1957 ?', 'Le Ghana', ['Le Sénégal', 'Le Mali', "L'Algérie"], "Premier pays d'Afrique subsaharienne indépendant."),
    ('Quelle dynastie a régné en France de 987 à 1328 ?', 'Les Capétiens', ['Les Bourbons', 'Les Mérovingiens', 'Les Carolingiens'], 'Hugues Capet en 987.'),
    ('Quel empire fut dirigé par Mansa Moussa ?', "L'empire du Mali", ["L'empire du Ghana", "L'empire Songhaï", 'Le Kanem-Bornou'], 'XIVe siècle.'),
    ("Quelle organisation africaine a remplacé l'OUA en 2002 ?", "L'Union africaine", ['La CEDEAO', "L'ONU", 'La Ligue arabe'], 'Créée à Durban.'),
]

HIST_BANK = [(f[0], f[1]) for f in HIST_DATES] + [(f[0], f[1]) for f in HIST_PERSONNES] + [(f[0], f[1]) for f in HIST_EXTRA2] + [(f[0], f[1]) for f in HIST_ADD2]


def gen_hist(level, count):
    items = []

    def t_date(f, i):
        noun, d = f
        faux = [x for x in ["1914", "1945", "1957", "1958", "1960", "1962", "1975", "1989", "2002", "1848", "1885", "1789"] if x != d]
        rnd.shuffle(faux)
        if i % 3 == 0:
            return mkq(f"En quelle année a eu lieu : {noun} ?", d, faux[:3], f"{noun} : {d}.")
        return mkq(f"Quel événement correspond à l'année {d} ?", noun,
                   [x[0] for x in HIST_DATES if x[1] != d][:3], f"{d} : {noun}.")

    def t_pers(f, i):
        role, nom = f
        faux = [x[1] for x in HIST_PERSONNES if x[1] != nom]
        rnd.shuffle(faux)
        return mkq(f"Qui est : {role} ?", nom, faux[:3], f"{role} → {nom}.")

    items += _cycle(HIST_DATES, level, max(1, count // 3), t_date)
    items += _cycle(HIST_PERSONNES, level, max(1, count // 6), t_pers)
    # faits généraux
    bank = list(HIST_EXTRA2) + list(HIST_ADD2)
    rnd.shuffle(bank)
    i = 0
    while len(items) < count and i < len(bank):
        q, c_, f_, e_ = bank[i]
        items.append(mkq(q, c_, f_, e_))
        i += 1
    return items[:count]


GEO_ADD2 = [
    ("Quel est le plus long fleuve d'Afrique ?", 'Le Nil', ['Le Congo', 'Le Niger', 'Le Zambèze'], 'Environ 6 700 km.'),
    ("Quelle est la plus haute montagne d'Afrique ?", 'Le Kilimandjaro', ['Le mont Kenya', 'Le Ruwenzori', "L'Atlas"], '5 895 m en Tanzanie.'),
    ('Quel océan borde le Sénégal ?', "L'océan Atlantique", ["L'océan Indien", "L'océan Pacifique", "L'océan Arctique"], "À l'ouest du pays."),
    ('Quel pays est presque entièrement enclavé dans le Sénégal ?', 'La Gambie', ['La Guinée-Bissau', 'La Mauritanie', 'Le Mali'], 'Enclave le long du fleuve Gambie.'),
    ('Quelle est la capitale de la Mauritanie ?', 'Nouakchott', ['Nouadhibou', 'Rosso', 'Atar'], 'Depuis 1960.'),
    ("Quel est le plus grand pays d'Afrique par la superficie ?", "L'Algérie", ['Le Soudan', 'La RDC', 'Le Mali'], '2,38 millions de km².'),
    ("Quel pays africain compte le plus d'habitants ?", 'Le Nigeria', ["L'Égypte", "L'Éthiopie", "L'Afrique du Sud"], 'Plus de 220 millions.'),
    ("Quel est le plus grand lac d'Afrique ?", 'Le lac Victoria', ['Le lac Tanganyika', 'Le lac Tchad', 'Le lac Malawi'], 'Environ 68 000 km².'),
    ('Quel canal relie la Méditerranée à la mer Rouge ?', 'Le canal de Suez', ['Le canal de Panama', 'Le canal de Corinthe', 'Le canal de Kiel'], 'Égypte, ouvert en 1869.'),
    ("Quel détroit sépare l'Afrique de l'Europe ?", 'Le détroit de Gibraltar', ['Le Bosphore', 'Le détroit de Malacca', 'Le pas de Calais'], '14 km de large.'),
    ('Quel est le plus grand désert chaud du monde ?', 'Le Sahara', ['Le Gobi', "L'Atacama", 'Le Kalahari'], 'Environ 9 millions de km².'),
    ("Quelle chaîne de montagnes sépare l'Europe de l'Asie ?", "L'Oural", ['Les Alpes', 'Les Pyrénées', 'Le Caucase'], 'Frontière naturelle.'),
    ("Quelle est la capitale de la Côte d'Ivoire ?", 'Yamoussoukro', ['Abidjan', 'Bouaké', 'Daloa'], 'Capitale politique depuis 1983.'),
    ('Quel est le plus vaste pays du monde ?', 'La Russie', ['Le Canada', 'La Chine', 'Les États-Unis'], '17 millions de km².'),
    ('Quelle est la plus grande forêt tropicale du monde ?', 'La forêt amazonienne', ['La forêt du Congo', 'La forêt de Bornéo', 'La forêt indienne'], 'Amérique du Sud.'),
    ('Quelle mer est la plus salée ?', 'La mer Morte', ['La Méditerranée', 'La mer Rouge', 'La mer Noire'], 'Environ 34 % de sel.'),
    ("Quelle est la capitale de l'Espagne ?", 'Madrid', ['Barcelone', 'Séville', 'Valence'], 'Capitale depuis 1561.'),
    ('Quelle région du Sénégal est la plus arrosée ?', 'La Casamance', ['Le Ferlo', 'La Petite Côte', 'Le Siné-Saloum'], 'Climat soudano-guinéen.'),
    ('Quel fleuve marque la frontière nord du Sénégal ?', 'Le fleuve Sénégal', ['La Gambie', 'Le Sine', 'Le Saloum'], 'Frontière avec la Mauritanie.'),
    ('Quel est le plus petit État du monde ?', 'Le Vatican', ['Monaco', 'Saint-Marin', 'Le Liechtenstein'], '0,44 km².'),
]

def gen_geo(level, count):
    items = []

    def t_cap(f, i):
        pays, cap, cont, mon = f
        faux = [p[1] for p in PAYS_UNIK if p[1] != cap]
        rnd.shuffle(faux)
        return mkq(f"Quelle est la capitale du {pays} ?", cap, faux[:3], f"La capitale du {pays} est {cap}.")

    def t_rev(f, i):
        pays, cap, cont, mon = f
        faux = [p[0] for p in PAYS_UNIK if p[0] != pays]
        rnd.shuffle(faux)
        return mkq(f"{cap} est la capitale de quel pays ?", pays, faux[:3], f"{cap} → {pays}.")

    def t_fleuve(f, i):
        nom, cont, pays = f
        faux = [x[0] for x in FLEUVES if x[0] != nom]
        rnd.shuffle(faux)
        return mkq(f"Dans quel pays se jette principalement le fleuve {nom} ?", pays, faux[:3], f"Le {nom} traverse notamment {pays}.")

    def t_mont(f, i):
        nom, pays, cont = f
        faux = [x[1] for x in MONTS if x[1] != pays]
        rnd.shuffle(faux)
        return mkq(f"Dans quel pays se trouve {nom} ?", pays, faux[:3], f"{nom} se situe en {pays}.")

    part = max(1, count // 4)
    items += _cycle(PAYS_UNIK, level, part, t_cap)
    items += _cycle(PAYS_UNIK, level, part, t_rev)
    items += _cycle(FLEUVES, level, part, t_fleuve)
    items += _cycle(MONTS, level, max(1, count // 5), t_mont)
    bank = list(GEO_EXTRA2) + list(GEO_ADD2)
    rnd.shuffle(bank)
    i = 0
    while len(items) < count and i < len(bank):
        q, c_, f_, e_ = bank[i]
        items.append(mkq(q, c_, f_, e_))
        i += 1
    return items[:count]


SVT_FACTS = list({f[0]: f for f in (SVT_FACTS + SVT_EXTRA)}.values())


SVT_ADD2 = [
    ('Quel est le plus grand organe du corps humain ?', 'La peau', ['Le foie', 'Le cœur', 'Les poumons'], 'La peau couvre environ 2 m².'),
    ("Combien d'os compte le squelette humain adulte ?", '206', ['186', '226', '246'], "206 os chez l'adulte."),
    ("Quel organe produit l'insuline ?", 'Le pancréas', ['Le foie', 'Les reins', "L'estomac"], 'Cellules bêta des îlots de Langerhans.'),
    ('Quel est le rôle des globules rouges ?', "Transporter l'oxygène", ['Détruire les microbes', 'Coaguler le sang', 'Produire des anticorps'], "Grâce à l'hémoglobine."),
    ('Quel gaz les plantes absorbent-elles pour la photosynthèse ?', 'Le dioxyde de carbone', ["L'oxygène", "L'azote", 'Le méthane'], 'CO₂ + eau + lumière → glucose + O₂.'),
    ('Quel organe filtre le sang ?', 'Le rein', ['Le foie', 'La rate', 'Le pancréas'], "Le rein filtre et forme l'urine."),
    ("Quelle est l'unité de base du système nerveux ?", 'Le neurone', ['La cellule gliale', 'Le nerf', 'Le ganglion'], "Le neurone transmet l'influx nerveux."),
    ('Quel muscle permet la respiration ?', 'Le diaphragme', ['Le cœur', 'Le biceps', 'Le triceps'], 'Muscle respiratoire principal.'),
    ('Quel groupe sanguin est dit « donneur universel » ?', 'O−', ['AB+', 'A+', 'B−'], "L'absence d'antigènes A, B et Rh."),
    ('Quel est le rôle des plaquettes ?', 'La coagulation du sang', ['Le transport du fer', 'La défense immunitaire', 'La digestion'], 'Les plaquettes forment le caillot.'),
    ("Quelle partie de la cellule contient l'ADN ?", 'Le noyau', ['La membrane', 'Le cytoplasme', 'La vacuole'], 'Chez les eucaryotes.'),
    ('Quel organe est responsable de la détoxification ?', 'Le foie', ['Le rein', 'Le poumon', 'Le cœur'], 'Le foie métabolise les toxines.'),
    ('Quelle vitamine est produite par la peau au soleil ?', 'La vitamine D', ['La vitamine C', 'La vitamine A', 'La vitamine B12'], "Sous l'action des UV."),
    ('Combien de chambres compte le cœur humain ?', '4', ['2', '3', '6'], 'Deux oreillettes et deux ventricules.'),
    ('Quel est le nom du vaisseau qui transporte le sang du cœur vers les organes ?', "L'artère", ['La veine', 'Le capillaire', 'Le nerf'], 'Les artères partent du cœur.'),
    ('Quel est le plus long os du corps humain ?', 'Le fémur', ['Le tibia', "L'humérus", 'Le radius'], 'Os de la cuisse.'),
    ("Quel organe sécrète l'acide chlorhydrique ?", "L'estomac", ["L'intestin grêle", 'Le foie', 'Le côlon'], 'pH gastrique très acide.'),
    ('Quelle membrane entoure les poumons ?', 'La plèvre', ['Le péricarde', 'Le péritoine', 'La méninge'], 'La plèvre protège les poumons.'),
    ("Quel est le rôle des reins dans l'équilibre du corps ?", "Réguler l'eau et les sels minéraux", ['Produire des globules rouges', 'Digérer les protéines', "Transporter l'oxygène"], 'Filtration et équilibre hydro-minéral.'),
    ('Quel organe produit la bile ?', 'Le foie', ['La vésicule biliaire', 'Le pancréas', "L'estomac"], 'La bile est stockée dans la vésicule.'),
    ('Quel est le mode de reproduction des bactéries ?', 'La division cellulaire', ['La fécondation', 'Le bourgeonnement sexué', 'La sporulation sexuée'], 'Scissiparité (division binaire).'),
    ('Quelle maladie est causée par un manque de fer ?', "L'anémie", ['Le diabète', "L'asthme", 'La grippe'], 'Anémie ferriprive.'),
    ('Quel organe est touché par la bronchite ?', 'Les bronches', ["L'estomac", 'Le rein', 'Le foie'], 'Inflammation des bronches.'),
    ("Quelle partie du cerveau contrôle l'équilibre ?", 'Le cervelet', ['Le bulbe rachidien', "L'hypothalamus", 'Le cortex'], 'Le cervelet coordonne les mouvements.'),
    ('Quel est le pH normal du sang ?', 'Environ 7,4', ['Environ 5,0', 'Environ 9,0', 'Environ 2,0'], 'Légèrement basique.'),
    ('Quel est le rôle de la chlorophylle ?', 'Capter la lumière', ["Transporter l'eau", 'Digérer les aliments', 'Absorber les sels'], 'Pigment vert des chloroplastes.'),
    ('Quelle est la plus petite unité du vivant ?', 'La cellule', ["L'atome", 'La molécule', 'Le tissu'], 'Unité structurale et fonctionnelle.'),
    ("Quel type de cellule n'a pas de noyau ?", 'La bactérie', ['Le neurone', 'La cellule végétale', 'Le globule blanc'], 'Procaryote.'),
    ("Quel organe permet l'absorption des nutriments ?", "L'intestin grêle", ["L'estomac", 'Le côlon', "L'œsophage"], 'Villositsés intestinaux.'),
    ('Quel est le rôle des enzymes digestives ?', 'Accélérer la dégradation des aliments', ["Transporter l'oxygène", 'Détruire les bactéries', 'Coaguler le sang'], 'Catalyseurs biologiques.'),
    ('Quelle hormone régule le taux de sucre dans le sang ?', "L'insuline", ["L'adrénaline", 'La thyroxine', 'La testostérone'], 'Hypoglycémiante.'),
    ('Quel organe est le siège de la phonation ?', 'Le larynx', ['Le pharynx', 'La trachée', "L'œsophage"], "Les cordes vocales s'y trouvent."),
    ('Quel est le rôle des lymphocytes ?', "Défendre l'organisme", ["Transporter l'oxygène", 'Digérer les lipides', "Filtrer l'urine"], 'Immunité spécifique.'),
    ("Combien de paires de chromosomes possède l'humain ?", '23', ['22', '24', '46'], '23 paires = 46 chromosomes.'),
    ('Quel organe produit les spermatozoïdes ?', 'Le testicule', ['La prostate', "L'épididyme", 'Le pénis'], 'Glande sexuelle mâle.'),
]

def gen_svt(level, count):
    return _cycle(list(SVT_FACTS) + list(SVT_ADD2), level, count,
                  lambda f, i: mkq(f[0], f[1], f[2], f[3]))


ECO_FACTS = list({f[0]: f for f in (ECO_FACTS + ECO_EXTRA)}.values())


def gen_eco(level, count):
    """Faits + calculs économiques procéduraux (réponses calculées)."""
    items = _cycle(ECO_FACTS, level, min(count, len(ECO_FACTS)),
                   lambda f, i: mkq(f[0], f[1], f[2], f[3]))
    guard = 0
    while len(items) < count and guard < count * 60:
        guard += 1
        k = rnd.randrange(6)
        try:
            if k == 0:      # bénéfice
                pa = rnd.randrange(500, 5000, 100); qte = rnd.randint(2, 40)
                cout = rnd.randrange(300, pa, 50)
                ben = (pa - cout) * qte
                items.append(mkq(
                    f"Un commerçant achète un article {_fmt(cout)} F et le revend {_fmt(pa)} F. "
                    f"Quel est son bénéfice total pour {qte} articles ?",
                    f"{_fmt(ben)} F", [f"{_fmt(pa*qte)} F", f"{_fmt(cout*qte)} F", f"{_fmt(ben//2)} F"],
                    f"Bénéfice unitaire = {_fmt(pa)} − {_fmt(cout)} = {_fmt(pa-cout)} F ; "
                    f"total = {_fmt(pa-cout)} × {qte} = {_fmt(ben)} F"))
            elif k == 1:    # pourcentage de réduction
                prix = rnd.randrange(1000, 20000, 500); pct = rnd.choice([5, 10, 15, 20, 25, 30, 40, 50])
                red = prix * pct // 100
                items.append(mkq(f"Un article coûte {_fmt(prix)} F. Il est soldé à −{pct} %. Quel est le nouveau prix ?",
                                 f"{_fmt(prix-red)} F", [f"{_fmt(red)} F", f"{_fmt(prix)} F", f"{_fmt(prix+red)} F"],
                                 f"Réduction = {_fmt(prix)} × {pct}/100 = {_fmt(red)} F ; "
                                 f"prix = {_fmt(prix)} − {_fmt(red)} = {_fmt(prix-red)} F"))
            elif k == 2:    # intérêt simple
                cap = rnd.randrange(10000, 500000, 10000); taux = rnd.choice([2, 3, 5, 6, 8, 10]); ans = rnd.randint(1, 5)
                interet = cap * taux * ans // 100
                items.append(mkq(
                    f"Un capital de {_fmt(cap)} F est placé à {taux} % par an pendant {ans} an(s). "
                    f"Quel est l'intérêt simple produit ?",
                    f"{_fmt(interet)} F", [f"{_fmt(cap*taux//100)} F", f"{_fmt(interet*2)} F", f"{_fmt(cap+interet)} F"],
                    f"I = C × t × n / 100 = {_fmt(cap)} × {taux} × {ans} / 100 = {_fmt(interet)} F"))
            elif k == 3:    # TVA
                ht = rnd.randrange(1000, 50000, 500); tva = rnd.choice([18, 20])
                ttc = ht + ht * tva // 100
                items.append(mkq(f"Un produit coûte {_fmt(ht)} F hors taxe. Avec une TVA de {tva} %, quel est le prix TTC ?",
                                 f"{_fmt(ttc)} F", [f"{_fmt(ht*tva//100)} F", f"{_fmt(ht)} F", f"{_fmt(ttc+ht//10)} F"],
                                 f"TVA = {_fmt(ht)} × {tva}/100 = {_fmt(ht*tva//100)} F ; "
                                 f"TTC = {_fmt(ht)} + {_fmt(ht*tva//100)} = {_fmt(ttc)} F"))
            elif k == 4:    # variation en %
                v1 = rnd.randrange(1000, 10000, 500); pct = rnd.choice([10, 20, 25, 50])
                v2 = v1 + v1 * pct // 100
                var = round((v2 - v1) * 100 / v1, 1)
                items.append(mkq(f"Le chiffre d'affaires passe de {_fmt(v1)} F à {_fmt(v2)} F. Quelle est la variation en % ?",
                                 f"+{_fmt(var)} %", [f"+{_fmt(var*2)} %", f"{_fmt(v2-v1)} %", f"+{_fmt(round(var/2,1))} %"],
                                 f"Variation = ({_fmt(v2)} − {_fmt(v1)}) / {_fmt(v1)} × 100 = {_fmt(var)} %"))
            else:           # part en %
                tot = rnd.randrange(1000, 20000, 500); part = tot * rnd.choice([10, 20, 25, 40]) // 100
                pct = round(part * 100 / tot, 1)
                items.append(mkq(f"Sur un budget de {_fmt(tot)} F, une famille dépense {_fmt(part)} F en loyer. "
                                 f"Quelle part du budget cela représente-t-il ?",
                                 f"{_fmt(pct)} %", [f"{_fmt(round(pct*2,1))} %", f"{_fmt(part)} %", f"{_fmt(round(pct/2,1))} %"],
                                 f"Part = {_fmt(part)} / {_fmt(tot)} × 100 = {_fmt(pct)} %"))
        except Exception:
            continue
    return items[:count]


INFO_FACTS = list({f[0]: f for f in (INFO_FACTS + INFO_EXTRA)}.values())


def gen_info(level, count):
    """Faits + calculs réels : conversions de base, puissances de 2, unités de stockage."""
    items = _cycle(INFO_FACTS, level, min(count, len(INFO_FACTS)),
                   lambda f, i: mkq(f[0], f[1], f[2], f[3]))
    g = 0
    while len(items) < count and g < count * 60:
        g += 1
        k = rnd.randrange(5)
        try:
            if k == 0:      # binaire -> décimal
                n = rnd.randint(1, 255)
                b = bin(n)[2:]
                faux = [str(n + 1), str(n - 1), str(n + 2)]
                items.append(mkq(f"Que vaut le nombre binaire {b} en décimal ?", str(n), faux,
                                 f"{b}₂ = {n}₁₀"))
            elif k == 1:    # décimal -> hexadécimal
                n = rnd.randint(16, 4095)
                h = format(n, "X")
                faux = [format(n + 1, "X"), format(n - 1, "X"), format(n + 16, "X")]
                items.append(mkq(f"Quelle est l'écriture hexadécimale de {n} ?", h, faux,
                                 f"{n}₁₀ = {h}₁₆"))
            elif k == 2:    # puissance de 2
                e = rnd.randint(4, 16)
                v = 2 ** e
                items.append(mkq(f"Combien vaut 2^{e} ?", str(v),
                                 [str(v * 2), str(v // 2), str(v + 2)],
                                 f"2^{e} = {v}"))
            elif k == 3:    # conversion d'unités
                ko = rnd.choice([1, 2, 4, 8, 16, 32, 64])
                items.append(mkq(f"Combien d'octets contient {ko} Ko (1 Ko = 1024 o) ?",
                                 str(ko * 1024), [str(ko * 1000), str(ko * 1024 * 1024), str(ko * 8)],
                                 f"{ko} × 1024 = {ko*1024} octets"))
            else:           # addition binaire
                a, b2 = rnd.randint(1, 60), rnd.randint(1, 60)
                items.append(mkq(f"Que vaut {bin(a)[2:]}₂ + {bin(b2)[2:]}₂ en binaire ?",
                                 bin(a + b2)[2:], [bin(a + b2 + 1)[2:], bin(a + b2 - 1)[2:], bin(a * b2)[2:]],
                                 f"{a} + {b2} = {a+b2} soit {bin(a+b2)[2:]}₂"))
        except Exception:
            continue
    return items[:count]


# ─────────────────────────────────────────────────────────────
#  LANGUES : anglais, espagnol, arabe
# ─────────────────────────────────────────────────────────────
VERBES_EN = {
    "be": ("was/were", "been"), "go": ("went", "gone"), "have": ("had", "had"),
    "do": ("did", "done"), "see": ("saw", "seen"), "take": ("took", "taken"),
    "make": ("made", "made"), "come": ("came", "come"), "give": ("gave", "given"),
    "know": ("knew", "known"), "write": ("wrote", "written"), "speak": ("spoke", "spoken"),
    "eat": ("ate", "eaten"), "drink": ("drank", "drunk"), "run": ("ran", "run"),
    "read": ("read", "read"), "buy": ("bought", "bought"), "think": ("thought", "thought"),
    "bring": ("brought", "brought"), "teach": ("taught", "taught"),
}
VOCAB_EN = [
    ("school", "école"), ("book", "livre"), ("teacher", "professeur"), ("student", "élève"),
    ("water", "eau"), ("house", "maison"), ("friend", "ami"), ("family", "famille"),
    ("market", "marché"), ("money", "argent"), ("work", "travail"), ("city", "ville"),
    ("morning", "matin"), ("night", "nuit"), ("table", "table"), ("chair", "chaise"),
    ("bread", "pain"), ("child", "enfant"), ("world", "monde"), ("country", "pays"),
    ("to learn", "apprendre"), ("to write", "écrire"), ("to read", "lire"), ("to speak", "parler"),
]
VOCAB_EN2 = [
    ("school bag", "cartable"), ("pencil", "crayon"), ("paper", "papier"), ("window", "fenêtre"),
    ("door", "porte"), ("floor", "sol"), ("river", "rivière"), ("sea", "mer"),
    ("mountain", "montagne"), ("tree", "arbre"), ("flower", "fleur"), ("rain", "pluie"),
    ("wind", "vent"), ("sun", "soleil"), ("moon", "lune"), ("star", "étoile"),
    ("road", "route"), ("car", "voiture"), ("plane", "avion"), ("train", "train"),
    ("boat", "bateau"), ("doctor", "médecin"), ("nurse", "infirmière"), ("police", "police"),
    ("market", "marché"), ("shop", "magasin"), ("price", "prix"), ("cheap", "bon marché"),
    ("expensive", "cher"), ("happy", "heureux"), ("sad", "triste"), ("tired", "fatigué"),
    ("hungry", "affamé"), ("easy", "facile"), ("difficult", "difficile"), ("big", "grand"),
    ("small", "petit"), ("fast", "rapide"), ("slow", "lent"), ("hot", "chaud"),
    ("cold", "froid"), ("young", "jeune"), ("old", "vieux"), ("to run", "courir"),
    ("to eat", "manger"), ("to drink", "boire"), ("to sleep", "dormir"), ("to work", "travailler"),
    ("to help", "aider"), ("to answer", "répondre"), ("to ask", "demander"), ("to open", "ouvrir"),
    ("to close", "fermer"), ("to buy", "acheter"), ("to sell", "vendre"), ("to play", "jouer"),
]
VOCAB_ES2 = [
    ("bolígrafo", "stylo"), ("papel", "papier"), ("ventana", "fenêtre"), ("puerta", "porte"),
    ("suelo", "sol"), ("río", "rivière"), ("mar", "mer"), ("montaña", "montagne"),
    ("árbol", "arbre"), ("flor", "fleur"), ("lluvia", "pluie"), ("viento", "vent"),
    ("sol", "soleil"), ("luna", "lune"), ("estrella", "étoile"), ("calle", "rue"),
    ("coche", "voiture"), ("avión", "avion"), ("tren", "train"), ("barco", "bateau"),
    ("médico", "médecin"), ("enfermera", "infirmière"), ("tienda", "magasin"), ("precio", "prix"),
    ("barato", "bon marché"), ("caro", "cher"), ("feliz", "heureux"), ("triste", "triste"),
    ("cansado", "fatigué"), ("hambriento", "affamé"), ("fácil", "facile"), ("difícil", "difficile"),
    ("grande", "grand"), ("pequeño", "petit"), ("rápido", "rapide"), ("lento", "lent"),
    ("caliente", "chaud"), ("frío", "froid"), ("joven", "jeune"), ("viejo", "vieux"),
    ("correr", "courir"), ("comer", "manger"), ("beber", "boire"), ("dormir", "dormir"),
    ("trabajar", "travailler"), ("ayudar", "aider"), ("responder", "répondre"), ("preguntar", "demander"),
    ("abrir", "ouvrir"), ("cerrar", "fermer"), ("comprar", "acheter"), ("vender", "vendre"),
    ("jugar", "jouer"), ("escuchar", "écouter"), ("mirar", "regarder"), ("escribir", "écrire"),
]
VOCAB_ES = [
    ("escuela", "école"), ("libro", "livre"), ("profesor", "professeur"), ("estudiante", "élève"),
    ("agua", "eau"), ("casa", "maison"), ("amigo", "ami"), ("familia", "famille"),
    ("mercado", "marché"), ("dinero", "argent"), ("trabajo", "travail"), ("ciudad", "ville"),
    ("mañana", "matin"), ("noche", "nuit"), ("mesa", "table"), ("silla", "chaise"),
    ("pan", "pain"), ("niño", "enfant"), ("mundo", "monde"), ("país", "pays"),
]
VERBES_ES = {
    "hablar": ["hablo", "hablas", "habla", "hablamos", "habláis", "hablan"],
    "comer": ["como", "comes", "come", "comemos", "coméis", "comen"],
    "vivir": ["vivo", "vives", "vive", "vivimos", "vivís", "viven"],
    "ser": ["soy", "eres", "es", "somos", "sois", "son"],
    "estar": ["estoy", "estás", "está", "estamos", "estáis", "están"],
    "tener": ["tengo", "tienes", "tiene", "tenemos", "tenéis", "tienen"],
    "ir": ["voy", "vas", "va", "vamos", "vais", "van"],
    "hacer": ["hago", "haces", "hace", "hacemos", "hacéis", "hacen"],
}
PRO_ES = ["yo", "tú", "él/ella", "nosotros", "vosotros", "ellos/ellas"]
ARA_FACTS = [
    ("Comment dit-on « école » en arabe ?", "مدرسة", ["كتاب", "ماء", "بيت"], "مدرسة (madrasa) = école."),
    ("Comment dit-on « livre » en arabe ?", "كتاب", ["مدرسة", "قلم", "باب"], "كتاب (kitab) = livre."),
    ("Comment dit-on « eau » en arabe ?", "ماء", ["خبز", "لبن", "شمس"], "ماء (ma') = eau."),
    ("Comment dit-on « maison » en arabe ?", "بيت", ["باب", "نافذة", "كرسي"], "بيت (bayt) = maison."),
    ("Comment dit-on « professeur » en arabe ?", "أستاذ", ["طالب", "طبيب", "مهندس"], "أستاذ (ustadh) = professeur."),
    ("Comment dit-on « élève » en arabe ?", "طالب", ["أستاذ", "كتاب", "قلم"], "طالب (talib) = élève."),
    ("Comment dit-on « bonjour » en arabe ?", "مرحبا", ["وداعا", "شكرا", "من فضلك"], "مرحبا (marhaba) = bonjour."),
    ("Comment dit-on « merci » en arabe ?", "شكرا", ["مرحبا", "عفوا", "نعم"], "شكرا (shukran) = merci."),
    ("Quel est le chiffre 1 en arabe ?", "واحد", ["اثنان", "ثلاثة", "أربعة"], "واحد (wahid) = un."),
    ("Quel est le chiffre 2 en arabe ?", "اثنان", ["واحد", "ثلاثة", "خمسة"], "اثنان (ithnan) = deux."),
    ("Quel est le chiffre 3 en arabe ?", "ثلاثة", ["اثنان", "أربعة", "ستة"], "ثلاثة (thalatha) = trois."),
    ("Quel est le chiffre 4 en arabe ?", "أربعة", ["ثلاثة", "خمسة", "سبعة"], "أربعة (arba'a) = quatre."),
    ("Quel est le chiffre 5 en arabe ?", "خمسة", ["أربعة", "ستة", "ثمانية"], "خمسة (khamsa) = cinq."),
    ("Quel est le chiffre 10 en arabe ?", "عشرة", ["تسعة", "ثمانية", "مئة"], "عشرة (ashara) = dix."),
    ("Comment dit-on « soleil » en arabe ?", "شمس", ["قمر", "نجم", "سماء"], "شمس (shams) = soleil."),
    ("Comment dit-on « lune » en arabe ?", "قمر", ["شمس", "نجم", "أرض"], "قمر (qamar) = lune."),
    ("Comment dit-on « ciel » en arabe ?", "سماء", ["أرض", "بحر", "جبل"], "سماء (sama') = ciel."),
    ("Comment dit-on « terre » en arabe ?", "أرض", ["سماء", "ماء", "نار"], "أرض (ard) = terre."),
    ("Comment dit-on « lumière » en arabe ?", "نور", ["ظلام", "صوت", "هواء"], "نور (nur) = lumière."),
    ("Comment dit-on « nom » en arabe ?", "اسم", ["كلمة", "جملة", "حرف"], "اسم (ism) = nom."),
    ("Comment dit-on « mot » en arabe ?", "كلمة", ["جملة", "حرف", "رقم"], "كلمة (kalima) = mot."),
    ("Comment dit-on « phrase » en arabe ?", "جملة", ["كلمة", "حرف", "كتاب"], "جملة (jumla) = phrase."),
    ("Comment dit-on « écriture » en arabe ?", "كتابة", ["قراءة", "سماع", "كلام"], "كتابة (kitaba) = écriture."),
    ("Comment dit-on « lecture » en arabe ?", "قراءة", ["كتابة", "سماع", "رسم"], "قراءة (qira'a) = lecture."),
    ("Comment dit-on « papa » en arabe ?", "أب", ["أم", "أخ", "أخت"], "أب (ab) = père."),
    ("Comment dit-on « maman » en arabe ?", "أم", ["أب", "أخ", "جد"], "أم (umm) = mère."),
    ("Comment dit-on « frère » en arabe ?", "أخ", ["أخت", "أب", "ابن"], "أخ (akh) = frère."),
    ("Comment dit-on « sœur » en arabe ?", "أخت", ["أخ", "أم", "بنت"], "أخت (ukht) = sœur."),
    ("Comment dit-on « ami » en arabe ?", "صديق", ["عدو", "جار", "أستاذ"], "صديق (sadiq) = ami."),
    ("Comment dit-on « ville » en arabe ?", "مدينة", ["قرية", "شارع", "بيت"], "مدينة (madina) = ville."),
    ("Comment dit-on « route » en arabe ?", "طريق", ["شارع", "مدينة", "باب"], "طريق (tariq) = route."),
    ("Comment dit-on « porte » en arabe ?", "باب", ["نافذة", "جدار", "سقف"], "باب (bab) = porte."),
    ("Comment dit-on « pain » en arabe ?", "خبز", ["ماء", "لبن", "لحم"], "خبز (khubz) = pain."),
    ("Comment dit-on « lait » en arabe ?", "لبن", ["ماء", "خبز", "شاي"], "لبن (laban) = lait."),
    ("Comment dit-on « santé » en arabe ?", "صحة", ["مرض", "طب", "دواء"], "صحة (sihha) = santé."),
    ("Comment dit-on « médecin » en arabe ?", "طبيب", ["طالب", "أستاذ", "مهندس"], "طبيب (tabib) = médecin."),
    ("Comment dit-on « pays » en arabe ?", "بلد", ["مدينة", "قرية", "بيت"], "بلد (balad) = pays."),
    ("Comment dit-on « travail » en arabe ?", "عمل", ["راحة", "لعب", "نوم"], "عمل ('amal) = travail."),
    ("Comment dit-on « science » en arabe ?", "علم", ["جهل", "فن", "لعب"], "علم ('ilm) = science."),
    ("Comment dit-on « histoire » en arabe ?", "تاريخ", ["جغرافيا", "رياضيات", "فن"], "تاريخ (tarikh) = histoire."),
]


def gen_eng(level, count):
    items = []
    pool = []
    for v, (past, pp) in VERBES_EN.items():
        pool.append(("past", v, past))
        pool.append(("pp", v, pp))
    rnd.shuffle(pool)
    li = LVL_IDX[level]
    for kind, v, ans in pool:
        if len(items) >= count * 2 // 3:
            break
        faux = [x[1][0] for x in VERBES_EN.items() if x[0] != v]
        rnd.shuffle(faux)
        if kind == "past":
            items.append(mkq(f"What is the simple past of « {v} » ?", ans, faux[:3],
                             f"{v} → {ans} (simple past)"))
        else:
            items.append(mkq(f"What is the past participle of « {v} » ?", ans, faux[:3],
                             f"{v} → {ans} (past participle)"))
    ALL_EN = list({w: (w, f) for (w, f) in (VOCAB_EN + VOCAB_EN2)}.values())
    vocab = list(ALL_EN)
    rnd.shuffle(vocab)
    i = 0
    while len(items) < count:
        w, fr = vocab[i % len(vocab)]
        faux = [x[1] for x in ALL_EN if x[1] != fr]
        rnd.shuffle(faux)
        items.append(mkq(f"Que signifie « {w} » en français ?", fr, faux[:3], f"{w} = {fr}"))
        i += 1
    return items[:count]


def gen_es(level, count):
    items = []
    combos = [(v, i) for v in VERBES_ES for i in range(6)]
    rnd.shuffle(combos)
    for (v, i) in combos:
        if len(items) >= count * 2 // 3:
            break
        bon = VERBES_ES[v][i]
        faux = [x for x in VERBES_ES[v] if x != bon]
        rnd.shuffle(faux)
        items.append(mkq(f"Conjugue « {v} » au présent : {PRO_ES[i]} ___", bon, faux[:3],
                         f"{v} → {PRO_ES[i]} {bon}"))
    ALL_ES = list({w: (w, f) for (w, f) in (VOCAB_ES + VOCAB_ES2)}.values())
    vocab = list(ALL_ES)
    rnd.shuffle(vocab)
    i = 0
    while len(items) < count:
        w, fr = vocab[i % len(vocab)]
        faux = [x[1] for x in ALL_ES if x[1] != fr]
        rnd.shuffle(faux)
        items.append(mkq(f"Que signifie « {w} » en français ?", fr, faux[:3], f"{w} = {fr}"))
        i += 1
    return items[:count]



ARA_EXTRA = [
    ("صباح", ["soir", "nuit", "midi"], "matin"), ("مساء", ["matin", "nuit", "midi"], "soir"),
    ("ليل", ["jour", "matin", "midi"], "nuit"), ("نهار", ["nuit", "soir", "matin"], "jour"),
    ("قلم", ["livre", "table", "chaise"], "stylo"), ("ورقة", ["crayon", "table", "mur"], "feuille"),
    ("كرسي", ["table", "lit", "porte"], "chaise"), ("سرير", ["chaise", "table", "sol"], "lit"),
    ("نافذة", ["porte", "mur", "toit"], "fenêtre"), ("سقف", ["sol", "mur", "porte"], "plafond"),
    ("بحر", ["rivière", "désert", "montagne"], "mer"), ("نهر", ["mer", "lac", "pluie"], "fleuve"),
    ("جبل", ["mer", "forêt", "désert"], "montagne"), ("شجرة", ["fleur", "herbe", "fruit"], "arbre"),
    ("زهرة", ["arbre", "feuille", "racine"], "fleur"), ("مطر", ["neige", "vent", "soleil"], "pluie"),
    ("ريح", ["pluie", "neige", "feu"], "vent"), ("ثلج", ["pluie", "vent", "feu"], "neige"),
    ("نار", ["eau", "terre", "air"], "feu"), ("هواء", ["eau", "feu", "terre"], "air"),
    ("خبز", ["riz", "viande", "poisson"], "pain"), ("لحم", ["pain", "lait", "eau"], "viande"),
    ("سمك", ["viande", "pain", "lait"], "poisson"), ("تفاحة", ["orange", "banane", "raisin"], "pomme"),
    ("موز", ["pomme", "orange", "datte"], "banane"), ("تمر", ["raisin", "figue", "olive"], "datte"),
    ("كتاب", ["cahier", "stylo", "sac"], "livre"), ("دفتر", ["livre", "stylo", "table"], "cahier"),
    ("حقيبة", ["livre", "cahier", "stylo"], "cartable"), ("سبورة", ["chaise", "table", "porte"], "tableau"),
    ("قسم", ["maison", "rue", "marché"], "classe"), ("مكتبة", ["école", "marché", "hôpital"], "bibliothèque"),
    ("مستشفى", ["école", "marché", "mosquée"], "hôpital"), ("سوق", ["école", "hôpital", "maison"], "marché"),
    ("مسجد", ["école", "hôpital", "marché"], "mosquée"), ("طريق", ["maison", "porte", "mur"], "route"),
    ("سيارة", ["vélo", "bateau", "avion"], "voiture"), ("طائرة", ["voiture", "vélo", "train"], "avion"),
    ("قطار", ["avion", "voiture", "vélo"], "train"), ("سفينة", ["avion", "train", "voiture"], "bateau"),
    ("أحد", ["lundi", "mardi", "dimanche"], "dimanche"), ("اثنين", ["dimanche", "mardi", "jeudi"], "lundi"),
    ("ثلاثاء", ["lundi", "mercredi", "vendredi"], "mardi"), ("أربعاء", ["mardi", "jeudi", "samedi"], "mercredi"),
    ("خميس", ["mercredi", "vendredi", "dimanche"], "jeudi"), ("جمعة", ["jeudi", "samedi", "lundi"], "vendredi"),
    ("سبت", ["vendredi", "dimanche", "mardi"], "samedi"), ("سنة", ["mois", "jour", "heure"], "année"),
    ("شهر", ["année", "jour", "semaine"], "mois"), ("أسبوع", ["mois", "année", "jour"], "semaine"),
    ("يوم", ["heure", "mois", "année"], "jour"), ("ساعة", ["minute", "jour", "mois"], "heure"),
    ("دقيقة", ["heure", "jour", "mois"], "minute"), ("وقت", ["lieu", "gens", "chose"], "temps"),
    ("رجل", ["femme", "enfant", "vieillard"], "homme"), ("امرأة", ["homme", "enfant", "jeune"], "femme"),
    ("ولد", ["fille", "homme", "femme"], "garçon"), ("بنت", ["garçon", "homme", "femme"], "fille"),
    ("معلم", ["élève", "médecin", "ingénieur"], "enseignant"), ("مهندس", ["médecin", "élève", "professeur"], "ingénieur"),
    ("تلميذ", ["professeur", "médecin", "paysan"], "élève"), ("فلاح", ["professeur", "médecin", "ingénieur"], "paysan"),
    ("مارس", ["mars", "mai", "juin"], "mars"), ("يناير", ["janvier", "juillet", "août"], "janvier"),
    ("فبراير", ["février", "septembre", "octobre"], "février"), ("أبريل", ["avril", "novembre", "décembre"], "avril"),
]

def gen_ara(level, count):
    """Deux gabarits : mot arabe → français, et français → mot arabe."""
    items = []
    facts = list(ARA_FACTS)
    rnd.shuffle(facts)
    for f in facts:
        items.append(mkq(f[0], f[1], f[2], f[3]))
        if len(items) >= count: return items[:count]
    # gabarit inversé sur le vocabulaire complémentaire
    pool = list(ARA_EXTRA)
    rnd.shuffle(pool)
    i = 0
    while len(items) < count and pool:
        w, faux_fr, fr = pool[i % len(pool)]
        faux = [x for x in faux_fr]
        rnd.shuffle(faux)
        items.append(mkq(f"Comment dit-on « {fr} » en arabe ?", w, faux[:3],
                         f"« {fr} » se dit {w} en arabe."))
        i += 1
        if i > count * 3: break
    return items[:count]


GENERATORS = {
    "math": gen_math, "fr": gen_fr, "phys": gen_phys, "chim": gen_chim,
    "svt": gen_svt, "hist": gen_hist, "geo": gen_geo, "eng": gen_eng,
    "info": gen_info, "eco": gen_eco, "es": gen_es, "ara": gen_ara,
}


def build(cible_par_matiere_niveau):
    """Construit {(sujet, niveau): [items]} en garantissant le même nombre partout."""
    out = {}
    for code, _nom in SUBJECTS:
        gen = GENERATORS[code]
        for lvl in LEVELS:
            items = []
            vus = set()
            essais = 0
            while len(items) < cible_par_matiere_niveau and essais < 40:
                essais += 1
                batch = gen(lvl, cible_par_matiere_niveau + 40)
                for it in batch:
                    key = (it["q"], it["o"][it["i"]])
                    if key in vus:
                        continue
                    vus.add(key)
                    items.append(it)
                    if len(items) >= cible_par_matiere_niveau:
                        break
            out[(code, lvl)] = items
    return out
