from pathlib import Path

import os
from services.document_extractor_base import DocumentExtractorBase
import logging

logger = logging.getLogger(__name__)

class FileExtractor(DocumentExtractorBase):
    def __init__(self, documents_base_path):
        super().__init__()

        self.documents_base_path = documents_base_path

    def _read_cades_content(self, file_path):
        """
        Legge un file .p7m, estrae firmatari, verifica la struttura 
        e restituisce il contenuto.
        """
        try:
            with open(file_path, 'rb') as f:
                dati_firme = f.read()

            return self._read_cades_from_binary(dati_firme)

        except Exception as e:
            logger.error(f"Errore durante l'elaborazione del file: {e}")

    def _read_pdf_content(self, file_path):
        """
        Mantiene la firma originale. Legge il file e delega al metodo binario.
        """
        with open(file_path, "rb") as f:
            pdf_bytes = f.read()
        
        # Invocazione del metodo di estrazione logica
        return self._read_pdf_from_binary(pdf_bytes)

    def get_documents_content(
            self, 
            base_folder,
            excluded_file_names=[]
            ):

        base_files_path = Path(os.path.join(self.documents_base_path, base_folder))

        # Verifica se il percorso esiste davvero prima di cercare i file
        if not base_files_path.exists() or not base_files_path.is_dir():
            raise Exception(f'invalid folder: {base_files_path}')

        for nome_file in os.listdir(base_files_path):
            percorso_completo = os.path.join(base_files_path, nome_file)
            if not os.path.isfile(percorso_completo):
                continue

            if excluded_file_names and any(nome_file in f for f in excluded_file_names):
                logger.info(f'file ${nome_file} to be skipped')
                continue

            try:
                self._process_document_content(percorso_completo, nome_file)
            except Exception as e:
                logger.error(str(e))
                break
        
        return self._file_contents