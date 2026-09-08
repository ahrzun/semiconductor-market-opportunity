-- Business question: in the final year of the horizon, which segments score highest, and what
-- is actually driving each score? A ranking without its drivers cannot be argued with, and a
-- recommendation that cannot be argued with will not survive a leadership review.
--
-- Expected shape: 8 rows, one per segment, ordered by opportunity score descending. Columns:
-- rank, segment, recommendation, score, and the seven weighted factor contributions, plus the
-- single largest contributor named.

SELECT
    s.rank_in_year,
    d.segment_name,
    d.recommendation,
    ROUND(s.opportunity_score, 1)                       AS opportunity_score,
    ROUND(s.contrib_serviceable_market_size, 1)         AS c_serviceable_market,
    ROUND(s.contrib_cagr, 1)                            AS c_cagr,
    ROUND(s.contrib_design_services_addressability, 1)  AS c_addressability,
    ROUND(s.contrib_strategic_fit, 1)                   AS c_strategic_fit,
    ROUND(s.contrib_customer_demand, 1)                 AS c_customer_demand,
    ROUND(s.contrib_competitive_intensity, 1)           AS c_uncrowdedness,
    ROUND(s.contrib_entry_feasibility, 1)               AS c_entry_feasibility,
    CASE MAX(
        s.contrib_serviceable_market_size,
        s.contrib_cagr,
        s.contrib_design_services_addressability,
        s.contrib_strategic_fit,
        s.contrib_customer_demand,
        s.contrib_competitive_intensity,
        s.contrib_entry_feasibility
    )
        WHEN s.contrib_serviceable_market_size        THEN 'Serviceable market'
        WHEN s.contrib_cagr                           THEN 'CAGR'
        WHEN s.contrib_design_services_addressability THEN 'Addressability'
        WHEN s.contrib_strategic_fit                  THEN 'Strategic fit'
        WHEN s.contrib_customer_demand                THEN 'Customer demand'
        WHEN s.contrib_competitive_intensity          THEN 'Low crowding'
        ELSE 'Entry feasibility'
    END AS largest_driver
FROM fact_opportunity_score AS s
JOIN dim_segment AS d ON d.segment_id = s.segment_id
WHERE s.year = 2030
ORDER BY s.rank_in_year;
