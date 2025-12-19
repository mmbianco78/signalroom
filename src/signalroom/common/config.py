"""Application configuration using pydantic-settings."""

from functools import lru_cache

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # -------------------------------------------------------------------------
    # Supabase / Postgres
    # -------------------------------------------------------------------------
    supabase_url: str = ""
    supabase_db_host: str = ""
    supabase_db_port: int = 5432
    supabase_db_name: str = "postgres"
    supabase_db_user: str = "postgres"
    supabase_db_password: SecretStr = SecretStr("")

    @property
    def postgres_connection_string(self) -> str:
        """Build Postgres connection string for dlt."""
        password = self.supabase_db_password.get_secret_value()
        return (
            f"postgresql://{self.supabase_db_user}:{password}"
            f"@{self.supabase_db_host}:{self.supabase_db_port}/{self.supabase_db_name}"
        )

    # -------------------------------------------------------------------------
    # Temporal
    # -------------------------------------------------------------------------
    temporal_address: str = "localhost:7233"
    temporal_namespace: str = "default"
    temporal_task_queue: str = "api-tasks"
    temporal_tls_cert_path: str | None = None
    temporal_tls_key_path: str | None = None

    # -------------------------------------------------------------------------
    # S3
    # -------------------------------------------------------------------------
    aws_access_key_id: str = ""
    aws_secret_access_key: SecretStr = SecretStr("")
    aws_region: str = "us-east-1"
    s3_bucket_name: str = ""
    s3_prefix: str = ""

    # -------------------------------------------------------------------------
    # Notifications
    # -------------------------------------------------------------------------
    slack_bot_token: SecretStr = SecretStr("")
    slack_channel_id: str = ""
    resend_api_key: SecretStr = SecretStr("")
    resend_from_email: str = ""
    twilio_account_sid: str = ""
    twilio_auth_token: SecretStr = SecretStr("")
    twilio_from_number: str = ""

    # -------------------------------------------------------------------------
    # Source APIs
    # -------------------------------------------------------------------------
    everflow_api_key: SecretStr = SecretStr("")
    redtrack_api_key: SecretStr = SecretStr("")
    posthog_api_key: SecretStr = SecretStr("")
    posthog_project_id: str = ""
    posthog_host: str = "https://app.posthog.com"
    mautic_base_url: str = ""
    mautic_client_id: str = ""
    mautic_client_secret: SecretStr = SecretStr("")
    google_sheets_credentials_path: str = ""


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Convenience alias
settings = get_settings()
