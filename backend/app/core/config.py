from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Enigma Support API"
    app_version: str = "2.0.0"

    database_url: str = "postgresql://admin:password@db:5432/enigma_db"

    cors_origins: list[str] = ["*"]

    class Config:
        env_file = ".env"


settings = Settings()
