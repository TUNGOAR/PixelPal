"""LLM 抽象接口。"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Callable, Awaitable


@dataclass
class ChatMessage:
    role: str
    content: str


class LLMClient(ABC):
    @abstractmethod
    async def stream_chat(
        self,
        messages: list[ChatMessage],
        on_token: Callable[[str], None],
        on_done: Callable[[], None],
        on_error: Callable[[Exception], None],
    ) -> None:
        ...
