from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from jose import jwt

from core.database import get_db
from core.settings import get_settings
from models.models import User
from core.security import verify_password, create_access_token, create_refresh_token, get_password_hash
from models.schemas import Token, PasswordChange
from core.auth import get_current_user_id, get_unverified_user_id

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
            detail={"code": "INVALID_CREDENTIALS", "message": "Username o password errati"},
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 3. Genera i Token
    access_token = create_access_token(data={"sub": user.id})
    refresh_token = create_refresh_token(data={"sub": user.id})
    
    if user.must_change_password:
        # Restituiamo 200 o un codice specifico, ma includiamo i token 
        # affinché il front-end possa chiamare /change-password
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "username": user.username,
            "must_change_password": True 
        }

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "username": user.username,
        "must_change_password": False
    }

@router.post("/refresh", response_model=Token)
async def refresh_token(
    old_refresh_token: str, 
    db: Session = Depends(get_db)):
    """
    Riceve un refresh token valido e genera un nuovo access token.
    """
    settings = get_settings()
    try:
        payload = jwt.decode(old_refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=401, 
                detail={"code": "INVALID_CREDENTIALS", "message": "Invalid refresh token"})
    except Exception:
        raise HTTPException(status_code=401, detail={"code": "TOKEN_EXPIRED", "message": "Refresh token scaduto o non valido"})

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

@router.post("/change-password", status_code=status.HTTP_200_OK)
async def change_password(
    password_data: PasswordChange,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_unverified_user_id) # Verifica che l'utente sia loggato
):
    """
    Endpoint per il cambio password dell'utente autenticato.
    """
    
    # 1. Cerchiamo l'utente nel database tramite l'ID estratto dal token
    current_user = db.query(User).filter(User.id == current_user_id).first()

    # 2. Verifichiamo che l'utente esista e non sia disabilitato
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "INVALID_USER", "message": "Invalid user"}
        )
    
    # 3. Verifichiamo che l'utente esista e che non sia disabilitato
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "NOT_ACTIVE_USER", "message": "Invalid user"}
        )
    
    # 3.1. Check if locked
    if current_user.is_locked:
        raise HTTPException(status_code=403, detail={"code": "LOCKED_ACCOUNT", "message": "Invalid user"})

    # 4. Verifichiamo che la vecchia password sia corretta
    if not verify_password(password_data.old_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "INVALID_CREDENTIALS", "message": "Invalid user"}
        )

    # 5. Generiamo l'hash della nuova password
    new_hashed_password = get_password_hash(password_data.new_password)
    
    # 6. Aggiorniamo il database
    current_user.hashed_password = new_hashed_password
    current_user.must_change_password = False

    db.commit()

    return {"detail": "Password aggiornata con successo"}

@router.post("/logout")
async def logout(current_user_id: str = Depends(get_current_user_id)):
    """
    Nel JWT stateless, il logout si gestisce lato client eliminando il token.
    Tuttavia, puoi implementare una 'Blacklist' sul DB se vuoi invalidarli lato server.
    """
    return {"detail": "Logout effettuato con successo (rimuovere il token lato client)"}



@router.post("/reset-password")
async def reset_password(
    user_name: str,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id)
):
    ##TODO CHECK ADMIN USER
    target_user = db.query(User).filter(User.username == user_name).first()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail={"code": "INVALID_USER", "message": "Invalid user"})
    
    target_user.must_change_password = True
    target_user.is_active = True
    target_user.is_locked = False
    target_user.hashed_password = get_password_hash("Comunale123!")
    
    db.commit()

    return {"detail": "Password aggiornata con successo"}
