"""
使用示例：从任何 OpenAI 客户端调用 ClarifyAgent。
运行前请确保服务器已启动（python -m clarify_agent）。
"""
from openai import OpenAI

# 关键：把 base_url 指向本地 ClarifyAgent
client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="any-string",  # 真正的 Key 在 .env 里
)

# 用一个会话 ID 保持多轮状态
SESSION = "demo-user-001"

# ===== 第一轮：模糊输入 =====
print("=" * 60)
print("第一轮：用户说得很模糊")
print("=" * 60)

r1 = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "帮我写个排序函数"}],
    extra_body={"session_id": SESSION},
)
print(r1.choices[0].message.content)

# ===== 第二轮：用户回答澄清问题 =====
print("\n" + "=" * 60)
print("第二轮：用户回答澄清问题")
print("=" * 60)

r2 = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "升序排序，空列表返回空列表"}],
    extra_body={"session_id": SESSION},
)
print(r2.choices[0].message.content)