import os
import io

from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google.oauth2 import service_account
import httplib2
import google_auth_httplib2
from urllib.parse import urlparse

from core.settings import get_settings
from services.document_extractor_base import DocumentExtractorBase
import logging

logger = logging.getLogger(__name__)

class GDriveExtractor(DocumentExtractorBase):
    def __init__(self, credentials_path, root_folder_id):
        super().__init__()

        self.root_folder_id = root_folder_id
        self.service = self.__build_gdrive_service(credentials_path)

    def __get_proxy_config(self):
        """
        Rileva la configurazione proxy dalle variabili d'ambiente standard di Linux.
        """
        settings = get_settings()
        
        if not settings.PROXY_ENABLED:
            return None

        # Legge http_proxy o https_proxy (standard Linux)
        proxy_url = os.environ.get('http_proxy') or os.environ.get('https_proxy')
        
        if proxy_url:
            parsed = urlparse(proxy_url)
            # httplib2 richiede un oggetto ProxyInfo
            return httplib2.ProxyInfo(
                proxy_type=httplib2.socks.PROXY_TYPE_HTTP,
                proxy_host=parsed.hostname,
                proxy_port=parsed.port or 8080,
                proxy_user=parsed.username, # Sarà None se non c'è login
                proxy_pass=parsed.password  # Sarà None se non c'è login
            )
        return None

    def __build_gdrive_service(self, credentials_path):

        creds = service_account.Credentials.from_service_account_file(
            credentials_path, 
            scopes=['https://www.googleapis.com/auth/drive.readonly']
        )

        proxy_info = proxy_info = self.__get_proxy_config()

        http_transport = httplib2.Http(timeout=45, proxy_info=proxy_info)

        authorized_http = google_auth_httplib2.AuthorizedHttp(creds, http=http_transport)

        return build(
            'drive', 'v3', 
            http=authorized_http, 
            cache_discovery=False
        )

    def _download_file_bytes(self, file_id):
        """
        Scarica il contenuto di un file da Drive e lo restituisce come bytes.
        """
        request = self.service.files().get_media(fileId=file_id)
        file_buffer = io.BytesIO()
        downloader = MediaIoBaseDownload(file_buffer, request)
        
        done = False
        while not done:
            status, done = downloader.next_chunk()
        
        return file_buffer.getvalue()
    
    def _find_subdirectory_id(self, folder_name):
        """
        Cerca una sottocartella con un nome specifico all'interno della root_folder_id.
        """
        query = (
            f"name = '{folder_name}' "
            f"and '{self.root_folder_id}' in parents "
            f"and mimeType = 'application/vnd.google-apps.folder' "
            f"and trashed = false"
        )
        results = self.service.files().list(q=query, fields="files(id, name)").execute()
        items = results.get('files', [])
        
        if not items:
            logger.error(f"Sottocartella '{folder_name}' non trovata in Drive partendo da {self.root_folder_id}.")
            return None
        
        return items[0]['id']
    
    def _read_pdf_content(self, document_ref):
        """
        Implementazione specifica per PDF su Drive.
        document_ref qui è il file_id di Google Drive.
        """
        pdf_bytes = self._download_file_bytes(document_ref)
        return self._read_pdf_from_binary(pdf_bytes)

    def _read_cades_content(self, document_ref):
        """
        Implementazione specifica per P7M su Drive.
        document_ref qui è il file_id di Google Drive.
        """
        p7m_bytes = self._download_file_bytes(document_ref)
        return self._read_cades_from_binary(p7m_bytes)

    def get_documents_content(self, folder_name, excluded_file_names=[]):
        """
        Scansiona una cartella di Google Drive ed estrae il contenuto di tutti i file.
        """
        self._file_contents = [] # Reset dei contenuti precedenti
        
        try:
            folder_id = self._find_subdirectory_id(folder_name)
            if not folder_id:
                return []
            
            # Query per elencare i file nella cartella specificata
            query = f"'{folder_id}' in parents and trashed = false"
            results = self.service.files().list(
                q=query, 
                fields="files(id, name)"
            ).execute()
            
            items = results.get('files', [])

            for item in items:
                file_name = item['name']
                file_id = item['id']

                if file_name in excluded_file_names:
                    continue

                # Chiamata al metodo della classe base che smista il file per tipo
                self._process_document_content(
                    document_ref=file_id, 
                    document_name=file_name
                )

            return self._file_contents

        except Exception as e:
            logger.error(f"Errore durante l'accesso a Google Drive: {e}")
            return []