from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # LINE（必填）
    LINE_CHANNEL_ACCESS_TOKEN: str
    LINE_CHANNEL_SECRET: str
    LINE_USER_ID: str = ""

    # Shioaji（留空則行情功能停用，LINE 仍可啟動）
    SHIOAJI_API_KEY: str = ""
    SHIOAJI_SECRET_KEY: str = ""
    SHIOAJI_SIMULATION: bool = True

    # App
    DATABASE_URL: str = "sqlite:///./data/bot.db"
    TIMEZONE: str = "Asia/Taipei"
    MORNING_PUSH_HOUR: int = 8
    MORNING_PUSH_MINUTE: int = 30
    HOLIDAYS: str = ""  # 休市日，逗號分隔，例如 2026-10-25,2026-12-25

    @property
    def holiday_set(self) -> set[str]:
        return {d.strip() for d in self.HOLIDAYS.split(",") if d.strip()}


settings = Settings()
