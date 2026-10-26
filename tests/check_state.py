import sqlite3
c = sqlite3.connect('/home/user/deploy/ecolemax.db')

print("=== QUIZ PAR DIFFICULTÉ ===")
for diff, n in c.execute("SELECT difficulte, COUNT(*) FROM quiz GROUP BY difficulte ORDER BY difficulte"):
    print(f"  {diff}: {n}")
print(f"TOTAL QUIZ: {c.execute('SELECT COUNT(*) FROM quiz').fetchone()[0]}")

print("\n=== EXERCICES PAR DIFFICULTÉ ===")
for diff, n in c.execute("SELECT difficulte, COUNT(*) FROM exercises GROUP BY difficulte ORDER BY difficulte"):
    print(f"  {diff}: {n}")
print(f"TOTAL EXERCICES: {c.execute('SELECT COUNT(*) FROM exercises').fetchone()[0]}")

print("\n=== QUIZ DIFFICILE PAR CATÉGORIE ===")
for cat, n in c.execute("SELECT categorie, COUNT(*) FROM quiz WHERE difficulte='difficulte' GROUP BY categorie"):
    print(f"  {cat}: {n}")

c.close()
