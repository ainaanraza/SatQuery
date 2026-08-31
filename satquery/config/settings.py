import os
class Settings:
    ENV = os.getenv("SATQUERY_ENV", "development")
    MODEL_PROVIDER = os.getenv("SATQUERY_MODEL_PROVIDER", "mock")
    DEVICE = os.getenv("SATQUERY_DEVICE", "cpu")
