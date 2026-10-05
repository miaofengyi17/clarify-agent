"""
会话状态管理。
支持两种后端：
- memory：存内存，简单快速，重启丢失
- redis：存 Redis，重启保留，适合生产
"""
import json
import threading
from typing import Dict
from .config import config


class MemorySessionStore:
    """线程安全的内存会话存储。"""

    def __init__(self):
        self._lock = threading.Lock()
        self._data: Dict[str, dict] = {}

    def get(self, session_id: str) -> dict:
        """读取会话状态，不存在则返回空状态。"""
        with self._lock:
            return self._data.get(session_id, self._empty())

    def set(self, session_id: str, state: dict) -> None:
        """写入会话状态。"""
        with self._lock:
            self._data[session_id] = state

    def clear(self, session_id: str) -> None:
        """清空某个会话。"""
        with self._lock:
            self._data.pop(session_id, None)

    @staticmethod
    def _empty() -> dict:
        """空会话的初始结构。"""
        return {
            "task_description": "",
            "confirmed_constraints": [],
            "current_code": "",
            "last_test_error": "",
            "history": [],
        }


class RedisSessionStore:
    """基于 Redis 的会话存储。"""

    def __init__(self, url: str):
        import redis
        self._client = redis.from_url(url, decode_responses=True)

    def get(self, session_id: str) -> dict:
        raw = self._client.get(f"clarify:{session_id}")
        if raw:
            return json.loads(raw)
        return MemorySessionStore._empty()

    def set(self, session_id: str, state: dict) -> None:
        self._client.set(
            f"clarify:{session_id}",
            json.dumps(state),
            ex=3600 * 24 * 7,
        )

    def clear(self, session_id: str) -> None:
        self._client.delete(f"clarify:{session_id}")


def get_session_store():
    """根据配置返回对应的会话存储实例。"""
    if config.session_backend == "redis":
        return RedisSessionStore(config.redis_url)
    return MemorySessionStore()


# 全局单例（这一行很关键，server.py 就是从这里导入的）
session_store = get_session_store()