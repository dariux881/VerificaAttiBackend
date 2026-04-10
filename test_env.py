import os
from core.settings import get_settings

print("--- Verifica Variabili d'Ambiente Sistema ---")
print(f"APP_PORT in OS: {os.environ.get('APP_PORT')}")
print(f"LOG_FOLDER in OS: {os.environ.get('LOG_FOLDER')}")

print("\n--- Verifica Pydantic ---")
settings = get_settings()
print(f"Pydantic PORT: {settings.PORT}")
print(f"Pydantic LOG_FOLDER: {settings.LOG_FOLDER}")

# Verifica dove Pydantic sta cercando il file .env
from core.settings import Settings
print(f"\nConfigurazione env_file: {Settings.model_config.get('env_file') if hasattr(Settings, 'model_config') else Settings.Config.env_file}")