-- Business question: which segments grow faster than the industry middle over the forward
-- window, and does that growth actually translate into a high opportunity score? Growth alone
-- is not a reason to commit design capacity; growth in a market you cannot sell into is not.
--
-- Expected shape: at most 8 rows, only segments whose mean forward CAGR exceeds the median
-- across segments, ordered by mean CAGR descending. Columns include the mean opportunity score
-- and the gap between the segment's CAGR rank and its opportunity rank.

WITH forward AS (
    SELECT
        f.segment_id,
        AVG(f.cagr_pct)                        AS mean_cagr_pct,
        AVG(f.serviceable_market_usd_bn)       AS mean_serviceable_usd_bn,
        AVG(s.opportunity_score)               AS mean_opportunity_score
    FROM fact_segment_year AS f
    JOIN fact_opportunity_score AS s
      ON s.segment_id = f.segment_id AND s.year = f.year
    WHERE f.year BETWEEN 2026 AND 2030
    GROUP BY f.segment_id
),
ranked AS (
    SELECT
        segment_id,
        mean_cagr_pct,
        mean_serviceable_usd_bn,
        mean_opportunity_score,
        RANK() OVER (ORDER BY mean_cagr_pct DESC)          AS cagr_rank,
        RANK() OVER (ORDER BY mean_opportunity_score DESC)  AS opportunity_rank
    FROM forward
),
-- SQLite has no median function; the average of the two central values is taken explicitly.
median_cagr AS (
    SELECT AVG(mean_cagr_pct) AS median_value
    FROM (
        SELECT mean_cagr_pct
        FROM forward
        ORDER BY mean_cagr_pct
        LIMIT 2 OFFSET 3
    )
)
SELECT
    d.segment_name,
    d.recommendation,
    ROUND(r.mean_cagr_pct, 1)             AS mean_cagr_pct_2026_2030,
    ROUND(r.mean_serviceable_usd_bn, 2)   AS mean_serviceable_usd_bn,
    ROUND(r.mean_opportunity_score, 1)    AS mean_opportunity_score,
    r.cagr_rank,
    r.opportunity_rank,
    r.cagr_rank - r.opportunity_rank      AS growth_premium_rank_gap
FROM ranked AS r
JOIN dim_segment AS d ON d.segment_id = r.segment_id
CROSS JOIN median_cagr AS m
WHERE r.mean_cagr_pct > m.median_value
ORDER BY r.mean_cagr_pct DESC;
