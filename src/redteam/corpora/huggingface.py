"""Load an arbitrary Hugging Face dataset for a one-off corpus audit.

The four built-in corpora are commit-pinned loaders in the `LOADERS` registry.
This module is the escape hatch: point the audit at *any* adversarial dataset
on the Hub (or a local split) and get the same quality / duplication / language
/ staleness analysis. That is the reach-multiplier — people can audit their own
corpus, not just ours.

Loaded rows become `AttackCase`s with `source="external"` and
`category="unknown"`; the exclusion filter still runs before anything is
audited or previewed, so an ad-hoc dataset can't smuggle excluded content into
a report.

`rows_to_cases` is pure (takes an iterable of row mappings) so it is unit-tested
without any network; `load_hf_dataset` is the thin `datasets` wrapper around it.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from redteam.corpora._base import stable_id
from redteam.schemas import AttackCase


def rows_to_cases(
    rows: Iterable[Mapping[str, Any]],
    *,
    dataset: str,
    prompt_column: str,
    limit: int | None = None,
) -> list[AttackCase]:
    """Map dataset rows to AttackCases. Pure — no I/O.

    Rows with a missing/blank prompt are skipped. `dataset` seeds a stable id
    so re-auditing the same dataset yields the same ids.
    """
    cases: list[AttackCase] = []
    for row in rows:
        if limit is not None and len(cases) >= limit:
            break
        raw = row.get(prompt_column)
        if raw is None:
            continue
        prompt = str(raw).strip()
        if not prompt:
            continue
        cases.append(
            AttackCase(
                id=stable_id("external", dataset, prompt),
                source="external",
                category="unknown",
                severity="medium",
                prompt=prompt,
                expected_behaviour="refuse",
            )
        )
    return cases


def load_hf_dataset(
    dataset: str,
    *,
    prompt_column: str,
    split: str = "train",
    config: str | None = None,
    revision: str | None = None,
    limit: int | None = None,
) -> list[AttackCase]:
    """Load a Hugging Face dataset split into AttackCases for auditing.

    `revision` pins a dataset commit/tag — strongly recommended for a
    reproducible audit. Raises ValueError if `prompt_column` is not a field of
    the dataset.
    """
    from datasets import load_dataset

    # Security: `dataset` is an arbitrary, user-supplied repo id. We load it as
    # data only — never execute dataset code. `datasets` >= 3 no longer runs
    # loading scripts by default and >= 4 removed remote-code loading entirely
    # (there is no `trust_remote_code` to enable), so this stays data-only.
    ds = load_dataset(dataset, name=config, split=split, revision=revision)

    columns = list(getattr(ds, "column_names", []) or [])
    if columns and prompt_column not in columns:
        raise ValueError(
            f"prompt-column {prompt_column!r} not in dataset columns {columns}. "
            "Pass --prompt-column with one of those."
        )
    return rows_to_cases(ds, dataset=dataset, prompt_column=prompt_column, limit=limit)
