"""Verify that the numbers written in a findings document match the run artifact.

The failure this guards against is specific. A claims check that confirms a
cited file *exists*, or that compares a computed value against a number the
author typed into the checker, verifies nothing about the document: both pass
when the document is wrong. The first never opens the artifact; the second never
opens the document.

This script opens **both**. It recomputes each quantity from
`results/*.jsonl` and asserts the rendered value appears verbatim in the
markdown. A figure changed in the document without changing the data fails, and
a figure that drifts in the data without being updated in the document also
fails.

    python scripts/check_finding_claims.py            # exit 1 on any mismatch
    python scripts/check_finding_claims.py --list     # show what is checked

Exit code is the signal. Do not pipe this into anything whose status you then
read — see finding #9.
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "findings" / "a-preregistered-null-at-p-0-0001.md"
RUN = ROOT / "results" / "guard_4bit.jsonl"

_SPEC = importlib.util.spec_from_file_location(
    "report_locale_provenance", ROOT / "scripts" / "report_locale_provenance.py"
)
assert _SPEC and _SPEC.loader
report = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = report
_SPEC.loader.exec_module(report)


def _items() -> list[dict[str, Any]]:
    _, by_item = report.load(RUN)
    return [v for v in by_item.values() if len(v) == len(report.CONDITIONS)]


def _rate(items: list[dict[str, Any]], a: str, b: str) -> dict[str, Any]:
    return report.change_rate(items, a, b)


def _unsafe_pct(items: list[dict[str, Any]], cond: str) -> str:
    verdicts = [i[cond]["verdict"] for i in items]
    ok = [v for v in verdicts if v != report.UNPARSEABLE]
    return f"{100 * sum(1 for v in ok if v == 1) / len(ok):.1f}%"


def build_claims() -> list[tuple[str, Callable[[], str]]]:
    """(label, thunk) pairs. Each thunk returns the string that must appear."""
    items = _items()
    benign = [i for i in items if i["native"]["split"] == "hard_negative"]
    harmful = [i for i in items if i["native"]["split"] == "harmful"]
    tai = [i for i in items if i["native"]["tai_collapse"]]
    primary = _rate(items, "native", "glyph_only")

    return [
        ("primary changed/total", lambda: f"{primary['changed']} / {primary['n']}"),
        ("primary rate", lambda: f"{100 * primary['rate']:.1f}%"),
        ("primary discordant b", lambda: f"b = {primary['b']}"),
        ("primary discordant c", lambda: f"c = {primary['c']}"),
        ("benign rate", lambda: f"{100 * _rate(benign, 'native', 'glyph_only')['rate']:.1f}%"),
        ("benign c", lambda: str(_rate(benign, "native", "glyph_only")["c"])),
        ("harmful rate", lambda: f"{100 * _rate(harmful, 'native', 'glyph_only')['rate']:.1f}%"),
        (
            "C vs B rate",
            lambda: f"{100 * _rate(items, 'native', 'dictionary_localised')['rate']:.1f}%",
        ),
        ("A vs D rate", lambda: f"{100 * _rate(items, 'glyph_only', 'hong_kong')['rate']:.1f}%"),
        ("A vs D on tai", lambda: f"{100 * _rate(tai, 'glyph_only', 'hong_kong')['rate']:.1f}%"),
        ("C vs D on tai", lambda: f"{100 * _rate(tai, 'native', 'hong_kong')['rate']:.1f}%"),
        ("tai subgroup size", lambda: f"{len(tai)} "),
        ("base rate native", lambda: _unsafe_pct(items, "native")),
        ("base rate dictionary", lambda: _unsafe_pct(items, "dictionary_localised")),
        ("base rate glyph-only", lambda: _unsafe_pct(items, "glyph_only")),
        ("base rate hong-kong", lambda: _unsafe_pct(items, "hong_kong")),
        ("discordant pair count", lambda: f"n = {primary['changed']}"),
        ("concordant pair count", lambda: f"n = {primary['n'] - primary['changed']}"),
    ]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true", help="print the checked values and exit")
    args = ap.parse_args()

    if not RUN.exists():
        print(f"FAIL: run artifact missing: {RUN.relative_to(ROOT)}")
        return 1
    if not DOC.exists():
        print(f"FAIL: document missing: {DOC.relative_to(ROOT)}")
        return 1

    text = DOC.read_text(encoding="utf-8")
    claims = build_claims()

    if not claims:
        # A checker with nothing to check passes vacuously. Refuse to.
        print("FAIL: no claims defined; the check would be vacuous")
        return 1

    failures = 0
    for label, thunk in claims:
        value = thunk()
        present = value in text
        if args.list:
            print(f"  {label:<24} {value!r}")
            continue
        if not present:
            print(f"MISMATCH  {label:<24} recomputed {value!r} does not appear in the document")
            failures += 1

    if args.list:
        print(f"\n{len(claims)} values recomputed from {RUN.relative_to(ROOT)}")
        return 0

    if failures:
        print(f"\n{failures} of {len(claims)} claims do not match the artifact.")
        return 1
    print(f"ok: {len(claims)} claims in {DOC.name} match values recomputed from the run artifact.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
