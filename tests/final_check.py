import sqlite3
c = sqlite3.connect('/home/user/deploy/ecolemax.db')

# Vérifier les catégories des quiz difficulte
rows = c.execute("SELECT categorie, COUNT(*) FROM quiz WHERE difficulte='difficulte' GROUP BY categorie ORDER BY categorie").fetchall()
print("Quiz difficulte par catégorie:")
for cat, n in rows:
    print(f"  {cat}: {n}")

total_difficulte = c.execute("SELECT COUNT(*) FROM quiz WHERE difficulte='difficulte'").fetchone()[0]
print(f"Total difficulte: {total_difficulte}")

# Vérifier les catégories des quiz facile
rows2 = c.execute("SELECT categorie, COUNT(*) FROM quiz WHERE difficulte='facile' GROUP BY categorie ORDER BY categorie").fetchall()
print("\nQuiz facile par catégorie:")
for cat, n in rows2:
    print(f"  {cat}: {n}")

c.close()
