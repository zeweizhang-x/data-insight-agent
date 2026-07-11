from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # 这些字段会从环境变量或 .env 文件中读取。
    # 必填项：数据库和 Redis 连接地址。
    DATABASE_URL: str
    REDIS_URL: str

    # 可选项：如果暂时还没有接入大模型服务，可以保持空字符串。
    LLM_API_KEY: str = ""
    LLM_BASE_URL: str = ""
    LLM_MODEL: str = ""

    # 告诉 pydantic-settings 去哪里找 .env 文件。
    # parents[2] 表示项目根目录，也就是 `data-insight-agent/.env`。
    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[2] / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    # 用缓存避免每次调用都重新解析环境变量。
    # 对于配置这种“启动后基本不变”的数据，这是更高效的写法。
    return Settings()
