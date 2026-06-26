"""DeepSeek 实现：OpenAI 兼容协议。"""
from __future__ import annotations

from typing import Callable

from openai import AsyncOpenAI

from .base import ChatMessage, LLMClient


class DeepSeekClient(LLMClient):
    def __init__(self, api_key: str, base_url: str, model: str):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self._client = AsyncOpenAI(api_key=api_key, base_url=base_url)

    async def stream_chat(
        self,
        messages: list[ChatMessage],
        on_token: Callable[[str], None],
        on_done: Callable[[], None],
        on_error: Callable[[Exception], None],
    ) -> None:
        try:
            payload = [{"role": m.role, "content": m.content} for m in messages]
            stream = await self._client.chat.completions.create(
                model=self.model,
                messages=payload,
                stream=True,
            )
            async for chunk in stream:
                delta = chunk.choices[0].delta.content
                if delta:
                    on_token(delta)
            on_done()
        except Exception as e:
            on_error(e)