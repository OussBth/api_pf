from fastapi import APIRouter, HTTPException, Query
from app.models.user import UserRequest
from app.services import run_playbook

router = APIRouter(prefix="/api/user", tags=["user"])

@router.get("", summary="Lister tous les utilisateurs avec pagination")
async def list_users(skip: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=200)):
    """
    Retourne une liste paginée de tous les utilisateurs du système.
    - **skip**: Nombre d'utilisateurs à sauter (début à 0).
    - **limit**: Nombre maximum d'utilisateurs à retourner (entre 1 et 200).
    """
    result = run_playbook("user", "list_users", {})
    
    if result.get('return_code') != 0:
        raise HTTPException(status_code=500, detail={
            "status": "error",
            "message": "L'exécution du playbook pour lister les utilisateurs a échoué.",
            "data": result
        })
    
    all_users = result['result'].get('results', [])
    total_users = len(all_users)
    paginated_users = all_users[skip : skip + limit]
    
    return {
        "status": "success",
        "data": {
            "users": paginated_users,
            "total": total_users,
            "skip": skip,
            "limit": limit
        }
    }

@router.get("/groups", summary="Lister les groupes avec pagination")
async def list_groups(
    username: str = Query(None, description="Optionnel: nom d'utilisateur pour filtrer les groupes"),
    skip: int = Query(0, ge=0),
    limit: int = Query(60, ge=1, le=200)
):
    """
    Retourne une liste paginée de groupes.
    - **username**: Si fourni, liste les groupes de cet utilisateur. Sinon, tous les groupes du système.
    - **skip**: Nombre de groupes à sauter.
    - **limit**: Nombre maximum de groupes à retourner.
    """
    payload = {"username": username} if username else {}
    result = run_playbook("user", "list_groups", payload)
    
    if result.get('return_code') != 0:
        raise HTTPException(status_code=500, detail={
            "status": "error",
            "message": "L'exécution du playbook pour lister les groupes a échoué.",
            "data": result
        })
        
    all_groups = result['result'].get('results', [])
    total_groups = len(all_groups)
    paginated_groups = all_groups[skip : skip + limit]

    return {
        "status": "success",
        "data": {
            "groups": paginated_groups,
            "total": total_groups,
            "skip": skip,
            "limit": limit
        }
    }


@router.post("", summary="Créer un nouvel utilisateur")
async def create_user(req: UserRequest):
    if req.action != 'create' or not req.username or not req.password:
        raise HTTPException(400, detail={
            "status": "fail",
            "message": "L'action doit être 'create' et les champs 'username' et 'password' sont requis."
        })
    
    result = run_playbook("user", req.action, req.dict())
    
    if result.get('return_code') != 0:
        raise HTTPException(500, detail={
            "status": "error", "message": "La création de l'utilisateur a échoué.", "data": result
        })
    
    return {"status": "success", "data": {"message": f"Utilisateur '{req.username}' créé avec succès."}}

@router.post("/group/create", summary="Créer un nouveau groupe")
async def create_group(req: UserRequest):
    if req.action != 'create_group' or not req.group:
        raise HTTPException(400, detail={
            "status": "fail", "message": "L'action doit être 'create_group' et le champ 'group' est requis."
        })
    
    result = run_playbook("user", req.action, req.dict())
    
    if result.get('return_code') != 0:
        raise HTTPException(500, detail={
            "status": "error", "message": "La création du groupe a échoué.", "data": result
        })
    
    return {"status": "success", "data": {"message": f"Groupe '{req.group}' créé avec succès."}}

@router.post("/group", summary="Ajouter un utilisateur à un groupe")
async def add_user_to_group(req: UserRequest):
    if req.action != 'add_group' or not req.username or not req.group:
        raise HTTPException(400, detail={
            "status": "fail", "message": "L'action doit être 'add_group' et les champs 'username' et 'group' sont requis."
        })
        
    result = run_playbook("user", req.action, req.dict())
    
    if result.get('return_code') != 0:
        raise HTTPException(500, detail={
            "status": "error", "message": "L'ajout au groupe a échoué.", "data": result
        })
        
    return {"status": "success", "data": {"message": f"L'utilisateur '{req.username}' a été ajouté au groupe '{req.group}'."}}

@router.delete("/group", summary="Retirer un utilisateur d'un groupe")
async def remove_user_from_group(req: UserRequest):
    if req.action != 'del_group' or not req.username or not req.group:
        raise HTTPException(400, detail={
            "status": "fail", "message": "L'action doit être 'del_group' et les champs 'username' et 'group' sont requis."
        })
        
    result = run_playbook("user", req.action, req.dict())
    
    if result.get('return_code') != 0:
        raise HTTPException(500, detail={
            "status": "error", "message": "Le retrait du groupe a échoué.", "data": result
        })
        
    return {"status": "success", "data": {"message": f"L'utilisateur '{req.username}' a été retiré du groupe '{req.group}'."}}

@router.delete("", summary="Supprimer un utilisateur")
async def delete_user(req: UserRequest):
    if req.action != 'delete' or not req.username:
        raise HTTPException(400, detail={
            "status": "fail", "message": "L'action doit être 'delete' et le champ 'username' est requis."
        })
    
    result = run_playbook("user", req.action, req.dict())
    
    if result.get('return_code') != 0:
        raise HTTPException(500, detail={
            "status": "error", "message": "La suppression de l'utilisateur a échoué.", "data": result
        })
    
    return {"status": "success", "data": {"message": f"Utilisateur '{req.username}' supprimé avec succès."}}

@router.put("", summary="Changer le mot de passe d'un utilisateur")
async def change_password(req: UserRequest):
    if req.action != 'password' or not req.username or not req.password:
        raise HTTPException(400, detail={
            "status": "fail", "message": "L'action doit être 'password' et les champs 'username' et 'password' sont requis."
        })
    
    result = run_playbook("user", req.action, req.dict())
    
    if result.get('return_code') != 0:
        raise HTTPException(500, detail={
            "status": "error", "message": "Le changement de mot de passe a échoué.", "data": result
        })
    
    return {"status": "success", "data": {"message": f"Mot de passe de l'utilisateur '{req.username}' changé avec succès."}}