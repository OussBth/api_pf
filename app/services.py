import subprocess
import json
import os
import time
from typing import Any, Dict

# On importe notre nouvelle fonction de log depuis le module de base de données.
from app.database import log_playbook_run

# --- Configuration Globale Ansible ---
ANSIBLE_PLAYBOOK_PATH = '/home/deb/API/FPJ/venv/bin/ansible-playbook'
INVENTORY  = 'inventory/hosts.ini'
PLAYBOOK   = 'playbook.yml'
VAULT_OPTS = ['--vault-password-file', '/home/deb/.vault_pass.txt']
ENV        = os.environ.copy()
ENV['ANSIBLE_STDOUT_CALLBACK'] = 'json'


def summarize(ansible_json: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyse la sortie JSON d'Ansible pour en extraire les informations utiles.
    """
    stats = ansible_json.get('stats', {})
    
    # Cherche la première tâche qui a échoué.
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

    # Si pas d'erreur, cherche le résultat d'une tâche "Afficher...".
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
                        return {'stats': stats, 'raw_result': res['msg']}

    return {'stats': stats, 'results': "Exécution terminée avec succès sans sortie à afficher."}


def run_playbook(service: str, action: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Exécute un playbook et enregistre le résultat dans la base de données de métriques.
    """
    start_time = time.time()

    extra = {'service': service, 'user_action': action, 'payload': payload}
    cmd = [
        ANSIBLE_PLAYBOOK_PATH,
        '-i', INVENTORY,
        *VAULT_OPTS,
        PLAYBOOK,
        '--extra-vars', json.dumps(extra)
    ]
    proc = subprocess.run(cmd, env=ENV, capture_output=True, text=True)

    # --- ENREGISTREMENT DANS LA BASE DE DONNÉES ---
    duration = time.time() - start_time
    status_label = "success" if proc.returncode == 0 else "failure"
    log_playbook_run(service, action, status_label, duration)
    # ---------------------------------------------

    try:
        ans_json = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return {'return_code': proc.returncode, 'stderr': proc.stderr, 'raw': proc.stdout}

    return {
        'return_code': proc.returncode,
        'result':      summarize(ans_json),
        'stderr':      proc.stderr
    }