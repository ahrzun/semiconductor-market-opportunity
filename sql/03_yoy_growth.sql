-- Business question: how volatile is each segment's realized year-on-year growth, and where do
-- the cyclical troughs fall? A services firm staffing against a segment needs to know whether
-- the demand line is smooth or whether it will be carrying idle engineers through a down year.
--
-- Expected shape: 72 rows (8 segments x 9 year-pairs; 2021 has no prior year), ordered by
-- segment then year. Columns: segment, year, TAM, TAM YoY %, serviceable YoY %, score move.

WITH stepped AS (
    SELECT
        d.segment_name,
        f.year,
        f.market_size_usd_bn,
        LAG(f.market_size_usd_bn)        OVER w AS prior_tam,
        f.serviceable_market_usd_bn,
        LAG(f.serviceable_market_usd_bn) OVER w AS prior_serviceable,
        s.opportunity_score,
        LAG(s.opportunity_score)         OVER w AS prior_score
    FROM fact_segment_year AS f
    JOIN fact_opportunity_score AS s
      ON s.segment_id = f.segment_id AND s.year = f.year
    JOIN dim_segment AS d ON d.segment_id = f.segment_id
    WINDOW w AS (PARTITION BY f.segment_id ORDER BY f.year)
)
SELECT
    segment_name,
    year,
    ROUND(market_size_usd_bn, 2)                                    AS market_size_usd_bn,
    ROUND((market_size_usd_bn / prior_tam - 1) * 100, 1)            AS tam_yoy_pct,
    ROUND((serviceable_market_usd_bn / prior_serviceable - 1) * 100, 1) AS serviceable_yoy_pct,
    ROUND(opportunity_score - prior_score, 1)                       AS opportunity_score_delta
FROM stepped
WHERE prior_tam IS NOT NULL
ORDER BY segment_name, year;
