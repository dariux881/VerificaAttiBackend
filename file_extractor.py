from asn1crypto import cms
import base64
import fitz
import os
from pypdf import PdfReader
import io
from PIL import Image
import logging

logger = logging.getLogger(__name__)

class FileExtractor():
    def __init__(self):
        pass

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

    def _read_cades_content(self, file_path):
        """
        Legge un file .p7m, estrae firmatari, verifica la struttura 
        e restituisce il contenuto.
        """
        try:
            with open(file_path, 'rb') as f:
                dati_firme = f.read()

            # Decodifichiamo la struttura PKCS#7 (ContentInfo)
            info_contenuto = cms.ContentInfo.load(dati_firme)
            
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

            return {
                'signers': firmatari,
                'text': text,
                'images': images
            }

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

    def extract_content_from_files(self, base_files_path):
        # Estensioni supportate
        EXT_PDF = ('.pdf',)
        EXT_P7M = ('.p7m',)
        EXT_IMG = ('.jpg', '.jpeg', '.png', '.tiff')

        # Verifica se il percorso esiste davvero prima di cercare i file
        if not base_files_path.exists() or not base_files_path.is_dir():
            raise Exception(f'invalid folder: {base_files_path}')
        
        file_contents = []

        for nome_file in os.listdir(base_files_path):
            percorso_completo = os.path.join(base_files_path, nome_file)
            if not os.path.isfile(percorso_completo):
                continue

            estensione = nome_file.lower()
            dati_documento = {
                "filename": nome_file,
                "signers": [],
                "text": "",
                "images": []
            }

            try:
                is_content_valid = False

                # 1. GESTIONE P7M
                if estensione.endswith(EXT_P7M):
                    logger.debug(f"Processing P7M: {nome_file}")
                    risultato_p7m = self._read_cades_content(percorso_completo)
                    dati_documento.update(risultato_p7m)
                    is_content_valid = True

                # 2. GESTIONE PDF (Diretto)
                elif estensione.endswith(EXT_PDF):
                    logger.debug(f"Processing PDF: {nome_file}")
                    # Creiamo una sottocartella specifica per le immagini di questo PDF
                    content = self._read_pdf_content(percorso_completo) 
                    dati_documento.update(content)
                    is_content_valid = True

                # 3. GESTIONE IMMAGINI (Dirette)
                elif estensione.endswith(EXT_IMG):
                    logger.debug(f"Processing Immagine: {nome_file}")
                    dati_documento["images"] = [percorso_completo]
                    dati_documento["text"] = "[Immagine pura - Nessun testo estratto]"
                    is_content_valid = True

                if is_content_valid:
                    file_contents.append(dati_documento)
                    
            except Exception as e:
                logger.error(str(e))
                break
        
        return file_contents