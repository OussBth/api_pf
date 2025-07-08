from fastapi import APIRouter

# Crée une instance de routeur avec un préfixe commun pour toutes les routes de ce fichier.
router = APIRouter(prefix="/api", tags=["Actions"])

# Ce dictionnaire sert de catalogue central pour toutes les actions possibles.
# C'est la "source de vérité" que l'interface web (test_websocket.html) utilise pour se construire.
# Pour ajouter une nouvelle fonctionnalité à l'interface, il suffit de la décrire ici.
AVAILABLE_ACTIONS = {
    "user": [
        {
            "action_id": "list_users",
            "description": "Lister tous les utilisateurs Linux",
            "required_fields": []
        },
        {
            "action_id": "list_groups",
            "description": "Lister les groupes (tous ou par utilisateur)",
            "required_fields": [
                {"name": "username", "type": "text", "optional": True}
            ]
        },
        {
            "action_id": "create",
            "description": "Créer un nouvel utilisateur",
            "required_fields": [
                {"name": "username", "type": "text"},
                {"name": "password", "type": "password"}
            ]
        }
    ],
    "webserver": [
        {
            "action_id": "list",
            "description": "Lister tous les sites web configurés",
            "required_fields": []
        },
        {
            "action_id": "create",
            "description": "Créer un nouveau site web Nginx",
            "required_fields": [
                {"name": "server_name", "type": "text"},
                {"name": "root_dir(/var/www/\"nom_du_site\")", "type": "text"},
                {"name": "port", "type": "number", "default": 80}
            ]
        },
        {
            "action_id": "delete",
            "description": "Supprimer un site web Nginx",
            "required_fields": [
                {"name": "server_name", "type": "text"}
            ]
        }
    ]
}


@router.get("/actions", summary="Lister toutes les actions de playbook disponibles")
async def get_available_actions():
    """Retourne la liste structurée des services et actions possibles."""
    # Cet endpoint retourne simplement le dictionnaire ci-dessus au format JSON.
    return AVAILABLE_ACTIONS