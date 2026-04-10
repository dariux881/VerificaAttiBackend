from sqlalchemy.orm import Session
from core.database import SessionLocal, engine
from models import models
from core.security import get_password_hash
import uuid
import logging

logger = logging.getLogger(__name__)

def create_superuser():
    db: Session = SessionLocal()
    
    # 1. Dati dell'admin
    admin_username = "admin"
    admin_email = "admin@esempio.it"
    admin_password = "PasswordSegreta123!" # Cambiala subito!

    # 2. Controllo se esiste già
    user_exists = db.query(models.User).filter(models.User.username == admin_username).first()
    if user_exists:
        logger.error(f"L'utente {admin_username} esiste già.")
        return

    # 3. Creazione record con password hashata
    new_admin = models.User(
        id=str(uuid.uuid4()),
        username=admin_username,
        email=admin_email,
        hashed_password=get_password_hash(admin_password),
        full_name="Operatore",
        is_active=True
    )

    try:
        db.add(new_admin)
        db.commit()
        logger.info(f"--- UTENTE ADMIN CREATO CON SUCCESSO ---")
        logger.info(f"Username: {admin_username}")
        logger.debug(f"Password: {admin_password}")
        logger.info(f"-----------------------------------------")
    except Exception as e:
        db.rollback()
        logger.error(f"Errore durante la creazione: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    create_superuser()