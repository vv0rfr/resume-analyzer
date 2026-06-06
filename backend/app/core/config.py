"""
核心配置模块
通过 pydantic-settings 从 .env 文件和环境变量加载配置
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """应用配置"""

    # DeepSeek API
    deepseek_api_key: str = "your-deepseek-api-key-here"
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-chat"

    # 服务
    app_host: str = "0.0.0.0"
    app_port: int = 8010
    debug: bool = True

    # 数据库
    database_url: str = "sqlite:///./resume_analyzer.db"

    # CORS（允许前端跨域访问）
    cors_origins: list[str] = ["http://localhost:5173"]

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }


@lru_cache()
def get_settings() -> Settings:
    """获取配置单例（带缓存）"""
    return Settings()
