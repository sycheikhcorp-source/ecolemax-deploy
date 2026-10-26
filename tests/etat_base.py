import sqlite3

conn = sqlite3.connect('/home/user/deploy/ecolemax.db')
cur = conn.cursor()

print("=== ÉTAT DE LA BASE ===\n")

# Quiz par difficulté
print("QUIZ PAR DIFFICULTÉ:")
for row in cur.execute("SELECT difficulte, COUNT(*) FROM quiz GROUP BY difficulte ORDER BY difficulte"):
    print(f"  {row[0]}: {row[1]}")
print(f"  TOTAL: {cur.execute('SELECT COUNT(*) FROM quiz').fetchone()[0]}\n")

# Exercices par difficulté
print("EXERCICES PAR DIFFICULTÉ:")
for row in cur.execute("SELECT difficulte, COUNT(*) FROM exercises GROUP BY difficulte ORDER BY difficulte"):
    print(f"  {row[0]}: {row[1]}")
print(f"  TOTAL: {cur.execute('SELECT COUNT(*) FROM exercises').fetchone()[0]}\n")

# Quiz facile par catégorie
print("QUIZ FACILE PAR CATÉGORIE:")
for row in cur.execute("SELECT categorie, COUNT(*) FROM quiz WHERE difficulte='facile' GROUP BY categorie ORDER BY categorie"):
    print(f"  {row[0]}: {row[1]}")

# Quiz difficulte par catégorie
print("\nQUIZ DIFFICILE PAR CATÉGORIE:")
for row in cur.execute("SELECT categorie, COUNT(*) FROM quiz WHERE difficulte='difficulte' GROUP BY categorie ORDER BY categorie"):
    print(f"  {row[0]}: {row[1]}")

# Quiz moyen par catégorie (aperçu)
print("\nQUIZ MOYEN PAR CATÉGORIE (sample):")
for row in cur.execute("SELECT categorie, COUNT(*) FROM quiz WHERE difficulte='moyen' GROUP BY categorie ORDER BY categorie LIMIT 15"):
    print(f"  {row[0]}: {row[1]}")

conn.close()
