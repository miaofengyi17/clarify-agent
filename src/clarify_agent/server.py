"""
FastAPI 服务器。
对外暴露一个 OpenAI 兼容的 /v1/chat/completions 端点。
"""
import uuid
import time
import re
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from .config import config
from .clarifier import is_ambiguous, generate_questions
from .session import session_store
from .proxy import forward_chat_completion
from .prompts import CONTEXT_PANEL_PROMPT

# 创建 FastAPI 应用
app = FastAPI(title="ClarifyAgent", version="0.1.0")


# ===== 请求数据结构 =====

class ChatMessage(BaseModel):
    """单条消息。"""
    role: str
    content: str


class ChatCompletionRequest(BaseModel):
    """兼容 OpenAI 的请求体。"""
    model: str
    messages: List[ChatMessage]
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = None
    stream: Optional[bool] = False
    session_id: Optional[str] = None  # 我们额外加的字段，用于多轮会话


# ===== 健康检查 =====

@app.get("/health")
async def health():
    """健康检查接口。"""
    return {"status": "ok", "version": "0.1.0"}


@app.get("/v1/models")
async def list_models():
    """列出可用模型（兼容 OpenAI 格式）。"""
    return {
        "object": "list",
        "data": [
            {"id": "clarify-agent", "object": "model", "owned_by": "clarify-agent"}
        ],
    }


# ===== 核心接口 =====

@app.post("/v1/chat/completions")
async def chat_completions(req: ChatCompletionRequest):
    """兼容 OpenAI 的对话接口。"""

    # 1. 确定会话 ID
    session_id = req.session_id or "default"
    state = session_store.get(session_id)

    # 2. 取出用户最后一条消息
    user_messages = [m for m in req.messages if m.role == "user"]
    if not user_messages:
        raise HTTPException(status_code=400, detail="没有找到用户消息。")
    user_message = user_messages[-1].content

    # 3. 第一轮时检查是否模糊
    is_first_turn = len(state["history"]) == 0
    if is_first_turn and config.enable_clarify:
        ambiguous, missing = is_ambiguous(user_message)
        if ambiguous:
            # 生成澄清问题
            questions = generate_questions(user_message, missing)
            state["task_description"] = user_message
            state["history"].append({"role": "user", "content": user_message})
            session_store.set(session_id, state)

            # 直接返回面板 + 问题，不走上游模型
            answer = (
                "【上下文面板】\n"
                f"- 当前理解的任务：{user_message}\n"
                "- 已知的约束条件：暂无\n"
                "- 代码处理的情况：需要先澄清需求\n\n"
                "【澄清问题】\n"
                + "\n".join(f"{i+1}. {q}" for i, q in enumerate(questions))
            )
            return _completion_response(req.model, answer)

    # 4. 构造上下文面板，注入到 system prompt
    if config.enable_context_panel:
        panel = CONTEXT_PANEL_PROMPT.format(
            task_description=state["task_description"] or user_message,
            confirmed_constraints="\n".join(state["confirmed_constraints"]) or "暂无",
            current_code=state["current_code"] or "暂无",
            last_test_error=state["last_test_error"] or "暂无",
            user_message=user_message,
        )
        forwarded_messages = [{"role": "system", "content": panel}]
        for m in req.messages:
            forwarded_messages.append({"role": m.role, "content": m.content})
    else:
        forwarded_messages = [{"role": m.role, "content": m.content} for m in req.messages]

    # 5. 更新会话历史
    state["history"].append({"role": "user", "content": user_message})
    # 只保留最近 N 轮，防止无限增长
    state["history"] = state["history"][-config.max_session_turns:]
    session_store.set(session_id, state)

    # 6. 转发给上游大模型
    payload = {
        "model": req.model,
        "messages": forwarded_messages,
        "temperature": req.temperature,
        "max_tokens": req.max_tokens,
        "stream": False,
    }
    result = await forward_chat_completion(payload)

    # 7. 从模型回复里提取代码，更新会话状态
    try:
        content = result["choices"][0]["message"]["content"]
        _update_state_from_reply(state, content)
        session_store.set(session_id, state)
    except Exception:
        pass

    return JSONResponse(result)


def _update_state_from_reply(state: dict, content: str) -> None:
    """从模型回复中提取代码，存到当前会话状态。"""
    m = re.search(r"```(?:python)?\s*\n?(.*?)```", content, re.DOTALL)
    if m:
        state["current_code"] = m.group(1).strip()


def _completion_response(model: str, content: str) -> dict:
    """构造一个兼容 OpenAI 的响应。"""
    return {
        "id": f"chatcmpl-{uuid.uuid4().hex[:12]}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": model,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": content},
                "finish_reason": "stop",
            }
        ],
        "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
    }


@app.delete("/v1/sessions/{session_id}")
async def clear_session(session_id: str):
    """手动清空某个会话。"""
    session_store.clear(session_id)
    return {"status": "cleared", "session_id": session_id}