import os
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from core.database import init_db

from pathlib import Path

from core.settings import get_settings
from document_loader import DocumentLoader
from file_extractor import FileExtractor

from routes import verifica_atti, auth

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Eseguito all'avvio
    init_db()
    yield
    # Eseguito allo spegnimento (pulizia se necessaria)

app = FastAPI(lifespan=lifespan)

# Configurazione CORS per permettere a React di comunicare con FastAPI
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().ALLOWED_HOSTS,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(verifica_atti.router)
app.include_router(auth.router)


@app.get("/get-file-data")
def get_data(atto : str):
    settings = get_settings()
    
    base_files_path = Path(os.path.join(settings.DOCUMENT_BASE_PATH, atto))

    file_contents = []
    try:
        file_extractor = FileExtractor()
        file_contents = file_extractor.extract_content_from_files(base_files_path)
    except Exception as e:
        print("error in getting file content: " + str(e))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Files not found")
    
    # Qui puoi inserire la tua logica Python esistente
    return {"status": "success", "contents": file_contents }

@app.get("/get-cdr-table")
def get_cdr_table():
    document_loader = DocumentLoader()

    try:
        cdr_table = document_loader.get_cdr_table()
    except Exception as e:
        print("error in getting CDR table: " + str(e))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid CDR table")

    return {"status": "success", "cdr_table": cdr_table}

@app.get("/cdr-detail")
def get_cdr_detail(cdr_code : str):
    document_loader = DocumentLoader()

    cdr_code = cdr_code.zfill(3)

    try:
        cdr_table = document_loader.get_cdr_table()
    except Exception as e:
        print("error in getting CDR table: " + str(e))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid CDR table")

    return {"status": "success", "cdr_code": cdr_code, "cdr_detail": cdr_table.get(cdr_code, {})}

@app.get("/rup-delegation")
def get_rup_delegation(operation_code : str):
    document_loader = DocumentLoader()

    try:
        rup_table = document_loader.get_rup_delegation_table()
    except Exception as e:
        print("error in getting RUP delegation table: " + str(e))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid RUP delegation table")

    return {"status": "success", "operation_code": operation_code, "detail": rup_table.get(operation_code, {}) }

@app.get("/iva-code-detail")
def get_iva_code_detail(iva_code : str):
    document_loader = DocumentLoader()

    try:
        iva_table = document_loader.get_iva_codes()
    except Exception as e:
        print("error in getting IVA codes: " + str(e))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid IVA codes")

    return {"status": "success", "iva_code": iva_code, "detail": iva_table.get(iva_code, {}) }

@app.get("/siope-details")
def get_siope_details(code : str):
    document_loader = DocumentLoader()

    try:
        siope_table = document_loader.get_siope_table()
    except Exception as e:
        print("error in getting SIOPE details: " + str(e))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid SIOPE table details")

    return {"status": "success", "siope_code": code, "detail": siope_table.get(code, {}) }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)