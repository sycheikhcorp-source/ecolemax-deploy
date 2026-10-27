# -*- coding: utf-8 -*-
"""
ÉcoleMax — moteur de réponse locale.
Répond instantanément, sans réseau, aux questions courantes :
calculs, équations, pourcentages, conjugaison, capitales, faits vérifiés.
Utilisé comme dernier recours de la chaîne IA (et comme accélérateur hors ligne).
"""
import ast as _ast
import math as _math
import operator as _op
import re as _re
import unicodedata as _ud

import content_gen as G

# ─────────────────────────────────────────────────────────────
# Index de faits vérifiés
# ─────────────────────────────────────────────────────────────
FAITS = []          # [(question, reponse, explication)]
_INDEX = []         # [(mots, idx)]

_STOP = set("""
le la les un une des du de d au aux a et ou ou est sont etait etaient quel quelle quels quelles
que qui quoi dont ou comment pourquoi combien quand dans sur sous pour par avec sans ce cet cette ces
son sa ses leur leurs mon ma mes ton ta tes notre nos votre vos il elle ils elles on nous vous je tu
the of and is are what which who how why when where a an to in on for with
""".split())


def _norm(t):
    t = _ud.normalize("NFD", (t or "").lower())
    t = "".join(c for c in t if _ud.category(c) != "Mn")
    t = _re.sub(r"[^a-z0-9\u0600-\u06FF ]+", " ", t)
    return [w for w in t.split() if len(w) > 2 and w not in _STOP]


def _ajouter(question, reponse, explication=""):
    """Ajoute un fait de façon atomique (FAITS et _INDEX restent alignés)."""
    try:
        q = str(question)
        r = reponse if isinstance(reponse, str) else ", ".join(map(str, reponse))
        e = explication if isinstance(explication, str) else ", ".join(map(str, explication))
        mots = set(_norm(" ".join([q, r, e])))
        if not mots:
            return
        FAITS.append((q, r, e))
        _INDEX.append(mots)
    except Exception:
        pass


def _construire():
    if FAITS:
        return
    for f in getattr(G, "SVT_FACTS", []):
        _ajouter(f[0], f[1], f[3] if len(f) > 3 else "")
    for f in getattr(G, "ECO_FACTS", []):
        _ajouter(f[0], f[1], f[3] if len(f) > 3 else "")
    for f in getattr(G, "INFO_FACTS", []):
        _ajouter(f[0], f[1], f[3] if len(f) > 3 else "")
    for f in getattr(G, "HIST_EXTRA2", []):
        _ajouter(f[0], f[1], f[3] if len(f) > 3 else "")
    for f in getattr(G, "GEO_EXTRA2", []):
        _ajouter(f[0], f[1], f[3] if len(f) > 3 else "")
    for f in getattr(G, "ARA_FACTS", []):
        _ajouter(f[0], f[1], f[3] if len(f) > 3 else "")
    for f in getattr(G, "ARA_EXTRA", []):
        try:
            arabe, faux, sens = f[0], f[1], f[2]
            _ajouter("Comment dit-on « %s » en arabe ?" % sens, arabe,
                     "« %s » se dit %s en arabe." % (sens, arabe))
        except Exception:
            pass
    # capitales
    for p in getattr(G, "PAYS", []):
        try:
            _ajouter("Quelle est la capitale du %s ?" % p[0], p[1],
                     "Capitale du %s (%s), monnaie : %s." % (p[0], p[2], p[3]))
        except Exception:
            pass
    # fleuves
    for f in getattr(G, "FLEUVES", []):
        try:
            _ajouter("Où se trouve le fleuve %s ?" % f[0], "%s (%s)" % (f[1], f[2]),
                     "Le %s coule en %s, principalement en %s." % (f[0], f[1], f[2]))
        except Exception:
            pass
    # montagnes
    for m in getattr(G, "MONTS", []):
        try:
            _ajouter("Dans quel pays se trouve le %s ?" % m[0], m[1],
                     "Le %s se situe en %s (%s)." % (m[0], m[1], m[2]))
        except Exception:
            pass
    # dates historiques
    for d in getattr(G, "HIST_DATES", []):
        try:
            _ajouter("En quelle année : %s ?" % d[0], str(d[1]),
                     "%s : %s." % (d[0], d[1]))
        except Exception:
            pass
    for hp in getattr(G, "HIST_PERSONNES", []):
        try:
            _ajouter("Qui est-ce ? %s" % hp[0], str(hp[1]), "%s : %s." % (hp[0], hp[1]))
        except Exception:
            pass


def chercher_fait(question, seuil=0.42):
    """Retourne (question, reponse, explication, score) du meilleur fait."""
    _construire()
    mots = set(_norm(question))
    if not mots:
        return None
    if len(FAITS) != len(_INDEX):
        return None
    best, best_score = None, 0.0
    for i, idx in enumerate(_INDEX):
        if not idx:
            continue
        inter = len(mots & idx)
        if inter == 0:
            continue
        couverture = inter / float(len(mots))
        score = couverture * (0.55 + 0.45 * min(1.0, inter / 3.0))
        if score > best_score:
            best_score, best = score, i
    if best is None or best_score < seuil:
        return None
    q, r, e = FAITS[best]
    return q, r, e, best_score


# ─────────────────────────────────────────────────────────────
# Calculs
# ─────────────────────────────────────────────────────────────
_OPS = {_ast.Add: _op.add, _ast.Sub: _op.sub, _ast.Mult: _op.mul,
        _ast.Div: _op.truediv, _ast.Pow: _op.pow, _ast.Mod: _op.mod,
        _ast.USub: _op.neg, _ast.UAdd: _op.pos, _ast.FloorDiv: _op.floordiv}


def _calc(expr):
    node = _ast.parse(expr, mode="eval").body

    def ev(n):
        if isinstance(n, _ast.Constant):
            return n.value
        if isinstance(n, _ast.BinOp):
            return _OPS[type(n.op)](ev(n.left), ev(n.right))
        if isinstance(n, _ast.UnaryOp):
            return _OPS[type(n.op)](ev(n.operand))
        raise ValueError("expression non autorisée")

    return ev(node)


def _fmt_num(x):
    if isinstance(x, float):
        if abs(x - round(x)) < 1e-9:
            return str(int(round(x)))
        return ("%.4f" % x).rstrip("0").rstrip(".")
    return str(x)


def _essai_calcul(q):
    t = q.lower()
    t = t.replace("×", "*").replace("x", "*") if _re.search(r"\d\s*[x×]\s*\d", t) else t
    t = (t.replace("÷", "/").replace("²", "^2").replace("³", "^3")
          .replace("plus", "+").replace("moins", "-").replace("fois", "*").replace("multiplié par", "*")
          .replace("divisé par", "/").replace("sur", "/"))

    # pourcentage : "combien font 15 % de 200"
    m = _re.search(r"(\d+(?:[.,]\d+)?)\s*%\s*(?:de|du|des)\s*(\d+(?:[.,]\d+)?)", t)
    if m:
        a = float(m.group(1).replace(",", "."))
        b = float(m.group(2).replace(",", "."))
        return "%s %% de %s = **%s**" % (_fmt_num(a), _fmt_num(b), _fmt_num(a * b / 100.0))

    # équation ax + b = c
    m = _re.search(r"(-?\d*)\s*([a-zA-Z])\s*([+-]\s*\d+(?:[.,]\d+)?)?\s*=\s*(-?\d+(?:[.,]\d+)?)", t)
    if m and "=" in t:
        coef = m.group(1)
        var = m.group(2)
        coef = -1.0 if coef == "-" else (1.0 if coef in ("", "+") else float(coef.replace(",", ".")))
        b = 0.0
        if m.group(3):
            b = float(m.group(3).replace(" ", "").replace(",", "."))
        c = float(m.group(4).replace(",", "."))
        if coef != 0:
            x = (c - b) / coef
            etapes = "%s%s %s = %s" % ("" if coef == 1 else _fmt_num(coef), var,
                                        ("+ " + _fmt_num(b)) if b >= 0 else ("- " + _fmt_num(-b)),
                                        _fmt_num(c))
            return ("Équation : %s\n\nOn isole %s : %s%s = %s %s\n\n**%s = %s**"
                    % (etapes, var, "" if coef == 1 else _fmt_num(coef), var, _fmt_num(c),
                       ("- " + _fmt_num(b)) if b >= 0 else ("+ " + _fmt_num(-b)),
                       var, _fmt_num(x)))

    # expression pure
    expr = _re.sub(r"[^0-9+\-*/().^ %]", "", t)
    expr = expr.replace("^", "**").strip()
    if not expr or not _re.search(r"\d", expr) or not _re.search(r"[+\-*/]", expr):
        return None
    try:
        val = _calc(expr)
        return "**%s = %s**" % (expr.replace("**", "^"), _fmt_num(val))
    except Exception:
        return None


# ─────────────────────────────────────────────────────────────
# Conjugaison
# ─────────────────────────────────────────────────────────────
_TEMPS = {"présent": "présent", "present": "présent", "imparfait": "imparfait",
          "futur": "futur", "conditionnel": "conditionnel", "subjonctif": "subjonctif"}
_PERS = ["je", "tu", "il / elle", "nous", "vous", "ils / elles"]


def _essai_conjugaison(q):
    t = q.lower()
    if not _re.search(r"conjugu|conjugaison|\bverbe\b", t):
        return None
    temps = None
    for k, v in _TEMPS.items():
        if k in t:
            temps = v
            break
    if not temps:
        temps = "présent"
    m = _re.search(r"(?:verbe\s+|conjugue\s+(?:le\s+verbe\s+)?)([a-zà-ÿéèêëîïôöûüç\-]+)", t)
    if not m:
        return None
    verbe = m.group(1)
    table = getattr(G, "VERBES_FR", {})
    if verbe not in table or temps not in table[verbe]:
        return None
    formes = table[verbe][temps]
    lignes = ["- **%s** %s" % (p, f) for p, f in zip(_PERS, formes)]
    return "Conjugaison de **%s** au **%s** :\n\n%s" % (verbe, temps, "\n".join(lignes))


# ─────────────────────────────────────────────────────────────
# Point d'entrée
# ─────────────────────────────────────────────────────────────
def repondre_localement(question):
    q = (question or "").strip()
    if not q:
        return "Pose-moi une question : un calcul, une définition, une date, une règle de grammaire…"

    for essai in (_essai_calcul, _essai_conjugaison):
        try:
            r = essai(q)
        except Exception:
            r = None
        if r:
            return r

    try:
        hit = chercher_fait(q)
    except Exception:
        hit = None
    if hit:
        hq, hr, he, _score = hit
        txt = "**Réponse : %s**" % hr
        if he:
            txt += "\n\n%s" % he
        if hq and _norm(hq) != _norm(q):
            txt += "\n\n_Question liée : %s_" % hq
        return txt

    return ("Je n'ai pas trouvé de réponse précise hors ligne. Reformule ta question "
            "en une phrase courte (ex. « Quelle est la capitale du Mali ? », « Combien font 25 % de 80 ? »). "
            "Le professeur IA en ligne répondra en détail dès que la connexion le permet.")


if __name__ == "__main__":
    tests = [
        "Combien font 21 × 3 ?",
        "25 % de 80",
        "Résous 3x + 5 = 20",
        "Quelle est la capitale du Sénégal ?",
        "Quelle est la capitale du Mali ?",
        "Qui était Mansa Moussa ?",
        "Que signifie HTML ?",
        "Quelle est la monnaie du Sénégal ?",
        "Conjugue le verbe être au présent",
        "Conjugue aller au futur",
        "Quel organe pompe le sang ?",
        "En quelle année l'indépendance du Sénégal ?",
    ]
    for t in tests:
        print("Q:", t)
        print("  →", repondre_localement(t).replace("\n", " / ")[:170])
        print()
