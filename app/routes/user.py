# On importe les classes de base de FastAPI.
from fastapi import APIRouter, HTTPException, Query
# On importe le modèle Pydantic pour la validation des données.
from app.models.user import UserRequest
# On importe la fonction principale qui exécute les playbooks.
from app.services import run_playbook

# Le préfixe /api/user sera ajouté à toutes les URL de ce routeur.
router = APIRouter(prefix="/api/user", tags=["user"])


@router.get("", summary="Lister tous les utilisateurs")
async def list_users(skip: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=200)):
    result = run_playbook("user", "list_users", {})
    if result.get('return_code') != 0:
        raise HTTPException(status_code=500, detail={"status": "error", "data": result})
    
    all_users = result['result'].get('results', [])
    paginated_users = all_users[skip : skip + limit]
    
    return {"status": "success", "data": {"users": paginated_users, "total": len(all_users)}}


@router.get("/groups", summary="Lister les groupes")
async def list_groups(
    username: str = Query(None, description="Optionnel: nom d'utilisateur pour filtrer les groupes"),
    skip: int = Query(0, ge=0),
    limit: int = Query(60, ge=1, le=200)
):
    payload = {"username": username} if username else {}
    result = run_playbook("user", "list_groups", payload)
    
    if result.get('return_code') != 0:
        raise HTTPException(status_code=500, detail={"status": "error", "data": result})
        
    all_groups = result['result'].get('results', [])
    paginated_groups = all_groups[skip : skip + limit]

    return {"status": "success", "data": {"groups": paginated_groups, "total": len(all_groups)}}


@router.post("", summary="Créer un nouvel utilisateur")
async def create_user(req: UserRequest):
    if req.action != 'create' or not req.username or not req.password:
        raise HTTPException(400, detail={"status": "fail", "message": "Action 'create' et champs 'username'/'password' requis."})
    
    # On exécute directement le playbook, sans interaction avec la DB.
    result = run_playbook("user", req.action, req.dict())
    
    if result.get('return_code') != 0:
        raise HTTPException(500, detail={"status": "error", "data": result})
    
    return {"status": "success", "data": {"message": f"Utilisateur '{req.username}' créé avec succès."}}


@router.put("", summary="Changer le mot de passe d'un utilisateur")
async def change_password(req: UserRequest):
    if req.action != 'password' or not req.username or not req.password:
        raise HTTPException(400, detail={"status": "fail", "message": "Action 'password' et champs 'username'/'password' requis."})
    
    result = run_playbook("user", req.action, req.dict())
    
    if result.get('return_code') != 0:
        raise HTTPException(500, detail={"status": "error", "data": result})
    
    return {"status": "success", "data": {"message": f"Mot de passe de l'utilisateur '{req.username}' changé avec succès."}}


@router.delete("", summary="Supprimer un utilisateur")
async def delete_user(req: UserRequest):
    if req.action != 'delete' or not req.username:
        raise HTTPException(400, detail={"status": "fail", "message": "Action 'delete' et champ 'username' requis."})
    
    result = run_playbook("user", req.action, req.dict())
    
    if result.get('return_code') != 0:
        raise HTTPException(500, detail={"status": "error", "data": result})
    
    return {"status": "success", "data": {"message": f"Utilisateur '{req.username}' supprimé avec succès."}}


# --- Routes pour les Groupes ---

@router.post("/group/create", summary="Créer un nouveau groupe")
async def create_group(req: UserRequest):
    if req.action != 'create_group' or not req.group:
        raise HTTPException(400, detail={"status": "fail", "message": "Action 'create_group' et champ 'group' requis."})
    
    result = run_playbook("user", req.action, req.dict())
    
    if result.get('return_code') != 0:
        raise HTTPException(500, detail={"status": "error", "data": result})
    
    return {"status": "success", "data": {"message": f"Groupe '{req.group}' créé avec succès."}}


@router.post("/group", summary="Ajouter un utilisateur à un groupe")
async def add_user_to_group(req: UserRequest):
    if req.action != 'add_group' or not req.username or not req.group:
        raise HTTPException(400, detail={"status": "fail", "message": "Action 'add_group' et champs 'username'/'group' requis."})
        
    result = run_playbook("user", req.action, req.dict())
    
    if result.get('return_code') != 0:
        raise HTTPException(500, detail={"status": "error", "data": result})
        
    return {"status": "success", "data": {"message": f"L'utilisateur '{req.username}' a été ajouté au groupe '{req.group}'."}}


@router.delete("/group", summary="Retirer un utilisateur d'un groupe")
async def remove_user_from_group(req: UserRequest):
    if req.action != 'del_group' or not req.username or not req.group:
        raise HTTPException(400, detail={"status": "fail", "message": "Action 'del_group' et champs 'username'/'group' requis."})
        
    result = run_playbook("user", req.action, req.dict())
    
    if result.get('return_code') != 0:
        raise HTTPException(500, detail={"status": "error", "data": result})
        
    return {"status": "success", "data": {"message": f"L'utilisateur '{req.username}' a été retiré du groupe '{req.group}'."}}