"""Disk-backed response cache.

Lesson L2 from PROJECT-1-KIT.md: cache every API call. Eval reruns are
constant during development; without a cache, each tweak to the scoring
layer would re-spend the same budget on the same prompts.

Key: SHA1 of canonical JSON of (target_id, model_version, system, messages,
max_tokens). The system prompt + max_tokens are part of the key because
flipping a defence on/off changes them and would silently return wrong
cached data otherwise.

Storage layout:
    {cache_root}/{target_id}/{first2-of-hash}/{rest-of-hash}.json

The two-level directory split keeps `ls` snappy for caches with many
thousands of entries.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from redteam.schemas import Message, TargetResponse

DEFAULT_CACHE_ROOT = Path("data/cache/responses")


class ResponseCache:
    """Read-through, write-through cache. Plain JSON on disk."""

    def __init__(self, cache_root: Path | None = None) -> None:
        self.cache_root = cache_root or DEFAULT_CACHE_ROOT

    @staticmethod
    def make_key(
        *,
        target_id: str,
        model_version: str,
        messages: list[Message],
        system: str | None,
        max_tokens: int,
    ) -> str:
        # Canonical form: sort_keys for stable hash across runs.
        payload = json.dumps(
            {
                "target_id": target_id,
                "model_version": model_version,
                "system": system or "",
                "messages": [m.model_dump() for m in messages],
                "max_tokens": max_tokens,
            },
            sort_keys=True,
        )
        return hashlib.sha1(payload.encode("utf-8")).hexdigest()

    def _path_for(self, target_id: str, key: str) -> Path:
        return self.cache_root / target_id / key[:2] / f"{key[2:]}.json"

    def get(self, *, target_id: str, key: str) -> TargetResponse | None:
        path = self._path_for(target_id, key)
        if not path.exists():
            return None
        try:
            return TargetResponse.model_validate_json(path.read_text())
        except Exception:
            # Corrupt cache entry — treat as a miss; next put() overwrites.
            return None

    def put(self, *, target_id: str, key: str, response: TargetResponse) -> None:
        path = self._path_for(target_id, key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(response.model_dump_json(indent=2))

    def clear(self, target_id: str | None = None) -> int:
        """Delete cache entries. Returns count removed.

        clear() with no arg wipes everything. clear(target_id="x") wipes
        only that target's entries.
        """
        root = self.cache_root if target_id is None else self.cache_root / target_id
        if not root.exists():
            return 0
        count = 0
        for path in root.rglob("*.json"):
            path.unlink()
            count += 1
        return count
