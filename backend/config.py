"""应用配置管理"""
import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # 数据库
    DB_HOST: str = os.getenv("DB_HOST", "127.0.0.1")
    DB_PORT: int = int(os.getenv("DB_PORT", "3306"))
    DB_USER: str = os.getenv("DB_USER", "root")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
    DB_NAME: str = os.getenv("DB_NAME", "kids_english")

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
            f"?charset=utf8mb4"
        )

    # LLM
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")
    LLM_BASE_URL: str = os.getenv("LLM_BASE_URL", "https://api.deepseek.com")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "deepseek-chat")

    # TTS (Edge-TTS 免费，无需配置)
    TTS_PROVIDER: str = os.getenv("TTS_PROVIDER", "edge")  # edge / tencent

    # ASR (预留，Demo用Whisper本地或mock)
    ASR_PROVIDER: str = os.getenv("ASR_PROVIDER", "whisper")

    # 应用
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8003
    DEMO_USER_ID: int = 1  # Demo阶段固定用户ID


settings = Settings()
