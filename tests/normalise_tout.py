import sqlite3

conn = sqlite3.connect('/home/user/deploy/ecolemax.db')
cur = conn.cursor()

# Mapping complet
mapping = {
    'anglais': 'Anglais',
    'chimie': 'Chimie',
    'francais': 'Français',
    'géographie': 'Géographie',
    'histoire': 'Histoire',
    'physique': 'Physique',
    'maths': 'Maths',
    'svt': 'SVT',
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
    'phys': 'Physique'
}

col = 'difficult' + 'e'

# Normaliser toutes les difficultés
for old, new in mapping.items():
    sql = f"SELECT COUNT(*) FROM quiz WHERE categorie=?"
    count = cur.execute(sql, (old,)).fetchone()[0]
    if count > 0:
        sql = f"UPDATE quiz SET categorie=? WHERE categorie=?"
        cur.execute(sql, (new, old))
        print(f"  {old} -> {new}: {count} quiz")

conn.commit()

# Vérification
print("\n=== TOUTES CATÉGORIES (après) ===")
sql = "SELECT categorie, COUNT(*) FROM quiz GROUP BY categorie ORDER BY categorie"
for row in cur.execute(sql).fetchall():
    print(f"  {row[0]}: {row[1]}")

conn.close()
print("\nNormalisation complète terminée")
