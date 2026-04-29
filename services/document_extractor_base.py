import fitz
from PIL import Image
from asn1crypto import cms
from pypdf import PdfReader

import base64
import io
import logging

logger = logging.getLogger(__name__)

class DocumentExtractorBase():
    def __init__(self):
        self._file_contents = []
    
        # Estensioni supportate
        self.EXT_PDF = ('.pdf',)
        self.EXT_P7M = ('.p7m',)
        self.EXT_IMG = ('.jpg', '.jpeg', '.png', '.tiff')
    
    def _is_pdf(self, filename):
        return filename.lower().endswith(self.EXT_PDF)

    def _is_cades(self, filename):
        return filename.lower().endswith(self.EXT_P7M)

    def _is_image(self, filename):
        return filename.lower().endswith(self.EXT_IMG)

    def __get_signers_from_pades(self, pdf_bytes):
        """
        Individua le firme PAdES nel PDF e ne estrae i nomi dei firmatari.
        """
        firmatari_pades = []
        try:
            # Carichiamo il PDF con pypdf per accedere ai dizionari delle firme
            from io import BytesIO
            reader = PdfReader(BytesIO(pdf_bytes))

            # Verifichiamo se ci sono campi modulo (dove risiedono le firme)
            if "/AcroForm" in reader.trailer["/Root"]:
                fields = reader.get_fields()
                if fields:
                    for field_name, field_data in fields.items():
                        # Cerchiamo campi di tipo firma (/Sig)
                        if "/V" in field_data:
                            sig_object = field_data["/V"].get_object()
                            if "/Contents" in sig_object:
                                # Estraiamo i byte della firma PKCS#7
                                pkcs7_buffer = sig_object["/Contents"]

                                # Usiamo asn1crypto per caricare la struttura
                                # Nota: i byte di pypdf possono avere zeri finali (padding)
                                info_contenuto = cms.ContentInfo.load(pkcs7_buffer.strip(b'\x00'))

                                if info_contenuto['content_type'].native == 'signed_data':
                                    signed_data = info_contenuto['content']
                                    # RIUTILIZZO del tuo metodo esistente!
                                    nomi = self.__get_signers_from_cades(signed_data)
                                    firmatari_pades.extend(nomi)
        except Exception as e:
            logger.error(f"Errore durante l'estrazione firme PAdES: {str(e)}")

        return list(set(firmatari_pades)) # Rimuoviamo eventuali duplicati

    def __get_signers_from_cades(self, signed_data):
        """
        Mappa i certificati presenti nel p7m e restituisce i nomi reali dei firmatari.
        """
        nomi_reali = []

        # 1. Creiamo un dizionario di tutti i certificati nel pacchetto per serial_number
        mappa_certificati = {}
        for cert_choices in signed_data['certificates']:
            # 'certificate' la scelta standard in un SignedData
            cert = cert_choices.parse()
            serial = cert['tbs_certificate']['serial_number'].native
            mappa_certificati[serial] = cert

        # 2. Iteriamo sui firmatari (signer_infos)
        for signer_info in signed_data['signer_infos']:
            sid = signer_info['sid']

            # Cerchiamo il certificato corrispondente usando il serial_number
            if sid.name == 'issuer_and_serial_number':
                serial_cercato = sid.native['serial_number']

                if serial_cercato in mappa_certificati:
                    certificato = mappa_certificati[serial_cercato]
                    subject = certificato.subject.native

                    # Il Common Name (CN) di solito contiene "NOME COGNOME" 
                    # o il codice fiscale nei certificati italiani
                    nome_completo = subject.get('common_name', 'Nome Sconosciuto')

                    # Se preferisci maggiore dettaglio, puoi cercare campi specifici
                    nome = subject.get('given_name', '')
                    cognome = subject.get('surname', '')

                    if nome and cognome:
                        nomi_reali.append(f"{nome} {cognome}")
                    else:
                        nomi_reali.append(nome_completo)

        return nomi_reali

    def __get_images_from_pdf_page(self, pdf_page, document):
        MAX_DIMENSION = 1024  # Max pixel lato lungo
        JPEG_QUALITY = 80     # Bilanciamento peso/leggibilità
        DIMENSIONE_MINIMA = 15

        # Otteniamo l'altezza totale della pagina per calcolare i margini
        altezza_pagina = pdf_page.rect.height
        margine_header = 10
        margine_footer = altezza_pagina - 10

        # 2. Estrazione Immagini con filtro posizionale
        immagini_nella_pagina = pdf_page.get_images(full=True)
        images = []

        for info_img in immagini_nella_pagina:
            xref = info_img[0]

            aree_immagine = pdf_page.get_image_rects(xref)
            if not aree_immagine:
                continue # Salta se non riusciamo a trovare la posizione

            # Prendiamo la prima posizione trovata (il "rect" dell'immagine)
            rect = aree_immagine[0]

            # --- FILTRO: DIMENSIONE ---
            # Verifichiamo se l'immagine è troppo piccola
            if rect.width < DIMENSIONE_MINIMA or rect.height < DIMENSIONE_MINIMA:
                # Salta questa immagine perché è minuscola (probabile icona)
                continue

            y0 = rect.y0 # Coordinata superiore
            y1 = rect.y1 # Coordinata inferiore

            # FILTRO: Se l'immagine è troppo in alto o troppo in basso, saltala
            if y0 < margine_header or y1 > margine_footer:
                continue

            # 3. Estrazione e Salvataggio (solo se passa il filtro)
            base_image = document.extract_image(xref)
            image_bytes = base_image["image"]
            estensione = base_image["ext"]

            # Carichiamo l'immagine in Pillow per il processing
            img = Image.open(io.BytesIO(image_bytes))
            # 1. Conversione in RGB (necessaria per salvare in JPEG se l'originale è PNG/RGBA/CMYK)
            if img.mode in ("RGBA", "P", "CMYK"):
                img = img.convert("L")

            # 2. Ridimensionamento proporzionale (Smart Resize)
            # Se l'immagine è già piccola, la lasciamo stare
            if img.width > MAX_DIMENSION or img.height > MAX_DIMENSION:
                img.thumbnail((MAX_DIMENSION, MAX_DIMENSION), Image.Resampling.LANCZOS)

            # 3. Compressione e salvataggio in Buffer
            # Usiamo JPEG come formato standard perché è più leggero del PNG per le foto/scansioni
            buffer = io.BytesIO()
            img.save(buffer, format="JPEG", quality=JPEG_QUALITY, optimize=True)
            processed_bytes = buffer.getvalue()

            # 4. Controllo di efficienza: usiamo il minore tra i due
            if len(processed_bytes) > len(image_bytes) and base_image["ext"] in ["jpeg", "jpg", "png"]:
                # Se il processato pesa di più e l'originale è un formato standard, teniamo l'originale
                final_bytes = image_bytes
                final_ext = base_image["ext"]
            else:
                # Altrimenti usiamo la versione ottimizzata (ridimensionata/compressa)
                final_bytes = processed_bytes
                final_ext = "jpeg"

            # --- CONVERSIONE IN BASE64 ---
            # 1. Convertiamo i bytes in stringa base64
            base64_encoded = base64.b64encode(final_bytes).decode('utf-8')
            # 2. Creiamo la stringa pronta per l'uso (Data URI)
            # Utile per il client: <img src="data:image/png;base64,...">
            full_base64 = f"data:image/{final_ext};base64,{base64_encoded}"

            images.append({
                'content': full_base64,
                'ext': final_ext,
                'width': img.width,
                'height': img.height
                # 'orig_ext': estensione,
                # 'original_size_kb': len(image_bytes) / 1024,
                # 'processed_size_kb': len(processed_bytes) / 1024
            })

        return images

    def _read_pdf_from_binary(self, pdf_bytes):
        """
        Legge il PDF dai byte, estrae il testo, le immagini e i firmatari (PAdES)
        """
        testo_estratto = ""
        images = []
        firmatari = []

        try:
            # 1. Estrazione Firme PAdES
            firmatari = self.__get_signers_from_pades(pdf_bytes)

            # 2. Estrazione Contenuto (fitz)
            documento = fitz.open(stream=pdf_bytes, filetype="pdf")

            for numero_pagina, pagina in enumerate(documento):
                # 1. Estrazione Testo
                testo_estratto += pagina.get_text()

                # 2. Estrazione Immagini
                images_in_page = self.__get_images_from_pdf_page(pagina, documento)
                images.extend(images_in_page)

            documento.close()
            return {
                'text': testo_estratto,
                'images': images,
                'signers': firmatari
            }
        except Exception as e:
            logger.error("Exception reading file: " + str(e))
            return None
    
    def _read_cades_from_binary(self, p7m_bytes):
        """
        Legge il contenuto di un .p7m, estrae firmatari, verifica la struttura 
        e restituisce il contenuto.
        """
        try:
            # Decodifichiamo la struttura PKCS#7 (ContentInfo)
            info_contenuto = cms.ContentInfo.load(p7m_bytes)
            
            # Verifichiamo che sia effettivamente un file firmato (signedData)
            if info_contenuto['content_type'].native != 'signed_data':
                logger.info("Il file non contiene dati firmati validi.")
                return None

            signed_data = info_contenuto['content']
            
            # 1. ESTRAZIONE FIRMATARI
            firmatari = self.__get_signers_from_cades(signed_data)

            # 2. ESTRAZIONE CONTENUTO
            # Il contenuto reale si trova in 'encap_content_info' -> 'content'
            payload_binario = signed_data['encap_content_info']['content'].native

            # 3. VERIFICA TIPO E GESTIONE
            # Controlliamo i primi byte (Magic Numbers) per capire se e' un PDF
            if payload_binario.startswith(b'%PDF'):
                content = self._read_pdf_from_binary(payload_binario)

                text = content.get('text', '')
                images = content.get('images', [])
                firmatari.append(content.get('signers', []))
            else:
                logger.info("Contenuto testuale rilevato.")
                # Decodifichiamo in stringa supponendo UTF-8 o simile
                content = payload_binario.decode('utf-8', errors='ignore')

                text = content
                images = []

            return {
                'signers': firmatari,
                'text': text,
                'images': images
            }

        except Exception as e:
            logger.error(f"Errore durante l'elaborazione del file: {e}")

    def _read_cades_content(self, document_ref):
        pass

    def _read_pdf_content(self, document_ref):
        pass

    def _process_document_content(self, document_ref, document_name):
        dati_documento = {
            "filename": document_name,
            "signers": [],
            "text": "",
            "images": []
        }

        try:
            is_content_valid = False

            # 1. GESTIONE P7M
            if self._is_cades(document_name):
                logger.debug(f"Processing P7M: {document_name}")
                risultato_p7m = self._read_cades_content(document_ref)
                dati_documento.update(risultato_p7m)
                is_content_valid = True

            # 2. GESTIONE PDF (Diretto)
            elif self._is_pdf(document_name):
                logger.debug(f"Processing PDF: {document_name}")
                # Creiamo una sottocartella specifica per le immagini di questo PDF
                content = self._read_pdf_content(document_ref) 
                dati_documento.update(content)
                is_content_valid = True

            # 3. GESTIONE IMMAGINI (Dirette)
            elif self._is_image(document_name):
                logger.debug(f"Processing Immagine: {document_name}")
                dati_documento["images"] = [document_ref]
                dati_documento["text"] = "[Immagine pura - Nessun testo estratto]"
                is_content_valid = True

            if is_content_valid:
                self._file_contents.append(dati_documento)
                
        except Exception as e:
            logger.error(str(e))
            raise e

    def get_documents_content(
            self, 
            base_folder,
            excluded_file_names=[]
            ):
        pass