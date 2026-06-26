import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pixelpet.llm_client import ChatMessage, LLMClient
from pixelpet.llm_client.deepseek import DeepSeekClient


@pytest.mark.asyncio
async def test_stream_chat_emits_tokens():
    # mock chunks
    chunk1 = MagicMock()
    chunk1.choices = [MagicMock()]
    chunk1.choices[0].delta.content = "你好"
    chunk2 = MagicMock()
    chunk2.choices = [MagicMock()]
    chunk2.choices[0].delta.content = "呀"
    chunk3 = MagicMock()
    chunk3.choices = [MagicMock()]
    chunk3.choices[0].delta.content = None

    async def fake_stream():
        yield chunk1
        yield chunk2
        yield chunk3

    fake_response = fake_stream()

    with patch("pixelpet.llm_client.deepseek.AsyncOpenAI") as mock_cls:
        mock_openai = mock_cls.return_value
        mock_openai.chat.completions.create = AsyncMock(return_value=fake_response)

        client = DeepSeekClient(api_key="x", base_url="https://x", model="m")

        tokens: list[str] = []
        done_called = False

        def on_token(t):
            tokens.append(t)

        def on_done():
            nonlocal done_called
            done_called = True

        await client.stream_chat(
            messages=[ChatMessage("user", "hi")],
            on_token=on_token,
            on_done=on_done,
            on_error=lambda e: pytest.fail(f"unexpected error: {e}"),
        )

        assert "".join(tokens) == "你好呀"
        assert done_called is True