from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.database import init_db
from app.routes.user import router as user_router
from app.routes.webserver import router as webserver_router
from app.routes.streaming import router as streaming_router
from app.routes.actions import router as actions_router
from app.routes.dashboard import router as dashboard_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(
    title="API de Contrôle Ansible",
    description="Une API pour piloter des playbooks Ansible.",
    version="1.5.0", # Version simplifiée
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# On n'inclut plus le routeur d'authentification
app.include_router(user_router)
app.include_router(webserver_router)
app.include_router(streaming_router)
app.include_router(actions_router)
app.include_router(dashboard_router)

@app.get("/", tags=["Root"])
def read_root():
    return {"message": "Bienvenue sur l'API de Contrôle Ansible"}