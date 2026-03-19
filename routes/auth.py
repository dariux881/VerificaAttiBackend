from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from jose import jwt

from core.database import get_db
from core.settings import get_settings
from models.models import User
from core.security import verify_password, create_access_token, create_refresh_token
from models.schemas import Token # Assumi esistano in un file security.py

router = APIRouter(prefix="/auth", tags=["Autenticazione"])

@router.post("/login", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: Session = Depends(get_db)
):
    # 1. Cerca l'utente nel database
    user = db.query(User).filter(User.username == form_data.username).first()
    
    # 2. Verifica esistenza e password
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Username o password errati",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 3. Genera i Token
    access_token = create_access_token(data={"sub": user.id})
    refresh_token = create_refresh_token(data={"sub": user.id})

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "username": user.username
    }

@router.post("/refresh", response_model=Token)
async def refresh_token(old_refresh_token: str, db: Session = Depends(get_db)):
    """
    Riceve un refresh token valido e genera un nuovo access token.
    """
    settings = get_settings()
    try:
        payload = jwt.decode(old_refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid refresh token")
    except Exception:
        raise HTTPException(status_code=401, detail="Refresh token scaduto o non valido")

    # Genera nuova coppia di token
    new_access = create_access_token(data={"sub": user_id})
    new_refresh = create_refresh_token(data={"sub": user_id})

    user = db.query(User).filter(User.id == user_id).first()
    
    return {
        "access_token": new_access,
        "refresh_token": new_refresh,
        "token_type": "bearer",
        "username": user.username
    }

@router.post("/logout")
async def logout():
    """
    Nel JWT stateless, il logout si gestisce lato client eliminando il token.
    Tuttavia, puoi implementare una 'Blacklist' sul DB se vuoi invalidarli lato server.
    """
    return {"detail": "Logout effettuato con successo (rimuovere il token lato client)"}