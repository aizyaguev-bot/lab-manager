from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
import pathlib

# .env lives in the project root (one level above backend/)
_ENV_FILE = pathlib.Path(__file__).parent.parent.parent / ".env"

class Settings(BaseSettings):
    pdu_username: str = "ftlab"
    pdu_password: str = ""
    kvm_username: str = "admin"
    kvm_password: str = ""
    lab_manager_master_key: str = ""
    database_url: str = "sqlite+aiosqlite:///./lab_manager.db"

    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
    )

@lru_cache
def get_settings() -> Settings:
    return Settings()
