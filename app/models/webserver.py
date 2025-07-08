from pydantic import BaseModel
from typing import Literal, Optional

# Définit un modèle de données pour les requêtes liées aux sites web.
class WebsiteRequest(BaseModel):
    # Valide que l'action est l'une des actions autorisées.
    action: Literal[
        'create', 'delete', 'enable', 'disable', 'update'
    ]
    # Le nom du serveur (domaine) est toujours requis.
    server_name: str
    # Le dossier racine n'est requis que pour certaines actions (ex: 'create').
    root_dir: Optional[str] = None
    # Le port a une valeur par défaut de 80 si non fourni.
    port: int = 80