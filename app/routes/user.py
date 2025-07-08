# On importe 'Depends' pour l'injection de dépendances
from fastapi import APIRouter, HTTPException, Query, Depends
from app.models.user import UserRequest
from app.services import run_playbook
# On importe nos dépendances de sécurité depuis le module d'authentification
from app.auth import get_current_user, require_role

# Importations nécessaires pour la création d'utilisateur dans la DB
import sqlite3
from app.database import APP_DB_FILE, get_user_by_username
from app.security import get_password_hash


router = APIRouter(prefix="/api/user", tags=["user"])


@router.get("", summary="Lister tous les utilisateurs (Authentifié)")
# N'importe quel utilisateur authentifié peut accéder à cette route.
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: dict = Depends(get_current_user)
):
    result = run_playbook("user", "list_users", {})
    
    if result.get('return_code') != 0:
        raise HTTPException(status_code=500, detail={"status": "error", "message": "L'exécution du playbook a échoué.", "data": result})
    
    all_users = result['result'].get('results', [])
    total_users = len(all_users)
    paginated_users = all_users[skip : skip + limit]
    
    return {"status": "success", "data": {"users": paginated_users, "total": total_users, "skip": skip, "limit": limit}}


@router.get("/groups", summary="Lister les groupes (Authentifié)")
# N'importe quel utilisateur authentifié peut accéder à cette route.
async def list_groups(
    username: str = Query(None, description="Optionnel: nom d'utilisateur pour filtrer les groupes"),
    skip: int = Query(0, ge=0),
    limit: int = Query(60, ge=1, le=200),
    current_user: dict = Depends(get_current_user)
):
    payload = {"username": username} if username else {}
    result = run_playbook("user", "list_groups", payload)
    
    if result.get('return_code') != 0:
        raise HTTPException(status_code=500, detail={"status": "error", "message": "L'exécution du playbook a échoué.", "data": result})
        
    all_groups = result['result'].get('results', [])
    total_groups = len(all_groups)
    paginated_groups = all_groups[skip : skip + limit]

    return {"status": "success", "data": {"groups": paginated_groups, "total": total_groups, "skip": skip, "limit": limit}}


@router.post("", summary="Créer un nouvel utilisateur (Admin seulement)")
# On exige le rôle "admin" pour cette route.
async def create_user(req: UserRequest, current_user: dict = Depends(require_role("admin"))):
    if req.action != 'create' or not req.username or not req.password:
        raise HTTPException(400, detail={"status": "fail", "message": "L'action doit être 'create' et les champs 'username' et 'password' sont requis."})

    # Vérifie si l'utilisateur existe déjà dans la base de données de l'API.
    if get_user_by_username(req.username):
        raise HTTPException(status_code=400, detail={"status": "fail", "message": "Ce nom d'utilisateur existe déjà."})

    # Hache le mot de passe avant toute opération.
    hashed_password = get_password_hash(req.password)
    
    # Lance le playbook pour créer l'utilisateur sur le système.
    payload_for_ansible = {"username": req.username, "password": hashed_password}
    result = run_playbook("user", req.action, payload_for_ansible)
    
    if result.get('return_code') != 0:
        raise HTTPException(500, detail={"status": "error", "message": "La création de l'utilisateur sur le système a échoué.", "data": result})

    # Si la création système réussit, on enregistre l'utilisateur dans notre base de données.
    conn = sqlite3.connect(APP_DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users (username, hashed_password) VALUES (?, ?)", (req.username, hashed_password))
    conn.commit()
    conn.close()
    
    return {"status": "success", "data": {"message": f"Utilisateur '{req.username}' créé avec succès."}}


@router.put("", summary="Changer le mot de passe d'un utilisateur (Admin seulement)")
# On exige le rôle "admin" pour cette route.
async def change_password(req: UserRequest, current_user: dict = Depends(require_role("admin"))):
    if req.action != 'password' or not req.username or not req.password:
        raise HTTPException(400, detail={"status": "fail", "message": "L'action doit être 'password' et les champs 'username' et 'password' sont requis."})
    
    # Hache le nouveau mot de passe.
    hashed_password = get_password_hash(req.password)
    
    payload_for_ansible = {"username": req.username, "password": hashed_password}
    result = run_playbook("user", req.action, payload_for_ansible)
    
    if result.get('return_code') != 0:
        raise HTTPException(500, detail={"status": "error", "message": "Le changement de mot de passe a échoué.", "data": result})
    
    # Met à jour le mot de passe dans la base de données de l'API.
    conn = sqlite3.connect(APP_DB_FILE)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET hashed_password = ? WHERE username = ?", (hashed_password, req.username))
    conn.commit()
    conn.close()
    
    return {"status": "success", "data": {"message": f"Mot de passe de l'utilisateur '{req.username}' changé avec succès."}}


@router.delete("", summary="Supprimer un utilisateur (Admin seulement)")
# On exige le rôle "admin" pour cette route.
async def delete_user(req: UserRequest, current_user: dict = Depends(require_role("admin"))):
    if req.action != 'delete' or not req.username:
        raise HTTPException(400, detail={"status": "fail", "message": "L'action doit être 'delete' et le champ 'username' est requis."})
    
    result = run_playbook("user", req.action, req.dict())
    
    if result.get('return_code') != 0:
        raise HTTPException(500, detail={"status": "error", "message": "La suppression de l'utilisateur a échoué.", "data": result})
    
    # Supprime l'utilisateur de la base de données de l'API.
    conn = sqlite3.connect(APP_DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE username = ?", (req.username,))
    conn.commit()
    conn.close()
    
    return {"status": "success", "data": {"message": f"Utilisateur '{req.username}' supprimé avec succès."}}


@router.post("/group", summary="Ajouter un utilisateur à un groupe (Admin seulement)")
# On exige le rôle "admin" pour cette route.
async def add_user_to_group(req: UserRequest, current_user: dict = Depends(require_role("admin"))):
    if req.action != 'add_group' or not req.username or not req.group:
        raise HTTPException(400, detail={"status": "fail", "message": "L'action doit être 'add_group' et les champs 'username' et 'group' sont requis."})
        
    result = run_playbook("user", req.action, req.dict())
    
    if result.get('return_code') != 0:
        raise HTTPException(500, detail={"status": "error", "message": "L'ajout au groupe a échoué.", "data": result})
        
    return {"status": "success", "data": {"message": f"L'utilisateur '{req.username}' a été ajouté au groupe '{req.group}'."}}


@router.delete("/group", summary="Retirer un utilisateur d'un groupe (Admin seulement)")
# On exige le rôle "admin" pour cette route.
async def remove_user_from_group(req: UserRequest, current_user: dict = Depends(require_role("admin"))):
    if req.action != 'del_group' or not req.username or not req.group:
        raise HTTPException(400, detail={"status": "fail", "message": "L'action doit être 'del_group' et les champs 'username' et 'group' sont requis."})
        
    result = run_playbook("user", req.action, req.dict())
    
    if result.get('return_code') != 0:
        raise HTTPException(500, detail={"status": "error", "message": "Le retrait du groupe a échoué.", "data": result})
        
    return {"status": "success", "data": {"message": f"L'utilisateur '{req.username}' a été retiré du groupe '{req.group}'."}}