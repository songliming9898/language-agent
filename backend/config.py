"""应用配置管理"""
from urllib.parse import quote_plus
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # 数据库
    DB_HOST: str = "127.0.0.1"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str = ""
    DB_NAME: str = "kids_english"

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"mysql+pymysql://{quote_plus(self.DB_USER)}:{quote_plus(self.DB_PASSWORD)}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
            f"?charset=utf8mb4"
        )

    # LLM
    LLM_API_KEY: str = ""
    LLM_BASE_URL: str = "https://api.deepseek.com"
    LLM_MODEL: str = "deepseek-chat"

    # TTS (阿里云语音合成，请在 .env 中配置)
    TTS_PROVIDER: str = "aliyun"
    ALIYUN_AK_ID: str = ""
    ALIYUN_AK_SECRET: str = ""
    ALIYUN_TTS_APP_KEY: str = ""

    # ASR
    ASR_PROVIDER: str = "whisper"

    # 应用
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8003
    DEMO_USER_ID: int = 1  # Demo阶段固定用户ID

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()
