#!/usr/bin/env python3
"""Analyse du contenu existant : exercices, quiz, langues."""
import sqlite3

c = sqlite3.connect('/home/user/deploy/ecolemax.db')

print("=== EXERCICES ===")
total = c.execute("SELECT COUNT(*) FROM exercises").fetchone()[0]
print("total:", total)
print("par sujet:")
for r in c.execute("SELECT sujet_code, COUNT(*) FROM exercises GROUP BY sujet_code ORDER BY COUNT(*) DESC"):
    print("  ", r[0], ":", r[1])
print("par niveau:")
for r in c.execute("SELECT niveau, COUNT(*) FROM exercises GROUP BY niveau"):
    print("  ", r[0], ":", r[1])

print()
print("=== QUIZ ===")
total_q = c.execute("SELECT COUNT(*) FROM quiz").fetchone()[0]
print("total:", total_q)
print("par categorie:")
for r in c.execute("SELECT categorie, COUNT(*) FROM quiz GROUP BY categorie ORDER BY COUNT(*) DESC"):
    print("  ", r[0], ":", r[1])

print()
print("=== MATIERES (sujets) ===")
for r in c.execute("SELECT code, nom FROM sujets ORDER BY ordre"):
    n_ex = c.execute("SELECT COUNT(*) FROM exercises WHERE sujet_code=?", (r[0],)).fetchone()[0]
    n_q = c.execute("SELECT COUNT(*) FROM quiz WHERE categorie=?", (r[0],)).fetchone()[0]
    print(f"  {r[0]:6s} {r[1]:15s} | exercices: {n_ex:5d} | quiz: {n_q:5d}")

print()
print("=== LANGUES IA ===")
print("fr, en, es, pt, ar, de, zh, hi, ru, ja (10 langues)")
