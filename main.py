from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from core.database import init_db

from core.settings import get_settings

from routes import verifica_atti, auth, verifica_atti_tools, admin

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Eseguito all'avvio
    init_db()
    yield
    # Eseguito allo spegnimento (pulizia se necessaria)

app = FastAPI(lifespan=lifespan)

# Configurazione CORS per permettere a React di comunicare con FastAPI
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().ALLOWED_HOSTS,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(verifica_atti.router)
app.include_router(auth.router)
app.include_router(verifica_atti_tools.router)
app.include_router(admin.router)

if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        app, 
        host=settings.HOST, 
        port=settings.PORT)