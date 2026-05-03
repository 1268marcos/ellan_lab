from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql://admin:admin@localhost:5432/ellan"
    model_artifact_path: str = "./artifacts/rf_failure.joblib"
    enable_train_scheduler: bool = False  # ENABLE_TRAIN_SCHEDULER=true
    scheduler_hour: int = 2
    scheduler_timezone: str = "America/Sao_Paulo"


settings = Settings()
