"""
模糊性检测 + 澄清问题生成。
这是整个项目的核心逻辑。
"""
import json
import re
from typing import List, Tuple
from openai import OpenAI
from .config import config
from .prompts import AMBIGUITY_JUDGE_PROMPT, CLARIFY_QUESTIONS_PROMPT


# 用于判断和生成问题的客户端（用便宜的小模型）
_client = OpenAI(
    api_key=config.upstream_api_key,
    base_url=config.upstream_base_url,
)


def is_ambiguous(user_message: str) -> Tuple[bool, List[str]]:
    """
    判断用户输入是否模糊。
    返回 (是否模糊, 缺少的约束列表)。
    """
    # 如果关闭了澄清功能，直接返回不模糊
    if not config.enable_clarify:
        return False, []

    # 快速启发式：太短或太泛的消息直接判定为模糊
    if len(user_message.strip()) < 15:
        return True, ["任务细节"]

    try:
        resp = _client.chat.completions.create(
            model=config.judge_model,
            messages=[
                {
                    "role": "user",
                    "content": AMBIGUITY_JUDGE_PROMPT.format(user_message=user_message),
                }
            ],
            temperature=0.0,  # 判断类任务要确定性
            max_tokens=200,
        )
        text = resp.choices[0].message.content.strip()
        # 从回复里抠出 JSON
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            data = json.loads(match.group(0))
            return bool(data.get("ambiguous", False)), data.get("missing", [])
    except Exception as e:
        # 出错就当不模糊，保证不影响主流程
        print(f"[clarifier] 判断失败: {e}")

    return False, []


def generate_questions(user_message: str, missing: List[str]) -> List[str]:
    """
    生成 1-3 个澄清问题。
    从 LLM 回复里解析编号列表。
    """
    try:
        resp = _client.chat.completions.create(
            model=config.judge_model,
            messages=[
                {
                    "role": "user",
                    "content": CLARIFY_QUESTIONS_PROMPT.format(
                        user_message=user_message,
                        missing=", ".join(missing) if missing else "未指定",
                    ),
                }
            ],
            temperature=0.5,  # 生成问题可以有点多样性
            max_tokens=200,
        )
        text = resp.choices[0].message.content.strip()
        questions = []
        for line in text.split("\n"):
            line = line.strip()
            # 匹配 "1. xxx" 这种编号
            m = re.match(r"^\d+\.\s*(.+)$", line)
            if m:
                questions.append(m.group(1).strip())
        return questions[: config.max_clarify_questions]
    except Exception as e:
        print(f"[clarifier] 生成问题失败: {e}")
        return []