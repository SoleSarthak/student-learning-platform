from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # "development" | "test" | "production"
    ENVIRONMENT: str = "development"

    DATABASE_URL: str
    REDIS_URL: str = "redis://localhost:6379/0"

    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Comma-separated list of allowed browser origins.
    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"

    # Simple Redis-backed rate limiting for login / register.
    RATE_LIMIT_ENABLED: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origins_list(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.CORS_ORIGINS.split(",")
            if origin.strip()
        ]

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() == "production"

    @model_validator(mode="after")
    def refuse_weak_secret_in_production(self) -> "Settings":
        # Fail fast: a guessable JWT secret means anyone can forge tokens.
        if self.is_production:
            weak = (
                len(self.JWT_SECRET_KEY) < 32
                or "change" in self.JWT_SECRET_KEY.lower()
            )
            if weak:
                raise ValueError(
                    "JWT_SECRET_KEY must be at least 32 characters and not a "
                    "placeholder when ENVIRONMENT=production. "
                    "Generate one with: python -c \"import secrets; "
                    "print(secrets.token_urlsafe(48))\""
                )
        return self


settings = Settings()
