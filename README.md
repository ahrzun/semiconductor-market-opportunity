# Semiconductor Market Opportunity & Competitive Intelligence

> Illustrative dataset constructed to be directionally consistent with publicly reported
> industry estimates. Figures are for methodology demonstration and are not market research.

A Business Analyst portfolio project: a prioritization framework and a go/no-go recommendation
for where a semiconductor engineering-services firm should commit finite design capacity.

## Objective

Cyient Semiconductors has finite design and engineering capacity. Across the semiconductor value
chain, which end-market segments should it prioritize for expansion of its design services over
the next three to five years, which warrant selective or partnership entry, and which should it
deprioritize?

The deliverable is a framework and a recommendation. It is not a forecast.

## Data integrity

Every number in this repository is synthetic. Nothing was extracted from a purchased dataset,
a subscription database, or a specific published report. The magnitudes are set so that the
*relationships between segments* match what the public record describes - memory is a huge market
an outsourced design house can barely sell into, silicon photonics is tiny and compounding fast,
automotive and analog sit mid-size and top-of-fit - which is enough to demonstrate and defend a
method.

`data/DATA_PROVENANCE.md` states, per segment, which kind of organisation publishes the estimates
each magnitude was sanity-checked against, and marks plainly which fields are analyst judgment
rather than modelled quantities. No figure is attributed to a named report, page or URL, and none
should be quoted as if it were.

## The recommendation

| Call | Segments | 2030 serviceable market | Share of pool |
|---|---|---|---|
| Prioritize | Automotive & ADAS silicon, Analog & mixed-signal, HPC / AI accelerator ASICs | USD 127bn | 72% |
| Selective | Silicon photonics / optical interconnect, Power electronics (SiC / GaN) | USD 21bn | 12% |
| Deprioritize | MEMS & sensors, RF & 5G front-end, Memory (DRAM / NAND) | USD 28bn | 16% |

The full argument is in [`report/analysis_memo.md`](report/analysis_memo.md).

## Method

Eight end-market segments, modelled 2021-2030 on nine attributes. Seven feed a weighted additive
score. Each factor is min-max normalized to 0-100 across the eight segments **within each year**,
so a score states relative standing in that year rather than an absolute quantity. Competitive
intensity is inverted before weighting.

| Factor | Weight | Direction |
|---|---|---|
| Serviceable market size | 20% | higher better |
| CAGR | 20% | higher better |
| Design-services addressability | 15% | higher better |
| Strategic fit | 15% | higher better |
| Customer demand | 10% | higher better |
| Competitive intensity | 10% | **inverted** |
| Entry feasibility | 10% | higher better |

### Why serviceable market rather than TAM

Serviceable market is `market_size_usd_bn x design_services_addressable_pct` - TAM multiplied by
the share of a segment realistically reachable by an outsourced design-services provider. It is
used everywhere the score is computed, and it is the strongest analytical choice in the project.

A design-services firm cannot sell into a market. It can only sell into the part of that market
that gets outsourced. Memory makes the point: USD 271bn of TAM in 2030, second-largest in the
set, and under 5% of it addressable, because memory design stays captive inside a handful of
integrated device manufacturers. Ranked on TAM it comes second. Ranked on serviceable market it
comes fifth. A framework built on headline size would have pointed capacity straight at the worst
segment in the set. `sql/06_serviceable_vs_tam_gap.sql` quantifies that gap for every segment.

### Weights live in one place

`config/weights.yaml` is the only definition of the weights. The Python scorer reads it directly;
`src/build_excel.py` writes the same values into labelled input cells and points every workbook
formula at those cells. Neither hardcodes a weight, so the two cannot drift apart.

### Sensitivity

Any ranking presented here comes with the result that shows whether it holds. The model is
re-scored under three alternative weightings - growth-weighted, feasibility-weighted and
fit-weighted - off exactly the same normalized inputs. Memory stays eighth and RF & 5G stays
seventh under every profile in every forward year. Nothing else is fixed: HPC ranges from first
to sixth. That distinction between what the data settles and what our weights settle is reported
alongside the ranking rather than buried.

## Reproduce

Requires Python 3.11 or newer.

```bash
git clone <this repository>
cd cyient_semi_conductor_project
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
make all
```

`make all` runs in a few seconds and regenerates every artifact from scratch:

```
generate_data.py -> clean.py -> score.py -> sensitivity.py -> load_sqlite.py
                 -> build_excel.py -> build_deck.py
```

Individual targets: `make data`, `make score`, `make db`, `make excel`, `make deck`, `make clean`.
Every script also runs standalone (`python src/score.py`) and is idempotent - running the
pipeline twice produces byte-identical output, because generation is seeded and deterministic.

If `python3` on your path is not the interpreter with the requirements installed, pass it in:
`make all PYTHON=.venv/bin/python`.

## What gets built

| Path | Artifact |
|---|---|
| `data/raw/` | three generated source CSVs |
| `data/processed/` | star schema: `dim_segment`, `fact_segment_year`, `fact_opportunity_score`, `fact_sensitivity` |
| `db/market.db` | SQLite database built from the processed CSVs |
| `sql/` | schema plus seven analytical queries; `RESULTS.md` holds their real output |
| `excel/opportunity_scoring.xlsx` | live scoring model - change a weight, the ranking moves |
| `powerbi/` | DAX measures, model documentation, and a three-page dashboard build guide |
| `presentation/market_strategy.pptx` | seven-slide executive deck |
| `report/analysis_memo.md` | two-page analyst memo |

The Excel workbook is a working model, not a report of results. Weights sit in one highlighted
input block on the Assumptions sheet, and normalization, contributions, score, rank, sensitivity
and the recommendation band are all live formulas pointing at it. Its computed values were
verified cell by cell against the Python pipeline.

A `.pbix` is a binary that the pipeline cannot generate, so
[`powerbi/DASHBOARD_BUILD_GUIDE.md`](powerbi/DASHBOARD_BUILD_GUIDE.md) replaces it: field
placements, coordinates, conditional-formatting rules and a pre-presentation check list, written
for someone who has never seen the dataset.

## Key findings

1. **Ranking on TAM and ranking on serviceable market give different answers.** Memory falls from
   second to fifth; automotive, analog and power electronics each rise a place. Between 74% and
   96% of every segment's TAM is unreachable.
2. **The prioritize group is concentrated.** Automotive, analog and HPC hold 72% of the 2030
   serviceable pool and take the three highest forward scores.
3. **Power electronics grows and gets worse.** TAM rises 56% between 2027 and 2030 while the
   opportunity score falls from 55.9 to 40.0, because competitive intensity climbs 39 points as
   announced SiC capacity converts to supply. `sql/05_anomaly_size_vs_score.sql` isolates it.
4. **Long engagements carry the pool.** Segments running 14-19 month design cycles hold 46% of
   the serviceable market at a mean score of 56; those under 14 months hold 9% at a mean of 36.
5. **The ranking is robust at the bottom and fragile in the middle.** See Sensitivity above.

## Dashboard

Screenshots are added here once the Power BI report is built from the guide. The three pages are
Executive Overview, Opportunity Analysis, and Recommendation.

```
![Page 1 - Executive Overview](powerbi/screenshots/page-1-executive-overview.png)
![Page 2 - Opportunity Analysis](powerbi/screenshots/page-2-opportunity-analysis.png)
![Page 3 - Recommendation](powerbi/screenshots/page-3-recommendation.png)
```

## Limitations

Read these before quoting anything from this repository.

- **The data is synthetic.** It is calibrated to be directionally sensible, not accurate. No
  number here is a market estimate, and none should be repeated as one.
- **Four of the seven scored factors are analyst judgment.** Strategic fit, customer demand,
  competitive intensity and entry feasibility are opinions expressed as 0-100 scores. They carry
  45% of the weight between them. The sensitivity analysis exists because of this, and it does
  not eliminate the problem - it only shows how much of the ranking survives it.
- **The addressable-share assumption is unverified and load-bearing.** It is the single number
  that moves memory from second place to fifth. It has no external source.
- **Competitive dynamics are static.** Competitive intensity follows a smooth modelled path. One
  large entrant, exit or acquisition would move a segment faster than anything shown here.
- **There is no customer, pricing or capacity data.** Nothing uses pipeline, win rates, rate
  cards or utilisation, so serviceable market is a revenue proxy and says nothing about margin. A
  large segment served at low utilisation may be worth less than a small one that is not served
  at all.
- **Scores are relative within a year and not comparable across years in level terms.** A segment
  scoring 60 in 2026 and 55 in 2030 has lost ground against its peers; it has not necessarily got
  worse in absolute terms.
- **The horizon is a projection from a single base year**, not a forecast, and it carries no
  confidence interval because none would be meaningful on synthetic data.
