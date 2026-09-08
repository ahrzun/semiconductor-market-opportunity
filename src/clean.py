"""Reshape the raw CSVs into the processed star schema and validate them.

clean.py owns the descriptive layer: one dimension table and one fact table at segment-year
grain. It computes serviceable market size, which is the quantity the rest of the project scores
on. It does not score anything and it does not read config/weights.yaml.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"

QUALITATIVE_FACTORS = [
    "competitive_intensity",
    "customer_demand",
    "entry_feasibility",
    "strategic_fit",
    "talent_availability",
]

FACT_COLUMNS = [
    "segment_id",
    "year",
    "market_size_usd_bn",
    "cagr_pct",
    "design_services_addressable_pct",
    "serviceable_market_usd_bn",
    "competitive_intensity",
    "customer_demand",
    "entry_feasibility",
    "strategic_fit",
    "talent_availability",
    "design_cycle_months",
]


def load_raw() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    segments = pd.read_csv(RAW_DIR / "segments.csv")
    metrics = pd.read_csv(RAW_DIR / "segment_year_metrics.csv")
    quality = pd.read_csv(RAW_DIR / "qualitative_scores.csv")
    return segments, metrics, quality


def build_fact(metrics: pd.DataFrame, quality: pd.DataFrame) -> pd.DataFrame:
    wide = quality.pivot(index=["segment_id", "year"], columns="factor", values="score")
    wide = wide.reset_index().rename_axis(None, axis=1)

    fact = metrics.merge(wide, on=["segment_id", "year"], how="inner", validate="one_to_one")

    # The whole argument of the project sits on this line. A design-services firm cannot sell
    # into TAM; it sells into the slice of TAM that is actually outsourced.
    fact["serviceable_market_usd_bn"] = (
        fact["market_size_usd_bn"] * fact["design_services_addressable_pct"]
    ).round(4)

    return fact[FACT_COLUMNS].sort_values(["segment_id", "year"], ignore_index=True)


def build_dim(segments: pd.DataFrame, fact: pd.DataFrame) -> pd.DataFrame:
    dim = segments.copy()

    # A plain-language addressability tier, so the dashboard can group without re-deriving it.
    latest = fact.sort_values("year").groupby("segment_id").tail(1).set_index("segment_id")
    pct = dim["segment_id"].map(latest["design_services_addressable_pct"])
    dim["addressability_tier"] = pd.cut(
        pct,
        bins=[-0.01, 0.08, 0.18, 1.0],
        labels=["Low", "Moderate", "High"],
    ).astype(str)

    return dim.sort_values("segment_id", ignore_index=True)


def validate(dim: pd.DataFrame, fact: pd.DataFrame) -> None:
    assert len(dim) == 8, f"expected 8 segments, got {len(dim)}"
    assert not fact.isna().any().any(), "processed fact table contains nulls"
    assert fact.duplicated(["segment_id", "year"]).sum() == 0, "duplicate segment-year rows"

    years_per_segment = fact.groupby("segment_id")["year"].nunique().unique()
    assert list(years_per_segment) == [10], "every segment needs a complete 2021-2030 panel"

    assert set(fact["segment_id"]) == set(dim["segment_id"]), "fact/dim key mismatch"

    for factor in QUALITATIVE_FACTORS:
        assert fact[factor].between(0, 100).all(), f"{factor} outside 0-100"
    assert fact["design_services_addressable_pct"].between(0, 1).all(), "addressability outside 0-1"
    assert (fact["market_size_usd_bn"] > 0).all(), "non-positive market size"
    assert (fact["serviceable_market_usd_bn"] <= fact["market_size_usd_bn"]).all(), (
        "serviceable market cannot exceed TAM"
    )


def main() -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    segments, metrics, quality = load_raw()
    fact = build_fact(metrics, quality)
    dim = build_dim(segments, fact)
    validate(dim, fact)

    dim.to_csv(PROCESSED_DIR / "dim_segment.csv", index=False, lineterminator="\n")
    fact.to_csv(PROCESSED_DIR / "fact_segment_year.csv", index=False, lineterminator="\n")
    print(f"processed: dim_segment {dim.shape}, fact_segment_year {fact.shape} -> {PROCESSED_DIR}")


if __name__ == "__main__":
    main()
