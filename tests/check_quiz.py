import sqlite3
c = sqlite3.connect('/home/user/deploy/ecolemax.db')

print("=== QUIZ maths PAR DIFFICULTÉ ===")
for diff, n in c.execute("SELECT difficulte, COUNT(*) FROM quiz WHERE categorie='maths' GROUP BY difficulte"):
    print(f"  {diff}: {n}")

print("\n=== TOTAL QUIZ maths ===")
total = c.execute("SELECT COUNT(*) FROM quiz WHERE categorie='maths'").fetchone()[0]
print(f"  {total}")

print("\n=== TOTAL QUIZ PAR DIFFICULTÉ ===")
for diff, n in c.execute("SELECT difficulte, COUNT(*) FROM quiz GROUP BY difficulte ORDER BY difficulte"):
    print(f"  {diff}: {n}")

print("\n=== TOTAL QUIZ ===")
total3 = c.execute("SELECT COUNT(*) FROM quiz").fetchone()[0]
print(f"  {total3}")

print("\n=== EXERCICES PAR DIFFICULTÉ ===")
for diff, n in c.execute("SELECT difficulte, COUNT(*) FROM exercises GROUP BY difficulte ORDER BY difficulte"):
    print(f"  {diff}: {n}")

print("\n=== TOTAL EXERCICES ===")
total4 = c.execute("SELECT COUNT(*) FROM exercises").fetchone()[0]
print(f"  {total4}")

c.close()
