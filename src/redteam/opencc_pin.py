"""Frozen definition of the OpenCC treatment.

"OpenCC" alone is not a treatment definition. The conversion an experiment
applies is determined by specific dictionary files, and those files change
between releases — OpenCC master carries an August 2026 fix to greedy
``s2twp`` matching that is not in the 1.4.1 release pinned here, and several
dictionaries gained entries after 1.4.1 (``TWPhrases`` 775 → 817,
``TWVariantsPhrases`` 4 → 12). A run reporting only "converted with OpenCC"
cannot be reproduced.

This module records the package version, the upstream commit, and both the
source and compiled SHA-256 of every dictionary in the conversion chains this
project uses. `verify_pin()` checks the installed files against it, so a
silent dependency upgrade fails loudly instead of quietly changing the
treatment mid-study.

Scope of s2twp
--------------
``TWPhrases`` carries **775** entries. Taiwan's official cross-strait
difference list (中華語文知識庫 / 中華語文大辭典) contains more than 4,800
groups. ``s2twp`` is therefore a *partial* vocabulary mapping and must never
be described as comprehensive Taiwan localisation. Its proper-name coverage is
sparse and uneven rather than absent: 奧巴馬→歐巴馬, 新西蘭→紐西蘭 and
老撾→寮國 are present; 布什→布希, 悉尼→雪梨 and 里根→雷根 are not.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

PACKAGE = "OpenCC"
PACKAGE_VERSION = "1.4.1"
UPSTREAM_REPO = "https://github.com/BYVoid/OpenCC"
UPSTREAM_TAG = "ver.1.4.1"
UPSTREAM_COMMIT = "81223ed87ae53283ef518e2deac34b7971f8a39e"

#: Simplified source characters in STCharacters that map to more than one
#: traditional target. Each occurrence in a source text is an *opportunity*
#: for the character-restoration stage to pick the wrong member of the set —
#: not a failure, since the phrase dictionaries resolve most of them in
#: context. Extracted from the pinned STCharacters.txt; the count is the
#: audit's independently reported 275.
#:
#: This is a superset of the contemporary semantic collapses: it also contains
#: archaic distinctions, surnames, place names and pure variant preferences.
#: Treat it as the reproducible denominator, not as a list of 275 live
#: ambiguities.
MULTI_TARGET_SOURCE_CHARS: frozenset[str] = frozenset(
    "㐹万丑个丰了于云亘仆仇仑价仿伙余佛佣俊修借僵克党具冢冬冲凄准凌几凶出划别刮制勋千升卜占卤卷厂历厘"
    "参发只台叶叹吁吃合吊同后向吣呆周咨咸咽哄哗唇啮喂噪回团困坐坛坝坯埙堤复夫夸夹奸姜娘娴宁它家尝尸尽"
    "局岩岳巨布帘席干并幸广庵弥弦当录彩征径御志念恤恶愈愿戚扇才扎托扣折抵拐拿挂挨挽捆捍据搜摆斗斤斫旋"
    "昆暗曲札术朱朴杆杠杯杰松板极果枪柜栗核梁棱檗欲毁汇沈沾泛注浚涂涌淀游溪滟漓澄炼烟焰熏狸玩琅璇症皂"
    "矩确硷私秋种穗筑筱签糊系累纤绱绷耇胄背胜胡脏腊腌膻致舍艳芸苏苔苹范荐荡荫药获蒙蔑藤虫蚝蜡蝎表袅裥"
    "证谥谷豆象赝赞跖辟迹适郁酸采里鉴针钟钥钫钻铲链锄锫镋镎镢镰闲雕面须饥鹇"
)


@dataclass(frozen=True, slots=True)
class DictPin:
    """One dictionary, pinned by content rather than by name."""

    entries: int  # non-comment, non-blank lines in the upstream .txt
    source_sha256: str  # upstream data/dictionary/<name>.txt at UPSTREAM_COMMIT
    compiled_sha256: str  # the installed <name>.ocd2 actually used at runtime


#: Every dictionary loaded by s2t / s2tw / s2twp / s2hk / s2hkp.
#: Entry counts exclude the licence/provenance comment header each file
#: carries — counting raw lines inflates every figure by 6 to 16.
DICTIONARIES: dict[str, DictPin] = {
    "STCharacters": DictPin(
        entries=4012,
        source_sha256="81c27e6364fd164181276197b9215cf95f7f12a050aa207375248a5badf8d6fc",
        compiled_sha256="49b4f15e9b161eb66b961a17a2105c7c57da12d85dd872037b827e09aa5ee4c3",
    ),
    "STPhrases": DictPin(
        entries=49139,
        source_sha256="7f121e46abc71c1055ebee0445be4a98290023124657b24557f1a36bd2dc144d",
        compiled_sha256="f28fca11a3813071a628e2c897e4462908c3e890d335ea247da1f1be8953fec8",
    ),
    "TWPhrases": DictPin(
        entries=775,
        source_sha256="8d6442e0cf60b0401ccd97d9c48e9fab08d13cbd63ff2ec57e26d1a880c1bbc7",
        compiled_sha256="109bb27fc318f48d9c5001b74dea12fe2b3c54250efbdb52c919f518e1591de6",
    ),
    "TWVariants": DictPin(
        entries=38,
        source_sha256="48e694ad1ac43fd5927285e4fb3aa8a8dc9d9c065d6d3d314527c021a12839e2",
        compiled_sha256="f8a6e00b7b03b406a74fed43a7293aa12c4646cc7fd38a8d2ecf8da88267bef6",
    ),
    "TWVariantsPhrases": DictPin(
        entries=4,
        source_sha256="7bb61076ab1cca0783fdc823225cd816977d170df74140d143b0dc932085d142",
        compiled_sha256="549d7025f70caf89381d396f5d9555b57c17cee8e604915dd6a7315cc7cc6a68",
    ),
    "HKVariants": DictPin(
        entries=66,
        source_sha256="e5cd4345303224587102f2c9e4d2b67d2b7e349c6ce9152e4a118f4656cf7302",
        compiled_sha256="b4be56685bddda964977bbd271f976df939d1f46a75332b8f9e793d0f06e6c7c",
    ),
    "HKVariantsPhrases": DictPin(
        entries=272,
        source_sha256="e23019c35405065d7ea174fe7487e0bde064b1af56532b3986033c9bb98e555c",
        compiled_sha256="80c215b6bef0f324a71340bc21164d063c5540af6f50c07fd1c703af9c1207da",
    ),
    "HKPhrases": DictPin(
        entries=39,
        source_sha256="ff4f4ee5a586fa4d322dc10d52251166e1429c269f124e7e087b117022fc82bf",
        compiled_sha256="adc4b4514975b1199479765e6c385ac34598a4f9f013fed71f6187d36307d4dc",
    ),
}

#: The conversion chains, read from the installed config JSONs rather than
#: recalled. `s2tw` is NOT `s2t` — it runs a real Taiwan variant stage. What
#: it lacks is TWPhrases.
CHAINS: dict[str, tuple[str, ...]] = {
    "s2t": ("STPhrases", "STCharacters"),
    "s2tw": ("STPhrases", "STCharacters", "TWVariantsPhrases", "TWVariants"),
    "s2twp": (
        "STPhrases",
        "STCharacters",
        "TWPhrases",
        "TWVariantsPhrases",
        "TWVariants",
    ),
    "s2hk": ("STPhrases", "STCharacters", "HKVariantsPhrases", "HKVariants"),
    "s2hkp": (
        "STPhrases",
        "STCharacters",
        "HKPhrases",
        "HKVariantsPhrases",
        "HKVariants",
    ),
}


def _dictionary_dir() -> Path:
    import opencc

    return Path(opencc.__file__).parent / "clib" / "share" / "opencc"


def installed_digests() -> dict[str, str]:
    """SHA-256 of each compiled dictionary as actually installed."""
    root = _dictionary_dir()
    out: dict[str, str] = {}
    for name in DICTIONARIES:
        path = root / f"{name}.ocd2"
        out[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    return out


def verify_pin() -> list[str]:
    """Return a list of mismatches; empty means the treatment is unchanged.

    Returning a list rather than raising lets a caller record the drift in a
    run header. An empty list is a real check, not an absent one — the
    accompanying test asserts the dictionary set is non-empty first.
    """
    problems: list[str] = []
    actual = installed_digests()
    for name, pin in DICTIONARIES.items():
        got = actual.get(name)
        if got != pin.compiled_sha256:
            problems.append(f"{name}.ocd2 sha256 {got} != pinned {pin.compiled_sha256}")
    return problems


def pin_record() -> dict[str, object]:
    """Serialisable treatment definition, for embedding in a run header."""
    return {
        "package": PACKAGE,
        "package_version": PACKAGE_VERSION,
        "upstream_repo": UPSTREAM_REPO,
        "upstream_tag": UPSTREAM_TAG,
        "upstream_commit": UPSTREAM_COMMIT,
        "multi_target_source_chars": len(MULTI_TARGET_SOURCE_CHARS),
        "dictionaries": {
            name: {
                "entries": pin.entries,
                "source_sha256": pin.source_sha256,
                "compiled_sha256": pin.compiled_sha256,
            }
            for name, pin in DICTIONARIES.items()
        },
        "chains": {name: list(chain) for name, chain in CHAINS.items()},
        "pin_verified": not verify_pin(),
    }
