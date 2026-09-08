"""Generate the illustrative raw dataset for the segment opportunity model.

Every figure produced here is synthetic. Magnitudes are set so that the *relative* picture
across segments matches what is publicly reported about the industry (memory is a huge market
that an outsourced design house can barely sell into; silicon photonics is tiny but compounding
fast; automotive and analog sit in the middle on size and at the top on fit). See
data/DATA_PROVENANCE.md.

Output is fully deterministic: one fixed seed, one draw order, fixed rounding. Re-running
overwrites the three raw CSVs with byte-identical content.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

SEED = 20240901
BASE_YEAR = 2024
YEARS = list(range(2021, 2031))
RAW_DIR = Path(__file__).resolve().parents[1] / "data" / "raw"

# A single sector cycle applied to every segment, scaled by each segment's cycle beta. Real
# semiconductor revenue does not compound smoothly; a model whose series are perfectly smooth
# invites the reader to distrust the whole thing. Zero at the base year so the anchor holds.
SECTOR_CYCLE = {
    2021: 0.045,
    2022: 0.010,
    2023: -0.065,
    2024: 0.000,
    2025: 0.022,
    2026: 0.012,
    2027: -0.020,
    2028: 0.004,
    2029: 0.010,
    2030: 0.000,
}

# Anchors are (year -> value) and are linearly interpolated between adjacent anchors. Two
# anchors describe a straight drift; three describe a deliberate kink.
SEGMENTS = [
    {
        "segment_id": "AUTO",
        "segment_name": "Automotive & ADAS silicon",
        "value_chain_stage": "SoC / ASIC design",
        "cycle_beta": 0.6,
        "tam_base_usd_bn": 82.0,
        "cagr_anchors": {2021: 10.8, 2030: 8.2},
        "addressable_anchors": {2021: 0.205, 2030: 0.245},
        "design_cycle_anchors": {2021: 17.0, 2030: 19.5},
        "qualitative_anchors": {
            "competitive_intensity": {2021: 56.0, 2030: 68.0},
            "customer_demand": {2021: 82.0, 2030: 91.0},
            "entry_feasibility": {2021: 68.0, 2030: 72.0},
            "strategic_fit": {2021: 85.0, 2030: 90.0},
            "talent_availability": {2021: 74.0, 2030: 82.0},
        },
        "notes": "Long programme lengths and functional-safety work favour an embedded/VLSI services partner.",
    },
    {
        "segment_id": "HPC",
        "segment_name": "HPC / AI accelerator ASICs",
        "value_chain_stage": "Custom ASIC design",
        "cycle_beta": 1.2,
        "tam_base_usd_bn": 145.0,
        "cagr_anchors": {2021: 27.0, 2030: 16.0},
        "addressable_anchors": {2021: 0.105, 2030: 0.135},
        "design_cycle_anchors": {2021: 22.0, 2030: 25.0},
        "qualitative_anchors": {
            "competitive_intensity": {2021: 80.0, 2030: 92.0},
            "customer_demand": {2021: 88.0, 2030: 96.0},
            "entry_feasibility": {2021: 48.0, 2030: 42.0},
            "strategic_fit": {2021: 68.0, 2030: 76.0},
            "talent_availability": {2021: 50.0, 2030: 60.0},
        },
        "notes": "Largest prize and the hardest entry; hyperscaler in-house teams absorb most of the work.",
    },
    {
        "segment_id": "PWR",
        "segment_name": "Power electronics (SiC / GaN)",
        "value_chain_stage": "Device & module design",
        "cycle_beta": 0.8,
        "tam_base_usd_bn": 28.0,
        "cagr_anchors": {2021: 19.5, 2027: 16.5, 2030: 11.0},
        "addressable_anchors": {2021: 0.170, 2030: 0.190},
        "design_cycle_anchors": {2021: 13.0, 2030: 15.0},
        # The planted anomaly. TAM compounds through 2030, but capacity announced between 2025
        # and 2027 lands as competition after 2027 and the segment crowds sharply.
        "qualitative_anchors": {
            "competitive_intensity": {2021: 44.0, 2027: 56.0, 2030: 94.0},
            "customer_demand": {2021: 74.0, 2027: 84.0, 2030: 80.0},
            "entry_feasibility": {2021: 66.0, 2030: 60.0},
            "strategic_fit": {2021: 62.0, 2030: 68.0},
            "talent_availability": {2021: 46.0, 2030: 58.0},
        },
        "notes": "Growth is real; the margin pool crowds once announced SiC capacity converts to supply.",
    },
    {
        "segment_id": "RF5G",
        "segment_name": "RF & 5G front-end",
        "value_chain_stage": "RF IC design",
        "cycle_beta": 1.0,
        "tam_base_usd_bn": 34.0,
        "cagr_anchors": {2021: 9.0, 2030: 6.4},
        "addressable_anchors": {2021: 0.150, 2030: 0.170},
        "design_cycle_anchors": {2021: 11.5, 2030: 12.5},
        "qualitative_anchors": {
            "competitive_intensity": {2021: 70.0, 2030: 76.0},
            "customer_demand": {2021: 70.0, 2030: 63.0},
            "entry_feasibility": {2021: 60.0, 2030: 58.0},
            "strategic_fit": {2021: 66.0, 2030: 72.0},
            "talent_availability": {2021: 60.0, 2030: 68.0},
        },
        "notes": "Mature handset demand; incremental infrastructure and satellite work only.",
    },
    {
        "segment_id": "PHOT",
        "segment_name": "Silicon photonics / optical interconnect",
        "value_chain_stage": "Photonic IC & packaging design",
        "cycle_beta": 0.9,
        "tam_base_usd_bn": 9.0,
        "cagr_anchors": {2021: 29.0, 2030: 22.0},
        "addressable_anchors": {2021: 0.190, 2030: 0.225},
        "design_cycle_anchors": {2021: 19.0, 2030: 21.0},
        "qualitative_anchors": {
            "competitive_intensity": {2021: 38.0, 2030: 54.0},
            "customer_demand": {2021: 62.0, 2030: 84.0},
            "entry_feasibility": {2021: 42.0, 2030: 46.0},
            "strategic_fit": {2021: 44.0, 2030: 54.0},
            "talent_availability": {2021: 26.0, 2030: 38.0},
        },
        "notes": "Fastest compounding market in the set, but the thinnest talent pool in India.",
    },
    {
        "segment_id": "MEMS",
        "segment_name": "MEMS & sensors",
        "value_chain_stage": "Mixed-signal & sensor design",
        "cycle_beta": 0.7,
        "tam_base_usd_bn": 21.0,
        "cagr_anchors": {2021: 9.2, 2030: 7.0},
        "addressable_anchors": {2021: 0.180, 2030: 0.200},
        "design_cycle_anchors": {2021: 9.5, 2030: 10.5},
        "qualitative_anchors": {
            "competitive_intensity": {2021: 54.0, 2030: 62.0},
            "customer_demand": {2021: 60.0, 2030: 66.0},
            "entry_feasibility": {2021: 74.0, 2030: 76.0},
            "strategic_fit": {2021: 64.0, 2030: 70.0},
            "talent_availability": {2021: 62.0, 2030: 70.0},
        },
        "notes": "Easy to enter and easy to leave; short engagements make revenue hard to forecast.",
    },
    {
        "segment_id": "MEM",
        "segment_name": "Memory (DRAM / NAND)",
        "value_chain_stage": "Captive IDM design",
        "cycle_beta": 1.9,
        "tam_base_usd_bn": 165.0,
        "cagr_anchors": {2021: 11.0, 2030: 7.0},
        "addressable_anchors": {2021: 0.035, 2030: 0.045},
        "design_cycle_anchors": {2021: 28.0, 2030: 31.0},
        "qualitative_anchors": {
            "competitive_intensity": {2021: 76.0, 2030: 84.0},
            "customer_demand": {2021: 52.0, 2030: 58.0},
            "entry_feasibility": {2021: 26.0, 2030: 24.0},
            "strategic_fit": {2021: 32.0, 2030: 38.0},
            "talent_availability": {2021: 42.0, 2030: 48.0},
        },
        "notes": "Headline TAM leader and the clearest trap: design stays captive inside three IDMs.",
    },
    {
        "segment_id": "ANLG",
        "segment_name": "Analog & mixed-signal",
        "value_chain_stage": "Analog / mixed-signal design",
        "cycle_beta": 0.8,
        "tam_base_usd_bn": 92.0,
        "cagr_anchors": {2021: 7.4, 2030: 5.8},
        "addressable_anchors": {2021: 0.225, 2030: 0.255},
        "design_cycle_anchors": {2021: 15.0, 2030: 17.0},
        "qualitative_anchors": {
            "competitive_intensity": {2021: 58.0, 2030: 64.0},
            "customer_demand": {2021: 74.0, 2030: 80.0},
            "entry_feasibility": {2021: 78.0, 2030: 82.0},
            "strategic_fit": {2021: 88.0, 2030: 92.0},
            "talent_availability": {2021: 80.0, 2030: 86.0},
        },
        "notes": "Slowest growth, deepest fit; the volume base that funds capacity elsewhere.",
    },
]

QUALITATIVE_FACTORS = [
    "competitive_intensity",
    "customer_demand",
    "entry_feasibility",
    "strategic_fit",
    "talent_availability",
]


def interpolate(anchors: dict[int, float], years: list[int]) -> np.ndarray:
    """Piecewise-linear path through the anchor years, held flat outside the anchor range."""
    anchor_years = sorted(anchors)
    return np.interp(years, anchor_years, [anchors[y] for y in anchor_years])


def chain_market_size(base: float, cagr_pct: np.ndarray, years: list[int]) -> np.ndarray:
    """Walk the TAM out from the base year in both directions using each year's growth rate.

    cagr_pct[i] is the growth rate carrying year i into year i+1, so the base-year anchor is
    reproduced exactly rather than drifting out of a single compound factor.
    """
    base_idx = years.index(BASE_YEAR)
    size = np.empty(len(years), dtype=float)
    size[base_idx] = base
    for i in range(base_idx + 1, len(years)):
        size[i] = size[i - 1] * (1.0 + cagr_pct[i - 1] / 100.0)
    for i in range(base_idx - 1, -1, -1):
        size[i] = size[i + 1] / (1.0 + cagr_pct[i] / 100.0)
    return size


def build() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    rng = np.random.default_rng(SEED)
    years = YEARS
    cycle = np.array([SECTOR_CYCLE[y] for y in years])

    dim_rows: list[dict] = []
    metric_rows: list[dict] = []
    quality_rows: list[dict] = []

    for seg in SEGMENTS:
        dim_rows.append(
            {
                "segment_id": seg["segment_id"],
                "segment_name": seg["segment_name"],
                "value_chain_stage": seg["value_chain_stage"],
                "cycle_beta": seg["cycle_beta"],
                "analyst_note": seg["notes"],
            }
        )

        cagr = interpolate(seg["cagr_anchors"], years)
        addressable = interpolate(seg["addressable_anchors"], years)
        design_cycle = interpolate(seg["design_cycle_anchors"], years)

        # Trend TAM, then the shared sector cycle scaled by segment beta, then a small
        # idiosyncratic wobble. Order of draws is fixed, so the output is reproducible.
        trend = chain_market_size(seg["tam_base_usd_bn"], cagr, years)
        idio = rng.normal(0.0, 0.008, size=len(years))
        size = trend * (1.0 + cycle * seg["cycle_beta"] + idio)

        for i, year in enumerate(years):
            metric_rows.append(
                {
                    "segment_id": seg["segment_id"],
                    "year": year,
                    "market_size_usd_bn": round(float(size[i]), 3),
                    "cagr_pct": round(float(cagr[i]), 2),
                    "design_services_addressable_pct": round(float(addressable[i]), 4),
                    "design_cycle_months": round(float(design_cycle[i]), 1),
                }
            )

        for factor in QUALITATIVE_FACTORS:
            path = interpolate(seg["qualitative_anchors"][factor], years)
            jitter = rng.normal(0.0, 1.1, size=len(years))
            values = np.clip(path + jitter, 1.0, 99.0)
            for i, year in enumerate(years):
                quality_rows.append(
                    {
                        "segment_id": seg["segment_id"],
                        "year": year,
                        "factor": factor,
                        "score": round(float(values[i]), 1),
                    }
                )

    segments = pd.DataFrame(dim_rows).sort_values("segment_id", ignore_index=True)
    metrics = pd.DataFrame(metric_rows).sort_values(["segment_id", "year"], ignore_index=True)
    quality = pd.DataFrame(quality_rows).sort_values(
        ["segment_id", "year", "factor"], ignore_index=True
    )
    return segments, metrics, quality


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    segments, metrics, quality = build()
    segments.to_csv(RAW_DIR / "segments.csv", index=False, lineterminator="\n")
    metrics.to_csv(RAW_DIR / "segment_year_metrics.csv", index=False, lineterminator="\n")
    quality.to_csv(RAW_DIR / "qualitative_scores.csv", index=False, lineterminator="\n")
    print(
        f"raw: {len(segments)} segments, {len(metrics)} segment-years, "
        f"{len(quality)} qualitative observations -> {RAW_DIR}"
    )


if __name__ == "__main__":
    main()
