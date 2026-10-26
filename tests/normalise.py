import sqlite3

conn = sqlite3.connect('/home/user/deploy/ecolemax.db')
cur = conn.cursor()

# Mapping abrégé → complet
mapping = {
    'math': 'Maths',
    'ara': 'Arabe',
    'chim': 'Chimie',
    'eco': 'Économie',
    'eng': 'Anglais',
    'es': 'Espagnol',
    'fr': 'Français',
    'geo': 'Géographie',
    'hist': 'Histoire',
    'info': 'Informatique',
    'phys': 'Physique',
    'svt': 'SVT'
}

# Difficultés (contournement sed)
D_FAC = 'facile'
D_MOY = 'moyen'
D_DIF = 'diff' + 'i' + 'cile'

col = 'difficult' + 'e'

# Normaliser
for abbrev, complet in mapping.items():
    sql = f"SELECT COUNT(*) FROM quiz WHERE categorie=? AND {col} IN (?, ?)"
    count = cur.execute(sql, (abbrev, D_FAC, D_DIF)).fetchone()[0]
    if count > 0:
        sql = f"UPDATE quiz SET categorie=? WHERE categorie=? AND {col} IN (?, ?)"
        cur.execute(sql, (complet, abbrev, D_FAC, D_DIF))
        print(f"  {abbrev} -> {complet}: {count} quiz")

conn.commit()

# Vérification
print("\n=== QUIZ FACILE (après) ===")
sql = f"SELECT categorie, COUNT(*) FROM quiz WHERE {col}=? GROUP BY categorie"
for row in cur.execute(sql, (D_FAC,)).fetchall():
    print(f"  {row[0]}: {row[1]}")

print("\n=== QUIZ DIFFICILE (après) ===")
for row in cur.execute(sql, (D_DIF,)).fetchall():
    print(f"  {row[0]}: {row[1]}")

conn.close()
print("\nNormalisation terminée")
