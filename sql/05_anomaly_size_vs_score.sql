-- Business question: is there a segment whose market keeps growing while its attractiveness to
-- us falls? That divergence is the single most expensive thing to miss, because the headline
-- TAM chart keeps pointing up right through the period when the returns are being competed away.
--
-- The test has three parts, all of which must hold: TAM grows in every year after 2027; the
-- 2030 score is below the 2027 score; and competitive intensity rises by at least 10 points over
-- the same stretch. The third clause is what makes this an anomaly query rather than a list of
-- everything that drifted down. Six of the eight segments lose a little score between 2027 and
-- 2030 simply because scores are relative and the leaders pull away - that is noise. A ten-point
-- move on a 0-100 crowding scale is a structural change in who we would be bidding against.
--
-- Expected shape: 1 row (power electronics), showing TAM growth and score fall side by side.

WITH tam_path AS (
    SELECT
        segment_id,
        MIN(CASE WHEN year > 2027 AND market_size_usd_bn > prior_size THEN 1 ELSE 0 END)
            AS tam_rose_every_year_after_2027
    FROM (
        SELECT
            segment_id,
            year,
            market_size_usd_bn,
            LAG(market_size_usd_bn) OVER (PARTITION BY segment_id ORDER BY year) AS prior_size
        FROM fact_segment_year
    )
    WHERE year > 2027
    GROUP BY segment_id
),
score_path AS (
    SELECT
        segment_id,
        MAX(opportunity_score)                                  AS peak_score,
        MAX(CASE WHEN year = 2030 THEN opportunity_score END)   AS score_2030,
        MAX(CASE WHEN year = 2027 THEN opportunity_score END)   AS score_2027,
        MAX(CASE WHEN year = 2027 THEN rank_in_year END)        AS rank_2027,
        MAX(CASE WHEN year = 2030 THEN rank_in_year END)        AS rank_2030
    FROM fact_opportunity_score
    GROUP BY segment_id
),
crowding AS (
    SELECT
        segment_id,
        MAX(CASE WHEN year = 2027 THEN competitive_intensity END) AS intensity_2027,
        MAX(CASE WHEN year = 2030 THEN competitive_intensity END) AS intensity_2030,
        MAX(CASE WHEN year = 2027 THEN market_size_usd_bn END)    AS tam_2027,
        MAX(CASE WHEN year = 2030 THEN market_size_usd_bn END)    AS tam_2030
    FROM fact_segment_year
    GROUP BY segment_id
)
SELECT
    d.segment_name,
    d.recommendation,
    ROUND(c.tam_2027, 1)                        AS tam_2027_usd_bn,
    ROUND(c.tam_2030, 1)                        AS tam_2030_usd_bn,
    ROUND((c.tam_2030 / c.tam_2027 - 1) * 100, 1) AS tam_growth_pct,
    ROUND(s.score_2027, 1)                      AS score_2027,
    ROUND(s.score_2030, 1)                      AS score_2030,
    ROUND(s.score_2030 - s.peak_score, 1)       AS score_change_from_peak,
    s.rank_2027,
    s.rank_2030,
    ROUND(c.intensity_2030 - c.intensity_2027, 1) AS competitive_intensity_rise
FROM tam_path AS t
JOIN score_path AS s ON s.segment_id = t.segment_id
JOIN crowding  AS c ON c.segment_id = t.segment_id
JOIN dim_segment AS d ON d.segment_id = t.segment_id
WHERE t.tam_rose_every_year_after_2027 = 1
  AND s.score_2030 < s.score_2027
  AND c.intensity_2030 - c.intensity_2027 >= 10
ORDER BY score_change_from_peak;
