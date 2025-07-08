import subprocess
import json
import os
import ast # Utilisé pour évaluer une chaîne de caractères en tant qu'objet Python
from typing import Any, Dict

# --- Configuration Globale Ansible ---
# Ces variables définissent comment et où Ansible s'exécute.
# Il est préférable de les centraliser ici pour une maintenance facile.
ANSIBLE_PLAYBOOK_PATH = '/home/deb/API/FPJ/venv/bin/ansible-playbook'
INVENTORY  = 'inventory/hosts.ini'
PLAYBOOK   = 'playbook.yml'
VAULT_OPTS = ['--vault-password-file', '/home/deb/.vault_pass.txt']
# Crée une copie de l'environnement système actuel.
ENV        = os.environ.copy()
# Force Ansible à retourner sa sortie en JSON, ce qui est essentiel pour le parsing programmatique.
ENV['ANSIBLE_STDOUT_CALLBACK'] = 'json'


def summarize(ansible_json: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyse la sortie JSON complexe d'Ansible pour en extraire les informations les plus importantes.
    Son but est de transformer une sortie très verbeuse en un résumé concis.

    Processus :
    1.  Cherche d'abord une tâche qui a échoué. Si trouvée, elle retourne les détails de l'erreur.
    2.  Si aucune erreur n'est trouvée, elle cherche une tâche dont le nom contient "afficher"
        et essaie de parser son message pour retourner un résultat structuré.
    """
    stats = ansible_json.get('stats', {})

    # ÉTAPE 1 : Recherche d'erreurs
    for play in ansible_json.get('plays', []):
        for task in play.get('tasks', []):
            name = task['task'].get('name', 'Tâche inconnue')
            for host, res in task['hosts'].items():
                if res.get('failed'):
                    # Si une tâche échoue, on priorise le message d'erreur.
                    return {
                        'stats': stats,
                        'failed_task': name,
                        'reason': res.get('msg', 'Aucun message d\'erreur détaillé trouvé.')
                    }

    # ÉTAPE 2 : Recherche de résultats de succès
    for play in ansible_json.get('plays', []):
        for task in play.get('tasks', []):
            name = task['task'].get('name', '')
            for host, res in task['hosts'].items():
                # On ne s'intéresse qu'aux tâches d'affichage qui ont un message.
                if res.get('msg') and 'afficher' in name.lower():
                    # Idéalement, le message est une chaîne JSON formatée par le playbook.
                    try:
                        parsed_data = json.loads(res['msg'])
                        parsed_data.update({'stats': stats})
                        return parsed_data
                    except (json.JSONDecodeError, AttributeError):
                        # Si le message n'est pas du JSON, on tente une évaluation plus simple.
                        try:
                           parsed_data_list = ast.literal_eval(res['msg'].split(':', 1)[1].strip())
                           return {'stats': stats, 'results': parsed_data_list}
                        except: # En dernier recours, on retourne le message brut.
                            return {'stats': stats, 'results': res['msg']}

    # Si aucune erreur et aucune tâche d'affichage (ex: une action 'create' qui a juste réussi).
    return {'stats': stats, 'results': "Aucun résultat à afficher."}


def run_playbook(service: str, action: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    La fonction principale qui construit et exécute la commande ansible-playbook.
    C'est le pont entre l'API et le système d'automatisation.
    """
    # Prépare les variables à passer au playbook via --extra-vars.
    extra = {'service': service, 'user_action': action, 'payload': payload}
    cmd = [
        ANSIBLE_PLAYBOOK_PATH,
        '-i', INVENTORY,
        *VAULT_OPTS,
        PLAYBOOK,
        '--extra-vars', json.dumps(extra)
    ]
    # Exécute la commande comme un sous-processus et attend sa fin, en capturant sa sortie.
    proc = subprocess.run(cmd, env=ENV, capture_output=True, text=True)

    try:
        # Tente de parser la sortie standard comme du JSON.
        ans_json = json.loads(proc.stdout)
    except json.JSONDecodeError:
        # Si la sortie n'est pas du JSON (grosse erreur), on retourne la sortie brute pour le débogage.
        return {'return_code': proc.returncode, 'stderr': proc.stderr, 'raw': proc.stdout}

    # Retourne une réponse structurée avec le code de retour, le résultat résumé, et les erreurs standards.
    return {
        'return_code': proc.returncode,
        'result':      summarize(ans_json),
        'stderr':      proc.stderr
    }