"""Response cache unit tests."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from redteam.cache import ResponseCache
from redteam.schemas import Message, TargetResponse


def _resp(text: str = "hello") -> TargetResponse:
    return TargetResponse(
        target_id="claude-sonnet-4-6",
        model_version="claude-sonnet-4-6",
        request_messages=[Message(role="user", content="hi")],
        response_text=text,
        finish_reason="end_turn",
        input_tokens=3,
        output_tokens=2,
        cost_usd=Decimal("0.0001"),
        latency_ms=42,
    )


def test_cache_miss_then_hit_round_trip(tmp_path: Path) -> None:
    cache = ResponseCache(cache_root=tmp_path)
    msgs = [Message(role="user", content="hi")]
    key = ResponseCache.make_key(
        target_id="claude-sonnet-4-6",
        model_version="claude-sonnet-4-6",
        messages=msgs,
        system=None,
        max_tokens=128,
    )
    assert cache.get(target_id="claude-sonnet-4-6", key=key) is None  # miss
    cache.put(target_id="claude-sonnet-4-6", key=key, response=_resp("first"))
    hit = cache.get(target_id="claude-sonnet-4-6", key=key)
    assert hit is not None
    assert hit.response_text == "first"


def test_keys_differ_on_message_content(tmp_path: Path) -> None:
    _ = ResponseCache(cache_root=tmp_path)
    common = {
        "target_id": "claude-sonnet-4-6",
        "model_version": "claude-sonnet-4-6",
        "system": None,
        "max_tokens": 128,
    }
    k1 = ResponseCache.make_key(messages=[Message(role="user", content="a")], **common)
    k2 = ResponseCache.make_key(messages=[Message(role="user", content="b")], **common)
    assert k1 != k2


def test_keys_differ_on_system_prompt(tmp_path: Path) -> None:
    _ = ResponseCache(cache_root=tmp_path)
    common = {
        "target_id": "claude-sonnet-4-6",
        "model_version": "claude-sonnet-4-6",
        "messages": [Message(role="user", content="hi")],
        "max_tokens": 128,
    }
    k1 = ResponseCache.make_key(system=None, **common)
    k2 = ResponseCache.make_key(system="You are paranoid.", **common)
    assert k1 != k2


def test_corrupt_entry_returns_miss(tmp_path: Path) -> None:
    cache = ResponseCache(cache_root=tmp_path)
    key = "deadbeefdeadbeef"
    target_id = "claude-sonnet-4-6"
    path = cache._path_for(target_id, key)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("{not valid json")
    assert cache.get(target_id=target_id, key=key) is None


def test_clear_target_only(tmp_path: Path) -> None:
    cache = ResponseCache(cache_root=tmp_path)
    msgs = [Message(role="user", content="hi")]
    common = {
        "model_version": "claude-sonnet-4-6",
        "messages": msgs,
        "system": None,
        "max_tokens": 32,
    }
    k1 = ResponseCache.make_key(target_id="claude-sonnet-4-6", **common)
    k2 = ResponseCache.make_key(target_id="llama3.1-8b-local", **common)
    cache.put(target_id="claude-sonnet-4-6", key=k1, response=_resp("c"))
    cache.put(target_id="llama3.1-8b-local", key=k2, response=_resp("l"))
    removed = cache.clear(target_id="claude-sonnet-4-6")
    assert removed == 1
    assert cache.get(target_id="claude-sonnet-4-6", key=k1) is None
    assert cache.get(target_id="llama3.1-8b-local", key=k2) is not None
