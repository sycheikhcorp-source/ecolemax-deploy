# -*- coding: utf-8 -*-
"""
ÉcoleMax — construction du contenu équilibré.
Remplit les tables `exercises` et `quiz` avec un contenu vérifié,
au même nombre d'exercices sur chacun des 14 niveaux scolaires.
"""
import json
import os
import sqlite3
import sys
import random
import shutil
import datetime

import content_gen as G

DB = os.environ.get("DB_PATH", os.path.join(os.path.dirname(os.path.abspath(__file__)), "ecolemax.db"))
NOM_MATIERE = dict(G.SUBJECTS)


def diff_pour(level):
    li = G.LVL_IDX[level]
    if li <= 1:
        return "facile"
    if li <= 3:
        return random.choice(["facile", "facile", "moyen"])
    if li <= 5:
        return random.choice(["facile", "moyen", "moyen"])
    if li <= 7:
        return random.choice(["moyen", "moyen", "difficile"])
    return random.choice(["moyen", "difficile", "difficile"])


def main():
    cible = int(sys.argv[1]) if len(sys.argv) > 1 else 500
    print("Génération en cours (cible par matière/niveau = %d)…" % cible)

    random.seed(20261027)
    res_ex = G.build(cible)

    # quiz : nouveau tirage pour obtenir des questions différentes
    random.seed(77017)
    G.rnd.seed(77017)
    for k in list(G.GENERATORS):
        pass
    res_quiz = G.build(cible)

    # Nombre retenu par matière = minimum atteint sur tous les niveaux
    par_matiere = {}
    for code, _ in G.SUBJECTS:
        par_matiere[code] = min(len(res_ex[(code, l)]) for l in G.LEVELS)

    total_par_niveau = sum(par_matiere.values())
    print("\n--- Répartition retenue (identique sur les 14 niveaux) ---")
    for code, nom in G.SUBJECTS:
        print("  %-22s %5d" % (nom, par_matiere[code]))
    print("  %-22s %5d" % ("TOTAL PAR NIVEAU", total_par_niveau))
    print("  %-22s %5d" % ("TOTAL EXERCICES", total_par_niveau * len(G.LEVELS)))

    # Sauvegarde
    backup = DB + ".avant-contenu-" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    shutil.copy(DB, backup)
    print("\nSauvegarde :", backup)

    c = sqlite3.connect(DB, timeout=60)
    c.execute("PRAGMA journal_mode=WAL")

    # Colonne options (migration douce)
    cols = [r[1] for r in c.execute("PRAGMA table_info(exercises)")]
    if "options" not in cols:
        c.execute("ALTER TABLE exercises ADD COLUMN options TEXT DEFAULT ''")
        print("✅ colonne exercises.options ajoutée")
    cols = [r[1] for r in c.execute("PRAGMA table_info(quiz)")]
    if "options" not in cols:
        c.execute("ALTER TABLE quiz ADD COLUMN options TEXT DEFAULT ''")
        print("✅ colonne quiz.options ajoutée")

    # Remplacement du contenu pédagogique (jamais les données élèves)
    c.execute("DELETE FROM exercises")
    c.execute("DELETE FROM quiz")
    c.commit()

    n_ex = 0
    for code, nom in G.SUBJECTS:
        n = par_matiere[code]
        for level in G.LEVELS:
            items = res_ex[(code, level)][:n]
            rows = []
            for it in items:
                bon = it["o"][it["i"]]
                rows.append((
                    code,
                    "%s — %s" % (nom, level),
                    level,
                    "qcm",
                    it["q"],
                    bon,
                    it["e"],
                    diff_pour(level),
                    json.dumps(it["o"], ensure_ascii=False),
                ))
            c.executemany(
                "INSERT INTO exercises (sujet_code,titre,niveau,type,question,reponse,"
                "explication,difficulte,options) VALUES (?,?,?,?,?,?,?,?,?)", rows)
            n_ex += len(rows)
    c.commit()
    print("✅ exercices insérés :", n_ex)

    n_qz = 0
    for code, nom in G.SUBJECTS:
        n = par_matiere[code]
        cat = nom
        for level in G.LEVELS:
            items = res_quiz[(code, level)][:n]
            rows = []
            for it in items:
                rows.append((
                    cat,
                    it["q"],
                    it["i"],
                    it["e"],
                    diff_pour(level),
                    json.dumps(it["o"], ensure_ascii=False),
                ))
            c.executemany(
                "INSERT INTO quiz (categorie,question,reponse,explication,difficulte,options) "
                "VALUES (?,?,?,?,?,?)", rows)
            n_qz += len(rows)
    c.commit()
    print("✅ quiz insérés :", n_qz)

    # Index pour la rapidité
    for sql in [
        "CREATE INDEX IF NOT EXISTS idx_ex_combo ON exercises(niveau,sujet_code,difficulte)",
        "CREATE INDEX IF NOT EXISTS idx_quiz_cat2 ON quiz(categorie,difficulte)",
    ]:
        try:
            c.execute(sql)
        except Exception:
            pass
    c.commit()

    # Vérification
    print("\n--- Vérification ---")
    for row in c.execute("SELECT niveau, COUNT(*) FROM exercises GROUP BY niveau ORDER BY niveau"):
        print("  %-16s %6d" % (row[0], row[1]))
    print()
    tot = c.execute("SELECT COUNT(*) FROM exercises").fetchone()[0]
    nv = c.execute("SELECT COUNT(DISTINCT niveau) FROM exercises").fetchone()[0]
    print("  exercices : %d sur %d niveaux" % (tot, nv))
    print("  quiz      : %d sur %d catégories" % (
        c.execute("SELECT COUNT(*) FROM quiz").fetchone()[0],
        c.execute("SELECT COUNT(DISTINCT categorie) FROM quiz").fetchone()[0]))
    print("\n  contrôle d'égalité par niveau :")
    vals = [r[1] for r in c.execute("SELECT niveau, COUNT(*) FROM exercises GROUP BY niveau")]
    print("   min =", min(vals), "| max =", max(vals), "|",
          "✅ IDENTIQUES" if min(vals) == max(vals) else "❌ différents")

    # Intégrité des options
    bad = 0
    for (opt, rep) in c.execute("SELECT options, reponse FROM exercises"):
        try:
            o = json.loads(opt)
            if len(o) != 4 or rep not in o or len(set(o)) != 4:
                bad += 1
        except Exception:
            bad += 1
    print("  options invalides :", bad)

    c.execute("VACUUM")
    c.close()
    print("\n✅ Terminé")


if __name__ == "__main__":
    main()
