from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from models.models import Operazione, StatusEnum
import uuid
from datetime import datetime, timezone

class OperationService:
    @staticmethod
    def create_or_start(db: Session, parametro: str, user_id: str):
        # 1. Cerchiamo se esiste già il parametro
        op_esistente = db.query(Operazione).filter(Operazione.param == parametro).first()

        if op_esistente:
            # Se è PENDING, blocchiamo tutto
            if op_esistente.status == StatusEnum.PENDING:
                return None, "Operazione già in corso."
            
            # Se è DONE o ERROR, la "resettiamo" per un nuovo invio
            op_esistente.id = str(uuid.uuid4()) # Nuovo ID per il nuovo ciclo n8n
            op_esistente.status = StatusEnum.PENDING
            op_esistente.result_data = None
            op_esistente.created_at = datetime.now(timezone.utc)
            op_esistente.owner_id = user_id
            op_esistente.completed_at = None
            db.commit()
            return op_esistente, None

        # 2. Se non esiste, creiamo un nuovo record
        nuova_op = Operazione(
            id=str(uuid.uuid4()),
            param=parametro,
            status=StatusEnum.PENDING,
            owner_id = user_id,
            created_at = datetime.now(timezone.utc)
        )
        try:
            db.add(nuova_op)
            db.commit()
            db.refresh(nuova_op)
            return nuova_op, None
        except IntegrityError:
            db.rollback()
            return None, "Race condition: l'operazione è stata avviata simultaneamente da un altro utente."

    @staticmethod
    def process_result_and_save(db: Session, op_id: str, payload_data: dict):
        """
        Gestisce l'intera logica di ricezione dati da n8n:
        Parsing -> Calcolo Esito -> Persistenza
        """
        # 1. Recupero operazione
        db_op = db.query(Operazione).filter(Operazione.id == op_id).first()
        if not db_op:
            return False

        # 2. Trasformazione e calcolo esito peggiore (delegato a metodo interno)
        lista_grezza = payload_data.get("esito", [])
        outcome_status = StatusEnum.DONE
        result_data = None

        try:
            categorie, globali = OperationService._process_result_logic(lista_grezza)
            result_data = {
                "categorie": categorie,
                "globali": globali
            }
        except Exception as e:
            print(str(e))
            outcome_status = StatusEnum.ERROR

        # 3. Aggiornamento stato e dati
        db_op.status = outcome_status
        db_op.completed_at = datetime.now(timezone.utc)
        db_op.result_data = result_data
        
        db.commit()
        return outcome_status == StatusEnum.DONE

    @staticmethod
    def process_error_result_and_save(db: Session, op_id: str):
        """
        Gestisce l'intera logica di ricezione dati da n8n:
        Parsing -> Calcolo Esito -> Persistenza
        """
        # 1. Recupero operazione
        db_op = db.query(Operazione).filter(Operazione.id == op_id).first()
        if not db_op:
            return False

        # 2. Trasformazione e calcolo esito peggiore (delegato a metodo interno)
        outcome_status = StatusEnum.ERROR

        # 3. Aggiornamento stato e dati
        db_op.status = outcome_status
        db_op.completed_at = datetime.now(timezone.utc)
        db_op.result_data = None
        
        db.commit()
        return True

    @staticmethod
    def _process_result_logic(lista_grezza: list):
        """Metodo privato per la pura logica algoritmica"""
        categorie_pulite = {}
        info_globali = {}

        def get_worst(current, new):
            priority = {"NON_VALIDATO": 3, "WARNING": 2, "VALIDATO": 1, "": 0, None: 0}
            return new if priority.get(new, 0) > priority.get(current, 0) else current

        for item in lista_grezza:
            inner_controlli = item.get("controlli", [])
            if isinstance(inner_controlli, list) and len(inner_controlli) > 0:
                for block in inner_controlli:
                    target = block.get("output", {})
                    cat = target.get("categoria")
                    if cat:
                        if cat not in categorie_pulite:
                            categorie_pulite[cat] = {'titolo': cat, 'esito_globale': 'VALIDATO', 'controlli': []}
                        
                        atomici = target.get("controlli", [])
                        categorie_pulite[cat]['controlli'].append(atomici)
                        for ctrl in atomici:
                            categorie_pulite[cat]['esito_globale'] = get_worst(categorie_pulite[cat]['esito_globale'], ctrl.get("esito"))
            else:
                target = item.get("output", {})
                if "esito_finale_pratica" in target:
                    info_globali = {
                        "giudizio": target.get("giudizio_sintetico"),
                        "esito_finale": target.get("esito_finale_pratica")
                    }
        
        return categorie_pulite, info_globali