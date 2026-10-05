"""
请求转发模块。
把组装好的请求转发给真正的上游大模型。
"""
from typing import AsyncIterator
import httpx
from .config import config


async def forward_chat_completion(payload: dict) -> dict:
    """非流式转发：一次性拿到完整回复。"""
    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(
            f"{config.upstream_base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {config.upstream_api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
        )
        resp.raise_for_status()
        return resp.json()


async def forward_stream(payload: dict) -> AsyncIterator[bytes]:
    """流式转发：SSE 直通（预留功能）。"""
    async with httpx.AsyncClient(timeout=120.0) as client:
        async with client.stream(
            "POST",
            f"{config.upstream_base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {config.upstream_api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
        ) as resp:
            async for chunk in resp.aiter_bytes():
                yield chunk