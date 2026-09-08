-- Business question: how different is the picture when segments are ranked by the market a
-- design-services firm can actually sell into, rather than by headline TAM? This query exists to
-- quantify the cost of the lazy version of this analysis.
--
-- Expected shape: 8 rows in the 2030 view, ordered by the size of the rank movement. A large
-- positive rank_gap means headline TAM overstates the segment for our purposes.

WITH ranked AS (
    SELECT
        f.segment_id,
        f.market_size_usd_bn,
        f.serviceable_market_usd_bn,
        f.design_services_addressable_pct,
        RANK() OVER (ORDER BY f.market_size_usd_bn DESC)        AS tam_rank,
        RANK() OVER (ORDER BY f.serviceable_market_usd_bn DESC) AS serviceable_rank
    FROM fact_segment_year AS f
    WHERE f.year = 2030
)
SELECT
    d.segment_name,
    d.recommendation,
    ROUND(r.market_size_usd_bn, 1)                   AS tam_usd_bn,
    ROUND(r.serviceable_market_usd_bn, 1)            AS serviceable_usd_bn,
    ROUND(r.design_services_addressable_pct * 100, 1) AS addressable_pct,
    ROUND(r.market_size_usd_bn - r.serviceable_market_usd_bn, 1) AS unreachable_usd_bn,
    r.tam_rank,
    r.serviceable_rank,
    -- Positive: the segment looks better on TAM than it is. Negative: TAM understates it.
    r.serviceable_rank - r.tam_rank                  AS rank_gap
FROM ranked AS r
JOIN dim_segment AS d ON d.segment_id = r.segment_id
ORDER BY rank_gap DESC, r.tam_rank;
