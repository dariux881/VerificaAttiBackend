from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt, ExpiredSignatureError
from core.settings import get_settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_current_user_id(token: str = Depends(oauth2_scheme)) -> str:
    """
    Estrae lo user_id (sub) dal token JWT.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Impossibile validare le credenziali",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        settings = get_settings()
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )

        user_id: str = payload.get("sub") # 'sub' è lo standard per l'ID utente
        
        if user_id is None:
            raise credentials_exception
        
        return user_id
    
    except ExpiredSignatureError:
        # CASO SPECIFICO: Il token è valido ma è SCADUTO.
        # Solleviamo un'eccezione che suggerisce il redirect al login.
        # Nota: In un'API pura si restituisce spesso 401, 
        # ma se vuoi forzare il redirect:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="TOKEN_EXPIRED"
        )

    except JWTError:
        raise credentials_exception