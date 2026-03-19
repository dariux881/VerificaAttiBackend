from pydantic import BaseModel, EmailStr, ConfigDict
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum

# --- SCHEMI LOGIN ---
class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    username: str

class TokenData(BaseModel):
    username: Optional[str] = None

# --- SCHEMI UTENTE ---
class UserBase(BaseModel):
    username: str
    email: EmailStr
    full_name: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserRead(UserBase):
    id: str
    is_active: bool
    
    model_config = ConfigDict(from_attributes=True)

class UserLogin(BaseModel):
    username: str
    password: str

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: str | None = None

# --- SCHEMI OPERAZIONE ---
class OperazioneBase(BaseModel):
    param: str

class OperazioneCreate(OperazioneBase):
    owner_id: str # L'ID dell'utente che crea l'operazione

class OperazioneRead(OperazioneBase):
    id: str
    status: str
    owner_id: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    result_data: Optional[Dict[str, Any]] = None
    
    # Opzionale: includere dettagli dell'autore nella risposta
    # author: UserRead 

    model_config = ConfigDict(from_attributes=True)

class FeedbackCreate(BaseModel):
    operazione_id: str
    voto: str  # "UP" | "DOWN"
    commento: Optional[str] = None