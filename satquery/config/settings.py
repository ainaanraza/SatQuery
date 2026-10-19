import os
class Settings:
    ENV = os.getenv("SATQUERY_ENV", "development")
    MODEL_PROVIDER = os.getenv("SATQUERY_MODEL_PROVIDER", "mock")
    DEVICE = os.getenv("SATQUERY_DEVICE", "cpu")
    DB_PATH = os.getenv("SATQUERY_DB_PATH", "satquery_jobs.db")
