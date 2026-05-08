"""Exclusion filter — applied at corpus-load time per ETHICS.md.

Two-layer defence so a missed pattern in one layer is caught by the other:

1. **Source-category exclusion.** When the upstream dataset labels prompts
   by category (HarmBench's SemanticCategory, JailbreakBench's Category),
   drop entire categories outright. This is the cheap, deterministic layer.

2. **Keyword/regex blocklist.** For unlabeled prompts (AdvBench is just a
   CSV of goals with no taxonomy) we scan the text against a conservative
   regex list. Patterns favour precision over recall: false positives drop
   a benign prompt; false negatives leak something we promised in ETHICS.md
   we wouldn't test. False positives are the safer failure mode.

The unit test `tests/unit/test_exclusion_filter.py` feeds a curated set of
positive (must-be-flagged) and negative (must-pass) examples through this
module and asserts zero leakage.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass

from redteam.schemas import AttackCase, ExcludedTopic

# ---------------------------------------------------------------------------
# Regex blocklist
# ---------------------------------------------------------------------------

# Each ExcludedTopic maps to a list of regex patterns. A prompt is flagged
# if ANY pattern in ANY topic matches. Patterns are case-insensitive.
_PATTERNS: dict[ExcludedTopic, list[re.Pattern[str]]] = {
    "csam": [
        re.compile(r"\bcsam\b|\bcsem\b|\bchild[\s-]?porn", re.I),
        re.compile(
            r"\b(child|minor|kid|teen|underage|under[\s-]?(?:18|13))\b"
            r".{0,40}\b(sex|porn|nud|abuse|exploit|gromm|trafficking)",
            re.I,
        ),
        re.compile(
            r"\b(sex|porn|nud|abuse|exploit|grooming|trafficking)"
            r".{0,40}\b(child|minor|kid|teen|underage)\b",
            re.I,
        ),
    ],
    "bio_chem_radiological_nuclear_weapons_synthesis": [
        # Synthesis verbs near WMD agents.
        re.compile(
            r"\b(synthesi[sz]e|manufactur|produc|mak|creat|build|cook|brew|prepare)"
            r".{0,60}\b(sarin|tabun|vx\b|novichok|mustard\s*gas|chlorine\s*gas|"
            r"phosgene|ricin|botulinum|anthrax|smallpox|ebola|marburg|"
            r"nerve\s*agent|chemical\s*weapon|biological\s*weapon|bio[\s-]?weapon|"
            r"chem[\s-]?weapon|toxin)\b",
            re.I,
        ),
        re.compile(
            r"\b(synthesi[sz]e|manufactur|produc|mak|creat|build|construct|design)"
            r".{0,60}\b(nuclear\s*(?:weapon|bomb|device)|"
            r"fission\s*(?:weapon|bomb|device)|"
            r"dirty\s*bomb|radiological\s*(?:weapon|bomb|device|dispersal))\b",
            re.I,
        ),
        re.compile(r"\b(enrich|weapons[\s-]?grade)\s+(uranium|plutonium)\b", re.I),
        re.compile(
            r"\b(nerve\s*agent|toxin)\b.*\b(synthesi[sz]e|recipe|instructions|how[\s-]?to)\b",
            re.I,
        ),
    ],
    "detailed_self_harm_methods": [
        # Trailing word boundary intentionally omitted on `suicid` / `overdose`
        # — \b would never match inside "suicide" or "overdosed" (the next
        # char is a word char, so there is no boundary there).
        re.compile(
            r"\b(how\s+to|step[\s-]?by[\s-]?step|instructions|method|guide|tutorial)"
            r".{0,40}\b(suicid|kill\s+(?:my|one)self|self[\s-]?harm)",
            re.I,
        ),
        re.compile(
            r"\b(lethal|fatal|effective|painless|quickest)\s+(dose|method|way|technique)\b"
            r".{0,40}\b(suicid|kill\s+(?:my|one)self|overdose|self[\s-]?harm)",
            re.I,
        ),
        re.compile(r"\b(suicide|self[\s-]?harm)\s+(method|technique|recipe|tutorial)\b", re.I),
    ],
}

# ---------------------------------------------------------------------------
# Category-level exclusions
# ---------------------------------------------------------------------------

# Keyed by (source, source_category_string). When a loader passes a labelled
# category that matches one of these keys, the case is dropped without even
# scanning the prompt text.
#
# These category strings are the EXACT labels used upstream — keep them in
# sync with the dataset README. When in doubt: defer to the regex layer.
_CATEGORY_EXCLUSIONS: dict[tuple[str, str], ExcludedTopic] = {
    # HarmBench SemanticCategory (https://github.com/centerforaisafety/HarmBench)
    ("harmbench", "chemical_biological"): "bio_chem_radiological_nuclear_weapons_synthesis",
    ("harmbench", "cbrn"): "bio_chem_radiological_nuclear_weapons_synthesis",
    # JailbreakBench Category (https://huggingface.co/datasets/JailbreakBench/JBB-Behaviors)
    # The category contains a small number of CSAM-adjacent edge cases; the
    # whole category is dropped per ETHICS.md.
    ("jailbreakbench", "Sexual/Adult content"): "csam",
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class FilterResult:
    """Outcome of running one prompt through the filter."""

    excluded: bool
    topics: tuple[ExcludedTopic, ...]


def _scan_text(text: str) -> tuple[ExcludedTopic, ...]:
    hits: list[ExcludedTopic] = []
    for topic, patterns in _PATTERNS.items():
        if any(p.search(text) for p in patterns):
            hits.append(topic)
    return tuple(hits)


def filter_prompt(
    prompt: str,
    *,
    source: str,
    source_category: str | None = None,
) -> FilterResult:
    """Run a single prompt through the two-layer exclusion filter.

    `source_category` is the upstream dataset's own label, if it has one
    (e.g. HarmBench's SemanticCategory). Pass None for unlabeled corpora.
    """
    if source_category is not None:
        key = (source, source_category)
        if key in _CATEGORY_EXCLUSIONS:
            return FilterResult(excluded=True, topics=(_CATEGORY_EXCLUSIONS[key],))
    keyword_hits = _scan_text(prompt)
    if keyword_hits:
        return FilterResult(excluded=True, topics=keyword_hits)
    return FilterResult(excluded=False, topics=())


def filter_cases(cases: Iterable[AttackCase]) -> tuple[list[AttackCase], list[AttackCase]]:
    """Split a stream of AttackCases into (kept, excluded).

    A case that arrives with non-empty `excluded_topics` was already
    flagged by the loader (typically via the source-category gate, which
    needs upstream metadata that does not survive into AttackCase). We
    trust those and drop them straight into `excluded`.

    For everything else we run the regex layer on the prompt text. Cases
    that survive are returned unchanged (excluded_topics empty).
    """
    kept: list[AttackCase] = []
    excluded: list[AttackCase] = []
    for case in cases:
        if case.excluded_topics:
            excluded.append(case)
            continue
        result = filter_prompt(case.prompt, source=case.source)
        if result.excluded:
            excluded.append(case.model_copy(update={"excluded_topics": list(result.topics)}))
        else:
            kept.append(case)
    return kept, excluded
