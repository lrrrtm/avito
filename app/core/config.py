from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/avito_pr_service"

    class Config:
        env_file = ".env"


settings = Settings()
