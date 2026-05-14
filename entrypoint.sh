#!/bin/sh

# Funzione per gestire i fallimenti
handle_error() {
    echo "ERRORE CRITICO: Il comando precedente è fallito."
    echo "Il container rimarrà attivo per 60 secondi per permettere l'ispezione dei log..."
    sleep 60
    exit 1
}

# Applichiamo la gestione dell'errore a ogni comando critico
echo "Esecuzione migrazioni del database..."
alembic upgrade head || handle_error

echo "Avvio dell'applicazione..."
# Se python fallisce, eseguiamo comunque la pausa prima di uscire
python main.py || handle_error