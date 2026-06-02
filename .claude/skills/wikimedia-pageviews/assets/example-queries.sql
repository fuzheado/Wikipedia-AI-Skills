-- Pageview-related SQL queries for Wikimedia replicas
-- These use page_props.pp_propname = 'pageview_daily_average'
-- Run against database names ending in _p (e.g., enwiki_p)

-- ═══════════════════════════════════════════════════════════
-- 1. TOP PAGES IN A CATEGORY BY AVERAGE DAILY VIEWS
-- ═══════════════════════════════════════════════════════════

-- Top 50 in a category
SELECT p.page_title,
       CAST(pp.pp_value AS UNSIGNED) AS avg_daily_views
FROM page p
JOIN page_props pp ON pp.pp_page = p.page_id
JOIN categorylinks cl ON cl.cl_from = p.page_id
WHERE cl.cl_to = 'Physics'
  AND p.page_namespace = 0
  AND p.page_is_redirect = 0
  AND pp.pp_propname = 'pageview_daily_average'
ORDER BY avg_daily_views DESC
LIMIT 50;

-- ═══════════════════════════════════════════════════════════
-- 2. OVERALL MOST VIEWED PAGES
-- ═══════════════════════════════════════════════════════════

SELECT p.page_title,
       CAST(pp.pp_value AS UNSIGNED) AS avg_daily_views
FROM page p
JOIN page_props pp ON pp.pp_page = p.page_id
WHERE p.page_namespace = 0
  AND p.page_is_redirect = 0
  AND pp.pp_propname = 'pageview_daily_average'
ORDER BY avg_daily_views DESC
LIMIT 100;

-- ═══════════════════════════════════════════════════════════
-- 3. PAGES WITH NO PAGEVIEW DATA
-- ═══════════════════════════════════════════════════════════

SELECT p.page_title, p.page_len
FROM page p
LEFT JOIN page_props pp ON pp.pp_page = p.page_id
    AND pp.pp_propname = 'pageview_daily_average'
WHERE p.page_namespace = 0
  AND p.page_is_redirect = 0
  AND pp.pp_value IS NULL
LIMIT 50;

-- ═══════════════════════════════════════════════════════════
-- 4. HIGH-VOLUME PAGES IN A SPECIFIC NAMESPACE
-- ═══════════════════════════════════════════════════════════

-- Top talk pages
SELECT p.page_title,
       CAST(pp.pp_value AS UNSIGNED) AS avg_daily_views
FROM page p
JOIN page_props pp ON pp.pp_page = p.page_id
WHERE p.page_namespace = 1  -- Talk
  AND pp.pp_propname = 'pageview_daily_average'
ORDER BY avg_daily_views DESC
LIMIT 25;

-- Top Wikipedia project pages
SELECT p.page_title,
       CAST(pp.pp_value AS UNSIGNED) AS avg_daily_views
FROM page p
JOIN page_props pp ON pp.pp_page = p.page_id
WHERE p.page_namespace = 4  -- Wikipedia
  AND pp.pp_propname = 'pageview_daily_average'
ORDER BY avg_daily_views DESC
LIMIT 25;

-- ═══════════════════════════════════════════════════════════
-- 5. COMPARE POPULARITY ACROSS CATEGORIES
-- ═══════════════════════════════════════════════════════════

SELECT cl.cl_to AS category,
       COUNT(*) AS pages_with_data,
       ROUND(AVG(CAST(pp.pp_value AS UNSIGNED))) AS avg_views,
       ROUND(MAX(CAST(pp.pp_value AS UNSIGNED))) AS max_views
FROM categorylinks cl
JOIN page p ON cl.cl_from = p.page_id
JOIN page_props pp ON pp.pp_page = p.page_id
    AND pp.pp_propname = 'pageview_daily_average'
WHERE p.page_namespace = 0
  AND p.page_is_redirect = 0
GROUP BY cl.cl_to
HAVING pages_with_data > 50
ORDER BY avg_views DESC
LIMIT 25;

-- ═══════════════════════════════════════════════════════════
-- 6. FIND STUBS WITH UNEXPECTEDLY HIGH VIEWS
-- ═══════════════════════════════════════════════════════════

SELECT p.page_title,
       p.page_len,
       CAST(pp.pp_value AS UNSIGNED) AS avg_daily_views
FROM page p
JOIN page_props pp ON pp.pp_page = p.page_id
    AND pp.pp_propname = 'pageview_daily_average'
WHERE p.page_namespace = 0
  AND p.page_is_redirect = 0
  AND p.page_len < 5000  -- Stub threshold
  AND CAST(pp.pp_value AS UNSIGNED) > 1000  -- High traffic
ORDER BY avg_daily_views DESC
LIMIT 25;

-- ═══════════════════════════════════════════════════════════
-- 7. PAGES IN A CATEGORY RANKED BY VIEWS
-- ═══════════════════════════════════════════════════════════

SET @rank = 0;
SELECT @rank := @rank + 1 AS rank,
       p.page_title,
       CAST(pp.pp_value AS UNSIGNED) AS avg_daily_views
FROM page p
JOIN page_props pp ON pp.pp_page = p.page_id
JOIN categorylinks cl ON cl.cl_from = p.page_id
WHERE cl.cl_to = 'Physics'
  AND p.page_namespace = 0
  AND p.page_is_redirect = 0
  AND pp.pp_propname = 'pageview_daily_average'
ORDER BY avg_daily_views DESC
LIMIT 50;

-- ═══════════════════════════════════════════════════════════
-- 8. CROSS-REFERENCE: VIEWS VS EDITOR INTEREST
-- ═══════════════════════════════════════════════════════════

-- High-view pages with relatively few edits (possibly neglected)
SELECT p.page_title,
       CAST(pp.pp_value AS UNSIGNED) AS avg_daily_views,
       COUNT(r.rev_id) AS total_edits
FROM page p
JOIN page_props pp ON pp.pp_page = p.page_id
    AND pp.pp_propname = 'pageview_daily_average'
LEFT JOIN revision r ON r.rev_page = p.page_id
WHERE p.page_namespace = 0
  AND p.page_is_redirect = 0
GROUP BY p.page_id
HAVING total_edits < 50 AND avg_daily_views > 5000
ORDER BY avg_daily_views DESC
LIMIT 25;
