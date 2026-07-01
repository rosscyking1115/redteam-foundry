"""Language/script detection and attack-family inference (Phase 1b).

Two coarse, deterministic, stdlib-only taggers used by the corpus audit:

- `detect_language` — a **script-based** language classifier. It counts
  letters by Unicode script and returns a coarse label. It can tell Japanese
  (kana), Korean (hangul), Chinese (Han-only), and non-Latin scripts apart,
  and flags **code-switching** (a Latin + non-Latin mix). It deliberately does
  *not* distinguish languages that share a script (English vs French; Simplified
  vs Traditional Chinese) — that needs a real language-ID model and is Phase 4.
  Labelling it "script-based" keeps the claim honest.

- `infer_attack_families` — high-precision **surface-marker** patterns
  (instruction-override, roleplay/persona, indirect-injection framing,
  obfuscation). A match is a strong hint; a non-match means "no known marker",
  not "no attack". Reported as coverage, never as ground truth.
"""

from __future__ import annotations

import re
import unicodedata
from collections import Counter

from pydantic import BaseModel, ConfigDict

# ---------------------------------------------------------------------------
# Language / script detection
# ---------------------------------------------------------------------------

# Unicode-name prefixes → coarse script bucket. `unicodedata.name` is the
# robust way to bucket a letter (e.g. "LATIN SMALL LETTER A", "CJK UNIFIED
# IDEOGRAPH-4E2D", "HIRAGANA LETTER A", "HANGUL SYLLABLE GA").
_SCRIPT_PREFIXES: tuple[tuple[str, str], ...] = (
    ("LATIN", "latin"),
    ("CJK", "han"),
    ("HIRAGANA", "hiragana"),
    ("KATAKANA", "katakana"),
    ("HANGUL", "hangul"),
    ("CYRILLIC", "cyrillic"),
    ("ARABIC", "arabic"),
    ("HEBREW", "hebrew"),
    ("DEVANAGARI", "devanagari"),
    ("THAI", "thai"),
    ("GREEK", "greek"),
)

# A script must reach this share of the letters in a prompt to count toward the
# code-switching (mixed) decision — filters out a stray loanword character.
_MIXED_SHARE = 0.15


class LanguageTag(BaseModel):
    """Coarse language/script classification of one prompt."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    label: str  # coarse label used for coverage: ja/ko/zh/latin/<script>/unknown
    scripts: tuple[str, ...]  # every script bucket present, sorted
    mixed: bool  # Latin + non-Latin (or two non-Latin families) — code-switching


def _char_script(ch: str) -> str | None:
    """Script bucket for a single character, or None if it is not a letter."""
    if not unicodedata.category(ch).startswith("L"):
        return None
    try:
        name = unicodedata.name(ch)
    except ValueError:  # unnamed char
        return "other"
    for prefix, script in _SCRIPT_PREFIXES:
        if name.startswith(prefix):
            return script
    return "other"


def _macro_family(script: str) -> str:
    """Group scripts into language macro-families for the mixed-language test.

    Japanese legitimately mixes Han (kanji) + kana, so those collapse into one
    'cjk' family and are NOT treated as code-switching.
    """
    if script in ("han", "hiragana", "katakana", "hangul"):
        return "cjk"
    return script


def detect_language(text: str) -> LanguageTag:
    """Classify a prompt's script/language coarsely. Deterministic, stdlib-only."""
    counts: Counter[str] = Counter()
    for ch in text:
        script = _char_script(ch)
        if script is not None:
            counts[script] += 1

    total = sum(counts.values())
    if total == 0:
        return LanguageTag(label="unknown", scripts=(), mixed=False)

    # Primary label. Kana is uniquely Japanese; hangul uniquely Korean; Han
    # without either reads as Chinese. Otherwise fall back to the dominant
    # script bucket (Latin stays "latin" — not further resolved here).
    def has(script: str) -> bool:
        return counts.get(script, 0) / total >= 0.10

    if has("hangul"):
        label = "ko"
    elif has("hiragana") or has("katakana"):
        label = "ja"
    elif has("han"):
        label = "zh"
    else:
        label = counts.most_common(1)[0][0]

    # Code-switching: two or more distinct macro-families each above the share.
    fam_counts: Counter[str] = Counter()
    for script, c in counts.items():
        fam_counts[_macro_family(script)] += c
    present_families = [f for f, c in fam_counts.items() if c / total >= _MIXED_SHARE]
    mixed = len(present_families) >= 2

    return LanguageTag(label=label, scripts=tuple(sorted(counts)), mixed=mixed)


# ---------------------------------------------------------------------------
# Attack-family surface markers
# ---------------------------------------------------------------------------

# High-precision patterns. Favour precision over recall: a false "family" tag is
# worse than a miss, because the report frames coverage as "markers detected".
_ATTACK_FAMILY_PATTERNS: dict[str, tuple[re.Pattern[str], ...]] = {
    "instruction_override": (
        re.compile(
            r"\bignore (?:the |all |any |your )?(?:previous|above|prior|earlier|preceding)\b", re.I
        ),
        re.compile(
            r"\bdisregard (?:the |your |all )?(?:previous|above|prior|instructions|rules)\b", re.I
        ),
        re.compile(
            r"\bforget (?:your|the|all)\b.{0,20}\b(?:instructions|rules|guidelines|prompt)\b", re.I
        ),
    ),
    "roleplay_persona": (
        re.compile(r"\bpretend (?:to be|you are|that you|you're)\b", re.I),
        re.compile(r"\bact as (?:a |an |if |though )", re.I),
        re.compile(r"\brole[\s-]?play\b", re.I),
        re.compile(r"\bdeveloper mode\b", re.I),
        re.compile(r"\bDAN\b"),  # case-sensitive: the "DAN" jailbreak persona
        re.compile(
            r"\byou are (?:now )?(?:a |an )?(?:do anything now|unfiltered|jailbroken|unrestricted)\b",
            re.I,
        ),
    ),
    "indirect_injection": (
        re.compile(
            r"\b(?:the following|below|this)\b.{0,30}\b(?:document|email|web ?page|message|tool output|search result|comment)\b",
            re.I,
        ),
        re.compile(r"\b(?:system|admin|important)\b.{0,20}\b(?:note|message|instruction)\b", re.I),
    ),
    "obfuscation": (
        re.compile(r"\b(?:base64|rot13|leet\s?speak|caesar cipher)\b", re.I),
        re.compile(
            r"\b(?:in|using|write (?:it )?in|encode (?:it )?in)\b.{0,12}\b(?:morse|binary|hex(?:adecimal)?)\b",
            re.I,
        ),
    ),
}

# Stable list of the families this module can detect — so a corpus with zero
# matches for a family still reports it as 0, not as absent.
ATTACK_FAMILIES: tuple[str, ...] = tuple(_ATTACK_FAMILY_PATTERNS.keys())


def infer_attack_families(text: str) -> tuple[str, ...]:
    """Return the attack-family markers detected in a prompt (possibly empty)."""
    hits = [
        family
        for family, patterns in _ATTACK_FAMILY_PATTERNS.items()
        if any(p.search(text) for p in patterns)
    ]
    return tuple(hits)
