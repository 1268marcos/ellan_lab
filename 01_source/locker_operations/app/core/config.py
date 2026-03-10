from pydantic import BaseModel


class Settings(BaseModel):
    app_name: str = "locker_operations"
    app_env: str = "dev"


settings = Settings()
