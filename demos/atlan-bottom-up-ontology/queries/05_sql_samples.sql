-- =============================================================================
-- 05_sql_samples.sql — Same truth in SQL (DB.kidehen)
-- =============================================================================

-- Q1: List competing Win Rate definition claims (do NOT silently reconcile)
SELECT
  c.claim_id,
  c.definition_text,
  s.name AS source_name,
  s.system_type,
  c.confidence,
  c.valid_from,
  c.valid_to,
  c.status
FROM DB.kidehen.cc_claim AS c
JOIN DB.kidehen.cc_source AS s ON s.source_id = c.source_id
WHERE c.subject_ref = 'metric:1'
  AND c.claim_kind IN ('definition', 'metric')
ORDER BY c.confidence DESC;

-- Q2: Claims valid as-of a date (e.g. 2025-03-15) — the missing time dimension
SELECT
  c.claim_id,
  c.definition_text,
  s.name AS source_name,
  c.confidence,
  c.valid_from,
  c.valid_to
FROM DB.kidehen.cc_claim AS c
JOIN DB.kidehen.cc_source AS s ON s.source_id = c.source_id
WHERE c.subject_ref = 'metric:1'
  AND c.claim_kind = 'definition'
  AND c.valid_from <= CAST('2025-03-15' AS DATE)
  AND (c.valid_to IS NULL OR c.valid_to >= CAST('2025-03-15' AS DATE))
ORDER BY c.confidence DESC;

-- Q3a: Win rate formula A — closed-won / all closed (incl. disqualified)
SELECT
  'A: closed-won / all-closed' AS formula,
  SUM(CASE WHEN stage = 'closed-won' THEN 1 ELSE 0 END) AS wins,
  SUM(CASE WHEN stage IN ('closed-won','closed-lost','disqualified') THEN 1 ELSE 0 END) AS closed_all,
  CAST(SUM(CASE WHEN stage = 'closed-won' THEN 1 ELSE 0 END) AS DECIMAL(18,4))
    / NULLIF(SUM(CASE WHEN stage IN ('closed-won','closed-lost','disqualified') THEN 1 ELSE 0 END), 0)
    AS win_rate
FROM DB.kidehen.cc_opportunity;

-- Q3b: Win rate formula B — exclude never-qualified
SELECT
  'B: exclude never-qualified' AS formula,
  SUM(CASE WHEN stage = 'closed-won' AND reached_qualification = 1 THEN 1 ELSE 0 END) AS wins,
  SUM(CASE WHEN stage IN ('closed-won','closed-lost') AND reached_qualification = 1 THEN 1 ELSE 0 END) AS closed_qual,
  CAST(SUM(CASE WHEN stage = 'closed-won' AND reached_qualification = 1 THEN 1 ELSE 0 END) AS DECIMAL(18,4))
    / NULLIF(SUM(CASE WHEN stage IN ('closed-won','closed-lost') AND reached_qualification = 1 THEN 1 ELSE 0 END), 0)
    AS win_rate
FROM DB.kidehen.cc_opportunity;

-- Q3c: Win rate formula C — new-business only
SELECT
  'C: new-business only' AS formula,
  SUM(CASE WHEN stage = 'closed-won' AND is_new_business = 1 THEN 1 ELSE 0 END) AS wins,
  SUM(CASE WHEN stage IN ('closed-won','closed-lost') AND is_new_business = 1 THEN 1 ELSE 0 END) AS closed_nb,
  CAST(SUM(CASE WHEN stage = 'closed-won' AND is_new_business = 1 THEN 1 ELSE 0 END) AS DECIMAL(18,4))
    / NULLIF(SUM(CASE WHEN stage IN ('closed-won','closed-lost') AND is_new_business = 1 THEN 1 ELSE 0 END), 0)
    AS win_rate
FROM DB.kidehen.cc_opportunity;

-- Q4: Side-by-side three formulas (UNION) — disagreement made visible
SELECT * FROM (
  SELECT 'A: closed-won / all-closed' AS formula,
    CAST(SUM(CASE WHEN stage = 'closed-won' THEN 1 ELSE 0 END) AS DECIMAL(18,4))
      / NULLIF(SUM(CASE WHEN stage IN ('closed-won','closed-lost','disqualified') THEN 1 ELSE 0 END), 0) AS win_rate
  FROM DB.kidehen.cc_opportunity
) AS a
UNION ALL
SELECT * FROM (
  SELECT 'B: exclude never-qualified' AS formula,
    CAST(SUM(CASE WHEN stage = 'closed-won' AND reached_qualification = 1 THEN 1 ELSE 0 END) AS DECIMAL(18,4))
      / NULLIF(SUM(CASE WHEN stage IN ('closed-won','closed-lost') AND reached_qualification = 1 THEN 1 ELSE 0 END), 0) AS win_rate
  FROM DB.kidehen.cc_opportunity
) AS b
UNION ALL
SELECT * FROM (
  SELECT 'C: new-business only' AS formula,
    CAST(SUM(CASE WHEN stage = 'closed-won' AND is_new_business = 1 THEN 1 ELSE 0 END) AS DECIMAL(18,4))
      / NULLIF(SUM(CASE WHEN stage IN ('closed-won','closed-lost') AND is_new_business = 1 THEN 1 ELSE 0 END), 0) AS win_rate
  FROM DB.kidehen.cc_opportunity
) AS c;

-- Q5: Entity authority control (preferred + alt labels)
SELECT e.preferred_label, a.alt_label
FROM DB.kidehen.cc_entity AS e
LEFT JOIN DB.kidehen.cc_entity_alt_label AS a ON a.entity_id = e.entity_id
ORDER BY e.preferred_label, a.alt_label;
