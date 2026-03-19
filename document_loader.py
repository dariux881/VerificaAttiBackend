import os
import pandas as pd

from core.settings import get_settings

class DocumentLoader():
    def __init__(self):
        self.cdr_table = None
        self.rup_delegation_table = None
        self.iva_codes = None
        self.siope_table = None
        
    def _map_input(self, raw_table, mapping):
        """
        Mappa l'input dei dati raw nel formato dizionario richiesto.
        """

        output = {}

        for row in raw_table:
            # Estrazione dei valori usando le chiavi originali (con \n)
            # Usiamo .strip() per pulire eventuali spazi bianchi ai bordi
            main_key = str(row.get(mapping.get('key'), "")).strip()
            
            # Saltiamo le righe dove il codice CDR manca
            if not main_key or main_key == "nan":
                continue

            input_entry = {}
            for key in mapping.keys():
                if key == 'key': 
                    continue

                value = str(row.get(mapping.get(key), "")).strip()
                input_entry[key] = value

            # Costruzione dell'oggetto mappato
            output[main_key] = input_entry

        return output

    def get_cdr_table(self):
        """
        Legge il CSV e invoca _map_input.
        """

        if self.cdr_table:
            return self.cdr_table

        file_path = os.path.join(get_settings().SOURCES_BASE_PATH, 'tabella_cdr.csv')

        # Caricamento del CSV tramite pandas
        df = pd.read_csv(
            file_path, 
            encoding='latin-1',
            converters={"CODICE CDR": lambda x: str(x)})
        
        # Trasformazione del DataFrame in una lista di dizionari (formato record)
        # Questo crea il formato richiesto dal tuo ciclo: [{"Colonna": "Valore"}, ...]
        cdr_records = df.to_dict(orient='records')

        mapping = {
            "key": "CODICE CDR",
            "responsabile": "RESPONSABILI",
            "unità": "SETTORE/UNITA' DI STAFF/PROGETTI/QUARTIERI",
            "area_dipartimento" : "AREA/DIPARTIMENTO"
        }
        
        # Invocazione del metodo di mappatura
        self.cdr_table = self._map_input(cdr_records, mapping)

        return self.cdr_table

    def get_rup_delegation_table(self):
        """
        Legge il CSV per le nomine dei RUP e invoca _map_input.
        """

        if self.rup_delegation_table:
            return self.rup_delegation_table

        file_path = os.path.join(get_settings().SOURCES_BASE_PATH, 'tabella_nomina_rup.csv')

        # Caricamento del CSV tramite pandas
        df = pd.read_csv(file_path, encoding='latin-1')
        
        # Trasformazione del DataFrame in una lista di dizionari (formato record)
        # Questo crea il formato richiesto dal tuo ciclo: [{"Colonna": "Valore"}, ...]
        rup_records = df.to_dict(orient='records')

        mapping = {
            "key": "COD_INT",
            "descrizione": "DESCRIZIONE",
            "RUP": "RUP",
            "PG_nomina" : "Pg_nomina",
            "Importo_intervento" : "IMPORTO_INTERVENTO"
        }
        
        # Invocazione del metodo di mappatura
        self.rup_delegation_table = self._map_input(rup_records, mapping)

        return self.rup_delegation_table

    def get_iva_codes(self):
        """
        Legge il CSV per i codici IVA di SAP e invoca _map_input.
        """

        if self.iva_codes:
            return self.iva_codes

        file_path = os.path.join(get_settings().SOURCES_BASE_PATH, 'codici_iva.csv')

        # Caricamento del CSV tramite pandas
        df = pd.read_csv(file_path, encoding='latin-1')
        
        # Trasformazione del DataFrame in una lista di dizionari (formato record)
        # Questo crea il formato richiesto dal tuo ciclo: [{"Colonna": "Valore"}, ...]
        iva_records = df.to_dict(orient='records')

        mapping = {
            "key": "C.I.",
            "descrizione": "DESCRIZIONE",
            "dettaglio_operativo": "QUANDO SI UTILIZZA"
        }
        
        # Invocazione del metodo di mappatura
        self.iva_codes = self._map_input(iva_records, mapping)

        return self.iva_codes

    def get_siope_table(self):
        """
        Legge il CSV per i codici SIOPE invoca _map_input.
        """

        if self.siope_table:
            return self.siope_table
        
        file_path = os.path.join(get_settings().SOURCES_BASE_PATH, 'glossario_siope.csv')

        # Caricamento del CSV tramite pandas
        df = pd.read_csv(file_path, encoding='latin-1')
        
        # Trasformazione del DataFrame in una lista di dizionari (formato record)
        # Questo crea il formato richiesto dal tuo ciclo: [{"Colonna": "Valore"}, ...]
        siope_records = df.to_dict(orient='records')

        mapping = {
            "key": "Codice completo PdC",
            "descrizione": "DESCRIZIONE",
            "glossario": "GLOSSARIO"
        }
        
        # Invocazione del metodo di mappatura
        self.siope_table = self._map_input(siope_records, mapping)

        return self.siope_table
