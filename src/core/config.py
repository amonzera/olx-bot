from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # O pydantic carrega essas variaveis do `.env`.
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Persistencia local
    SQLITE_PATH: str = Field(default="olx_monitor.sqlite3")

    # Bot do Telegram
    TELEGRAM_BOT_TOKEN: str = Field(default="")
    TELEGRAM_CHAT_ID: str = Field(default="")
    TELEGRAM_ALLOWED_CHAT_IDS: str = Field(default="")

    # Limites conservadores para reduzir risco de bloqueio pela OLX.
    SCAN_INTERVAL_SECONDS: int = Field(default=1800)
    DELAY_BETWEEN_ALERT_REQUESTS_SECONDS: int = Field(default=90)
    DELAY_BETWEEN_PAGE_REQUESTS_SECONDS: int = Field(default=15)
    MAX_SEARCH_PAGES: int = Field(default=3)
    REQUEST_TIMEOUT_SECONDS: int = Field(default=15)
    REQUEST_RETRIES: int = Field(default=2)
    REQUEST_BACKOFF_SECONDS: float = Field(default=1.5)
    MAX_LISTING_AGE_DAYS: int = Field(default=30)
    DATA_RETENTION_DAYS: int = Field(default=30)
    DEBUG_DUMP_DIR: str = Field(default="debug_dumps")

    @property
    def sqlite_path(self) -> Path:
        return Path(self.SQLITE_PATH)

    @property
    def debug_dump_dir(self) -> Path:
        return Path(self.DEBUG_DUMP_DIR)

    @property
    def allowed_chat_ids(self) -> set[str]:
        raw_ids = self.TELEGRAM_ALLOWED_CHAT_IDS or self.TELEGRAM_CHAT_ID
        return {
            chat_id.strip()
            for chat_id in raw_ids.split(",")
            if chat_id.strip()
        }

# Instanciamos a classe de config. Assim podemos importar 'settings' em todo o código
settings = Settings()
