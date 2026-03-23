from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
import httpx
from sqlalchemy.orm import Session
from core.auth import get_current_user_id
from core.database import get_db

from core.settings import get_settings
from models.models import Feedback, Operazione, StatusEnum
from models.schemas import FeedbackCreate, OperazioneRead
from services.operation_service import OperationService

# Creiamo il router con un prefisso e dei tag per la documentazione automatica
router = APIRouter(
    prefix="/api/v1/verifica-atti",
    tags=["Gestione Verifica Atti"]
)

# --- ENDPOINT 1: AVVIO OPERAZIONE ---
@router.post("/start", response_model=OperazioneRead)
async def start_acts_check(
        parametro: str, 
        background_tasks: BackgroundTasks, 
        db: Session = Depends(get_db), 
        current_user_id: str = Depends(get_current_user_id)
    ):

    # Delega al service la gestione della consistenza
    op, errore = OperationService.create_or_start(db, parametro, current_user_id)
    
    if errore:
        raise HTTPException(status_code=400, detail=errore)

    # Funzione interna per invio a n8n
    async def send_operation_request(id_req, p):
        async with httpx.AsyncClient() as client:
            await client.post(get_settings().VERIFICA_ATTI_WEBHOOK_URL, json={"id_operazione": id_req, "testo": p})

    background_tasks.add_task(send_operation_request, op.id, parametro)
    return op

# --- ENDPOINT 2: RICEZIONE ESITO DA N8N ---
@router.post("/webhook-callback")
async def receive_result(payload: dict, db: Session = Depends(get_db)):
    # Il router estrae solo i parametri fondamentali
    id_op = payload.get("id_operazione")
    data = payload.get("data", {})

    # Delega tutta la logica di business e persistenza al service
    success = OperationService.process_result_and_save(db, id_op, data)

    if not success:
        # Il router decide solo quale codice HTTP restituire in base al risultato
        raise HTTPException(status_code=404, detail="Operazione non trovata")

    return {"status": "success"}

# --- ENDPOINT 2: RICEZIONE ESITO DA N8N ---
@router.post("/webhook-error-callback")
async def receive_error_result(payload: dict, db: Session = Depends(get_db)):
    # Il router estrae solo i parametri fondamentali
    id_op = payload.get("id_operazione")

    # Delega tutta la logica di business e persistenza al service
    success = OperationService.process_error_result_and_save(db, id_op)

    if not success:
        # Il router decide solo quale codice HTTP restituire in base al risultato
        raise HTTPException(status_code=404, detail="Operazione non trovata")

    return {"status": "success"}

# --- ENDPOINT 3: GET RESULT (POLLING) ---
@router.get("/status/{id_req}")
async def get_status(id_req: str, db: Session = Depends(get_db)):
    db_op = db.query(Operazione).filter(Operazione.id == id_req).first()
    if not db_op:
        raise HTTPException(status_code=404, detail="Operazione non trovata")
    
    is_completed =  db_op.status != StatusEnum.PENDING
    completion_time = __get_completion_time(db_op=db_op)

    return {
        "completed": is_completed,
        "results": db_op.result_data,
        "status": db_op.status,
        "created_at": db_op.created_at,
        "completed_at": db_op.completed_at,
        "completion_time": completion_time
    }

@router.get("/history")
async def get_history(
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id)
):
    # Recuperiamo le ultime 50 operazioni ordinate per data decrescente
    history = (db.query(Operazione)
               .order_by(Operazione.created_at.desc())
               .limit(50).all())
    
    return [
        {
            "id": op.id,
            "param": op.param,
            "status": op.status,
            "owner_id": op.owner_id,
            "is_mine": op.owner_id == current_user_id,
            "completed": op.status != StatusEnum.PENDING,
            "created_at": op.created_at,
            "results": op.result_data,
            "completed_at": op.completed_at,
            "completion_time": __get_completion_time(db_op=op)
        } for op in history
    ]

@router.post("/feedback")
async def post_feedback(
    fb: FeedbackCreate, 
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id)
):
    # 1. Recupero l'operazione originale
    op = db.query(Operazione).filter(Operazione.id == fb.operazione_id).first()
    
    if not op:
        raise HTTPException(status_code=400, detail="Operazione non trovata")
    
    # 2. Verifica autorizzazione: solo l'owner può dare feedback
    if op.owner_id != current_user_id:
        raise HTTPException(status_code=403, detail="Non puoi valutare operazioni altrui")

    # 3. Creazione snapshot
    nuovo_feedback = Feedback(
        user_id=current_user_id,
        operazione_id=op.id,
        voto=fb.voto,
        commento=fb.commento,
        param=op.param,
        status=op.status,
        result_data=op.result_data,
        created_at_op=op.created_at,
        completed_at_op=op.completed_at
    )
    
    db.add(nuovo_feedback)
    db.commit()
    return {"status": "success", "message": "Feedback registrato"}

def __get_completion_time(db_op: Operazione):
    
    is_completed =  db_op.status != StatusEnum.PENDING
    completion_time = None
    if is_completed and db_op.completed_at and db_op.created_at:
        completion_time = (db_op.completed_at - db_op.created_at).seconds//60
    
    return completion_time
