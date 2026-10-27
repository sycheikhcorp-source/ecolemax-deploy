# -*- coding: utf-8 -*-
"""
ÉcoleMax — construction du contenu (v3).

Objectif :
  • un nombre d'exercices STRICTEMENT IDENTIQUE pour chacun des 14 niveaux ;
  • ce nombre poussé au maximum que chaque matière permet ;
  • options stockées en JSON + index de la bonne réponse (plus d'analyse regex) ;
  • quiz : même logique par catégorie.

Le contenu est vérifié : chaque réponse est calculée ou issue d'une table de faits.
"""
import datetime
import json
import os
import random
import shutil
import sqlite3
import sys

import content_gen as G

DB = os.environ.get("DB_PATH", os.path.join(os.path.dirname(os.path.abspath(__file__)), "ecolemax.db"))
NOM = dict(G.SUBJECTS)
CIBLE = int(sys.argv[1]) if len(sys.argv) > 1 else 1200


def difficulte(level):
    i = G.LVL_IDX[level]
    if i <= 1:
        return "facile"
    if i <= 3:
        return random.choice(["facile", "facile", "moyen"])
    if i <= 5:
        return random.choice(["facile", "moyen", "moyen"])
    if i <= 7:
        return random.choice(["moyen", "moyen", "difficile"])
    return random.choice(["moyen", "difficile", "difficile"])


def colonnes(c, table):
    return [r[1] for r in c.execute("PRAGMA table_info(%s)" % table)]


def main():
    random.seed(20261027)
    print("Génération des exercices (cible %d/matière/niveau)…" % CIBLE)
    ex = G.build(CIBLE)

    print("Génération des quiz (tirage différent)…")
    random.seed(77017)
    G.rnd.seed(77017)
    qu = G.build(CIBLE)

    # Nombre retenu par matière = le plus petit des 14 niveaux (garantit l'égalité)
    dispo = {code: min(len(ex[(code, l)]) for l in G.LEVELS) for code, _ in G.SUBJECTS}
    dispo_q = {code: min(len(qu[(code, l)]) for l in G.LEVELS) for code, _ in G.SUBJECTS}

    total = sum(dispo.values())
    print("\n--- Répartition (identique sur les 14 niveaux) ---")
    for code, nom in G.SUBJECTS:
        print("  %-22s exercices %5d   quiz %5d" % (nom, dispo[code], dispo_q[code]))
    print("  %-22s %5d" % ("TOTAL PAR NIVEAU", total))
    print("  %-22s %5d" % ("TOTAL EXERCICES", total * len(G.LEVELS)))

    # ── sauvegarde ──
    bak = DB + ".bak3-" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    shutil.copy(DB, bak)
    print("\nSauvegarde :", bak)

    c = sqlite3.connect(DB, timeout=120)
    c.execute("PRAGMA journal_mode=WAL")
    c.execute("PRAGMA synchronous=OFF")

    # ── schéma : colonne options ──
    for table in ("exercises", "quiz"):
        if "options" not in colonnes(c, table):
            c.execute("ALTER TABLE %s ADD COLUMN options TEXT DEFAULT ''" % table)
            print("✅ %s.options ajoutée" % table)

    # on retire les index uniques hérités (on va tout réinsérer proprement)
    for idx in ("ux_ex_q", "ux_quiz_q", "idx_ex_combo", "idx_quiz_cat2"):
        c.execute("DROP INDEX IF EXISTS %s" % idx)

    c.execute("DELETE FROM exercises")
    c.execute("DELETE FROM quiz")
    c.commit()
    print("Tables pédagogiques vidées (les comptes élèves sont intacts).")

    # ── exercices ──
    n = 0
    for code, nom in G.SUBJECTS:
        k = dispo[code]
        for level in G.LEVELS:
            lot = ex[(code, level)][:k]
            lignes = []
            for it in lot:
                lignes.append((
                    code,
                    "%s — %s" % (nom, level),
                    level,
                    "qcm",
                    it["q"],
                    it["o"][it["i"]],
                    it["e"],
                    difficulte(level),
                    json.dumps(it["o"], ensure_ascii=False),
                    it["i"],
                ))
            c.executemany(
                "INSERT INTO exercises (sujet_code,titre,niveau,type,question,reponse,"
                "explication,difficulte,options,bonne_index) VALUES (?,?,?,?,?,?,?,?,?,?)", lignes)
            n += len(lignes)
    c.commit()
    print("✅ exercices : %d" % n)

    # ── quiz (dédoublonné : la table quiz n'a pas de notion de niveau) ──
    vus = set()
    nq = 0
    for code, nom in G.SUBJECTS:
        k = dispo_q[code]
        lignes = []
        for level in G.LEVELS:
            for it in qu[(code, level)][:k]:
                cle = (nom, it["q"])
                if cle in vus:
                    continue
                vus.add(cle)
                lignes.append((
                    nom, it["q"], it["i"], it["e"], difficulte(level),
                    json.dumps(it["o"], ensure_ascii=False),
                ))
        c.executemany(
            "INSERT INTO quiz (categorie,question,reponse,explication,difficulte,options) "
            "VALUES (?,?,?,?,?,?)", lignes)
        nq += len(lignes)
    c.commit()
    print("✅ quiz : %d" % nq)

    # ── index (rapidité des filtres) ──
    c.execute("CREATE INDEX IF NOT EXISTS idx_ex_combo ON exercises(niveau,sujet_code,difficulte)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_ex_sujet ON exercises(sujet_code)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_ex_niv ON exercises(niveau)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_quiz_cat ON quiz(categorie,difficulte)")
    c.commit()

    # ── vérification ──
    print("\n--- Vérification ---")
    vals = []
    for r in c.execute("SELECT niveau, COUNT(*) FROM exercises GROUP BY niveau ORDER BY niveau"):
        print("  %-16s %6d" % (r[0], r[1]))
        vals.append(r[1])
    print("  min = %d | max = %d | %s" % (
        min(vals), max(vals), "✅ IDENTIQUES sur les 14 niveaux" if min(vals) == max(vals) else "❌"))

    print("\n  quiz par catégorie :")
    for r in c.execute("SELECT categorie, COUNT(*) FROM quiz GROUP BY categorie ORDER BY COUNT(*) DESC"):
        print("    %-16s %6d" % (r[0], r[1]))

    mauvais = 0
    for opt, rep in c.execute("SELECT options, reponse FROM exercises"):
        try:
            o = json.loads(opt)
            if len(o) != 4 or rep not in o or len(set(o)) != 4:
                mauvais += 1
        except Exception:
            mauvais += 1
    print("\n  options invalides : %d" % mauvais)

    c.execute("VACUUM")
    c.close()
    print("\n✅ Terminé")


if __name__ == "__main__":
    main()
