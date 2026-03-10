from pydantic import BaseModel


class Settings(BaseModel):
    app_name: str = "platform_core"
    app_env: str = "dev"
    default_region: str = "SP"


settings = Settings()
