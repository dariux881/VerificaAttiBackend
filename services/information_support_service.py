from datetime import datetime, date, timedelta
from models.schemas import CDRVersion as CDRInput
from models.models import CDRVersion as CDRVersionDB
from sqlalchemy.orm import Session

from sqlalchemy import and_, update
from typing import Optional, Dict, Any
import uuid

class InformationSupportService:
    @staticmethod
    def import_cdr_table(db: Session, cdr_input : CDRInput, user_id : str):
        """
        Gestisce l'inserimento di una nuova versione CDR mantenendo la coerenza temporale.
        """
        # 1. Preparazione dati iniziali
        nuovo_inizio = cdr_input.inizio_validita.date()
        # Se non specificata, la fine è il 31-12-9999
        nuova_fine = cdr_input.fine_validita.date() if cdr_input.fine_validita else date(9999, 12, 31)
        
        # Crea nome_versione se manca
        nome_versione = cdr_input.nome_versione or f"Versione_{nuovo_inizio.strftime('%Y%m%d')}"
        
        try:
            # INIZIO TRANSAZIONE (gestito dal context manager del chiamante o db.begin())
            
            # 2. Chiudi la versione precedente
            # Cerchiamo la tabella che è attualmente "aperta" (quella che copre il nuovo inizio)
            # e la accorciamo al giorno prima.
            giorno_prima = nuovo_inizio - timedelta(days=1)
            
            # Aggiorniamo le tabelle esistenti la cui validità si sovrappone al nuovo inizio
            db.query(CDRVersionDB).filter(
                and_(
                    CDRVersionDB.inizio_validita < nuovo_inizio,
                    CDRVersionDB.fine_validita >= nuovo_inizio
                )
            ).update({"fine_validita": giorno_prima})

            # 3. Verifica sovrapposizioni future
            # Verifichiamo se esistono tabelle che iniziano proprio nel periodo della nuova
            conflitto = db.query(CDRVersionDB).filter(
                and_(
                    CDRVersionDB.inizio_validita >= nuovo_inizio,
                    CDRVersionDB.inizio_validita <= nuova_fine
                )
            ).first()

            if conflitto:
                raise ValueError(f"Conflitto di date: esiste già una tabella che inizia il {conflitto.inizio_validita}")

            dati_serializzabili = {
                codice: entry.model_dump() for codice, entry in cdr_input.dati.items()
            }

            # 4. Creazione dell'oggetto DB
            nuova_entry = CDRVersionDB(
                id=str(uuid.uuid4()), # Creazione ID univoco (UUID)
                nome_versione=nome_versione,
                inizio_validita=nuovo_inizio,
                fine_validita=nuova_fine,
                dati=dati_serializzabili
            )

            db.add(nuova_entry)
            
            # 5. Commit della transazione
            db.commit()
            db.refresh(nuova_entry)
            return nuova_entry

        except Exception as e:
            db.rollback() # Annulla tutto in caso di errore
            raise e