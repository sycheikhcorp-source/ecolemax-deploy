path = '/home/user/deploy/app.py'
content = open(path, 'r').read()

# Ajouter limite
old1 = 'difficulte = request.args.get("difficulte","")'
new1 = 'difficulte = request.args.get("difficulte","")\n    limite = request.args.get("limite","")'
content = content.replace(old1, new1, 1)

# Ajouter LIMIT
old2 = '    if difficile: q += " AND difficile=?"; params.append(difficulte)'
new2 = '    if difficile: q += " AND difficile=?"; params.append(difficulte)\n    if limite: q += " LIMIT " + str(int(limite))'
content = content.replace(old2, new2, 1)

open(path, 'w').write(content)
print('✅ paramètre limite ajouté')
