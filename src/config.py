import os
import logging
from logging.config import dictConfig


DEBUG = bool(os.getenv("DEBUG", False))
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "..", "data", "uploads")
UPLOAD_PDF = os.path.join(UPLOAD_FOLDER, 'upload.pdf')
PROCESSED_PDF = os.path.join(BASE_DIR, "..", "data", "processed.pdf")
EMBEDDING_URL = os.getenv("EMBEDDING_URL", "")
RECREATE_COLLECTION = not DEBUG

session_id = None
user_id = None
qdrant_client = None


LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "()": "uvicorn.logging.DefaultFormatter",
            "fmt": "%(levelname)s: %(message)s",
            "use_colors": True,
        },
        "access": {
            "()": "uvicorn.logging.AccessFormatter",
            "fmt": '%(levelname)s: %(client_addr)s - "%(request_line)s" %(status_code)s',
            "use_colors": True,
        },
    },
    "handlers": {
        "default": {
            "formatter": "default",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stderr",
        },
        "access": {
            "formatter": "access",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
        },
    },
    "loggers": {
        "pdf-agent": {"handlers": ["default"], "level": "DEBUG"},
        "uvicorn": {"handlers": ["default"], "level": "INFO", "propagate": False},
        "uvicorn.error": {"level": "INFO"},
        "uvicorn.access": {"handlers": ["access"], "level": "INFO", "propagate": False},
    },
}

dictConfig(LOGGING_CONFIG)
logger = logging.getLogger("pdf-agent")