import bcrypt
from datetime import datetime, timedelta, timezone
from jose import jwt
from core.settings import get_settings

settings = get_settings()
print(f"DEBUG: Secret Key caricata: {settings.SECRET_KEY[:5]}...")

def get_password_hash(password: str) -> str:
    # Genera il sale
    salt = bcrypt.gensalt()
    # Genera l'hash (ritorna bytes)
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    # Converti in stringa per salvarlo nel DB
    return hashed.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    # Confronta la password in chiaro con l'hash (entrambi convertiti in bytes)
    return bcrypt.checkpw(
        plain_password.encode('utf-8'), 
        hashed_password.encode('utf-8')
    )

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def create_refresh_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)