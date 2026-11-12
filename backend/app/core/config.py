from typing import Literal
from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application Information
    PROJECT_NAME: str = "DukaanAI Backend"
    SERVICE_NAME: str = "dukaanai-backend"
    VERSION: str = "0.1.0"
    ENVIRONMENT: Literal["development", "staging", "production", "test"] = "development"
    DEBUG: bool = False

    # Server Binding
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    API_V1_PREFIX: str = "/api/v1"

    # Database Configuration (PostgreSQL with psycopg v3 driver)
    DATABASE_URL: str = "postgresql+psycopg://postgres:postgres@localhost:5432/dukaanai_db"
    DATABASE_ECHO: bool = False
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    DATABASE_POOL_TIMEOUT: int = 30
    TEST_DATABASE_URL: str | None = None

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: str | None) -> str | None:
        if isinstance(v, str):
            if v.startswith("postgres://"):
                return v.replace("postgres://", "postgresql+psycopg://", 1)
            elif v.startswith("postgresql://") and not v.startswith("postgresql+psycopg://"):
                return v.replace("postgresql://", "postgresql+psycopg://", 1)
        return v

    # JWT & Authentication Configuration
    JWT_SECRET_KEY: str = "development_secret_key_minimum_32_characters_long_for_security_testing"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    JWT_ISSUER: str = "dukaanai-auth"
    JWT_AUDIENCE: str = "dukaanai-client"

    # OTP (One-Time Password) Configuration
    OTP_PROVIDER: Literal["dev", "sms", "fast2sms"] = "fast2sms"
    FAST2SMS_API_KEY: str | None = Field(default="PeW1QHZCQWdHfscirAsYG3xOf8VmLBNYaiwZ59Esv9bpulPmGCe7zY98URR4yqZGWD5biCgm90XskWzt")
    OTP_EXPIRE_SECONDS: int = 300  # 5 minutes
    OTP_MAX_ATTEMPTS: int = 5
    OTP_COOLDOWN_SECONDS: int = 60
    OTP_SECRET_PEPPER: str = "dukaanai_internal_otp_pepper_secret"

    # Logging Configuration
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: Literal["json", "text"] = "json"

    # CORS Configuration
    CORS_ORIGINS: list[str] = Field(default_factory=lambda: ["*"])

    @model_validator(mode="after")
    def validate_production_settings(self) -> "Settings":
        """Strict startup validation preventing insecure configurations in production."""
        if self.ENVIRONMENT == "production":
            if "development" in self.JWT_SECRET_KEY.lower() or len(self.JWT_SECRET_KEY) < 32:
                raise ValueError("Production JWT_SECRET_KEY must be a secure random string of at least 32 characters.")
            if self.OTP_PROVIDER == "dev":
                raise ValueError("OTP_PROVIDER='dev' is strictly prohibited in production environment.")
            if self.DEBUG:
                raise ValueError("DEBUG must be set to False in production environment.")
        return self


settings = Settings()
