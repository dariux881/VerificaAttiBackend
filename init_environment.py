from sqlalchemy.orm import Session
from core.database import SessionLocal, engine
from models import models
from core.security import get_password_hash
import uuid
import logging

logger = logging.getLogger(__name__)

def create_superuser(db):

    # 1. Dati dell'admin
    admin_username = "admin"
    admin_email = "admin@esempio.it"
    admin_password = "PasswordSegreta123!" # Cambiala subito!

    # 2. Controllo se esiste già
    user_exists = db.query(models.User).filter(models.User.username == admin_username).first()
    if user_exists:
        logger.warning(f"L'utente {admin_username} esiste già.")
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

def import_cdr_table(db):
    from core.settings import get_settings
    import os
    from pydantic_core import from_json
    from models.schemas import CDRVersion
    from services.information_support_service import InformationSupportService

    try:
        user_id = db.query(models.User).first() #TODO FILTER FOR ADMIN USER

        cdr_json = os.path.join(get_settings().SOURCES_BASE_PATH, 'init_cdr_table.json')
        if not os.path.isfile(cdr_json):
            logger.warning(f"'${cdr_json}' is not a valid file")
            return

        with open(cdr_json, 'r') as json_data:
            d = json_data.read()
            cdr = CDRVersion.model_validate(from_json(d))
            
            InformationSupportService.import_cdr_table(db, cdr, user_id)

            logger.info(f"--- TABELLA CDR IMPORTATA CON SUCCESSO ---")
    except Exception as e:
        db.rollback()
        logger.error(f"Errore durante l'import della tabella CDR: {str(e)}")
    finally:
        db.close()

def init_db(db):
    create_superuser(db)
    import_cdr_table(db)

if __name__ == "__main__":
    db: Session = SessionLocal()
    init_db(db)