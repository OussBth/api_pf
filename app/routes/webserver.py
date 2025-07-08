# On importe 'Depends' pour l'injection de dépendances
from fastapi import APIRouter, HTTPException, Depends
from app.models.webserver import WebsiteRequest
from app.services import run_playbook
# On importe nos dépendances de sécurité
from app.auth import get_current_user, require_role

router = APIRouter(prefix="/api/webserver", tags=["webserver"])


@router.post("", summary="Créer et activer un nouveau site web (Admin seulement)")
# On exige le rôle "admin" pour cette route
async def create_website(req: WebsiteRequest, current_user: dict = Depends(require_role("admin"))):
    if req.action != 'create' or not req.root_dir:
        raise HTTPException(400, detail={"status": "fail", "message": "L'action doit être 'create' et 'root_dir' est requis."})
    
    result = run_playbook("webserver", req.action, req.dict())
    
    if result.get('return_code') != 0:
        raise HTTPException(500, detail=result)
        
    return {"status": "success", "data": {"message": f"Site '{req.server_name}' créé et activé."}}


@router.delete("/{server_name}", summary="Supprimer un site web (Admin seulement)")
# On exige le rôle "admin" pour cette route
async def delete_website(server_name: str, current_user: dict = Depends(require_role("admin"))):
    payload = {"server_name": server_name, "action": "delete"}
    result = run_playbook("webserver", "delete", payload)
    
    if result.get('return_code') != 0:
        raise HTTPException(500, detail=result)
        
    return {"status": "success", "data": {"message": f"Site '{server_name}' supprimé."}}


@router.put("/{server_name}/status", summary="Activer ou désactiver un site (Admin seulement)")
# On exige le rôle "admin" pour cette route
async def set_website_status(server_name: str, req: WebsiteRequest, current_user: dict = Depends(require_role("admin"))):
    if req.action not in ['enable', 'disable']:
        raise HTTPException(400, detail={"status": "fail", "message": "L'action doit être 'enable' ou 'disable'."})

    payload = {"server_name": server_name, "action": req.action}
    result = run_playbook("webserver", req.action, payload)
    
    if result.get('return_code') != 0:
        raise HTTPException(500, detail=result)
        
    return {"status": "success", "data": {"message": f"Site '{server_name}' - statut changé à '{req.action}'."}}


@router.get("/{server_name}/status", summary="Vérifier le statut d'un site web (Authentifié)")
# N'importe quel utilisateur authentifié peut accéder à cette route
async def get_website_status(server_name: str, current_user: dict = Depends(get_current_user)):
    payload = {"server_name": server_name, "action": "status"}
    result = run_playbook("webserver", "status", payload)
    
    if result.get('return_code') != 0:
        raise HTTPException(500, detail=result)
        
    return {"status": "success", "data": {"status": result.get('result', {}).get('status', 'unknown')}}


@router.get("", summary="Lister tous les sites web (Authentifié)")
# N'importe quel utilisateur authentifié peut accéder à cette route
async def list_websites(current_user: dict = Depends(get_current_user)):
    payload = {"action": "list"}
    result = run_playbook("webserver", "list", payload)
    
    if result.get('return_code') != 0:
        raise HTTPException(500, detail=result)
        
    return {"status": "success", "data": {"websites": result.get('result', {}).get('websites', [])}}


@router.get("/{server_name}/config", summary="Obtenir la configuration d'un site web (Authentifié)")
# N'importe quel utilisateur authentifié peut accéder à cette route
async def get_website_config(server_name: str, current_user: dict = Depends(get_current_user)):
    payload = {"server_name": server_name, "action": "config"}
    result = run_playbook("webserver", "config", payload)
    
    if result.get('return_code') != 0:
        raise HTTPException(500, detail=result)
        
    return {"status": "success", "data": {"config": result.get('result', {}).get('config', {})}}


@router.put("/{server_name}/config", summary="Mettre à jour la configuration d'un site web (Admin seulement)")
# On exige le rôle "admin" pour cette route
async def update_website_config(server_name: str, req: WebsiteRequest, current_user: dict = Depends(require_role("admin"))):
    if req.action != 'update' or not req.root_dir:
        raise HTTPException(400, detail={"status": "fail", "message": "L'action doit être 'update' et 'root_dir' est requis."})
    
    payload = {"server_name": server_name, "root_dir": req.root_dir, "action": "update"}
    result = run_playbook("webserver", "update", payload)
    
    if result.get('return_code') != 0:
        raise HTTPException(500, detail=result)
        
    return {"status": "success", "data": {"message": f"Configuration du site '{server_name}' mise à jour."}}


@router.get("/{server_name}/logs", summary="Obtenir les logs d'un site web (Admin seulement)")
# On exige le rôle "admin" pour cette route, car les logs peuvent être sensibles
async def get_website_logs(server_name: str, current_user: dict = Depends(require_role("admin"))):
    payload = {"server_name": server_name, "action": "logs"}
    result = run_playbook("webserver", "logs", payload)
    
    if result.get('return_code') != 0:
        raise HTTPException(500, detail=result)
        
    return {"status": "success", "data": {"logs": result.get('result', {}).get('logs', [])}}