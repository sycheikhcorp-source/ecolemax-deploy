import sqlite3
c = sqlite3.connect('/home/user/deploy/ecolemax.db')

print("=== QUIZ DIFFICILE PAR CATÉGORIE ===")
rows = c.execute("SELECT categorie, COUNT(*) FROM quiz WHERE difficulte='difficulte' GROUP BY categorie ORDER BY categorie").fetchall()
for cat, n in rows:
    print(f"  {cat}: {n}")

total = c.execute("SELECT COUNT(*) FROM quiz WHERE difficulte='difficulte'").fetchone()[0]
print(f"TOTAL DIFFICILE: {total}")

print("\n=== QUIZ FACILE PAR CATÉGORIE ===")
rows2 = c.execute("SELECT categorie, COUNT(*) FROM quiz WHERE difficulte='facile' GROUP BY categorie ORDER BY categorie").fetchall()
for cat, n in rows2:
    print(f"  {cat}: {n}")

c.close()
