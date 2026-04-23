# app/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    NEO4J_URI: str
    NEO4J_USERNAME: str
    NEO4J_PASSWORD: str
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

try:
    settings = Settings()
    print("[OK] .env loaded successfully!")
except Exception as e:
    print(f"[ERROR] Failed to load .env: {e}")

    import os
    print(f"Current directory: {os.getcwd()}")