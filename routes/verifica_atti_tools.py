from core.settings import get_settings
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, HTTPException, status, Query
import os
from pathlib import Path
from sqlalchemy.orm import Session

from core.database import get_db

# Creiamo il router con un prefisso e dei tag per la documentazione automatica
router = APIRouter(
    prefix="/api",
    tags=["API supporto per agenti IA"]
)

@router.get("/get-file-data")
def get_data(atto : str):
    from file_extractor import FileExtractor

    
    file_contents = []
    try:
        settings = get_settings()
        base_files_path = Path(os.path.join(settings.DOCUMENT_BASE_PATH, atto))

        file_extractor = FileExtractor()
        file_contents = file_extractor.extract_content_from_files(base_files_path)
    except Exception as e:
        print("error in getting file content: " + str(e))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Files not found")
    
    # Qui puoi inserire la tua logica Python esistente
    return {"status": "success", "contents": file_contents }

@router.get("/cdr-detail")
def get_cdr_detail(
    cdr_code : str,
    ref_date: date = Query(..., description="Data di riferimento nel formato YYYY-MM-DD"),
    db : Session = Depends(get_db)
):
    from document_loader import DocumentLoader

    document_loader = DocumentLoader()

    cdr_code = cdr_code.zfill(3)

    try:
        cdr_table = document_loader.get_cdr_table_by_date(db, ref_date)
    except Exception as e:
        print("error in getting CDR table for date {ref_date}: " + str(e))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid CDR table")

    return {
        "status": "success", 
        "cdr_code": cdr_code, 
        "cdr_detail": cdr_table.get(cdr_code, {})
    }

@router.get("/rup-delegation")
def get_rup_delegation(operation_code : str):
    from document_loader import DocumentLoader

    document_loader = DocumentLoader()

    try:
        rup_table = document_loader.get_rup_delegation_table()
    except Exception as e:
        print("error in getting RUP delegation table: " + str(e))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid RUP delegation table")

    return {"status": "success", "operation_code": operation_code, "detail": rup_table.get(operation_code, {}) }

@router.get("/iva-code-detail")
def get_iva_code_detail(iva_code : str):
    from document_loader import DocumentLoader

    document_loader = DocumentLoader()

    try:
        iva_table = document_loader.get_iva_codes()
    except Exception as e:
        print("error in getting IVA codes: " + str(e))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid IVA codes")

    return {"status": "success", "iva_code": iva_code, "detail": iva_table.get(iva_code, {}) }

@router.get("/siope-details")
def get_siope_details(code : str):
    from document_loader import DocumentLoader

    document_loader = DocumentLoader()

    try:
        siope_table = document_loader.get_siope_table()
    except Exception as e:
        print("error in getting SIOPE details: " + str(e))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid SIOPE table details")

    return {"status": "success", "siope_code": code, "detail": siope_table.get(code, {}) }
