from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # 1. Делаем эти поля необязательными (None),
    # чтобы приложение не падало на Koyeb, если их нет.
    POSTGRES_USER: str | None = None
    POSTGRES_PASSWORD: str | None = None
    POSTGRES_DB: str | None = None
    POSTGRES_HOST: str = "db"
    POSTGRES_PORT: int = 5432

    # 2. Добавляем поле для полной ссылки (которую мы сунем в Koyeb)
    DATABASE_URL: str | None = None

    @property
    def database_url(self) -> str:
        # ВАРИАНТ 1: Если в .env (или Koyeb) задана полная ссылка - берем её
        if self.DATABASE_URL:
            # Маленький хак: Neon дает ссылку начинающуюся с postgres://
            # А SQLAlchemy (asyncpg) требует postgresql+asyncpg://
            # Мы меняем это прямо тут, чтобы не париться в конфигах
            url = self.DATABASE_URL
            if url and url.startswith("postgres://"):
                url = url.replace("postgres://", "postgresql+asyncpg://", 1)
            return url

        # ВАРИАНТ 2: Если полной ссылки нет, собираем по старинке (для локалки)
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
