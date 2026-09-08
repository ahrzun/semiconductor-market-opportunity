# Data provenance

> Illustrative dataset constructed to be directionally consistent with publicly reported
> industry estimates. Figures are for methodology demonstration and are not market research.

Read that sentence literally. No number in this repository was extracted from a purchased
dataset, a subscription database, or a specific published report. Everything in `data/raw/` is
produced by `src/generate_data.py` from a fixed seed. The value of the dataset is that the
*relationships between segments* are set up the way the public record describes them, which is
enough to demonstrate and defend a prioritization method.

## What is modelled versus what is asserted

| Field | Nature | How it was set |
|---|---|---|
| `market_size_usd_bn` | Modelled | 2024 base magnitude per segment, chained out to 2021-2030 using that segment's growth path, plus a shared sector cycle and a small idiosyncratic term. |
| `cagr_pct` | Modelled | Segment growth path, decelerating with maturity. This is the trend rate; realized year-on-year growth in the data differs from it because the sector cycle is applied on top. |
| `design_services_addressable_pct` | Analyst judgment | The share of segment TAM an outsourced design-services provider can realistically sell into. Not a published statistic in any source. |
| `competitive_intensity`, `customer_demand`, `entry_feasibility`, `strategic_fit`, `talent_availability` | Analyst judgment | 0-100 opinion scores. They are calibrated against each other, not measured. |
| `design_cycle_months` | Analyst judgment | Typical engagement length, used as a proxy for revenue stickiness. |

The qualitative 0-100 scores are the analyst's judgment, not measured data. They carry 45% of
the base weight between them, which is exactly why `src/sensitivity.py` exists: the ranking is
only worth presenting if it survives a reweighting of those judgments.

## Anchoring, by segment

The organisations below publish estimates of the kind used to sanity-check each magnitude. They
are named at the level of the publishing organisation and nothing more precise. No figure here
is attributed to a specific report, page, or URL, and none should be quoted as if it were.

| Segment | Magnitude anchored against | Direction the public record points |
|---|---|---|
| Automotive & ADAS silicon | WSTS segment reporting; automotive semiconductor supplier annual reports | Mid-sized market, high single to low double digit growth, unusually long design programmes and heavy functional-safety content. |
| HPC / AI accelerator ASICs | WSTS logic reporting; hyperscaler and merchant-accelerator annual reports | Largest growth pool in the industry, with much of the design work retained in-house by a small number of buyers. |
| Power electronics (SiC / GaN) | SEMI capacity and equipment reporting; compound-semiconductor supplier annual reports | Small but fast-compounding market; large announced capacity additions in the middle of the decade. |
| RF & 5G front-end | WSTS discrete and analog reporting; RF front-end supplier annual reports | Mature handset-driven demand with a concentrated incumbent set. |
| Silicon photonics / optical interconnect | SEMI advanced-packaging reporting; optical module supplier annual reports | Smallest market in the set and the fastest compounding, tied to datacentre interconnect. |
| MEMS & sensors | WSTS sensor reporting; MEMS supplier annual reports | Fragmented, moderate growth, short product cycles. |
| Memory (DRAM / NAND) | WSTS memory reporting; memory IDM annual reports | Largest headline TAM in the set, the most cyclical, and structurally captive to a handful of integrated device manufacturers. |
| Analog & mixed-signal | WSTS analog reporting; broad-line analog supplier annual reports | Large, slow-growing, highly fragmented at the design level, long product lifetimes. |

General framing of the industry structure and of where outsourced engineering capacity is
absorbed follows the published commentary of the McKinsey semiconductor practice and of SEMI.
Again: framing only, no figures.

## The deliberate anomaly

Power electronics (SiC / GaN) is constructed so that TAM rises every year to 2030 while its
opportunity score turns down after 2027, because competitive intensity climbs steeply once
announced capacity converts to supply. This is planted on purpose. It is the case the analysis
is designed to catch, and `sql/05_anomaly_size_vs_score.sql` surfaces it.

## Reproducibility

`src/generate_data.py` uses a single fixed seed (`SEED = 20240901`), a fixed draw order, and
fixed rounding. Running the pipeline twice produces byte-identical files. Changing the seed
changes the noise, not the story: the ordering of segments is set by the anchors, not the draws.
