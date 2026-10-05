#!/bin/bash
# cURL 调用示例

# ===== 第一轮：模糊输入 =====
echo "===== 第一轮：模糊输入 ====="
curl -s http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4o",
    "messages": [{"role": "user", "content": "帮我写个排序函数"}],
    "session_id": "curl-demo-001"
  }' | python -m json.tool

# ===== 第二轮：回答澄清问题 =====
echo -e "\n===== 第二轮：回答澄清问题 ====="
curl -s http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4o",
    "messages": [{"role": "user", "content": "升序，空列表返回空列表"}],
    "session_id": "curl-demo-001"
  }' | python -m json.tool

# ===== 清空会话 =====
echo -e "\n===== 清空会话 ====="
curl -s -X DELETE http://localhost:8000/v1/sessions/curl-demo-001 \
  | python -m json.tool