from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # O pydantic puxa essas vars do seu `.env`
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8", 
        extra="ignore" # ignora vars que não estao mapeadas
    )

    # Persistencia local
    SQLITE_PATH: str = Field(default="olx_monitor.sqlite3")

    # Banco de Dados legado/opcional
    DATABASE_URL: str = Field(default="postgresql+psycopg://postgres:postgres@localhost:5432/olx_monitor")
    
    # Filas / Cache (Redis)
    REDIS_URL: str = Field(default="redis://localhost:6379/0")
    CELERY_BROKER_URL: str = Field(default="redis://localhost:6379/0")
    CELERY_RESULT_BACKEND: str = Field(default="redis://localhost:6379/0")

    # Bot do Telegram
    TELEGRAM_BOT_TOKEN: str = Field(default="")
    TELEGRAM_CHAT_ID: str = Field(default="")

    # Limites (Evitar ser bloqueado pela OLX)
    DELAY_BETWEEN_REQUESTS_SECONDS: int = Field(default=5)
    REQUEST_TIMEOUT_SECONDS: int = Field(default=15)
    REQUEST_RETRIES: int = Field(default=2)
    REQUEST_BACKOFF_SECONDS: float = Field(default=1.5)
    MAX_LISTING_AGE_DAYS: int = Field(default=30)
    DEBUG_DUMP_DIR: str = Field(default="debug_dumps")

    @property
    def sqlite_path(self) -> Path:
        return Path(self.SQLITE_PATH)

    @property
    def debug_dump_dir(self) -> Path:
        return Path(self.DEBUG_DUMP_DIR)

# Instanciamos a classe de config. Assim podemos importar 'settings' em todo o código
settings = Settings()
