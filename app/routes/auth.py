from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta

# Importe les fonctions de sécurité et de base de données que nous avons créées
from app.auth import verify_password, create_access_token
from app.database import get_user_by_username

# Crée un nouveau routeur juste pour l'authentification
router = APIRouter(tags=["Authentication"])

@router.post("/token", summary="Obtenir un jeton d'accès")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Ceci est l'endpoint de connexion.
    Il prend un nom d'utilisateur et un mot de passe (via un formulaire url-encoded)
    et retourne un jeton d'accès JWT si les identifiants sont corrects.
    """
    # 1. On cherche l'utilisateur dans la base de données
    user = get_user_by_username(form_data.username)
    
    # 2. On vérifie si l'utilisateur existe ET si le mot de passe fourni est correct
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        # Si ce n'est pas le cas, on lève une erreur 401 Non Autorisé
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    # 3. Si tout est correct, on crée un jeton d'accès pour cet utilisateur
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user["username"]}, expires_delta=access_token_expires
    )
    
    # 4. On retourne le jeton au client
    return {"access_token": access_token, "token_type": "bearer"}