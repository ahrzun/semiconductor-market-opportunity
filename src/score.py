"""Compute the weighted opportunity score.

Method, in one paragraph: for each year independently, every factor is min-max normalized to
0-100 across the eight segments, competitive intensity is inverted so that crowded is bad, and
the normalized values are combined with the weights in config/weights.yaml. Because
normalization happens inside a year, a score is a statement about a segment's standing relative
to its peers in that year - not about an absolute quantity, and not comparable across years in
level terms. Rank movement across years is the meaningful signal.

Per-factor contributions are written out as separate columns so a dashboard can decompose any
score back into the drivers that produced it.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = ROOT / "data" / "processed"
WEIGHTS_PATH = ROOT / "config" / "weights.yaml"

# Scoring factor -> the column in fact_segment_year it is computed from. The keys must match
# the factor names in config/weights.yaml exactly; a mismatch raises rather than silently
# dropping a factor from the score.
FACTOR_SOURCES = {
    "serviceable_market_size": "serviceable_market_usd_bn",
    "cagr": "cagr_pct",
    "design_services_addressability": "design_services_addressable_pct",
    "strategic_fit": "strategic_fit",
    "customer_demand": "customer_demand",
    "competitive_intensity": "competitive_intensity",
    "entry_feasibility": "entry_feasibility",
}


def load_config(path: Path = WEIGHTS_PATH) -> dict:
    with path.open() as handle:
        config = yaml.safe_load(handle)

    for name, profile in config["profiles"].items():
        total = sum(profile["weights"].values())
        if abs(total - 1.0) > 1e-9:
            raise ValueError(f"weight profile '{name}' sums to {total}, expected 1.0")
        if set(profile["weights"]) != set(FACTOR_SOURCES):
            raise ValueError(f"weight profile '{name}' does not cover exactly the known factors")

    unknown = set(config["inverted_factors"]) - set(FACTOR_SOURCES)
    if unknown:
        raise ValueError(f"inverted_factors names unknown factors: {sorted(unknown)}")

    return config


def normalize_within_year(fact: pd.DataFrame, inverted: list[str]) -> pd.DataFrame:
    """Min-max each factor to 0-100 across segments, one year at a time."""
    out = fact[["segment_id", "year"]].copy()

    for factor, source in FACTOR_SOURCES.items():
        grouped = fact.groupby("year")[source]
        low, high = grouped.transform("min"), grouped.transform("max")
        spread = (high - low).replace(0.0, pd.NA)

        # A zero spread means the segments are indistinguishable on this factor this year; the
        # factor then carries no discriminating information and every segment sits mid-scale.
        normalized = ((fact[source] - low) / spread * 100.0).fillna(50.0)

        if factor in inverted:
            normalized = 100.0 - normalized

        out[f"norm_{factor}"] = normalized.round(4)

    return out


def apply_weights(normalized: pd.DataFrame, weights: dict[str, float]) -> pd.DataFrame:
    scored = normalized.copy()
    contribution_columns = []

    for factor, weight in weights.items():
        column = f"contrib_{factor}"
        scored[column] = (scored[f"norm_{factor}"] * weight).round(4)
        contribution_columns.append(column)

    scored["opportunity_score"] = scored[contribution_columns].sum(axis=1).round(4)
    scored["rank_in_year"] = (
        scored.groupby("year")["opportunity_score"]
        .rank(ascending=False, method="min")
        .astype(int)
    )
    return scored


def band_segments(scored: pd.DataFrame, config: dict) -> pd.DataFrame:
    """Recommendation bands from the mean score over the forward window.

    A single year is too thin a basis for a multi-year capacity commitment, and the last year of
    a projection is the least reliable one. The window average is the defensible cut.
    """
    window = config["forward_window"]
    bands = config["bands"]

    forward = scored[scored["year"].between(window["start_year"], window["end_year"])]
    mean_score = forward.groupby("segment_id")["opportunity_score"].mean().round(2)

    def label(score: float) -> str:
        if score >= bands["prioritize_min"]:
            return "Prioritize"
        if score >= bands["selective_min"]:
            return "Selective"
        return "Deprioritize"

    return pd.DataFrame(
        {
            "segment_id": mean_score.index,
            "forward_mean_score": mean_score.values,
            "recommendation": [label(s) for s in mean_score.values],
        }
    ).sort_values("segment_id", ignore_index=True)


def enrich_dim(bands: pd.DataFrame) -> None:
    """Attach the band to dim_segment so the dashboard can slice on it.

    clean.py owns the descriptive columns; this step owns only the two scored columns and
    rebuilds them from scratch every run, so repeated runs cannot accumulate state.
    """
    path = PROCESSED_DIR / "dim_segment.csv"
    dim = pd.read_csv(path).drop(columns=["forward_mean_score", "recommendation"], errors="ignore")
    dim = dim.merge(bands, on="segment_id", how="left", validate="one_to_one")
    dim.to_csv(path, index=False, lineterminator="\n")


def main() -> None:
    config = load_config()
    fact = pd.read_csv(PROCESSED_DIR / "fact_segment_year.csv")

    normalized = normalize_within_year(fact, config["inverted_factors"])
    base_weights = config["profiles"][config["base_profile"]]["weights"]
    scored = apply_weights(normalized, base_weights)

    scored = scored.sort_values(["segment_id", "year"], ignore_index=True)
    scored.to_csv(PROCESSED_DIR / "fact_opportunity_score.csv", index=False, lineterminator="\n")

    enrich_dim(band_segments(scored, config))

    latest = scored[scored["year"] == scored["year"].max()].sort_values("rank_in_year")
    print(f"scored: {scored.shape} -> {PROCESSED_DIR / 'fact_opportunity_score.csv'}")
    print("rank in final year: " + ", ".join(
        f"{row.rank_in_year}. {row.segment_id} ({row.opportunity_score:.1f})"
        for row in latest.itertuples()
    ))


if __name__ == "__main__":
    main()
