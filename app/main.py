from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.user import router as user_router
from app.routes.webserver import router as webserver_router
from app.routes.streaming import router as streaming_router
from app.routes.actions import router as actions_router

app = FastAPI(
    title="API de Contrôle Ansible",
    description="Une API pour piloter des playbooks Ansible via des requêtes HTTP et des WebSockets.",
    version="2.0.0",
)

# AJOUT : Configuration du middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Autorise toutes les origines (pour le développement)
    allow_credentials=True,
    allow_methods=["*"],  # Autorise toutes les méthodes (GET, POST, etc.)
    allow_headers=["*"],  # Autorise tous les en-têtes
)


# Inclusion des différents routeurs de l'application
app.include_router(user_router)
app.include_router(webserver_router)
app.include_router(streaming_router)
app.include_router(actions_router)


@app.get("/", tags=["Root"])
def root():
    return {"message": "Bienvenue sur l'API de Contrôle Ansible"}