import sqlite3

conn = sqlite3.connect('/home/user/deploy/ecolemax.db')
cur = conn.cursor()

print("=== TOUTES LES VALEURS DE CATÉGORIE POUR QUIZ DIFFICILE ===")
rows = cur.execute("SELECT categorie, COUNT(*) FROM quiz WHERE difficulte='difficulte' GROUP BY categorie").fetchall()
if not rows:
    print("  (Aucune donnée)")
for row in rows:
    print(f"  '{row[0]}': {row[1]}")

print("\n=== EXEMPLES DE QUIZ DIFFICILE ===")
for row in cur.execute("SELECT id, categorie, question, difficulte FROM quiz WHERE difficulte='difficulte' LIMIT 5"):
    print(f"  ID={row[0]}, cat='{row[1]}', q='{row[2][:60]}...', diff='{row[3]}'")

print("\n=== TOTAL QUIZ DIFFICILE ===")
print(f"  {cur.execute('SELECT COUNT(*) FROM quiz WHERE difficulte=\"difficulte\"').fetchone()[0]}")

conn.close()
