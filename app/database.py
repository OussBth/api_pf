import sqlite3
import os

METRICS_DB_FILE = "metrics.db"

def init_db():
    """
    Initialise la base de données des métriques et crée la table 'playbook_runs'.
    """
    print("INFO: Initialisation de la base de données de métriques...")
    conn = sqlite3.connect(METRICS_DB_FILE)
    cursor = conn.cursor()

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
    conn.commit()
    conn.close()
    print("INFO: Base de données des métriques prête.")


def log_playbook_run(service: str, action: str, status: str, duration: float):
    """
    Enregistre une exécution de playbook dans la base de données des métriques.
    """
    conn = sqlite3.connect(METRICS_DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO playbook_runs (service, action, status, duration) VALUES (?, ?, ?, ?)",
        (service, action, status, duration)
    )
    conn.commit()
    conn.close()

def get_dashboard_stats():
    """
    Récupère les statistiques depuis la base de données des métriques pour le dashboard.
    """
    conn = sqlite3.connect(METRICS_DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    runs = cursor.execute("SELECT status, COUNT(*) as count FROM playbook_runs GROUP BY status").fetchall()
    avg_duration = cursor.execute("SELECT action, AVG(duration) as avg_d FROM playbook_runs GROUP BY action").fetchall()
    conn.close()
    stats = {
        "success": next((r['count'] for r in runs if r['status'] == 'success'), 0),
        "failure": next((r['count'] for r in runs if r['status'] == 'failure'), 0),
        "avg_duration": {r['action']: round(r['avg_d'], 3) for r in avg_duration}
    }
    stats["total"] = stats["success"] + stats["failure"]
    return stats