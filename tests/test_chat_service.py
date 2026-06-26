import pytest
from pixelpet.chat_service import ChatService
from pixelpet.llm_client import LLMClient, ChatMessage


class FakeLLM(LLMClient):
    def __init__(self):
        self.received: list[ChatMessage] = []

    async def stream_chat(self, messages, on_token, on_done, on_error):
        self.received = list(messages)
        on_token("回")
        on_token("复")
        on_done()


@pytest.mark.asyncio
async def test_send_prepends_system_prompt():
    llm = FakeLLM()
    svc = ChatService(llm, system_prompt="SYS", history_max=10)
    await svc.send("hi", lambda t: None, lambda: None, lambda e: None)
    assert llm.received[0].role == "system"
    assert llm.received[0].content == "SYS"
    assert llm.received[-1].content == "hi"


@pytest.mark.asyncio
async def test_send_appends_assistant_reply_to_history():
    llm = FakeLLM()
    svc = ChatService(llm, system_prompt="SYS", history_max=10)
    await svc.send("hi", lambda t: None, lambda: None, lambda e: None)
    assert any(m.role == "assistant" and m.content == "回复" for m in svc.history)


@pytest.mark.asyncio
async def test_history_window_limits_to_max_turns():
    llm = FakeLLM()
    svc = ChatService(llm, system_prompt="SYS", history_max=2)
    for i in range(5):
        await svc.send(f"msg{i}", lambda t: None, lambda: None, lambda e: None)
    # 仅保留最近 2 轮 = 4 条消息
    assert len(svc.history) <= 4


def test_clear_resets_history():
    llm = FakeLLM()
    svc = ChatService(llm, system_prompt="SYS")
    svc.clear()
    assert svc.history == []
