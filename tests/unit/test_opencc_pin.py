"""Claims defended here.

The OpenCC treatment is defined by dictionary *content*, not by a package
name. These tests fail if an upgrade silently changes the conversion, and they
pin the three facts an earlier version of this project got wrong:

1. `s2tw` is not `s2t` — it runs a real Taiwan variant stage.
2. `s2twp` is a partial vocabulary mapping, not comprehensive localisation.
3. `s2hk` loads no HKPhrases, so it introduces no Cantonese morphology.

OpenCC is imported at module scope on purpose. If the `provenance` extra is
missing these tests must ERROR, not silently vanish from the count.
"""

from __future__ import annotations

import opencc  # noqa: F401  -- fail loudly if the extra is not installed

from redteam.opencc_pin import (
    CHAINS,
    DICTIONARIES,
    MULTI_TARGET_SOURCE_CHARS,
    installed_digests,
    pin_record,
    verify_pin,
)


def test_installed_dictionaries_match_the_pin() -> None:
    """The frozen treatment is actually what is installed.

    `verify_pin` returning an empty list is only evidence if there was
    something to check, so assert the dictionary set is non-empty first —
    otherwise a cleared DICTIONARIES dict would read as a passing check.
    """
    assert DICTIONARIES, "no dictionaries pinned — the check would be vacuous"
    assert len(installed_digests()) == len(DICTIONARIES)
    assert verify_pin() == [], "installed OpenCC dictionaries drifted from the pin"


def test_chains_are_read_from_the_configs_not_assumed() -> None:
    """s2tw carries a Taiwan variant stage; only s2twp carries TWPhrases."""
    assert CHAINS["s2t"] == ("STPhrases", "STCharacters")
    assert "TWVariants" in CHAINS["s2tw"]
    assert "TWPhrases" not in CHAINS["s2tw"], "s2tw has no vocabulary dictionary"
    assert "TWPhrases" in CHAINS["s2twp"]
    # The Hong Kong control must not acquire a phrase dictionary.
    assert "HKPhrases" not in CHAINS["s2hk"]
    assert "HKPhrases" in CHAINS["s2hkp"]


def test_twphrases_is_small_relative_to_the_official_difference_list() -> None:
    """775 entries against 4,800+ official groups.

    Pinned so 's2twp is comprehensive Taiwan localisation' cannot be written
    without this test going red.
    """
    assert DICTIONARIES["TWPhrases"].entries == 775
    assert DICTIONARIES["TWPhrases"].entries < 1000


def test_dictionary_entry_counts_exclude_comment_headers() -> None:
    """Each upstream .txt carries a licence/provenance header.

    Counting raw lines inflates every figure by 6 to 16 and silently
    disagrees with the published counts.
    """
    assert DICTIONARIES["TWVariants"].entries == 38
    assert DICTIONARIES["TWVariantsPhrases"].entries == 4
    assert DICTIONARIES["HKVariants"].entries == 66
    assert DICTIONARIES["HKVariantsPhrases"].entries == 272
    assert DICTIONARIES["HKPhrases"].entries == 39


def test_multi_target_inventory_is_the_reproducible_denominator() -> None:
    assert len(MULTI_TARGET_SOURCE_CHARS) == 275
    # The characters this study's headline turns on.
    for ch in "台里面发后干":
        assert ch in MULTI_TARGET_SOURCE_CHARS


def test_pin_record_is_serialisable_and_self_describing() -> None:
    record = pin_record()
    assert record["package_version"] == "1.4.1"
    assert record["upstream_commit"] == "81223ed87ae53283ef518e2deac34b7971f8a39e"
    assert record["pin_verified"] is True
    assert isinstance(record["dictionaries"], dict)
