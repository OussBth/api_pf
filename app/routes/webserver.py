# Importe les classes nécessaires de FastAPI pour créer les routes et gérer les erreurs.
from fastapi import APIRouter, HTTPException

# Importe le modèle Pydantic pour valider les données des requêtes liées aux sites web.
from app.models.webserver import WebsiteRequest

# Importe la fonction principale qui exécute les playbooks Ansible depuis le module de services.
from app.services import run_playbook

# Crée une instance de routeur. Toutes les routes définies dans ce fichier auront le préfixe /api/webserver
# et seront regroupées sous le tag "webserver" dans la documentation automatique.
router = APIRouter(prefix="/api/webserver", tags=["webserver"])


@router.post("", summary="Créer et activer un nouveau site web")
async def create_website(req: WebsiteRequest):
    """
    Endpoint pour créer une nouvelle configuration de site Nginx.
    Il crée le dossier racine, une page index.html de test,
    génère le fichier de configuration Nginx et active le site.
    """
    # Valide que l'action est bien 'create' et que le dossier racine est fourni.
    # C'est une sécurité pour s'assurer que la bonne route est utilisée avec les bons paramètres.
    if req.action != 'create' or not req.root_dir:
        raise HTTPException(400, detail={
            "status": "fail",
            "message": "L'action doit être 'create' et 'root_dir' est requis."
        })
    
    # Appelle la fonction run_playbook avec le service 'webserver', l'action 'create',
    # et le corps de la requête comme payload.
    result = run_playbook("webserver", req.action, req.dict())
    
    # Si le playbook Ansible retourne un code d'erreur, on lève une exception 500
    # en incluant la sortie complète d'Ansible pour le débogage.
    if result.get('return_code') != 0:
        raise HTTPException(500, detail=result)
        
    # Si tout réussit, on retourne un message de succès.
    return {"status": "success", "data": {"message": f"Site '{req.server_name}' créé et activé."}}


@router.delete("/{server_name}", summary="Supprimer un site web")
async def delete_website(server_name: str):
    """
    Endpoint pour supprimer complètement un site web.
    Il désactive le site puis supprime son fichier de configuration.
    Le nom du site est passé directement dans l'URL.
    """
    # Construit le payload pour le playbook. L'action est fixe et le server_name vient de l'URL.
    payload = {"server_name": server_name, "action": "delete"}
    result = run_playbook("webserver", "delete", payload)
    
    if result.get('return_code') != 0:
        raise HTTPException(500, detail=result)
        
    return {"status": "success", "data": {"message": f"Site '{server_name}' supprimé."}}


@router.put("/{server_name}/status", summary="Activer ou désactiver un site")
async def set_website_status(server_name: str, req: WebsiteRequest):
    """
    Endpoint pour changer le statut d'un site (activé/désactivé)
    sans supprimer sa configuration.
    """
    # Valide que l'action est soit 'enable', soit 'disable'.
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
    Vérifie si un site est actuellement activé (lien symbolique présent) ou désactivé.
    """
    payload = {"server_name": server_name, "action": "status"}
    result = run_playbook("webserver", "status", payload)
    
    if result.get('return_code') != 0:
        raise HTTPException(500, detail=result)
        
    # Extrait le statut ('enabled' ou 'disabled') du résultat retourné par la fonction summarize.
    return {"status": "success", "data": {"status": result.get('result', {}).get('status', 'unknown')}}


@router.get("", summary="Lister tous les sites web")
async def list_websites():
    """
    Liste tous les fichiers de configuration de sites trouvés dans /etc/nginx/sites-available.
    """
    payload = {"action": "list"}
    result = run_playbook("webserver", "list", payload)
    
    if result.get('return_code') != 0:
        raise HTTPException(500, detail=result)
        
    # Extrait la liste des sites web du résultat retourné par la fonction summarize.
    return {"status": "success", "data": {"websites": result.get('result', {}).get('websites', [])}}


@router.get("/{server_name}/config", summary="Obtenir la configuration d'un site web")
async def get_website_config(server_name: str):
    """
    Lit et retourne le contenu du fichier de configuration Nginx pour un site donné.
    """
    payload = {"server_name": server_name, "action": "config"}
    result = run_playbook("webserver", "config", payload)
    
    if result.get('return_code') != 0:
        raise HTTPException(500, detail=result)
        
    return {"status": "success", "data": {"config": result.get('result', {}).get('config', {})}}


@router.put("/{server_name}/config", summary="Mettre à jour la configuration d'un site web")
async def update_website_config(server_name: str, req: WebsiteRequest):
    """
    Met à jour un fichier de configuration de site existant.
    Utile pour changer le 'root_dir' ou d'autres paramètres via le template.
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
    Récupère les dernières lignes des fichiers de logs Nginx (accès et erreur).
    """
    payload = {"server_name": server_name, "action": "logs"}
    result = run_playbook("webserver", "logs", payload)
    
    if result.get('return_code') != 0:
        raise HTTPException(500, detail=result)
        
    return {"status": "success", "data": {"logs": result.get('result', {}).get('logs', [])}}