"""对话服务：维护上下文窗口，包装 LLM 流式调用。"""
from __future__ import annotations

from typing import Callable

from pixelpet.llm_client import LLMClient, ChatMessage


class ChatService:
    def __init__(self, llm: LLMClient, system_prompt: str, history_max: int = 10):
        self.llm = llm
        self.system_prompt = system_prompt
        self.history_max = history_max
        self._history: list[ChatMessage] = []

    @property
    def history(self) -> list[ChatMessage]:
        return list(self._history)

    def clear(self) -> None:
        self._history.clear()

    async def send(
        self,
        user_text: str,
        on_token: Callable[[str], None],
        on_done: Callable[[], None],
        on_error: Callable[[Exception], None],
    ) -> None:
        self._history.append(ChatMessage("user", user_text))
        messages = [ChatMessage("system", self.system_prompt), *self._history]

        collected: list[str] = []
        error_holder: list[Exception] = []

        def _on_token(t: str) -> None:
            collected.append(t)
            on_token(t)

        def _on_done() -> None:
            self._history.append(ChatMessage("assistant", "".join(collected)))
            self._trim()
            on_done()

        def _on_error(e: Exception) -> None:
            # 回滚刚才追加的 user
            if self._history and self._history[-1].role == "user":
                self._history.pop()
            error_holder.append(e)
            on_error(e)

        await self.llm.stream_chat(messages, _on_token, _on_done, _on_error)

    def _trim(self) -> None:
        # 保留最近 history_max * 2 条（user+assistant 为 1 轮）
        max_msgs = self.history_max * 2
        if len(self._history) > max_msgs:
            self._history = self._history[-max_msgs:]
