-- Business question: if segments are grouped by how long a typical design engagement runs, which
-- cohort carries the most serviceable market and the best scores? Long engagements are stickier
-- revenue and easier to staff against; short ones re-compete constantly. This is the revenue-
-- predictability argument that sits behind the recommendation.
--
-- Expected shape: 3 rows, one per design-cycle cohort, ordered from longest to shortest cycle.
-- Columns: cohort, segments in it, mean cycle length, total serviceable market, mean score, and
-- how much of the serviceable pool the cohort holds.

WITH cohorts AS (
    SELECT
        f.segment_id,
        f.design_cycle_months,
        f.serviceable_market_usd_bn,
        s.opportunity_score,
        CASE
            WHEN f.design_cycle_months >= 20 THEN 'Long (20+ months)'
            WHEN f.design_cycle_months >= 14 THEN 'Medium (14-19 months)'
            ELSE 'Short (under 14 months)'
        END AS design_cycle_cohort
    FROM fact_segment_year AS f
    JOIN fact_opportunity_score AS s
      ON s.segment_id = f.segment_id AND s.year = f.year
    WHERE f.year = 2030
)
SELECT
    c.design_cycle_cohort,
    COUNT(*)                                    AS segments_in_cohort,
    GROUP_CONCAT(d.segment_name, '; ')          AS segments,
    ROUND(AVG(c.design_cycle_months), 1)        AS mean_design_cycle_months,
    ROUND(SUM(c.serviceable_market_usd_bn), 1)  AS serviceable_usd_bn,
    ROUND(AVG(c.opportunity_score), 1)          AS mean_opportunity_score,
    ROUND(
        SUM(c.serviceable_market_usd_bn) * 100.0
        / (SELECT SUM(serviceable_market_usd_bn) FROM fact_segment_year WHERE year = 2030), 1
    ) AS share_of_serviceable_pool_pct
FROM cohorts AS c
JOIN dim_segment AS d ON d.segment_id = c.segment_id
GROUP BY c.design_cycle_cohort
ORDER BY mean_design_cycle_months DESC;
