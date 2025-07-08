# Fichier: callback_plugins/clean_output.py

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.plugins.callback import CallbackBase

DOCUMENTATION = '''
    name: clean_output
    type: stdout
    short_description: Affiche une sortie propre et les messages des tâches.
    description:
        - Cache les tâches ignorées (skipped).
        - Affiche les messages (msg) pour toutes les tâches qui en ont un.
    version_added: "2.0"
'''

class CallbackModule(CallbackBase):
    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'stdout'
    CALLBACK_NAME = 'clean_output'

    def v2_runner_on_skipped(self, result):
        # On ne veut toujours rien afficher pour les tâches ignorées.
        pass

    def v2_runner_on_ok(self, result):
        # --- C'EST LA PARTIE MODIFIÉE ET SIMPLIFIÉE ---
        
        # 1. On affiche le statut de base (OK ou CHANGED)
        if result.is_changed():
            self._display.display(f"CHANGED: [{result._host.get_name()}] {result.task_name}")
        else:
            self._display.display(f"OK: [{result._host.get_name()}] {result.task_name}")

        # 2. Si la tâche a un champ "msg" dans son résultat, on l'affiche.
        # Cette règle simple fonctionnera pour nos tâches "debug".
        if 'msg' in result._result and result._result['msg']:
            # On vérifie que le message n'est pas le message par défaut pour ne pas polluer.
            if isinstance(result._result['msg'], str) and result._result['msg'] != 'All items completed':
                self._display.display(f"  => {result._result['msg']}")
            # Si le message n'est pas une chaîne (ex: une liste dans un with_items), on l'affiche aussi.
            elif not isinstance(result._result['msg'], str):
                 self._display.display(f"  => {result._result['msg']}")


    def v2_runner_on_failed(self, result, ignore_errors=False):
        self._display.display(f"FAILED: [{result._host.get_name()}] {result.task_name}", color='red')
        self._display.display(f"  => {self._dump_results(result._result)}", color='red')

    def v2_playbook_on_stats(self, stats):
        self._display.display("\n--- PLAY RECAP ---")
        hosts = sorted(stats.processed.keys())
        for h in hosts:
            s = stats.summarize(h)
            self._display.display(f"{h} : ok={s['ok']} changed={s['changed']} failed={s['failures']}")