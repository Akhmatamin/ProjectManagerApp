from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENV_PATH = BASE_DIR / ".env"


class Settings(BaseSettings):
    database_host: str
    database_port: int = 5432
    database_name: str
    database_user: str
    database_password: str

    secret_key: str
    algorithm: str
    access_token_lifetime: int
    refresh_token_lifetime: int

    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    reset_code_expire_seconds: int = 300

    resend_api_key: str
    resend_from: str = 'onboarding@resend.dev'

    frontend_base_url : str = 'https://donatkivi-frontend-page.s3.eu-north-1.amazonaws.com/index.html'
    invite_link_expire_seconds: int = 260000 #3 days
    backend_base_url: str = 'http://127.0.0.1:8000'

    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str
    AWS_REGION: str = "eu-north-1"
    S3_BUCKET_NAME: str = "my-project-bucket-documents"


    model_config = SettingsConfigDict(
        env_file=ENV_PATH,
        env_file_encoding="utf-8",
        case_sensitive=False,
    )
    @property
    def database_url(self)-> str:
        return (
            f"postgresql+asyncpg://"
            f"{self.database_user}:{self.database_password}"
            f"@{self.database_host}:{self.database_port}"
            f"/{self.database_name}"
        )

@lru_cache
def get_settings() -> Settings:
    return Settings() # type: ignore[call-arg]