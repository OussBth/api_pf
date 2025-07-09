# On importe les classes de base de FastAPI. 'Depends' n'est plus nécessaire.
from fastapi import APIRouter, HTTPException
# On importe le modèle Pydantic pour la validation des données.
from app.models.webserver import WebsiteRequest
# On importe la fonction principale qui exécute les playbooks.
from app.services import run_playbook

# Le préfixe /api/webserver sera ajouté à toutes les URL de ce routeur.
router = APIRouter(prefix="/api/webserver", tags=["webserver"])


@router.post("", summary="Créer et activer un nouveau site web")
async def create_website(req: WebsiteRequest):
    """
    Crée une nouvelle configuration de site Nginx, le dossier racine,
    une page de test, et active le site. Route ouverte.
    """
    if req.action != 'create' or not req.root_dir:
        raise HTTPException(400, detail={"status": "fail", "message": "L'action doit être 'create' et 'root_dir' est requis."})
    
    result = run_playbook("webserver", req.action, req.dict())
    
    if result.get('return_code') != 0:
        raise HTTPException(500, detail=result)
        
    return {"status": "success", "data": {"message": f"Site '{req.server_name}' créé et activé."}}


@router.delete("/{server_name}", summary="Supprimer un site web")
async def delete_website(server_name: str):
    """
    Supprime complètement un site web (désactivation puis suppression du fichier de conf).
    Route ouverte.
    """
    payload = {"server_name": server_name, "action": "delete"}
    result = run_playbook("webserver", "delete", payload)
    
    if result.get('return_code') != 0:
        raise HTTPException(500, detail=result)
        
    return {"status": "success", "data": {"message": f"Site '{server_name}' supprimé."}}


@router.put("/{server_name}/status", summary="Activer ou désactiver un site")
async def set_website_status(server_name: str, req: WebsiteRequest):
    """
    Change le statut d'un site (activé/désactivé) sans supprimer sa configuration.
    Route ouverte.
    """
    if req.action not in ['enable', 'disable']:
        raise HTTPException(400, detail={"status": "fail", "message": "L'action doit être 'enable' ou 'disable'."})

    payload = {"server_name": server_name, "action": req.action}
    result = run_playbook("webserver", req.action, payload)
    
    if result.get('return_code') != 0:
        raise HTTPException(500, detail=result)
        
    return {"status": "success", "data": {"message": f"Site '{server_name}' - statut changé à '{req.action}'."}}


@router.get("/{server_name}/status", summary="Vérifier le statut d'un site web")
async def get_website_status(server_name: str):
    """
    Vérifie si un site est actuellement activé ou désactivé. Route ouverte.
    """
    payload = {"server_name": server_name, "action": "status"}
    result = run_playbook("webserver", "status", payload)
    
    if result.get('return_code') != 0:
        raise HTTPException(500, detail=result)
        
    return {"status": "success", "data": {"status": result.get('result', {}).get('status', 'unknown')}}


@router.get("", summary="Lister tous les sites web")
async def list_websites():
    """
    Liste tous les sites configurés. Route ouverte.
    """
    payload = {"action": "list"}
    result = run_playbook("webserver", "list", payload)
    
    if result.get('return_code') != 0:
        raise HTTPException(500, detail=result)
        
    return {"status": "success", "data": {"websites": result.get('result', {}).get('results', [])}}


@router.get("/{server_name}/config", summary="Obtenir la configuration d'un site web")
async def get_website_config(server_name: str):
    """
    Retourne le contenu du fichier de configuration Nginx pour un site. Route ouverte.
    """
    payload = {"server_name": server_name, "action": "config"}
    result = run_playbook("webserver", "config", payload)
    
    if result.get('return_code') != 0:
        raise HTTPException(500, detail=result)
        
    return {"status": "success", "data": {"config": result.get('result', {}).get('config', {})}}


@router.put("/{server_name}/config", summary="Mettre à jour la configuration d'un site web")
async def update_website_config(server_name: str, req: WebsiteRequest):
    """
    Met à jour un fichier de configuration de site existant. Route ouverte.
    """
    if req.action != 'update' or not req.root_dir:
        raise HTTPException(400, detail={"status": "fail", "message": "L'action doit être 'update' et 'root_dir' est requis."})
    
    payload = {"server_name": server_name, "root_dir": req.root_dir, "action": "update"}
    result = run_playbook("webserver", "update", payload)
    
    if result.get('return_code') != 0:
        raise HTTPException(500, detail=result)
        
    return {"status": "success", "data": {"message": f"Configuration du site '{server_name}' mise à jour."}}


@router.get("/{server_name}/logs", summary="Obtenir les logs d'un site web")
async def get_website_logs(server_name: str):
    """
    Récupère les dernières lignes des logs Nginx. Route ouverte.
    """
    payload = {"server_name": server_name, "action": "logs"}
    result = run_playbook("webserver", "logs", payload)
    
    if result.get('return_code') != 0:
        raise HTTPException(500, detail=result)
        
    return {"status": "success", "data": {"logs": result.get('result', {}).get('logs', [])}}