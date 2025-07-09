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
    Analyse la sortie JSON d'Ansible de manière cohérente.
    1. Cherche les erreurs en premier.
    2. Si pas d'erreur, cherche un message à afficher et place TOUJOURS
       le résultat final dans une clé nommée 'results'.
    """
    stats = ansible_json.get('stats', {})

    # Étape 1 : Recherche d'erreurs
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

    # Étape 2 : Recherche de résultats de succès
    for play in ansible_json.get('plays', []):
        for task in play.get('tasks', []):
            name = task['task'].get('name', '')
            for host, res in task['hosts'].items():
                if res.get('msg') and 'afficher' in name.lower():
                    # --- CORRECTION DE LA LOGIQUE ---
                    # On essaie de parser la sortie, peu importe son format,
                    # et on place le résultat final dans la clé 'results'.
                    try:
                        # Cas 1: Le message est déjà du JSON (ex: pour lister les sites)
                        # Le msg est: "{'websites': ['a', 'b']}"
                        parsed_data = json.loads(res['msg'])
                        # On extrait la valeur (ex: la liste ['a', 'b'])
                        final_result = list(parsed_data.values())[0]
                        return {'stats': stats, 'results': final_result}
                    except (json.JSONDecodeError, AttributeError, IndexError):
                        # Cas 2: Le message est une chaîne (ex: "Groupes: ['a', 'b']")
                        try:
                            list_str = res['msg'].split(':', 1)[1].strip()
                            final_result = ast.literal_eval(list_str)
                            return {'stats': stats, 'results': final_result}
                        except: # En dernier recours
                            return {'stats': stats, 'results': res['msg']}

    # Si aucune erreur et aucune tâche d'affichage
    return {'stats': stats, 'results': []}

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