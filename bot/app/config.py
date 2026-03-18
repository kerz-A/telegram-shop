from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Telegram
    bot_token: str
    webapp_url: str = ""

    # Database
    postgres_db: str = "shop_db"
    postgres_user: str = "shop_user"
    postgres_password: str = "password"
    postgres_host: str = "db"
    postgres_port: int = 5432

    # Internal webhook server
    bot_webhook_host: str = "0.0.0.0"
    bot_webhook_port: int = 8081

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
