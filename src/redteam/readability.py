"""One convention for "the matcher could not read this input".

Several matchers in this repository are anchored on ``\\b`` word boundaries and
Latin letters. That is not a stylistic choice — it is an *alphabet*, and it is
narrower than the text those matchers are handed. Chinese and Japanese are
unspaced, so a ``\\b``-anchored pattern has nothing to anchor on and matches
nothing. The pattern does not fail; it returns a confident negative.

Twice that produced a validator which could not read the input it existed to
catch, and reported the same value it would have reported for clean input:

* the exclusion filter, before ``_PATTERNS_ZH``, returned ``excluded=False`` for
  every Chinese prompt;
* the figure guard read Latin-1 PNG chunks and could not read ``κ``.

The lesson from both is that widening an alphabet is endless and checking
whether the input was *inside* it is cheap. So this module does not translate,
transliterate or tokenise anything. It answers one question — could a
word-delimited Latin matcher have read this at all? — and gives callers a
counted way to exclude what it could not.

The convention is deliberately the one already in
``scripts/report_locale_provenance.py``: a cell the instrument could not read is
**excluded from the computation and counted**, and the count is **published
alongside the result**. An exclusion nobody counts is the same defect one level
up — it turns "we could not read 40 of these" into silence.

Relationship to `detect_language`
---------------------------------
:func:`redteam.corpora.taxonomy.detect_language` is this repository's script
*classifier*: it buckets text into ja/ko/zh/latin/other and detects
code-switching. :func:`is_readable` here is deliberately **not** a second
classifier — it is a one-bit precondition ("is there any Latin letter for a
``\\b`` pattern to anchor on?") that several modules need, including
`taxonomy` itself. It lives at the bottom of the dependency graph so
`taxonomy` can import it, rather than the other way round; making it call
`detect_language` would create an import cycle and buy nothing, since the
question it answers is a strict subset of what the classifier computes.
"""

from __future__ import annotations

import unicodedata
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from typing import TypeVar

__all__ = ["ALPHABET", "Screen", "is_readable", "screen", "screen_texts"]

T = TypeVar("T")

#: Human-readable name of the alphabet these matchers actually cover. Quoted in
#: report output so a reader sees what was excluded and why.
ALPHABET = "word-delimited Latin script"


def is_readable(text: str) -> bool:
    """Could a ``\\b``-anchored, Latin-letter matcher have read `text` at all?

    True when the text contains any Latin letters. That is the exact
    precondition for the matchers this guards: with no Latin letters present,
    an English word-boundary pattern *cannot* match, so a non-match carries no
    information about the content.

    Partially-Latin text counts as readable, and deliberately. A code-switched
    prompt such as ``用中文解釋 photosynthesis`` has a Latin span the matchers
    genuinely can read, and these matchers are precision-oriented: a hit on the
    readable span is a true hit. Only the total absence of Latin letters makes
    the verdict vacuous.

    Text with no letters at all — digits, punctuation, an empty string — is
    reported unreadable. Nothing is there for a word-boundary pattern to bite
    on, so the same reasoning applies, and excluding-and-counting is the
    conservative direction.

    `unicodedata.name` is used rather than a codepoint range so accented and
    extended Latin (``é``, ``ł``, ``ǎ``) count as Latin, matching how
    `taxonomy._char_script` buckets them.
    """
    for ch in text:
        if not unicodedata.category(ch).startswith("L"):
            continue
        try:
            if unicodedata.name(ch).startswith("LATIN"):
                return True
        except ValueError:  # unnamed character — cannot be Latin
            continue
    return False


@dataclass(frozen=True, slots=True)
class Screen:
    """How much of a population the matcher could read, kept as a number.

    The point of carrying this alongside a result is that ``0`` and "we could
    not look" stop being the same value. A caller that reports a rate without
    reporting its :attr:`n_unreadable` has re-introduced the defect.
    """

    n_total: int
    n_unreadable: int

    @property
    def n_readable(self) -> int:
        return self.n_total - self.n_unreadable

    @property
    def any_unreadable(self) -> bool:
        return self.n_unreadable > 0

    @property
    def all_unreadable(self) -> bool:
        """True when nothing could be read — the result is undefined, not zero."""
        return self.n_total > 0 and self.n_readable == 0

    def note(self, unit: str = "case") -> str:
        """One clause naming the exclusion, for a report line or a detail field.

        Returns an empty string when nothing was excluded, so callers can append
        it unconditionally without a stray "0 excluded" on healthy input.
        """
        if not self.any_unreadable:
            return ""
        plural = unit if self.n_unreadable == 1 else f"{unit}s"
        return (
            f"{self.n_unreadable} of {self.n_total} {plural} excluded as unreadable (no {ALPHABET})"
        )


def screen[T](items: Sequence[T], text_of: Callable[[T], str]) -> tuple[list[T], Screen]:
    """Split `items` into the readable ones and a count of what was dropped.

    The two are returned together on purpose: it is not possible to take the
    filtered list from this function without also being handed the number that
    has to be reported with it.
    """
    readable = [item for item in items if is_readable(text_of(item))]
    return readable, Screen(n_total=len(items), n_unreadable=len(items) - len(readable))


def screen_texts(texts: Iterable[str]) -> Screen:
    """`screen` for the case where only the count is wanted, not the items."""
    seq = list(texts)
    return Screen(n_total=len(seq), n_unreadable=sum(1 for t in seq if not is_readable(t)))
