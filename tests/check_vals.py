import sqlite3
c = sqlite3.connect('/home/user/deploy/ecolemax.db')

print("=== VALEURS DIFFICULTÉ DANS QUIZ ===")
rows = c.execute("SELECT difficulte, COUNT(*) FROM quiz GROUP BY difficulte ORDER BY difficulte").fetchall()
for diff, n in rows:
    print(f"  {diff}: {n}")

print("\n=== QUIZ AVEC DIFFICULTÉ NULLE ===")
null_count = c.execute("SELECT COUNT(*) FROM quiz WHERE difficulte IS NULL OR difficulte=''").fetchone()[0]
print(f"  {null_count}")

print("\n=== QUIZ AVEC DIFFICULTÉ 'difficulte' (exact) ===")
difficulte = c.execute("SELECT COUNT(*) FROM quiz WHERE difficulte='difficulte'").fetchone()[0]
print(f"  {difficulte}")

c.close()
