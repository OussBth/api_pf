import asyncio
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

# Le chemin vers l'exécutable ansible-playbook
ANSIBLE_PLAYBOOK_PATH = '/home/deb/API/FPJ/venv/bin/ansible-playbook'
INVENTORY = 'inventory/hosts.ini'
PLAYBOOK = 'playbook.yml'
VAULT_OPTS = "--vault-password-file /home/deb/.vault_pass.txt"

router = APIRouter(prefix="/ws", tags=["streaming"])

@router.websocket("/run")
async def websocket_run_playbook(websocket: WebSocket):
    await websocket.accept()
    try:
        # 1. Attendre les paramètres du client (au format JSON)
        params_json = await websocket.receive_text()
        params = json.loads(params_json)

        service = params.get("service")
        action = params.get("user_action")
        payload = params.get("payload", {})

        # 2. Construire la commande Ansible
        extra_vars = json.dumps({'service': service, 'user_action': action, 'payload': payload})
        cmd = f"{ANSIBLE_PLAYBOOK_PATH} -i {INVENTORY} {VAULT_OPTS} {PLAYBOOK} --extra-vars '{extra_vars}'"

        await websocket.send_text(f"INFO: Lancement de la commande : {cmd}\n")

        # 3. Lancer le processus et lire la sortie en temps réel
        process = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        # 4. Streamer stdout et stderr vers le client
        while process.returncode is None:
            output = await asyncio.wait_for(process.stdout.readline(), timeout=60.0)
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