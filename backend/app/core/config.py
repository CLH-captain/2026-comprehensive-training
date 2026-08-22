from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "SZUT Club Activity Agent"
    app_env: Literal["development", "test", "production"] = "development"
    app_host: str = "127.0.0.1"
    app_port: int = 8000
    frontend_origin: str = "http://127.0.0.1:5173"

    database_url: str
    test_database_url: str

    jwt_secret: str
    jwt_expire_minutes: int = 60
    initial_admin_username: str = "admin"
    initial_admin_password: str = ""
    seed_user_password: str = ""

    hermes_base_url: str = "http://127.0.0.1:9120"
    hermes_api_key: str = ""
    hermes_executable: str = (
        r"C:\Users\陈立洪\AppData\Roaming\cn.org.hermesagent.desktop\runtime"
        r"\versions\0.19.0-cn.7\hermes-agent-cn-runtime-win32-x64.exe"
    )
    hermes_provider: str = "custom:127-0-0-1-11434"
    hermes_home: str = (
        r"C:\Users\陈立洪\AppData\Roaming\cn.org.hermesagent.desktop\runtime"
        r"\hermes-home"
    )
    hermes_working_directory: str = ".."
    hermes_timeout_seconds: float = 180.0
    agent_internal_key: str

    local_llm_base_url: str = "http://127.0.0.1:11434/v1"
    local_llm_model: str = "qwen3.5-4b-64k:latest"

    deepseek_base_url: str = "https://api.deepseek.com/v1"
    deepseek_api_key: str
    deepseek_model: str = "DeepSeek-v4-flash"

    model_config = SettingsConfigDict(
        env_file=("../.env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
