# Importe la classe principale de FastAPI pour créer l'application.
from fastapi import FastAPI
# Importe le middleware pour gérer les requêtes Cross-Origin (CORS).
from fastapi.middleware.cors import CORSMiddleware

# Importe les routeurs définis dans les autres fichiers du module 'routes'.
# Chaque routeur est comme un chapitre de votre API, gérant une section logique.
from app.routes.user import router as user_router
from app.routes.webserver import router as webserver_router
from app.routes.streaming import router as streaming_router
from app.routes.actions import router as actions_router

# Crée une instance de l'application FastAPI.
# Les métadonnées comme 'title' et 'description' apparaîtront dans la documentation automatique (ex: /docs).
app = FastAPI(
    title="API de Contrôle Ansible",
    description="Une API pour piloter des playbooks Ansible via des requêtes HTTP et des WebSockets.",
    version="2.0.0",
)

# Ajoute le middleware CORS à l'application.
# C'est une sécurité de navigateur qui empêche une page web d'une origine
# de faire des requêtes à une autre. Ce middleware donne la permission.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Autorise toutes les origines. Pour la production, on mettrait ici l'URL du frontend.
    allow_credentials=True,
    allow_methods=["*"],  # Autorise toutes les méthodes HTTP (GET, POST, PUT, DELETE, etc.).
    allow_headers=["*"],  # Autorise tous les en-têtes HTTP.
)

# Inclusion des différents routeurs dans l'application principale.
# C'est ce qui rend les endpoints de chaque fichier accessibles.
app.include_router(user_router)
app.include_router(webserver_router)
app.include_router(streaming_router) # Le routeur pour le WebSocket temps réel.
app.include_router(actions_router)   # Le routeur pour le catalogue d'actions.


@app.get("/", tags=["Root"])
def read_root():
    """
    Point de terminaison racine de l'API.
    Utile pour une vérification rapide (health check) pour voir si le serveur est en ligne.
    """
    return {"message": "Bienvenue sur l'API de Contrôle Ansible"}