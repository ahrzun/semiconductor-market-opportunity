"""Re-rank the segments under alternative weight profiles.

Normalization does not depend on the weights, so this reuses the norm_* columns already written
by score.py rather than recomputing them - the alternative profiles are guaranteed to be scored
off exactly the same normalized inputs as the house view.

The output answers one question: which parts of the ranking are a property of the data, and
which are a property of the weights we chose.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from score import apply_weights, load_config

ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = ROOT / "data" / "processed"

OUTPUT_COLUMNS = [
    "segment_id",
    "year",
    "profile",
    "profile_label",
    "opportunity_score",
    "rank_in_year",
    "base_rank",
    "rank_shift",
    "is_base_profile",
]


def build(scored: pd.DataFrame, config: dict) -> pd.DataFrame:
    base_name = config["base_profile"]
    norm_columns = [c for c in scored.columns if c.startswith("norm_")]
    normalized = scored[["segment_id", "year", *norm_columns]]

    base_rank = scored.set_index(["segment_id", "year"])["rank_in_year"]

    frames = []
    for name, profile in config["profiles"].items():
        rescored = apply_weights(normalized, profile["weights"])
        rescored["profile"] = name
        rescored["profile_label"] = profile["label"]
        rescored["base_rank"] = pd.MultiIndex.from_frame(
            rescored[["segment_id", "year"]]
        ).map(base_rank)
        # Positive shift means the profile ranks the segment better than the house view does.
        rescored["rank_shift"] = rescored["base_rank"] - rescored["rank_in_year"]
        rescored["is_base_profile"] = int(name == base_name)
        frames.append(rescored[OUTPUT_COLUMNS])

    return pd.concat(frames).sort_values(
        ["profile", "year", "rank_in_year"], ignore_index=True
    )


def summarise(sensitivity: pd.DataFrame, config: dict) -> None:
    window = config["forward_window"]
    forward = sensitivity[sensitivity["year"].between(window["start_year"], window["end_year"])]
    alternatives = forward[forward["is_base_profile"] == 0]

    swing = (
        alternatives.groupby("segment_id")["rank_shift"]
        .apply(lambda s: int(s.abs().max()))
        .sort_values(ascending=False)
    )
    stable = [seg for seg, shift in swing.items() if shift == 0]
    print(f"rank held under every alternative profile ({window['start_year']}-{window['end_year']}): "
          f"{', '.join(sorted(stable)) if stable else 'none'}")
    print("max rank swing vs house view: " + ", ".join(
        f"{seg} {shift} place(s)" for seg, shift in swing.items() if shift > 0
    ))


def main() -> None:
    config = load_config()
    scored = pd.read_csv(PROCESSED_DIR / "fact_opportunity_score.csv")

    sensitivity = build(scored, config)
    sensitivity.to_csv(PROCESSED_DIR / "fact_sensitivity.csv", index=False, lineterminator="\n")

    print(f"sensitivity: {sensitivity.shape} across {sensitivity['profile'].nunique()} profiles "
          f"-> {PROCESSED_DIR / 'fact_sensitivity.csv'}")
    summarise(sensitivity, config)


if __name__ == "__main__":
    main()
