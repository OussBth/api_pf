import asyncio
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

# Variables de configuration Ansible, spécifiques à ce module pour l'exécution en temps réel.
ANSIBLE_PLAYBOOK_PATH = '/home/deb/API/FPJ/venv/bin/ansible-playbook'
INVENTORY = 'inventory/hosts.ini'
PLAYBOOK = 'playbook.yml'
VAULT_OPTS = "--vault-password-file /home/deb/.vault_pass.txt"

router = APIRouter(prefix="/ws", tags=["streaming"])

# Définit un endpoint WebSocket sur /ws/run.
@router.websocket("/run")
async def websocket_run_playbook(websocket: WebSocket):
    # Accepte la connexion entrante du client (la page web).
    await websocket.accept()
    try:
        # 1. Attend de recevoir les paramètres de la commande depuis le client, au format JSON.
        params_json = await websocket.receive_text()
        params = json.loads(params_json)

        # Extrait les informations nécessaires pour construire la commande.
        service = params.get("service")
        action = params.get("user_action")
        payload = params.get("payload", {})

        # 2. Construit la commande shell complète à exécuter.
        extra_vars = json.dumps({'service': service, 'user_action': action, 'payload': payload})
        cmd = f"{ANSIBLE_PLAYBOOK_PATH} -i {INVENTORY} {VAULT_OPTS} {PLAYBOOK} --extra-vars '{extra_vars}'"

        await websocket.send_text(f"INFO: Lancement de la commande : {cmd}\n\n")

        # 3. Lance le processus en arrière-plan sans bloquer l'API (contrairement à subprocess.run).
        process = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        # 4. Lit la sortie du processus ligne par ligne et l'envoie au client en temps réel.
        while process.returncode is None:
            output = await asyncio.wait_for(process.stdout.readline(), timeout=300.0) # Timeout de 5 minutes
            if not output:
                break
            # Envoie chaque ligne de sortie au client via la connexion WebSocket.
            await websocket.send_text(output.decode().strip() + "\n")
        
        await process.wait() # Attend la fin complète du processus.
        await websocket.send_text("\nINFO: Exécution du playbook terminée.\n")

    except WebSocketDisconnect:
        print("Client déconnecté")
    except Exception as e:
        # En cas d'erreur dans le processus, on l'envoie au client.
        await websocket.send_text(f"ERREUR: {str(e)}\n")
    finally:
        # S'assure que la connexion est bien fermée à la fin.
        await websocket.close()