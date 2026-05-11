from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt, ExpiredSignatureError
from sqlalchemy.orm import Session

from core.settings import get_settings
from core.database import get_db
from models.models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def get_current_user_id_core(token: str, db : Session, skip_change_pwd = False) -> str:
    """
    Estrae lo user_id (sub) dal token JWT.
    """
    settings = get_settings()

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={"code": "INVALID_CREDENTIALS", "message": "Sessione non valida o scaduta"},
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )

        user_id: str = payload.get("sub") # 'sub' è lo standard per l'ID utente
        
        if user_id is None:
            raise credentials_exception
    
    except ExpiredSignatureError:
        # CASO SPECIFICO: Il token è valido ma è SCADUTO.
        # Solleviamo un'eccezione che suggerisce il redirect al login.
        # Nota: In un'API pura si restituisce spesso 401, 
        # ma se vuoi forzare il redirect:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "TOKEN_EXPIRED", "message": "La sessione è scaduta"}
        )

    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "USER_INACTIVE", "message": "L'account utente è disabilitato"}
        )

    if user.is_locked:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "USER_LOCKED", "message": "L'account è bloccato"}
        )

    # BLOCCO CRITICO: Se l'utente deve cambiare password, non può fare altro
    if user.must_change_password and not skip_change_pwd:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "PASSWORD_CHANGE_REQUIRED", 
                "message": "Operazione non permessa: è necessario cambiare la password"
            }
        )

    return user_id

def get_unverified_user_id(
        token: str = Depends(oauth2_scheme), 
        db: Session = Depends(get_db)) -> str:
    return get_current_user_id_core(
        token=token, 
        db=db,
        skip_change_pwd=True)

def get_current_user_id(
        token: str = Depends(oauth2_scheme), 
        db: Session = Depends(get_db)) -> str:
    return get_current_user_id_core(token=token, 
        db=db,
        skip_change_pwd=False)