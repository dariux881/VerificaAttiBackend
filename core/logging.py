
import logging
import logging.config
from pathlib import Path
import os

def setup_logging(settings):
    """Configura il sistema di logging"""
    
    try:
        # Crea directory logs se non esiste
        log_dir = Path(settings.LOG_FOLDER)
        log_dir.mkdir(exist_ok=True)
        
        logging_config = {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": settings.LOG_FORMAT,
                    "datefmt": "%Y-%m-%d %H:%M:%S",
                },
                "detailed": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(module)s - %(funcName)s - %(lineno)d - %(message)s",
                    "datefmt": "%Y-%m-%d %H:%M:%S",
                },
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "level": settings.LOG_LEVEL,
                    "formatter": "default",
                    "stream": "ext://sys.stdout",
                },
                "file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "level": "INFO",
                    "formatter": "detailed",
                    "filename": os.path.join(log_dir, "system.log"),
                    "maxBytes": 10485760,  # 10MB
                    "backupCount": 5,
                },
                "error_file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "level": "ERROR",
                    "formatter": "detailed", 
                    "filename": os.path.join(log_dir, "error.log"),
                    "maxBytes": 10485760,  # 10MB
                    "backupCount": 3,
                },
            },
            "loggers": {
                "": {  # Root logger
                    "level": settings.LOG_LEVEL,
                    "handlers": ["console", "file"],
                },
                "app": {
                    "level": settings.LOG_LEVEL,
                    "handlers": ["console", "file"],
                    "propagate": False,
                },
                "sqlalchemy.engine": {
                    "level": "WARNING" if not settings.DEBUG else "INFO",
                    "handlers": ["console", "file"],
                    "propagate": False,
                },
                "uvicorn": {
                    "level": "INFO",
                    "handlers": ["console", "file"],
                    "propagate": False,
                },
            },
        }
        
        logging.config.dictConfig(logging_config)
        
        # Log startup message
        logger = logging.getLogger("app.startup")
        logger.info(f"Logging configured - Level: {settings.LOG_LEVEL}")
    except Exception as e:
        print(f"error occurred: {str(e)}")