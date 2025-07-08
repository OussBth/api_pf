# Fichier: app/database.py

import sqlite3
import os

# Nom du fichier de la base de données SQLite. Il sera créé à la racine du projet.
DB_FILE = "metrics.db"

def init_db():
    """
    Initialise la connexion à la base de données et s'assure que la table
    pour enregistrer les exécutions de playbook existe.
    Cette fonction est conçue pour être appelée au démarrage de l'application.
    """
    print("INFO: Initialisation de la base de données de métriques...")
    # Crée une connexion au fichier de la base de données.
    conn = sqlite3.connect(DB_FILE)
    # Crée un curseur pour exécuter des commandes SQL.
    cursor = conn.cursor()

    # CORRECTION : Utilise "CREATE TABLE IF NOT EXISTS".
    # Cette commande est sûre : elle ne fera rien si la table existe déjà,
    # mais la créera si le fichier de base de données est neuf ou vide.
    # C'est la méthode standard pour initialiser des schémas de base de données.
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS playbook_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            service TEXT NOT NULL,
            action TEXT NOT NULL,
            status TEXT NOT NULL,
            duration REAL NOT NULL
        )
    ''')
    
    # Valide la transaction et enregistre les changements.
    conn.commit()
    # Ferme la connexion à la base de données.
    conn.close()
    print("INFO: Base de données prête.")


def log_playbook_run(service: str, action: str, status: str, duration: float):
    """
    Enregistre une nouvelle exécution de playbook dans la base de données.
    Cette fonction est appelée à la fin de chaque exécution dans services.py.
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    # Utilise des paramètres (?) pour insérer les données de manière sécurisée et éviter les injections SQL.
    cursor.execute(
        "INSERT INTO playbook_runs (service, action, status, duration) VALUES (?, ?, ?, ?)",
        (service, action, status, duration)
    )
    conn.commit()
    conn.close()


def get_dashboard_stats():
    """
    Interroge la base de données pour agréger et retourner les statistiques
    qui seront affichées sur le tableau de bord.
    """
    conn = sqlite3.connect(DB_FILE)
    # Permet d'accéder aux résultats de la requête par nom de colonne (ex: r['status']).
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Requête pour compter le nombre total d'exécutions par statut ('success' ou 'failure').
    runs = cursor.execute("SELECT status, COUNT(*) as count FROM playbook_runs GROUP BY status").fetchall()
    
    # Requête pour calculer la durée moyenne de chaque type d'action.
    avg_duration = cursor.execute("SELECT action, AVG(duration) as avg_d FROM playbook_runs GROUP BY action").fetchall()
    
    conn.close()
    
    # Met en forme les données dans un dictionnaire facile à utiliser pour l'API et le frontend.
    stats = {
        "success": next((r['count'] for r in runs if r['status'] == 'success'), 0),
        "failure": next((r['count'] for r in runs if r['status'] == 'failure'), 0),
        "avg_duration": {r['action']: round(r['avg_d'], 3) for r in avg_duration} # Arrondit à 3 décimales
    }
    stats["total"] = stats["success"] + stats["failure"]
    
    return stats