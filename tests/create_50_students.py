#!/usr/bin/env python3
import sqlite3, hashlib, os, secrets

def hash_pass(mdp):
    salt = os.urandom(16)
    h = hashlib.pbkdf2_hmac('sha256', mdp.encode(), salt, 50000)
    return "pbkdf2$" + salt.hex() + "$" + h.hex()

c = sqlite3.connect('/home/user/deploy/ecolemax.db')
c.row_factory = sqlite3.Row

niveaux = ["6ème", "5ème", "4ème", "3ème"]
matieres = ["math", "fr", "phys", "chim", "svt"]

created = 0
for i in range(1, 51):
    pseudo = f"eleve_test_{i:02d}"
    email = f"eleve_test_{i:02d}@ecolemax.test"
    pw = f"Test{i}!"  # mot de passe unique par élève
    phone = f"+22177{i:07d}"  # +221 77 XXXXXXXX
    niveau = niveaux[i % len(niveaux)]
    role = "eleve"

    # Vérifier si existe
    u = c.execute("SELECT id FROM users WHERE pseudo=?", (pseudo,)).fetchone()
    if u:
        # Mettre à jour
        c.execute("UPDATE users SET email=?, phone=?, mot_de_passe=?, niveau=?, phone_verified=1 WHERE id=?",
                  (email, phone, hash_pass(pw), niveau, u["id"]))
    else:
        c.execute("INSERT INTO users (pseudo,email,mot_de_passe,niveau,role,phone,phone_verified,created_at) VALUES (?,?,?,?,?,?,1,datetime('now'))",
                  (pseudo, email, hash_pass(pw), niveau, role, phone))
    created += 1

c.commit()

# Vérifier
total = c.execute("SELECT COUNT(*) FROM users WHERE pseudo LIKE 'eleve_test_%'").fetchone()[0]
print(f"✅ {created} comptes créés/mis à jour")
print(f"✅ Total comptes élèves test: {total}")

# Liste
for i in range(1, 6):
    u = c.execute("SELECT * FROM users WHERE pseudo=?", (f"eleve_test_{i:02d}",)).fetchone()
    print(f"  {u['pseudo']}: {u['email']}, {u['phone']}, mot de passe: Test{i}!")

c.close()
