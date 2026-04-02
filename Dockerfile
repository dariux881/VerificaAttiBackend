# --- STAGE 1: Builder ---
# Usiamo un'immagine completa per compilare le dipendenze
FROM python:3.12-slim AS builder

WORKDIR /app

# Variabili Proxy (se necessarie per scaricare i pacchetti)
ARG HTTP_PROXY
ENV http_proxy=$HTTP_PROXY
ENV https_proxy=$HTTP_PROXY

# Installiamo solo il necessario per compilare (es. per psycopg2 o simili)
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Installiamo le dipendenze in una cartella locale invece che nel sistema
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --prefix=/install -r requirements.txt


# --- STAGE 2: Final Image ---
# Usiamo l'immagine slim, ma senza i tool di compilazione (gcc, ecc.)
FROM python:3.12-slim

WORKDIR /app

# Copiamo solo le librerie già installate dallo stage builder
COPY --from=builder /install /usr/local
# Copiamo il codice sorgente
COPY . .

# Passiamo di nuovo l'ARG per assicurarci che sia disponibile in questo stage
ARG HTTP_PROXY
ENV http_proxy=$HTTP_PROXY
ENV https_proxy=$HTTP_PROXY

# Dipendenze di runtime (solo quelle strettamente necessarie per far girare il DB)
RUN apt-get update && \
    apt-get install -y --no-install-recommends libpq5 && \
    rm -rf /var/lib/apt/lists/*

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV APP_PORT=8000

EXPOSE ${APP_PORT}

CMD uvicorn main:app --host 0.0.0.0 --port ${APP_PORT}