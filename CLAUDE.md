# CLAUDE.md — Semiconductor Market Opportunity & Competitive Intelligence

Project instructions. These are binding for any work in this repository.

## What this project is

A Business Analyst portfolio project. It answers one question:

> Cyient Semiconductors has finite design and engineering capacity. Across the semiconductor
> value chain, which end-market segments should it prioritize for expansion of its design
> services over the next 3-5 years, which warrant selective/partnership entry, and which
> should it deprioritize?

The deliverable is a prioritization framework and a go/no-go recommendation. It is not a
forecast, and it is not a data science exercise. Every artifact should read as analyst work
produced for senior leadership at an engineering-services company.

## Data integrity — non-negotiable

Every number in this repository is illustrative and synthetic, calibrated to be directionally
consistent with publicly reported industry estimates. The disclosure must appear at the top of
`README.md`, in `data/DATA_PROVENANCE.md`, on slide 2 of the deck, and as a visible footnote on
every dashboard page.

Standard wording:

> Illustrative dataset constructed to be directionally consistent with publicly reported
> industry estimates. Figures are for methodology demonstration and are not market research.

Do not invent specific figures and attribute them to a named source. Do not fabricate URLs,
report titles, or page numbers. Anchor sources may be named at the level of the organisation
that publishes such estimates (WSTS, SEMI, McKinsey semiconductor practice, company annual
reports) and nothing more precise than that.

## Technical pins

- Python 3.11 or newer.
- pandas and numpy only for analysis. No scikit-learn, no statsmodels, no modelling libraries.
- SQLite is the database. No server-based database.
- No plotting libraries anywhere in the pipeline. Power BI owns all visuals; the Python layer
  produces tables, a workbook, and a deck.
- Every script in `src/` runs standalone (`python src/<script>.py`) and is idempotent: running
  it twice produces byte-identical output.
- Random generation is seeded and deterministic.
- `make all` must complete in under 60 seconds.

## Single source of truth

The scoring weights live in `config/weights.yaml` and nowhere else. The Python scorer reads
them from that file. The Excel model writes them into labelled input cells and references those
cells in live formulas. If a weight changes in the YAML, both must follow. Never hardcode a
weight inline in a script or a formula.

## Analytical rules

- Score on serviceable market size (`market_size_usd_bn * design_services_addressable_pct`),
  never on raw TAM. TAM is the market; serviceable market is the part a design-services firm can
  actually sell into.
- Normalize every factor min-max to 0-100 across segments within each year, so a score is a
  statement about relative standing in that year.
- Competitive intensity is inverted before weighting; more crowded is worse.
- Any ranking presented must be accompanied by the sensitivity result that shows whether it
  holds under alternative weight profiles.

## Style

- No emoji in code, commit messages, or the README. The deck may use a single colour-coded
  prioritize / selective / deprioritize legend.
- Comment the why, not the what.
- No dead code and no placeholder TODOs in committed files.
- Conventional commit messages.

## Layout

```
config/      weights.yaml - the only place weights are defined
data/raw/    generated source CSVs
data/processed/  star schema: dim_segment, fact_segment_year, fact_opportunity_score, fact_sensitivity
src/         pipeline scripts, run in Makefile order
sql/         schema plus seven analytical queries, with RESULTS.md holding real output
db/          market.db (generated)
excel/       opportunity_scoring.xlsx (generated)
powerbi/     DAX measures, model relationships, and a build guide for a three-page dashboard
presentation/ market_strategy.pptx (generated)
report/      analysis_memo.md
```

## Pipeline order

`generate_data.py` -> `clean.py` -> `score.py` -> `sensitivity.py` -> `load_sqlite.py` ->
`build_excel.py` -> `build_deck.py`. This is what `make all` runs.
