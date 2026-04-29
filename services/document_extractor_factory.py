from core.settings import get_settings
from models.models import Settings as SettingsModel
from services.file_extractor import FileExtractor
from services.gdrive_document_extractor import GDriveExtractor 
from sqlalchemy.orm import Session

import logging

logger = logging.getLogger(__name__)

class DocumentExtractorFactory:
    """
    Factory per creare l'istanza corretta di DocumentExtractor
    basata sulle configurazioni di sistema.
    """
    # Chiave utilizzata nel Database
    GDRIVE_ROOT_KEY = "GDRIVE_DOCUMENT_ROOT_FOLDER_ID"

    @staticmethod
    def get_root_folder_id(db: Session) -> str:
        """
        Recupera la Root Folder ID dal DB o dai Settings (fallback).
        """
        try:
            # Cerchiamo nel DB la configurazione specifica
            db_entry = db.query(SettingsModel).filter(
                SettingsModel.key == DocumentExtractorFactory.GDRIVE_ROOT_KEY
            ).first()

            if db_entry and db_entry.value:
                return db_entry.value
            
            # Se non esiste nel DB, usiamo il default dei Settings
            return get_settings().GDRIVE_FOLDER_ID
            
        except Exception as e:
            logger.error(f"Errore nel recupero GDRIVE_ROOT_KEY dal DB: {e}")
            return get_settings().GDRIVE_FOLDER_ID
        
    @staticmethod
    def get_extractor(db: Session):
        settings = get_settings()
        source = settings.EXTRACTOR_SOURCE.upper()

        if source == "GDRIVE":
            print("Inizializzazione GDriveExtractor...")
            dynamic_root_id = DocumentExtractorFactory.get_root_folder_id(db)

            return GDriveExtractor(
                credentials_path=settings.GDRIVE_CREDENTIALS_PATH,
                root_folder_id=dynamic_root_id
            )
        
        elif source == "LOCAL":
            print("Inizializzazione FileExtractor (Locale)...")
            # FileExtractor è la tua classe originale basata su cartelle locali
            return FileExtractor(settings.DOCUMENT_BASE_PATH)
        
        else:
            raise ValueError(f"Sorgente estrattore non supportata: {source}")
