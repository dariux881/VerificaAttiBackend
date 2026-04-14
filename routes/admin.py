from fastapi import APIRouter, Depends, HTTPException, HTTPException, status, Query
from sqlalchemy.orm import Session

from core.auth import get_current_user_id
from core.database import get_db
from models.schemas import CDRVersion

from services.information_support_service import InformationSupportService

# Creiamo il router con un prefisso e dei tag per la documentazione automatica
router = APIRouter(
    prefix="/admin",
    tags=["API supporto per la gestione del servizio"]
)

@router.post("/import-cdr-table")
async def post_cdr_table(
    cdr: CDRVersion, 
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id)
):
    ##TODO CHECK ADMIN USER

    try:
        InformationSupportService.import_cdr_table(db, cdr, current_user_id)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Dati non validi")

    return {
        'status': 'success',
        'message': 'CDR table successfully imported'
    }


@router.post("/setup-webhook-url")
async def setup_webhook_url(
    webhook_url: str, 
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id)
):
    ##TODO CHECK ADMIN USER

    try:
        InformationSupportService.setup_webhook_url(db, webhook_url, current_user_id)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Dati non validi")

    return {
        'status': 'success',
        'message': 'Webhook successfully set'
    }