from fastapi import APIRouter
from starlette.responses import HTMLResponse
from app.database import get_dashboard_stats
from app.services import run_playbook
import json

# Ce routeur a son propre préfixe et tag
router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])

@router.get("", response_class=HTMLResponse, summary="Afficher un tableau de bord dynamique")
async def get_dashboard():
    """
    Cet endpoint retourne une page HTML avec les métriques de l'application,
    collectées depuis la base de données et des appels directs au playbook.
    """
    # 1. Obtenir les stats depuis la base de données SQLite
    stats = get_dashboard_stats()
    
    # 2. Obtenir le nombre d'utilisateurs en temps réel
    users_result = run_playbook("user", "list_users", {})
    user_count = len(users_result.get("result", {}).get("results", []))
    
    # 3. Obtenir le nombre de sites en temps réel
    sites_result = run_playbook("webserver", "list", {})
    # Note: le playbook pour 'list' retourne la clé 'websites'
    site_count = len(sites_result.get("result", {}).get("websites", []))

    # 4. Prépare les données pour le graphique Chart.js
    chart_labels = json.dumps(list(stats["avg_duration"].keys()))
    chart_data = json.dumps(list(stats["avg_duration"].values()))

    # 5. Construit le HTML avec les vraies données
    html_content = f"""
    <html>
    <head>
        <title>Dashboard Métriques</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            body {{ font-family: sans-serif; background-color: #f4f4f9; margin: 40px; }}
            .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }}
            .metric {{ background-color: white; border-radius: 8px; padding: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); text-align: center; }}
            h1, h2 {{ color: #333; text-align: center; }}
            .value {{ font-size: 2.5em; font-weight: bold; margin: 10px 0; }}
            .success {{ color: #28a745; }} .failure {{ color: #dc3545; }}
        </style>
    </head>
    <body>
        <h1>Dashboard des Exécutions</h1>
        <div class="grid">
            <div class="metric">
                <h2>Total des Exécutions</h2>
                <p class="value">{stats['total']}</p>
            </div>
            <div class="metric">
                <h2>Succès / Échecs</h2>
                <p class="value">
                    <span class="success">{stats['success']}</span> / 
                    <span class="failure">{stats['failure']}</span>
                </p>
            </div>
            <div class="metric" style="grid-column: 1 / -1;">
                <h2>Durée Moyenne par Action (secondes)</h2>
                <canvas id="durationChart"></canvas>
            </div>
        </div>
        <script>
            const ctx = document.getElementById('durationChart');
            new Chart(ctx, {{
                type: 'bar',
                data: {{
                    labels: {chart_labels},
                    datasets: [{{
                        label: 'Durée moyenne (s)',
                        data: {chart_data},
                        backgroundColor: 'rgba(54, 162, 235, 0.6)',
                        borderColor: 'rgba(54, 162, 235, 1)',
                        borderWidth: 1
                    }}]
                }},
                options: {{ scales: {{ y: {{ beginAtZero: true }} }} }}
            }});
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)