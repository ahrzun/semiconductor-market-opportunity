-- Business question: which segments are adding the most serviceable revenue pool between the
-- base year and the end of the planning horizon, in absolute dollars rather than in percent?
-- Percentage growth flatters small markets; capacity is committed against dollars.
--
-- Expected shape: 8 rows, one per segment, ordered by serviceable market added, descending.
-- Columns: segment_name, recommendation, serviceable 2024, serviceable 2030, dollars added,
-- implied serviceable CAGR, TAM added.

WITH bookends AS (
    SELECT
        f.segment_id,
        MAX(CASE WHEN f.year = 2024 THEN f.serviceable_market_usd_bn END) AS serviceable_2024,
        MAX(CASE WHEN f.year = 2030 THEN f.serviceable_market_usd_bn END) AS serviceable_2030,
        MAX(CASE WHEN f.year = 2024 THEN f.market_size_usd_bn END)        AS tam_2024,
        MAX(CASE WHEN f.year = 2030 THEN f.market_size_usd_bn END)        AS tam_2030
    FROM fact_segment_year AS f
    WHERE f.year IN (2024, 2030)
    GROUP BY f.segment_id
)
SELECT
    d.segment_name,
    d.recommendation,
    ROUND(b.serviceable_2024, 2)                        AS serviceable_2024_usd_bn,
    ROUND(b.serviceable_2030, 2)                        AS serviceable_2030_usd_bn,
    ROUND(b.serviceable_2030 - b.serviceable_2024, 2)   AS serviceable_added_usd_bn,
    ROUND((POWER(b.serviceable_2030 / b.serviceable_2024, 1.0 / 6.0) - 1) * 100, 1)
                                                        AS serviceable_cagr_pct,
    ROUND(b.tam_2030 - b.tam_2024, 2)                   AS tam_added_usd_bn
FROM bookends AS b
JOIN dim_segment AS d ON d.segment_id = b.segment_id
ORDER BY serviceable_added_usd_bn DESC;
