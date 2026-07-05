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

    # TTS (火山引擎豆包 TTS，API Key 方式接入)
    TTS_PROVIDER: str = "doubao"
    DOUBAO_API_KEY: str = ""
    DOUBAO_VOICE: str = "BV001_streaming"

    # ASR (Sherpa-ONNX Paraformer 离线方案)
    ASR_PROVIDER: str = "sherpa_onnx"

    # 应用
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8003
    DEMO_USER_ID: int = 1  # Demo阶段固定用户ID

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()
