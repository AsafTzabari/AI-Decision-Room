"""Tests for the LLM client guard and retry behavior."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from llm.client import EmptyLLMResponseError, LLMClient, ModelTier


def _fake_response(content: str | None):
    class Choice:
        class Msg:
            pass

        message = Msg()

    Choice.message.content = content

    class Resp:
        choices = [Choice()]

    return Resp()


@pytest.mark.asyncio
async def test_complete_raises_on_empty_string(llm: LLMClient):
    async def mock_acompletion(**kwargs):
        return _fake_response("")

    with patch("llm.client.acompletion", side_effect=mock_acompletion):
        with pytest.raises(EmptyLLMResponseError):
            await llm.complete([{"role": "user", "content": "hi"}])


@pytest.mark.asyncio
async def test_complete_raises_on_whitespace_only(llm: LLMClient):
    async def mock_acompletion(**kwargs):
        return _fake_response("   \n  \t  ")

    with patch("llm.client.acompletion", side_effect=mock_acompletion):
        with pytest.raises(EmptyLLMResponseError):
            await llm.complete([{"role": "user", "content": "hi"}])


@pytest.mark.asyncio
async def test_complete_raises_on_none_content(llm: LLMClient):
    async def mock_acompletion(**kwargs):
        return _fake_response(None)

    with patch("llm.client.acompletion", side_effect=mock_acompletion):
        with pytest.raises(EmptyLLMResponseError):
            await llm.complete([{"role": "user", "content": "hi"}])


@pytest.mark.asyncio
async def test_complete_returns_non_empty_content(llm: LLMClient):
    async def mock_acompletion(**kwargs):
        return _fake_response("real answer")

    with patch("llm.client.acompletion", side_effect=mock_acompletion):
        result = await llm.complete([{"role": "user", "content": "hi"}])

    assert result == "real answer"


@pytest.mark.asyncio
async def test_complete_with_retry_succeeds_on_second_attempt(llm: LLMClient):
    call_count = {"n": 0}

    async def flaky(**kwargs):
        call_count["n"] += 1
        if call_count["n"] == 1:
            return _fake_response("")
        return _fake_response("recovered answer")

    with patch("llm.client.acompletion", side_effect=flaky):
        result = await llm.complete_with_retry(
            [{"role": "user", "content": "hi"}],
            tier=ModelTier.STANDARD,
            max_attempts=2,
        )

    assert result == "recovered answer"
    assert call_count["n"] == 2


@pytest.mark.asyncio
async def test_complete_with_retry_raises_after_exhausting_attempts(llm: LLMClient):
    call_count = {"n": 0}

    async def always_empty(**kwargs):
        call_count["n"] += 1
        return _fake_response("")

    with patch("llm.client.acompletion", side_effect=always_empty):
        with pytest.raises(EmptyLLMResponseError):
            await llm.complete_with_retry(
                [{"role": "user", "content": "hi"}],
                tier=ModelTier.STANDARD,
                max_attempts=3,
            )

    assert call_count["n"] == 3


@pytest.mark.asyncio
async def test_complete_with_retry_does_not_swallow_other_errors(llm: LLMClient):
    """Non-empty errors (e.g. network) must not be wrapped or retried."""

    async def raises_runtime(**kwargs):
        raise RuntimeError("provider unreachable")

    with patch("llm.client.acompletion", side_effect=raises_runtime):
        with pytest.raises(RuntimeError, match="provider unreachable"):
            await llm.complete_with_retry(
                [{"role": "user", "content": "hi"}],
                max_attempts=3,
            )


@pytest.mark.asyncio
async def test_complete_json_uses_retry(llm: LLMClient):
    call_count = {"n": 0}

    async def flaky(**kwargs):
        call_count["n"] += 1
        if call_count["n"] == 1:
            return _fake_response("")
        return _fake_response('[{"role_title": "X", "base_persona": "Y"}]')

    with patch("llm.client.acompletion", side_effect=flaky):
        parsed = await llm.complete_json([{"role": "user", "content": "hi"}])

    assert parsed == [{"role_title": "X", "base_persona": "Y"}]
    assert call_count["n"] == 2
