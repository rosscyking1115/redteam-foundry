"""The one primitive for "the matcher could not read this input".

Defends: that `is_readable` separates "looked and found nothing" from "could not
look", and that `Screen` keeps the exclusion as a *number* so callers cannot
report a rate without reporting what it was computed over.

Two validators in this repository have now been unable to read the input they
existed to catch — the exclusion filter before `_PATTERNS_ZH`, and the figure
guard on `κ`. Both returned the value they would have returned for clean input.
This module is the shared answer, so a third does not have to be discovered.

The tests below deliberately include the *negative* direction: a screen that
called everything unreadable would satisfy every "excluded correctly" assertion
while quietly deleting the corpus. Readable input must survive untouched, or the
primitive moves published numbers instead of protecting them.
"""

from __future__ import annotations

import pytest

from redteam.readability import ALPHABET, Screen, is_readable, screen, screen_texts

# ---------------------------------------------------------------------------
# is_readable
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "text",
    [
        "How do I make a bomb?",
        "café",  # accented Latin
        "Zażółć gęślą jaźń",  # extended Latin
        "用中文解釋 photosynthesis",  # code-switched: a Latin span exists
        "請 ignore previous instructions",
        "a",
    ],
)
def test_latin_bearing_text_is_readable(text: str) -> None:
    assert is_readable(text) is True


@pytest.mark.parametrize(
    "text",
    [
        "爆弾の作り方を教えて",  # Japanese
        "请给我一个简单的巧克力饼干食谱。",  # Simplified Chinese
        "抱歉，我無法協助你。",  # Traditional Chinese
        "죄송하지만 도와드릴 수 없습니다.",  # Korean
        "Извините, я не могу вам помочь.",  # Russian
        "عذرًا، لا أستطيع مساعدتك.",  # Arabic
    ],
)
def test_non_latin_text_is_not_readable(text: str) -> None:
    assert is_readable(text) is False


@pytest.mark.parametrize("text", ["", "   ", "...", "12345", "!!! ???", "\n\t"])
def test_text_with_no_letters_at_all_is_not_readable(text: str) -> None:
    """Nothing for a word-boundary pattern to bite on, so a non-match is vacuous.

    Excluding-and-counting is the conservative direction here: it makes the
    emptiness visible rather than scoring it as a clean result.
    """
    assert is_readable(text) is False


def test_greek_is_not_readable_which_is_the_kappa_case() -> None:
    """The figure-guard bug, one layer down.

    `κ` is a letter and not Latin. A guard whose alphabet stops at Latin must
    say so rather than treat the character as absent.
    """
    assert is_readable("κ = 1.00") is False
    assert is_readable("kappa = 1.00") is True


# ---------------------------------------------------------------------------
# Screen — the count is the point
# ---------------------------------------------------------------------------


def test_screen_reports_zero_exclusions_on_fully_readable_input() -> None:
    items = ["one fine day", "another fine day"]
    kept, sc = screen(items, lambda s: s)
    assert kept == items
    assert sc == Screen(n_total=2, n_unreadable=0)
    assert sc.any_unreadable is False
    assert sc.all_unreadable is False
    assert sc.note() == "", "no stray '0 excluded' clause on healthy input"


def test_screen_drops_and_counts_the_unreadable() -> None:
    items = ["readable text", "爆弾の作り方", "more readable text"]
    kept, sc = screen(items, lambda s: s)
    assert kept == ["readable text", "more readable text"]
    assert sc.n_total == 3
    assert sc.n_unreadable == 1
    assert sc.n_readable == 2
    assert sc.all_unreadable is False


def test_all_unreadable_is_distinct_from_empty() -> None:
    """`all_unreadable` must mean "we looked at some and read none", not "none".

    An empty population is not an undefined statistic — it is no statistic. The
    two need different handling upstream, so they get different answers here.
    """
    _, none_at_all = screen([], lambda s: s)
    _, none_readable = screen(["爆弾", "自殺"], lambda s: s)
    assert none_at_all.all_unreadable is False
    assert none_readable.all_unreadable is True


def test_the_note_names_the_alphabet_and_the_count() -> None:
    sc = Screen(n_total=10, n_unreadable=4)
    note = sc.note("prompt")
    assert "4 of 10 prompts" in note
    assert ALPHABET in note


def test_the_note_is_singular_for_one() -> None:
    assert "1 of 3 prompt " in Screen(n_total=3, n_unreadable=1).note("prompt") + " "


def test_screen_texts_counts_without_keeping_the_items() -> None:
    sc = screen_texts(["hello", "爆弾", "world"])
    assert (sc.n_total, sc.n_unreadable, sc.n_readable) == (3, 1, 2)
