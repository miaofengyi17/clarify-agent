# ClarifyAgent · 主动澄清 + 上下文面板中间件

> 一个兼容 OpenAI API 的即插即用中间件，为**任何大模型应用**自动加上「主动澄清」和「结构化上下文面板」的能力。

---

## 它解决什么问题

当你对 AI 说"帮我写个排序函数"时，大多数助手会直接猜一个版本给你，结果往往是：

- 忘了处理空列表
- 默认升序但你要降序
- 没考虑重复元素
- 报错后又得重说一遍

于是你被迫来回对话很多轮，才能拿到想要的代码。

---

## 它怎么解决

ClarifyAgent 坐在你和真正的大模型之间，自动做四件事：

1. **检测模糊性**：用一个小模型判断你的输入是否缺关键信息
2. **主动提问**：如果模糊，生成 1-3 个具体问题（升序还是降序？空列表怎么处理？）
3. **维护上下文面板**：把任务目标、已确认约束、当前代码、报错信息结构化保存
4. **自动注入**：每一轮都把面板拼进 prompt，模型永远不会忘记之前的约定

---

## 实测效果

在我们设计的 10 道编程题对照实验中：

| 条件 | 平均交互轮数 |
|------|-------------|
| 普通助手 + 模糊输入 | 2.2 轮 |
| **ClarifyAgent + 模糊输入** | **1.6 轮** |
| 普通助手 + 明确输入 | 1.0 轮 |
| ClarifyAgent + 明确输入 | 1.0 轮 |

结论：模糊任务下显著更快（约提升 27%），明确任务下没有额外负担。

---

## 快速开始

### 方式一：Docker（推荐）

```bash
git clone https://github.com/你的用户名/clarify-agent.git
cd clarify-agent
cp .env.example .env
# 编辑 .env，填入你的上游大模型 API Key
docker-compose up -d
```

服务启动在 `http://localhost:8000`。

### 方式二：Python 本地运行

```bash
git clone https://github.com/你的用户名/clarify-agent.git
cd clarify-agent
pip install -r requirements.txt
cp .env.example .env
# 编辑 .env 填入你的 Key
python -m clarify_agent
```

---

## 怎么接入到你现有的应用里

只要你的应用能改 `base_url`，就能用。

### Python（OpenAI SDK）

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="any-string",   # 真正的 Key 在 .env 里
)

response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "帮我写个排序函数"}],
    extra_body={"session_id": "user-123"},
)
print(response.choices[0].message.content)
```

### cURL

```bash
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4o",
    "messages": [{"role": "user", "content": "帮我写个排序函数"}],
    "session_id": "user-123"
  }'
```

### 任何兼容 OpenAI 的框架

把它们的 `OPENAI_BASE_URL` 改成 `http://localhost:8000/v1` 即可，比如：

- LangChain
- LlamaIndex
- AutoGen
- Dify
- FastGPT
- 你自己的应用

---

## 返回格式示例

### 输入模糊时

```
【上下文面板】
- 当前理解的任务：帮我写个排序函数
- 已知的约束条件：暂无
- 代码处理的情况：需要先澄清需求

【澄清问题】
1. 排序是升序还是降序？
2. 输入是否可能包含重复元素？
3. 空列表或非数字输入应如何处理？
```

### 用户回答后

```
【上下文面板】
- 当前理解的任务：帮我写个排序函数
- 已知的约束条件：升序、空列表返回空列表
- 代码处理的情况：已根据约束生成完整代码

​```python
def bubble_sort(arr):
    if not arr:
        return []
    n = len(arr)
    for i in range(n - 1):
        for j in range(n - 1 - i):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
    return arr
​```
```

---

## 配置项

编辑 `.env` 文件：

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `UPSTREAM_BASE_URL` | 上游大模型地址 | `https://api.openai.com/v1` |
| `UPSTREAM_API_KEY` | 你的大模型 API Key | 必填 |
| `JUDGE_MODEL` | 用来判断模糊性的小模型 | `gpt-4o-mini` |
| `SESSION_BACKEND` | 会话存储方式 | `memory` |
| `REDIS_URL` | 如果用 Redis 存储 | `redis://localhost:6379` |
| `ENABLE_CLARIFY` | 是否开启主动澄清 | `true` |
| `ENABLE_CONTEXT_PANEL` | 是否开启上下文面板 | `true` |
| `MAX_CLARIFY_QUESTIONS` | 最多问几个问题 | `3` |
| `MAX_SESSION_TURNS` | 单会话最大保留轮数 | `20` |

---

## 架构

```
你的应用
   │
   ▼
ClarifyAgent（本项目）
   │
   ├── 1. 模糊检测  ──► 输入是否缺关键信息？
   ├── 2. 生成问题  ──► 生成 1-3 个澄清问题
   ├── 3. 面板构建  ──► 从会话历史拼出上下文面板
   └── 4. 请求转发  ──► 把面板注入后转发给真正的大模型
   │
   ▼
真正的 LLM（OpenAI / 通义 / Claude / 任意）
```

---

## 核心机制

### 机制 1：主动澄清

当用户输入模糊时，不直接生成代码，而是先提问。这样能：

- 避免猜错方向
- 让用户一次说清关键约束
- 减少后续来回修改的轮数

### 机制 2：上下文面板

每次对话时，自动把历史状态结构化成面板，注入到 prompt 里。这样：

- 大模型不会忘记用户之前确认过的约束
- 不需要把整段对话历史都塞给模型（省 token）
- 关键信息一目了然

---

## 本地开发

```bash
pip install -r requirements.txt
pytest tests/
python -m clarify_agent
```

打开 `http://localhost:8000/docs` 查看交互式 API 文档。

---

## 路线图

- [x] OpenAI 兼容 API
- [x] 主动澄清
- [x] 上下文面板
- [x] 会话状态（内存 / Redis）
- [ ] 流式响应支持
- [ ] Anthropic / Qwen 原生适配
- [ ] Web UI 可视化面板
- [ ] PostgreSQL 持久化

---

## 开源协议

MIT License。

---

## 致谢

这个项目的想法来自对「人-LLM 交互评估」的研究。当大模型越来越强时，如何主动把模糊需求问清楚，比一味地猜答案更重要。