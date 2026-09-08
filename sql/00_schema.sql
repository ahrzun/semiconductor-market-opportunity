-- Star schema for the segment opportunity model.
--
-- One conformed dimension (dim_segment) and three facts, all at segment-year grain except the
-- sensitivity fact, which adds the weight profile to the grain. Rebuilt from data/processed by
-- src/load_sqlite.py; nothing is inserted by hand.

DROP TABLE IF EXISTS fact_sensitivity;
DROP TABLE IF EXISTS fact_opportunity_score;
DROP TABLE IF EXISTS fact_segment_year;
DROP TABLE IF EXISTS dim_segment;

CREATE TABLE dim_segment (
    segment_id          TEXT PRIMARY KEY,
    segment_name        TEXT NOT NULL,
    value_chain_stage   TEXT NOT NULL,
    cycle_beta          REAL NOT NULL,
    analyst_note        TEXT NOT NULL,
    addressability_tier TEXT NOT NULL CHECK (addressability_tier IN ('Low', 'Moderate', 'High')),
    forward_mean_score  REAL NOT NULL,
    recommendation      TEXT NOT NULL
        CHECK (recommendation IN ('Prioritize', 'Selective', 'Deprioritize'))
);

CREATE TABLE fact_segment_year (
    segment_id                      TEXT NOT NULL REFERENCES dim_segment (segment_id),
    year                            INTEGER NOT NULL,
    market_size_usd_bn              REAL NOT NULL CHECK (market_size_usd_bn > 0),
    cagr_pct                        REAL NOT NULL,
    design_services_addressable_pct REAL NOT NULL
        CHECK (design_services_addressable_pct BETWEEN 0 AND 1),
    -- market_size_usd_bn * design_services_addressable_pct. Stored rather than computed on read
    -- so that every consumer, including Power BI, uses the same definition.
    serviceable_market_usd_bn       REAL NOT NULL,
    competitive_intensity           REAL NOT NULL CHECK (competitive_intensity BETWEEN 0 AND 100),
    customer_demand                 REAL NOT NULL CHECK (customer_demand BETWEEN 0 AND 100),
    entry_feasibility               REAL NOT NULL CHECK (entry_feasibility BETWEEN 0 AND 100),
    strategic_fit                   REAL NOT NULL CHECK (strategic_fit BETWEEN 0 AND 100),
    talent_availability             REAL NOT NULL CHECK (talent_availability BETWEEN 0 AND 100),
    design_cycle_months             REAL NOT NULL CHECK (design_cycle_months > 0),
    PRIMARY KEY (segment_id, year)
);

CREATE TABLE fact_opportunity_score (
    segment_id                             TEXT NOT NULL REFERENCES dim_segment (segment_id),
    year                                   INTEGER NOT NULL,
    norm_serviceable_market_size           REAL NOT NULL,
    norm_cagr                              REAL NOT NULL,
    norm_design_services_addressability    REAL NOT NULL,
    norm_strategic_fit                     REAL NOT NULL,
    norm_customer_demand                   REAL NOT NULL,
    -- Already inverted: high means uncrowded, which is good.
    norm_competitive_intensity             REAL NOT NULL,
    norm_entry_feasibility                 REAL NOT NULL,
    contrib_serviceable_market_size        REAL NOT NULL,
    contrib_cagr                           REAL NOT NULL,
    contrib_design_services_addressability REAL NOT NULL,
    contrib_strategic_fit                  REAL NOT NULL,
    contrib_customer_demand                REAL NOT NULL,
    contrib_competitive_intensity          REAL NOT NULL,
    contrib_entry_feasibility              REAL NOT NULL,
    opportunity_score                      REAL NOT NULL CHECK (opportunity_score BETWEEN 0 AND 100),
    rank_in_year                           INTEGER NOT NULL CHECK (rank_in_year BETWEEN 1 AND 8),
    PRIMARY KEY (segment_id, year),
    FOREIGN KEY (segment_id, year) REFERENCES fact_segment_year (segment_id, year)
);

CREATE TABLE fact_sensitivity (
    segment_id       TEXT NOT NULL REFERENCES dim_segment (segment_id),
    year             INTEGER NOT NULL,
    profile          TEXT NOT NULL,
    profile_label    TEXT NOT NULL,
    opportunity_score REAL NOT NULL,
    rank_in_year     INTEGER NOT NULL,
    base_rank        INTEGER NOT NULL,
    -- Positive means the profile ranks the segment better than the house view does.
    rank_shift       INTEGER NOT NULL,
    is_base_profile  INTEGER NOT NULL CHECK (is_base_profile IN (0, 1)),
    PRIMARY KEY (segment_id, year, profile)
);

CREATE INDEX idx_fact_segment_year_year ON fact_segment_year (year);
CREATE INDEX idx_fact_opportunity_score_year ON fact_opportunity_score (year);
CREATE INDEX idx_fact_sensitivity_profile_year ON fact_sensitivity (profile, year);
