"""Human spot-check + Cohen's kappa.

Workflow:

  1. After a run is judged, call `export_for_human_review(run_path)` to
     write a CSV with ~5% of cases sampled deterministically by case_id.
     Each row carries the prompt, the response, and the judge's verdict;
     the human columns (`human_asr`, `human_refusal`, `notes`) are blank.

  2. Open the CSV in a spreadsheet, label the rows by hand, save.

  3. Call `compute_kappa(csv_path)` to get a `KappaScore` for both ASR
     and refusal. Kit acceptance: kappa > 0.6 (substantial agreement).

Sampling is deterministic — a SHA1 hash of `case_id` decides whether a
case is in the sample. Same run → same sample, every time. No `random`
seed dependence, so re-running the export against the same run JSON
won't shuffle which cases the human is asked about.

Cohen's kappa is implemented inline (~10 lines of arithmetic) so we
don't pull scipy in just for this.
"""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

CSV_FIELDS = [
    "case_id",
    "case_source",
    "case_category",
    "prompt",
    "response_text",
    "judge_asr",
    "judge_refusal",
    "judge_confidence",
    "judge_reasoning",
    "human_asr",
    "human_refusal",
    "notes",
]

# Truncate the response field in the CSV so the spreadsheet stays usable.
# The full response is always available in the run JSON.
_MAX_RESPONSE_PREVIEW = 800


def _is_sampled(case_id: str, sample_pct: float) -> bool:
    """Deterministic sampler keyed by case_id. Same case_id -> same verdict."""
    h = int(hashlib.sha1(case_id.encode("utf-8")).hexdigest()[:8], 16)
    return (h / 0xFFFF_FFFF) < sample_pct


def export_for_human_review(
    run_path: Path,
    *,
    sample_pct: float = 0.05,
    output_csv: Path | None = None,
) -> Path:
    """Read a scored RunResult JSON, write the human-review CSV.

    Returns the path of the written CSV.
    """
    if not (0.0 < sample_pct <= 1.0):
        raise ValueError(f"sample_pct must be in (0,1]; got {sample_pct}")

    data = json.loads(run_path.read_text(encoding="utf-8"))
    outcomes = data.get("outcomes", [])

    out = output_csv or run_path.with_suffix(".human-review.csv")
    with out.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for o in outcomes:
            if not _is_sampled(o["case_id"], sample_pct):
                continue
            response = (o.get("response_text") or "")[:_MAX_RESPONSE_PREVIEW]
            writer.writerow(
                {
                    "case_id": o["case_id"],
                    "case_source": o.get("case_source", ""),
                    "case_category": o.get("case_category", ""),
                    "prompt": o.get("prompt", ""),
                    "response_text": response,
                    "judge_asr": o.get("judge_asr", ""),
                    "judge_refusal": o.get("judge_refusal", ""),
                    "judge_confidence": o.get("judge_confidence", ""),
                    "judge_reasoning": o.get("judge_reasoning", ""),
                    "human_asr": "",
                    "human_refusal": "",
                    "notes": "",
                }
            )
    return out


# ---------------------------------------------------------------------------
# Cohen's kappa
# ---------------------------------------------------------------------------


class KappaScore(BaseModel):
    """Inter-rater agreement on a single binary dimension.

    Reports both Cohen's kappa and Krippendorff's alpha. They are usually
    close on binary 2-rater data; alpha is more robust to skewed marginals
    (the "kappa paradox") and generalises to multi-rater / ordinal cases.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    n: int = Field(ge=0, description="Rows where both judge and human gave a verdict.")
    agreement: float = Field(ge=0.0, le=1.0, description="Raw observed agreement (po).")
    kappa: float = Field(description="Cohen's kappa: (po - pe) / (1 - pe). NaN-safe.")
    alpha: float = Field(description="Krippendorff's alpha (binary nominal). NaN-safe.")


class KappaReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    csv_path: str
    n_rows: int
    n_human_filled: int
    asr: KappaScore
    refusal: KappaScore


def _binary_kappa(judge: list[int], human: list[int]) -> KappaScore:
    """Compute Cohen's kappa AND Krippendorff's alpha for two 0/1 vectors."""
    from redteam.stats import krippendorff_alpha_binary

    n = len(judge)
    if n == 0:
        return KappaScore(n=0, agreement=0.0, kappa=0.0, alpha=0.0)

    agree = sum(1 for j, h in zip(judge, human, strict=True) if j == h)
    po = agree / n

    p_j_pos = sum(judge) / n
    p_h_pos = sum(human) / n
    p_j_neg = 1 - p_j_pos
    p_h_neg = 1 - p_h_pos
    pe = p_j_pos * p_h_pos + p_j_neg * p_h_neg

    # If pe == 1, both raters are constant in the same direction; kappa is
    # undefined and we report 1.0 (perfect agreement) or 0.0 (perfect
    # disagreement) by convention. Otherwise the standard formula.
    kappa = (1.0 if po == 1.0 else 0.0) if pe >= 1.0 else (po - pe) / (1 - pe)
    alpha = krippendorff_alpha_binary(judge, human)

    return KappaScore(n=n, agreement=po, kappa=kappa, alpha=alpha)


def compute_kappa(csv_path: Path) -> KappaReport:
    """Read a human-filled CSV, compute kappa for asr and refusal columns."""
    with csv_path.open(encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))

    n_rows = len(rows)

    # Only count rows where the human filled BOTH asr and refusal columns.
    asr_judge: list[int] = []
    asr_human: list[int] = []
    refusal_judge: list[int] = []
    refusal_human: list[int] = []
    for r in rows:
        h_asr = (r.get("human_asr") or "").strip()
        h_ref = (r.get("human_refusal") or "").strip()
        if h_asr in {"0", "1"} and h_ref in {"0", "1"}:
            asr_judge.append(int(r["judge_asr"]))
            asr_human.append(int(h_asr))
            refusal_judge.append(int(r["judge_refusal"]))
            refusal_human.append(int(h_ref))

    return KappaReport(
        csv_path=str(csv_path),
        n_rows=n_rows,
        n_human_filled=len(asr_judge),
        asr=_binary_kappa(asr_judge, asr_human),
        refusal=_binary_kappa(refusal_judge, refusal_human),
    )
