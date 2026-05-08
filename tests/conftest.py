"""Pytest session config — load .env once before any test imports."""

from __future__ import annotations

from dotenv import load_dotenv

# Load .env from the repo root if present. Live smoke tests in tests/smoke/
# need ANTHROPIC_API_KEY etc.; unit tests don't, but loading is harmless.
load_dotenv()
