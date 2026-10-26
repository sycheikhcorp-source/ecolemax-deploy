import sqlite3
c = sqlite3.connect('/home/user/deploy/ecolemax.db')

print("=== QUIZ MOYEN PAR CATÉGORIE ===")
for cat, n in c.execute("SELECT categorie, COUNT(*) as nb FROM quiz WHERE difficulte='moyen' GROUP BY categorie ORDER BY nb DESC LIMIT 20"):
    print(f"  {cat}: {n}")

print("\n=== TOTAL QUIZ MOYEN ===")
total = c.execute("SELECT COUNT(*) FROM quiz WHERE difficulte='moyen'").fetchone()[0]
print(f"  {total}")

c.close()
