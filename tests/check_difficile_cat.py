import sqlite3

conn = sqlite3.connect('/home/user/deploy/ecolemax.db')
cur = conn.cursor()

print("=== QUIZ DIFFICILE - CATÉGORIES VIDES ===")
for row in cur.execute("SELECT id, categorie, question, difficulte FROM quiz WHERE difficulte='difficulte' AND (categorie IS NULL OR categorie='') LIMIT 10"):
    print(f"  ID={row[0]}, cat='{row[1]}', q='{row[2][:50]}...', diff='{row[3]}'")

print("\n=== TOTAL QUIZ DIFFICILE AVEC CATÉGORIE VIDE ===")
total = cur.execute("SELECT COUNT(*) FROM quiz WHERE difficulte='difficulte' AND (categorie IS NULL OR categorie='')").fetchone()[0]
print(f"  {total}")

print("\n=== QUIZ DIFFICILE - CATÉGORIES VALIDES ===")
for row in cur.execute("SELECT categorie, COUNT(*) FROM quiz WHERE difficulte='difficulte' AND categorie IS NOT NULL AND categorie != '' GROUP BY categorie"):
    print(f"  {row[0]}: {row[1]}")

conn.close()
