from fastapi import APIRouter

router = APIRouter(prefix="/api", tags=["Actions"])

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
                {"name": "root_dir", "type": "text"},
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
    """Retourne une liste structurée des services et actions possibles."""
    return AVAILABLE_ACTIONS