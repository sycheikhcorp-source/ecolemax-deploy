import sqlite3
c = sqlite3.connect('/home/user/deploy/ecolemax.db')

print("=== CATEGORIES AVEC QUIZ FACILE ===")
for cat, n in c.execute("SELECT categorie, COUNT(*) FROM quiz WHERE difficulte='facile' GROUP BY categorie"):
    print(f"  {cat}: {n}")

print("\n=== CATEGORIES AVEC QUIZ DIFFICILE ===")
for cat, n in c.execute("SELECT categorie, COUNT(*) FROM quiz WHERE difficulte='difficulte' GROUP BY categorie"):
    print(f"  {cat}: {n}")

print("\n=== CATEGORIES AVEC QUIZ MOYEN (sample) ===")
for cat, n in c.execute("SELECT categorie, COUNT(*) FROM quiz WHERE difficulte='moyen' GROUP BY categorie ORDER BY n DESC LIMIT 10"):
    print(f"  {cat}: {n}")

c.close()
