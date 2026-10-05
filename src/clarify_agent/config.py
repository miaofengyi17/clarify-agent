"""
配置管理模块。
所有配置从 .env 文件加载，集中在这一个地方，方便维护。
"""
import os
from dataclasses import dataclass
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()


@dataclass
class Config:
    """全局配置对象。"""

    upstream_base_url: str = os.getenv("UPSTREAM_BASE_URL", "https://api.openai.com/v1")
    upstream_api_key: str = os.getenv("UPSTREAM_API_KEY", "")
    judge_model: str = os.getenv("JUDGE_MODEL", "gpt-4o-mini")

    session_backend: str = os.getenv("SESSION_BACKEND", "memory")
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379")

    enable_clarify: bool = os.getenv("ENABLE_CLARIFY", "true").lower() == "true"
    enable_context_panel: bool = os.getenv("ENABLE_CONTEXT_PANEL", "true").lower() == "true"

    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8000"))
    log_level: str = os.getenv("LOG_LEVEL", "info")

    max_clarify_questions: int = int(os.getenv("MAX_CLARIFY_QUESTIONS", "3"))
    max_session_turns: int = int(os.getenv("MAX_SESSION_TURNS", "20"))


config = Config()