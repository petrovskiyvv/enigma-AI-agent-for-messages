from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Enigma Support API"
    app_version: str = "2.0.0"

    database_url: str = "postgresql://enigma:enigma@db:5432/enigma"

    cors_origins: list[str] = ["*"]

    telegram_bot_token: str = ""
    telegram_link_token_ttl_minutes: int = 10

    # ── AI ────────────────────────────────────────────────────────────────────
    groq_api_key: str = ""
    ai_model: str = "llama-3.3-70b-versatile"
    ai_max_tokens: int = 1500

    # ── IMAP (входящая почта) ─────────────────────────────────────────────────
    imap_host: str = ""
    imap_port: int = 993
    imap_user: str = ""
    imap_password: str = ""
    imap_mailbox: str = "INBOX"
    imap_poll_interval: int = 60   # секунды между проверками

    # ── SMTP (исходящая почта) ────────────────────────────────────────────────
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = ""            # адрес отправителя, если отличается от smtp_user

    class Config:
        env_file = ".env"


settings = Settings()
