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
        self._client = None  # lazy

    def _ensure_client(self):
        if self._client is None:
            if not self.api_key:
                raise RuntimeError("DeepSeek API key 未配置，请在设置中填写")
            self._client = AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)
        return self._client

    async def stream_chat(
        self,
        messages: list[ChatMessage],
        on_token: Callable[[str], None],
        on_done: Callable[[], None],
        on_error: Callable[[Exception], None],
    ) -> None:
        try:
            client = self._ensure_client()  # may raise RuntimeError if no api_key
            payload = [{"role": m.role, "content": m.content} for m in messages]
            stream = await client.chat.completions.create(
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