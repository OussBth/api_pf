# Fichier: app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# On importe directement notre fonction d'initialisation
from app.database import init_db

# Importe les routeurs définis dans les autres fichiers du module 'routes'.
from app.routes.user import router as user_router
from app.routes.webserver import router as webserver_router
from app.routes.streaming import router as streaming_router
from app.routes.actions import router as actions_router
from app.routes.dashboard import router as dashboard_router
from app.routes.auth import router as auth_router

# Crée l'instance de l'application FastAPI. On retire le paramètre 'lifespan'.
app = FastAPI(
    title="API de Contrôle Ansible",
    description="Une API pour piloter des playbooks Ansible via des requêtes HTTP et des WebSockets.",
    version="2.0.0",
)

# Ce décorateur attache la fonction à l'événement "startup" de l'application.
# Elle sera exécutée une seule fois, juste après le démarrage du serveur.
@app.on_event("startup")
def on_startup():
    print("INFO: Démarrage de l'application, initialisation de la base de données...")
    init_db()


# Ajoute le middleware CORS à l'application.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclusion des différents routeurs.
app.include_router(auth_router)
app.include_router(user_router)
app.include_router(webserver_router)
app.include_router(streaming_router)
app.include_router(actions_router)
app.include_router(dashboard_router)


@app.get("/", tags=["Root"])
def read_root():
    return {"message": "Bienvenue sur l'API de Contrôle Ansible"}