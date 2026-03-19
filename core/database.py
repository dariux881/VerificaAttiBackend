from sqlalchemy import create_engine, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


from core.settings import get_settings

# Sostituisci con le tue credenziali PostgreSQL
# db_url = get_settings().SQLALCHEMY_DATABASE_URL
db_url = "postgresql://atti_user:atti_pwd@127.0.0.1:5432/verifica_atti_db"

engine = create_engine(db_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def init_db():
    # Questo comando crea tutte le tabelle definite nei modelli 
    # se non esistono già nel database.
    from models.models import Operazione
    Base.metadata.create_all(bind=engine)

# Dependency per FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()