from datetime import datetime, timezone
import enum
import uuid
from pydantic import BaseModel
from sqlalchemy import Boolean, Column, ForeignKey, String, DateTime, JSON, Enum, Text
from sqlalchemy.orm import relationship
from typing import List, Optional, Dict, Any

from core.database import Base

class StatusEnum(str, enum.Enum):
    PENDING = "PENDING"
    DONE = "DONE"
    ERROR = "ERROR"
    
class User(Base):
    __tablename__ = "utenti"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))

    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)

    full_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relazione: permette di accedere a user.operazioni
    operazioni = relationship("Operazione", back_populates="author", cascade="all, delete-orphan")

class TokenBlacklist(Base):
    __tablename__ = "token_blacklist"
    
    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    token = Column(String, unique=True, index=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)

class Operazione(Base):
    __tablename__ = "operazioni"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4())) # UUID generato
    param = Column(String, index=True)
    status = Column(String, default=StatusEnum.PENDING)

    owner_id = Column(String, ForeignKey("utenti.id"), nullable=False)
    
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    completed_at = Column(DateTime, default=None, nullable=True)
    result_data = Column(JSON, nullable=True)        # Qui salviamo categorie e globali

    # Relazione: permette di accedere a operazione.author
    author = relationship("User", back_populates="operazioni")

class Feedback(Base):
    __tablename__ = "feedbacks"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, index=True) # Chi ha dato il feedback
    operazione_id = Column(String)      # ID originale (per tracciamento)
    voto = Column(String)                # "UP" o "DOWN"
    commento = Column(Text, nullable=True)
    
    # Snapshot dei dati dell'operazione
    param = Column(String)
    status = Column(String)
    result_data = Column(JSON)           # Copia esatta dei risultati
    created_at_op = Column(DateTime)     # Quando è nata l'op
    completed_at_op = Column(DateTime)   # Quando è finita l'op
    submitted_at = Column(DateTime, default=datetime.now(timezone.utc))