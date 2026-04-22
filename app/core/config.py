# app/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    NEO4J_URI: str
    NEO4J_USERNAME: str
    NEO4J_PASSWORD: str
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

try:
    settings = Settings()
    print(" Đã nạp file .env thành công!")
except Exception as e:
    print(f" Lỗi nạp file .env: {e}")

    import os
    print(f"Thư mục hiện tại: {os.getcwd()}")