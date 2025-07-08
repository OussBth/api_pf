import sqlite3
import os
from app.security import get_password_hash

APP_DB_FILE = "api_data.db"
METRICS_DB_FILE = "metrics.db"
# --- Initialisation des Bases de Données ---
# Cette fonction est appelée au démarrage de l'application pour créer les tables nécessaires.
def init_db():
    print("INFO: Initialisation des bases de données...")
    conn_app = sqlite3.connect(APP_DB_FILE)
    cursor_app = conn_app.cursor()
    cursor_app.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            hashed_password TEXT NOT NULL,
            role TEXT DEFAULT 'user' NOT NULL
        )
    ''')
    cursor_app.execute("SELECT COUNT(*) FROM users")
    if cursor_app.fetchone()[0] == 0:
        print("INFO: Création des utilisateurs par défaut...")
        admin_password = "adminpassword"
        admin_hashed_password = get_password_hash(admin_password)
        cursor_app.execute(
            "INSERT INTO users (username, hashed_password, role) VALUES (?, ?, ?)",
            ('admin', admin_hashed_password, 'admin')
        )
        user_password = "userpassword"
        user_hashed_password = get_password_hash(user_password)
        cursor_app.execute(
            "INSERT INTO users (username, hashed_password, role) VALUES (?, ?, ?)",
            ('user', user_hashed_password, 'user')
        )
    conn_app.commit()
    conn_app.close()
    conn_metrics = sqlite3.connect(METRICS_DB_FILE)
    cursor_metrics = conn_metrics.cursor()
    cursor_metrics.execute('''
        CREATE TABLE IF NOT EXISTS playbook_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            service TEXT NOT NULL,
            action TEXT NOT NULL,
            status TEXT NOT NULL,
            duration REAL NOT NULL
        )
    ''')
    conn_metrics.commit()
    conn_metrics.close()
    print("INFO: Bases de données prêtes.")

def get_user_by_username(username: str):
    conn = sqlite3.connect(APP_DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    user = cursor.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    conn.close()
    return user

def log_playbook_run(service: str, action: str, status: str, duration: float):
    conn = sqlite3.connect(METRICS_DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO playbook_runs (service, action, status, duration) VALUES (?, ?, ?, ?)",
        (service, action, status, duration)
    )
    conn.commit()
    conn.close()

def get_dashboard_stats():
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