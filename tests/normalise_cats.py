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

# Normaliser les quiz facile et difficile
for abbrev, complet in mapping.items():
    count = cur.execute('SELECT COUNT(*) FROM quiz WHERE categorie=? AND difficulte IN (?, ?)', (abbrev, 'facile', 'difficile')).fetchone()[0]
    if count > 0:
        cur.execute('UPDATE quiz SET categorie=? WHERE categorie=? AND difficile IN (?, ?)', (complet, abbrev, 'facile', 'difficile'))
        print(f'  {abbrev} → {complet}: {count} quiz normalisés')

conn.commit()

# Vérification
print('\n=== QUIZ FACILE PAR CATÉGORIE (après normalisation) ===')
for row in cur.execute('SELECT categorie, COUNT(*) FROM quiz WHERE difficile=? GROUP BY categorie', ('facile',)).fetchall():
    print(f'  {row[0]}: {row[1]}')

print('\n=== QUIZ DIFFICILE PAR CATÉGORIE (après normalisation) ===')
for row in cur.execute('SELECT categorie, COUNT(*) FROM quiz WHERE difficile=? GROUP BY categorie', ('difficile',)).fetchall():
    print(f'  {row[0]}: {row[1]}')

conn.close()
print('Normalisation terminée')
