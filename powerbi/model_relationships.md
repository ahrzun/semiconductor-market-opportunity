# Power BI model

> Illustrative dataset constructed to be directionally consistent with publicly reported
> industry estimates. Figures are for methodology demonstration and are not market research.

## Shape

A star. Two conformed dimensions filter three facts and one bridge. Nothing filters upward,
and there are no bidirectional relationships anywhere in the model.

```
                      dim_segment                     dim_year
                   (8 rows, segment_id)          (10 rows, year 2021-2030)
                           |                              |
        +------------------+----------+-------------------+------------------+
        |                  |          |                   |                  |
        v                  v          v                   v                  v
fact_segment_year   fact_opportunity_score   bridge_factor_contribution   fact_sensitivity
   (80 rows)              (80 rows)                (560 rows)                (320 rows)
                                                                                 ^
                                                                                 |
                                                                          dim_profile
                                                                          (4 rows, profile)
```

## Tables

| Table | Grain | Rows | Source |
|---|---|---|---|
| `dim_segment` | one row per segment | 8 | `data/processed/dim_segment.csv` |
| `dim_year` | one row per year | 10 | DAX calculated table |
| `dim_profile` | one row per weight profile | 4 | DAX calculated table |
| `fact_segment_year` | segment x year | 80 | `data/processed/fact_segment_year.csv` |
| `fact_opportunity_score` | segment x year | 80 | `data/processed/fact_opportunity_score.csv` |
| `fact_sensitivity` | segment x year x profile | 320 | `data/processed/fact_sensitivity.csv` |
| `bridge_factor_contribution` | segment x year x factor | 560 | unpivoted in Power Query from `fact_opportunity_score` |

## Relationships

Create these nine, in this order. Every one is single-direction, from the dimension to the fact.

| # | From (one side) | To (many side) | Key | Cardinality | Cross-filter | Active |
|---|---|---|---|---|---|---|
| 1 | `dim_segment[segment_id]` | `fact_segment_year[segment_id]` | segment_id | 1 to many | Single | Yes |
| 2 | `dim_segment[segment_id]` | `fact_opportunity_score[segment_id]` | segment_id | 1 to many | Single | Yes |
| 3 | `dim_segment[segment_id]` | `fact_sensitivity[segment_id]` | segment_id | 1 to many | Single | Yes |
| 4 | `dim_segment[segment_id]` | `bridge_factor_contribution[segment_id]` | segment_id | 1 to many | Single | Yes |
| 5 | `dim_year[year]` | `fact_segment_year[year]` | year | 1 to many | Single | Yes |
| 6 | `dim_year[year]` | `fact_opportunity_score[year]` | year | 1 to many | Single | Yes |
| 7 | `dim_year[year]` | `fact_sensitivity[year]` | year | 1 to many | Single | Yes |
| 8 | `dim_year[year]` | `bridge_factor_contribution[year]` | year | 1 to many | Single | Yes |
| 9 | `dim_profile[profile]` | `fact_sensitivity[profile]` | profile | 1 to many | Single | Yes |

Power BI will offer to autodetect relationships on load. Decline it and build these by hand:
autodetect will try to link the two facts to each other on `segment_id`, which creates an
ambiguous path and makes several measures return the wrong grain.

## Why the two calculated tables

`dim_year` exists so that year is a dimension rather than a column repeated inside three facts.
Without it, a year slicer only filters the fact it came from, and the page 2 play axis moves the
scatter while leaving the sensitivity visual behind.

`year` is deliberately a **whole number, not a date**. There is no calendar dimension and no
time-intelligence function anywhere in `measures.dax`; prior-year comparisons filter the integer
explicitly. Marking `dim_year` as a date table would be wrong here - the data has no day grain
and no fiscal calendar to honour.

`dim_profile` exists so the sensitivity profile can be sliced without the slicer also filtering
the base-view visuals through `fact_sensitivity`.

## Why the bridge table

`fact_opportunity_score` stores the seven weighted contributions as seven columns. That is the
right shape for a scorer and the wrong shape for a chart: a bar chart of "what drives this
segment's score" needs factor as a field, not seven measures. Unpivoting in Power Query produces
`bridge_factor_contribution` at segment x year x factor grain (8 x 10 x 7 = 560 rows), which
drives the decomposition visual from a single measure.

Keep both. The wide table backs the scatter and the KPI cards; the bridge backs the
decomposition. They are two shapes of the same 80 rows, not two versions of the truth.

## Hidden fields

Hide these from report view once the model is built, so the field list shows only what a report
author should touch:

- every `segment_id` and `year` column on the fact tables (filter through the dimensions instead)
- `norm_*` columns on `fact_opportunity_score` (intermediate values; the contributions are what
  a reader can interpret)
- `fact_sensitivity[base_rank]` and `fact_sensitivity[is_base_profile]` (consumed by measures)
- `dim_segment[cycle_beta]` (a data-generation parameter, not an analytical field)

## Sort order

Set `dim_segment[segment_name]` to sort by `dim_segment[forward_mean_score]` descending, so
every categorical axis in the report orders segments best-to-worst without per-visual sorting.
