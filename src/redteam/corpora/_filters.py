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

Scripts
-------
The blocklist is script-specific. Every English pattern is anchored on ``\\b``
word boundaries and ASCII letters, which **cannot match Chinese text at all** —
Chinese is unspaced, so there are no word boundaries to anchor on. Before the
`_PATTERNS_ZH` set existed this filter returned "clean" for every Chinese
prompt, and it did so because it could not read them, not because they were
clean. A gate that passes everything it cannot parse reports the same value as
a gate with nothing to catch.

Chinese patterns are written to match Simplified and Traditional forms in the
same expression (character classes such as ``[兒儿]``) rather than normalising
with OpenCC first. This filter is a CI-enforced safety gate and must not
acquire an optional dependency: if the ``provenance`` extra were absent, an
OpenCC-based filter would silently degrade to the blindness described above.

The unit test `tests/unit/test_exclusion_filter.py` feeds a curated set of
positive (must-be-flagged) and negative (must-pass) examples through this
module and asserts zero leakage, in both scripts.
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
            r"\b(synthesi[sz]e?|manufactur|produc|mak|creat|build|cook|brew|prepare)"
            r".{0,60}\b(sarin|tabun|vx\b|novichok|mustard\s*gas|chlorine\s*gas|"
            r"phosgene|ricin|botulinum|anthrax|smallpox|ebola|marburg|"
            r"nerve\s*agent|chemical\s*weapon|biological\s*weapon|bio[\s-]?weapon|"
            r"chem[\s-]?weapon|toxin)\b",
            re.I,
        ),
        re.compile(
            r"\b(synthesi[sz]e?|manufactur|produc|mak|creat|build|construct|design)"
            r".{0,60}\b(nuclear\s*(?:weapon|bomb|device)|"
            r"fission\s*(?:weapon|bomb|device)|"
            r"dirty\s*bomb|radiological\s*(?:weapon|bomb|device|dispersal))\b",
            re.I,
        ),
        re.compile(r"\b(enrich|weapons[\s-]?grade)\s+(uranium|plutonium)\b", re.I),
        re.compile(
            r"\b(nerve\s*agent|toxin)\b.*\b(synthesi[sz]e?|recipe|instructions|how[\s-]?to)\b",
            re.I,
        ),
    ],
    "detailed_self_harm_methods": [
        # Trailing word boundary intentionally omitted on `suicid` / `overdose`
        # — \b would never match inside "suicide" or "overdosed" (the next
        # char is a word char, so there is no boundary there).
        # How-to / method framing (group 1) followed by a self-harm act
        # (group 2). Group 1 MUST precede group 2, which is what keeps
        # "suicide prevention" and "warning signs ... suicidal" benign —
        # they have no how-to framing before the term.
        re.compile(
            r"\b(how\s+(?:to|can|do|could|would)|step[\s-]?by[\s-]?step|instructions?|"
            r"methods?|ways?|guide|tutorial|easiest|best|quickest|fastest|painless(?:ly)?)"
            r".{0,40}\b(suicid|kill(?:ing)?\s+(?:my|one|your)self|self[\s-]?harm|overdos|"
            r"end(?:ing)?\s+(?:my|your|their|one's)\s+life|"
            r"take\s+(?:my|your|their|one's)\s+(?:own\s+)?life)",
            re.I,
        ),
        re.compile(
            r"\b(lethal|fatal|effective|painless|quickest|easiest)\s+(dose|method|way|technique)\b"
            r".{0,40}\b(suicid|kill\s+(?:my|one)self|overdose|self[\s-]?harm)",
            re.I,
        ),
        re.compile(
            r"\b(suicide|self[\s-]?harm)\s+(methods?|techniques?|recipe|tutorial|ways?)\b", re.I
        ),
    ],
}

# ---------------------------------------------------------------------------
# Chinese blocklist (Simplified + Traditional in one expression)
# ---------------------------------------------------------------------------

# Chinese has no word boundaries, so these patterns rely on adjacency instead
# of `\b`. Character classes carry both scripts: `[兒儿]` matches Traditional
# 兒 and Simplified 儿. Same precision-over-recall posture as the English set.
#
# Locale note: the Taiwan and PRC terms for the same concept can differ as
# whole words, not only as glyphs (e.g. 核子 / 核 usage, 資訊 / 信息). Where a
# term differs lexically rather than by character, both forms are listed.
_PATTERNS_ZH: dict[ExcludedTopic, list[re.Pattern[str]]] = {
    "csam": [
        # child + sexual/nude/abuse terms, in either order, within a short span
        re.compile(
            r"(?:[兒儿]童|幼[女童]|未成年|[蘿萝][莉丽]|童妓)[^。！？!?]{0,20}"
            r"(?:色情|性[交侵愛爱行]|裸|猥[褻亵]|[性淫][虐侵]|[賣卖]淫)"
        ),
        re.compile(
            r"(?:色情|裸[照體体]|猥[褻亵]|性[交侵])[^。！？!?]{0,20}"
            r"(?:[兒儿]童|幼[女童]|未成年)"
        ),
    ],
    "bio_chem_radiological_nuclear_weapons_synthesis": [
        # synthesis/manufacture verbs near a WMD agent
        re.compile(
            r"(?:合成|制[造備备]|製[造備备]|[制製]作|生[产產]|提[煉炼]|培養|培养)"
            r"[^。！？!?]{0,30}"
            r"(?:沙林|[塔苏]曼|芥子[氣气]|神[經经]毒[劑剂气氣]|光[氣气]|"
            r"蓖麻毒素|肉毒|炭疽|天花病毒|埃博拉|伊波拉|"
            r"生[化物][武菌]器|化学武器|化學武器|生物武器|毒[劑剂])"
        ),
        re.compile(
            r"(?:核武器|核[彈弹]|[髒脏][彈弹]|放射性武器|原子[彈弹])"
            r"[^。！？!?]{0,30}(?:[制製]造|制作|製作|如何|怎[麼么樣样])"
        ),
        re.compile(
            r"(?:如何|怎[麼么樣样]|教程|步[驟骤]|方法)[^。！？!?]{0,30}"
            r"(?:[制製]造|合成)[^。！？!?]{0,15}"
            r"(?:核[彈弹武]|生化武器|化學武器|化学武器|神[經经]毒)"
        ),
        re.compile(r"(?:[濃浓]縮[鈾铀]|浓缩铀|[武菌]器[級级][鈾铀][钚鈈])"),
    ],
    "detailed_self_harm_methods": [
        # how-to framing BEFORE the act, mirroring the English ordering rule so
        # that 自殺防治 ("suicide prevention") and 自殺警訊 stay benign.
        re.compile(
            r"(?:如何|怎[麼么樣样]|怎[樣样]|方法|步[驟骤]|教程|指南|"
            r"最[快好有]效|無痛|无痛|最不痛苦)[^。！？!?]{0,20}"
            r"(?:自[殺杀]|自[殘残]|[結结]束生命|了[結结]生命|"
            r"[過过]量服[藥药]|服毒)"
        ),
        re.compile(
            r"(?:自[殺杀]|自[殘残])[^。！？!?]{0,10}"
            r"(?:方法|方式|教程|指南|步[驟骤]|技巧)"
        ),
        re.compile(
            r"(?:致死|[緻致]命)[^。！？!?]{0,10}(?:[劑剂]量|[藥药]量)"
            r"[^。！？!?]{0,20}(?:自[殺杀]|[過过]量)"
        ),
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

# Normalised lookup so the gate survives upstream relabels that only differ
# in case or surrounding whitespace (e.g. "Sexual/Adult Content" vs
# "Sexual/Adult content"). Without this the exact-match gate silently
# re-admits an excluded category when a dataset revision tweaks a label.
_CATEGORY_EXCLUSIONS_NORM: dict[tuple[str, str], ExcludedTopic] = {
    (src.strip().casefold(), cat.strip().casefold()): topic
    for (src, cat), topic in _CATEGORY_EXCLUSIONS.items()
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
    """Scan against every script's blocklist.

    Both sets run on every prompt regardless of detected script: a
    code-switched prompt carries Latin and CJK in one string, and running only
    the "matching" set would let the other half through.
    """
    hits: list[ExcludedTopic] = []
    for topic in _PATTERNS:
        patterns = _PATTERNS[topic] + _PATTERNS_ZH.get(topic, [])
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
        key = (source.strip().casefold(), source_category.strip().casefold())
        topic = _CATEGORY_EXCLUSIONS_NORM.get(key)
        if topic is not None:
            return FilterResult(excluded=True, topics=(topic,))
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
