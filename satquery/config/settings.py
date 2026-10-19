import os
class Settings:
    ENV = os.getenv("SATQUERY_ENV", "development")
    MODEL_PROVIDER = os.getenv("SATQUERY_MODEL_PROVIDER", "mock")
    DEVICE = os.getenv("SATQUERY_DEVICE", "cpu")
    DB_PATH = os.getenv("SATQUERY_DB_PATH", "satquery_jobs.db")
    UPLOAD_DIR = os.getenv("SATQUERY_UPLOAD_DIR", "uploads")
    MAX_UPLOAD_MB = float(os.getenv("SATQUERY_MAX_UPLOAD_MB", "500"))
    # Extra directories (os.pathsep-separated) whose rasters /analyze may read, besides
    # the working directory and UPLOAD_DIR, e.g. a mounted dataset folder.
    INPUT_ROOTS = [p for p in os.getenv("SATQUERY_INPUT_ROOTS", "").split(os.pathsep) if p]
