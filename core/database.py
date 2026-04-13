from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from core.settings import get_settings
import logging

logger = logging.getLogger(__name__)

# Sostituisci con le tue credenziali PostgreSQL
db_url = get_settings().DATABASE_URL

logger.debug(f"database URL: {db_url}")
print(f"database URL: {db_url}")

engine = create_engine(db_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def init_db():
    try:
        # Questo comando crea tutte le tabelle definite nei modelli 
        # se non esistono già nel database.
        from models.models import Operazione, TokenBlacklist, User, Feedback
        Base.metadata.create_all(bind=engine)

        logger.info("DB created successfully")
    except Exception as e:
        logger.error(f"Error in creating DB: {str(e)}")
        raise

# Dependency per FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()