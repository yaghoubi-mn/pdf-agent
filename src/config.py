import os


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