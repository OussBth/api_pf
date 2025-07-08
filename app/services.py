import subprocess, json, os, ast
from typing import Any, Dict
from prometheus_client import Counter, Histogram
from opentelemetry import trace
import time

# -- Métriques Prometheus --
PLAYBOOK_RUNS = Counter(
    "playbook_runs_total",
    "Total des exécutions de playbook",
    ["service", "action", "status"]
)
PLAYBOOK_DURATION = Histogram(
    "playbook_run_duration_seconds",
    "Durée des exécutions de playbook",
    ["service", "action"]
)

# -- Traçabilité OpenTelemetry --
tracer = trace.get_tracer(__name__)
# -- Chemins et configurations Ansible --
ANSIBLE_PLAYBOOK_PATH = '/home/deb/API/FPJ/venv/bin/ansible-playbook'
INVENTORY  = 'inventory/hosts.ini'
PLAYBOOK   = 'playbook.yml'
VAULT_OPTS = ['--vault-password-file', '/home/deb/.vault_pass.txt']
ENV        = os.environ.copy()
ENV['ANSIBLE_STDOUT_CALLBACK'] = 'json'



def summarize(ansible_json: Dict[str, Any]) -> Dict[str, Any]:
    """
    Version améliorée qui rapporte la raison de l'échec OU le résultat du succès.
    """
    stats = ansible_json.get('stats', {})
    
    for play in ansible_json.get('plays', []):
        for task in play.get('tasks', []):
            name = task['task'].get('name', 'Tâche inconnue')
            for host, res in task['hosts'].items():
                if res.get('failed'):
                    return {
                        'stats': stats,
                        'failed_task': name,
                        'reason': res.get('msg', 'Aucun message d\'erreur détaillé trouvé.')
                    }

    for play in ansible_json.get('plays', []):
        for task in play.get('tasks', []):
            name = task['task'].get('name', '')
            for host, res in task['hosts'].items():
                if res.get('msg') and 'afficher' in name.lower():
                    try:
                        parsed_data = json.loads(res['msg'])
                        parsed_data.update({'stats': stats})
                        return parsed_data
                    except (json.JSONDecodeError, AttributeError):
                        try:
                           parsed_data_list = ast.literal_eval(res['msg'].split(':', 1)[1].strip())
                           return {'stats': stats, 'results': parsed_data_list}
                        except:
                            return {'stats': stats, 'results': res['msg']}

    return {'stats': stats, 'results': "Aucun résultat à afficher."}

def run_playbook(service: str, action: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    # 1. Démarrer une "span" de traçabilité pour cette exécution
    with tracer.start_as_current_span("run_ansible_playbook") as span:
        # Ajouter des attributs à la trace pour plus de détails
        span.set_attribute("ansible.service", service)
        span.set_attribute("ansible.action", action)
        
        start_time = time.time() # Démarrer le chronomètre pour l'histogramme

        extra = {'service': service, 'user_action': action, 'payload': payload}
        cmd = [
            ANSIBLE_PLAYBOOK_PATH, '-i', INVENTORY, *VAULT_OPTS, PLAYBOOK,
            '--extra-vars', json.dumps(extra)
        ]
        proc = subprocess.run(cmd, env=ENV, capture_output=True, text=True)

        # 2. Enregistrer les métriques Prometheus
        duration = time.time() - start_time
        PLAYBOOK_DURATION.labels(service=service, action=action).observe(duration)
        status_label = "success" if proc.returncode == 0 else "failure"
        PLAYBOOK_RUNS.labels(service=service, action=action, status=status_label).inc()
        
        # 3. Ajouter des attributs à la span pour les métriques
        try:
            ans_json = json.loads(proc.stdout)
        except json.JSONDecodeError:
            return {'return_code': proc.returncode, 'stderr': proc.stderr, 'raw': proc.stdout}

        return {'return_code': proc.returncode, 'result': summarize(ans_json), 'stderr': proc.stderr}