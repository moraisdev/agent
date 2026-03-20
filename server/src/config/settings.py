from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    mcp_server_name: str = "namastex-report-tools"
    mcp_host: str = "0.0.0.0"
    mcp_port: int = 8000

    database_url: str = Field(
        default="postgresql://readonly:readonly@localhost:5433/business",
        validation_alias="BUSINESS_DATABASE_URI",
    )
    db_statement_timeout_ms: int = 30_000

    auth_dev_mode: bool = Field(default=True, validation_alias="AUTH_DEV_MODE")
    auth_secret: str = Field(default="", validation_alias="AUTH_SECRET")
    auth_admin_ids: str = Field(default="", validation_alias="AUTH_ADMIN_IDS")

    @property
    def admin_ids_set(self) -> set[str]:
        if not self.auth_admin_ids:
            return set()
        return {uid.strip() for uid in self.auth_admin_ids.split(",") if uid.strip()}

    circuit_breaker_max_failures: int = 3
    circuit_breaker_cooldown_seconds: int = 300

    ema_alpha: float = 0.3
    anomaly_revenue_threshold: float = 0.15
    anomaly_sales_threshold: float = 0.30

    log_level: str = "INFO"

    @property
    def async_database_url(self) -> str:
        url = self.database_url
        if url.startswith("postgresql://"):
            return url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return url


settings = Settings()
