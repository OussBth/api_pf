import asyncio
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

# Variables de configuration Ansible
ANSIBLE_PLAYBOOK_PATH = '/home/deb/API/FPJ/venv/bin/ansible-playbook'
INVENTORY = 'inventory/hosts.ini'
PLAYBOOK = 'playbook.yml'
VAULT_OPTS = "--vault-password-file /home/deb/.vault_pass.txt"

router = APIRouter(prefix="/ws", tags=["streaming"])

# On retire la dépendance de sécurité de la signature de la fonction
@router.websocket("/run")
async def websocket_run_playbook(websocket: WebSocket):
    """
    Endpoint WebSocket ouvert pour lancer des playbooks et streamer la sortie.
    """
    await websocket.accept()
    try:
        # Attend les paramètres du client.
        params_json = await websocket.receive_text()
        params = json.loads(params_json)

        service = params.get("service")
        action = params.get("user_action")
        payload = params.get("payload", {})

        # Construit et lance la commande Ansible.
        extra_vars = json.dumps({'service': service, 'user_action': action, 'payload': payload})
        cmd = f"{ANSIBLE_PLAYBOOK_PATH} -i {INVENTORY} {VAULT_OPTS} {PLAYBOOK} --extra-vars '{extra_vars}'"

        await websocket.send_text(f"INFO: Lancement de la commande : {cmd}\n\n")

        process = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        # Lit et envoie la sortie en temps réel.
        while process.returncode is None:
            output = await asyncio.wait_for(process.stdout.readline(), timeout=300.0)
            if not output:
                break
            await websocket.send_text(output.decode().strip() + "\n")
        
        await process.wait()
        await websocket.send_text("\nINFO: Exécution du playbook terminée.\n")

    except WebSocketDisconnect:
        print("Client déconnecté")
    except Exception as e:
        await websocket.send_text(f"ERREUR: {str(e)}\n")
    finally:
        await websocket.close()