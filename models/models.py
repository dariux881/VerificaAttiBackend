from datetime import datetime, timezone
import enum
import uuid
from pydantic import BaseModel
from sqlalchemy import Boolean, Column, ForeignKey, String, DateTime, JSON, Enum, Text, Integer, Date
from sqlalchemy.orm import relationship
from typing import List, Optional, Dict, Any

from core.database import Base

class StatusEnum(str, enum.Enum):
    PENDING = "PENDING"
    DONE = "DONE"
    ERROR = "ERROR"

class Settings(Base):
    __tablename__ = "settings"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    key = Column(String, unique=True)
    value = Column(String)
    notes = Column(String, nullable=True)

    created_by = Column(String, nullable=False)
    updated_by = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True))
    updated_at = Column(DateTime(timezone=True))


class User(Base):
    __tablename__ = "utenti"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))

    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)

    full_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relazione: permette di accedere a user.operazioni
    operazioni = relationship("Operazione", back_populates="author", cascade="all, delete-orphan")

class TokenBlacklist(Base):
    __tablename__ = "token_blacklist"
    
    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    token = Column(String, unique=True, index=True, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)

class Operazione(Base):
    __tablename__ = "operazioni"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4())) # UUID generato
    param = Column(String, index=True)
    status = Column(String, default=StatusEnum.PENDING)

    owner_id = Column(String, ForeignKey("utenti.id"), nullable=False)
    
    created_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))
    completed_at = Column(DateTime(timezone=True), default=None, nullable=True)
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
    created_at_op = Column(DateTime(timezone=True))     # Quando è nata l'op
    completed_at_op = Column(DateTime(timezone=True))   # Quando è finita l'op
    submitted_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))

class CDRVersion(Base):
    __tablename__ = 'cdr_versions'

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    nome_versione = Column(String(100), nullable=False)
    
    # Range di validità (Granularità Giornaliera)
    inizio_validita = Column(Date, nullable=False, index=True)
    fine_validita = Column(Date, nullable=False, index=True)
    
    # Il contenuto della tabella (i codici e i dettagli)
    # Usiamo JSON per flessibilità, o una tabella correlata se preferisci
    dati = Column(JSON, nullable=False) 

    def __repr__(self):
        return f"<CDRVersion(nome={self.nome_versione}, dal={self.inizio_validita}, al={self.fine_validita})>"