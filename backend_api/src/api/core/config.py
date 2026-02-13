import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    """App settings loaded from environment variables."""

    postgres_url: str
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_exp_minutes: int = 60 * 24 * 7  # 7 days

    cors_allow_origins: list[str] = None


# PUBLIC_INTERFACE
def get_settings() -> Settings:
    """Load settings from environment variables.

    Required env vars:
    - POSTGRES_URL
    - JWT_SECRET_KEY

    Optional:
    - JWT_ALGORITHM (default HS256)
    - ACCESS_TOKEN_EXP_MINUTES
    - CORS_ALLOW_ORIGINS (comma-separated, default '*')
    """
    postgres_url = os.getenv("POSTGRES_URL")
    jwt_secret_key = os.getenv("JWT_SECRET_KEY")

    if not postgres_url:
        raise RuntimeError("Missing required environment variable: POSTGRES_URL")
    if not jwt_secret_key:
        raise RuntimeError("Missing required environment variable: JWT_SECRET_KEY")

    cors_raw = os.getenv("CORS_ALLOW_ORIGINS", "*")
    allow_origins = ["*"] if cors_raw.strip() == "*" else [o.strip() for o in cors_raw.split(",") if o.strip()]

    exp_raw = os.getenv("ACCESS_TOKEN_EXP_MINUTES", "")
    exp = int(exp_raw) if exp_raw.strip() else 60 * 24 * 7

    return Settings(
        postgres_url=postgres_url,
        jwt_secret_key=jwt_secret_key,
        jwt_algorithm=os.getenv("JWT_ALGORITHM", "HS256"),
        access_token_exp_minutes=exp,
        cors_allow_origins=allow_origins,
    )
