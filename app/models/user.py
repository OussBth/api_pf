from pydantic import BaseModel
from typing import Literal, Optional

# Définit un modèle de données pour les requêtes liées aux utilisateurs.
# Pydantic valide automatiquement que les données entrantes correspondent à ce schéma.
class UserRequest(BaseModel):
    # 'action' doit être l'une des valeurs de cette liste. Toute autre valeur sera rejetée.
    action: Literal[
        'create', 'delete', 'password',
        'add_group', 'del_group',
        'list_groups', 'list_users', 'create_group'
    ]
    # Les autres champs sont optionnels car ils ne sont pas requis pour toutes les actions.
    username: Optional[str] = None
    password: Optional[str] = None
    group:    Optional[str] = None