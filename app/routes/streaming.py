import asyncio
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from app.auth import get_current_user_from_ws

# Variables de configuration Ansible, spécifiques à ce module pour l'exécution en temps réel.
ANSIBLE_PLAYBOOK_PATH = '/home/deb/API/FPJ/venv/bin/ansible-playbook'
INVENTORY = 'inventory/hosts.ini'
PLAYBOOK = 'playbook.yml'
VAULT_OPTS = "--vault-password-file /home/deb/.vault_pass.txt"

router = APIRouter(prefix="/ws", tags=["streaming"])

# Définit un endpoint WebSocket sur /ws/run.
@router.websocket("/run")
async def websocket_run_playbook(
    websocket: WebSocket,
    current_user: dict = Depends(get_current_user_from_ws)
):
    """
    Endpoint WebSocket sécurisé. La connexion n'est acceptée que si un token valide
    est fourni en paramètre d'URL (ex: /ws/run?token=...).
    """
    await websocket.accept()
    # On peut savoir quel utilisateur a lancé le playbook
    await websocket.send_text(f"INFO: Connexion authentifiée pour l'utilisateur '{current_user['username']}'.\n")
    
    try:
        # 1. Attendre les paramètres du client
        params_json = await websocket.receive_text()
        params = json.loads(params_json)

        service = params.get("service")
        action = params.get("user_action")
        payload = params.get("payload", {})

        # 2. Construire et lancer la commande Ansible
        extra_vars = json.dumps({'service': service, 'user_action': action, 'payload': payload})
        cmd = f"{ANSIBLE_PLAYBOOK_PATH} -i {INVENTORY} --vault-password-file /home/deb/.vault_pass.txt {PLAYBOOK} --extra-vars '{extra_vars}'"

        await websocket.send_text(f"INFO: Lancement du playbook...\n\n")

        process = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        while process.returncode is None:
            output = await asyncio.wait_for(process.stdout.readline(), timeout=300.0)
            if not output:
                break
            await websocket.send_text(output.decode().strip() + "\n")
        
        await process.wait()
        await websocket.send_text("\nINFO: Exécution du playbook terminée.\n")

    except WebSocketDisconnect:
        print(f"Client '{current_user['username']}' déconnecté")
    except Exception as e:
        await websocket.send_text(f"ERREUR: {str(e)}\n")
    finally:
        await websocket.close()