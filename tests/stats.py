#!/usr/bin/env python3
import sqlite3
c = sqlite3.connect('/home/user/deploy/ecolemax.db')

queries = {
    "Utilisateurs": "SELECT COUNT(*) FROM users",
    "Eleves test": "SELECT COUNT(*) FROM users WHERE pseudo LIKE 'eleve_test_%'",
    "Exercices": "SELECT COUNT(*) FROM exercises",
    "Quiz": "SELECT COUNT(*) FROM quiz",
    "Abonnements": "SELECT COUNT(*) FROM abonnements",
    "Plans": "SELECT COUNT(*) FROM plans",
    "Supports": "SELECT COUNT(*) FROM supports",
    "Notifications": "SELECT COUNT(*) FROM notifications",
}

for label, q in queries.items():
    print(f"{label}: {c.execute(q).fetchone()[0]}")

c.close()
