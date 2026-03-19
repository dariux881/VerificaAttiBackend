from sqlalchemy.orm import Session
from core.database import SessionLocal, engine
from models import models
from core.security import get_password_hash
import uuid

def create_superuser():
    db: Session = SessionLocal()
    
    # 1. Dati dell'admin
    admin_username = "dario"
    admin_email = "dario@esempio.it"
    admin_password = "PasswordSegreta123!" # Cambiala subito!

    # 2. Controllo se esiste già
    user_exists = db.query(models.User).filter(models.User.username == admin_username).first()
    if user_exists:
        print(f"L'utente {admin_username} esiste già.")
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
        print(f"--- UTENTE ADMIN CREATO CON SUCCESSO ---")
        print(f"Username: {admin_username}")
        print(f"Password: {admin_password}")
        print(f"-----------------------------------------")
    except Exception as e:
        db.rollback()
        print(f"Errore durante la creazione: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    create_superuser()