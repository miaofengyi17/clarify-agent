"""
基础单元测试。
运行：pytest tests/
"""
import os

# 测试前需要先设置一个假 Key，避免导入时报错
os.environ["UPSTREAM_API_KEY"] = "fake-key-for-test"

from clarify_agent.session import MemorySessionStore


def test_session_store_basic():
    """测试会话存储的基本读写。"""
    store = MemorySessionStore()

    # 初始状态应该是空的
    state = store.get("s1")
    assert state["task_description"] == ""
    assert state["confirmed_constraints"] == []
    assert state["current_code"] == ""

    # 写入后应该能读到
    state["task_description"] = "写一个排序函数"
    store.set("s1", state)

    reloaded = store.get("s1")
    assert reloaded["task_description"] == "写一个排序函数"


def test_session_clear():
    """测试清空会话。"""
    store = MemorySessionStore()

    state = store.get("s1")
    state["task_description"] = "xxx"
    store.set("s1", state)

    # 清空后应该回到初始状态
    store.clear("s1")
    assert store.get("s1")["task_description"] == ""


def test_session_isolation():
    """测试不同会话之间互不干扰。"""
    store = MemorySessionStore()

    s1 = store.get("user-a")
    s1["task_description"] = "任务 A"
    store.set("user-a", s1)

    s2 = store.get("user-b")
    assert s2["task_description"] == ""  # 用户 B 的状态应该是干净的