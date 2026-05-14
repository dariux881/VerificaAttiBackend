# VerificaAttiBackend
Il backend per la Verifica automatica degli atti di liquidazione. Il sistema è basato su FastAPI e gestisce l'estrazione di informazioni da documenti, l'autenticazione degli utenti e l'integrazione con sorgenti esterne.

## 🛠 Prerequisiti
Prima di iniziare, assicurati di avere installato:
- **Python 3.12** o superiore.
- **Pip** (il gestore di pacchetti Python).
- Un database compatibile con **SQLAlchemy** (es. PostgreSQL o SQLite).
- **Podman** e Podman Desktop (*opzionale*, per l'esecuzione tramite container).

## 🚀 Installazione e Setup Locale
Segui questi passaggi per configurare l'ambiente di sviluppo:
### Clonazione e Ambiente Virtuale
```
# Crea un ambiente virtuale
python -m venv venv

# Attiva l'ambiente (Windows)
venv\Scripts\activate

# Attiva l'ambiente (Linux/macOS)
source venv/bin/activate

# Installa le dipendenze
pip install -r requirements.txt
```

### Configurazione Variabili d'Ambiente

Crea un file chiamato .env nella root del progetto (puoi basarti sul file .env.example).

Le variabili principali includono:
- `DATABASE_URL`: L'URL di connessione al database.
- `JWT_SECRET_KEY`: Chiave segreta per la firma dei token di sicurezza.
- `LOG_FOLDER`: Cartella dove verranno salvati i log.
- `PORT`: Porta di ascolto dell'applicazione (default: 8000).

### Setup del Database (Alembic)

Il progetto utilizza Alembic per gestire le migrazioni del database. Per creare la struttura iniziale delle tabelle, esegui:

```
alembic upgrade head
```

Questo comando allinea lo schema del database all'ultima versione disponibile.

### Inizializzazione Dati e Primo Utente
Per popolare il database con le configurazioni di base e creare l'utente amministratore iniziale (admin), esegui lo script di ambiente:

```
python init_environment.py
```

**Nota:** Questo script creerà l'utente admin con la password predefinita *PasswordSegreta123!*. Al primo accesso sarà necessario cambiarla.

## 🏃 Avvio dell'Applicazione
Esecuzione Diretta (Uvicorn)
Puoi avviare il server di sviluppo tramite il comando:

```
python main.py
```
Il server sarà attivo per impostazione predefinita su `http://0.0.0.0:8000`.

### Esecuzione tramite Docker/Podman
Se preferisci usare Docker o Podman, è presente un Dockerfile multi-stage ottimizzato:

```
docker build -t verifica-atti-backend .
docker run -p 8000:8000 verifica-atti-backend
```

## 📖 Documentazione API (Swagger)
Una volta avviata l'applicazione, FastAPI genera automaticamente la documentazione interattiva:
- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs) (Consigliato per testare le API direttamente dal browser).
- **Redoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc) (Per una documentazione più orientata alla lettura).

## 📁 Struttura del Progetto
- `core/`: Configurazioni centralizzate, database, log e sicurezza.
- `models/`: Modelli SQLAlchemy e schemi Pydantic.
- `routes/`: Endpoint API divisi per moduli (auth, verifica atti, admin).
- `services/`: Logica di business e servizi di estrazione documenti.
- `external_sources/`: File CSV/JSON per l'importazione iniziale dei dati.

## 📝 Note per lo Sviluppo
- **CORS**: Le origini consentite possono essere configurate tramite la variabile `ALLOWED_HOSTS` nel file `.env` o nelle variabili d'ambiente.
- **Logs**: I log di sistema vengono salvati nella cartella definita in `LOG_FOLDER` (default: `logs`).