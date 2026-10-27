from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    ADMIN_EMAIL: str
    ADMIN_PASSWORD: str
    THINGSPEAK_CHANNEL_ID: str
    THINGSPEAK_READ_API_KEY: str

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()
