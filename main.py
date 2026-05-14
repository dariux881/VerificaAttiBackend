from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from core.settings import get_settings

from routes import verifica_atti, auth, verifica_atti_tools, admin

settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    from core.database import init_db
    from core.logging import setup_logging

    # Eseguito all'avvio
    setup_logging(settings)

    # init_db() # **NB:** don't call init_db in production. Use alembic instead
    yield
    # Eseguito allo spegnimento (pulizia se necessaria)

app = FastAPI(lifespan=lifespan)

# Configurazione CORS per permettere a React di comunicare con FastAPI
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(verifica_atti.router)
app.include_router(auth.router)
app.include_router(verifica_atti_tools.router)
app.include_router(admin.router)

if __name__ == "__main__":
    import uvicorn
    import sys

    try:
        print(f"Avvio in corso sulla porta: {settings.PORT}")
        uvicorn.run(app, host=settings.HOST, port=settings.PORT)
    except Exception as e:
        # Questo scriverà l'errore nello stdout che systemd dovrebbe catturare
        print(f"ERRORE FATALE ALL'AVVIO: {e}", file=sys.stderr)
        sys.exit(1)