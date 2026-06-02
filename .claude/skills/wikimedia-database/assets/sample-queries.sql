-- Sample SQL Queries for Wikimedia Replicas
-- Run against database names ending in _p (e.g., enwiki_p)
-- 
-- Usage:
--   mysql -h 127.0.0.1 -P 3307 -u u12345 -p enwiki_p < sample-queries.sql
-- Or use: ./scripts/query.sh "SELECT ..."

-- ═══════════════════════════════════════════════════════════
-- 1. BASIC PAGE INFO
-- ═══════════════════════════════════════════════════════════

-- Get page metadata by title
SELECT page_id, page_title, page_len, page_touched, page_is_redirect
FROM page
WHERE page_title = 'Albert_Einstein' AND page_namespace = 0;

-- Search pages by title prefix
SELECT page_id, page_title, page_len
FROM page
WHERE page_title LIKE 'Python%' AND page_namespace = 0
ORDER BY page_len DESC
LIMIT 20;

-- ═══════════════════════════════════════════════════════════
-- 2. PAGE STATS
-- ═══════════════════════════════════════════════════════════

-- Largest articles on Wikipedia
SELECT page_title, page_len
FROM page
WHERE page_namespace = 0 AND page_is_redirect = 0
ORDER BY page_len DESC
LIMIT 25;

-- Longest articles by word count (approximate)
SELECT page_title, ROUND(page_len / 5) AS approx_words
FROM page
WHERE page_namespace = 0 AND page_is_redirect = 0
ORDER BY page_len DESC
LIMIT 25;

-- Smallest non-redirect articles (stubs)
SELECT page_title, page_len
FROM page
WHERE page_namespace = 0 AND page_is_redirect = 0 AND page_len > 0
ORDER BY page_len ASC
LIMIT 25;

-- ═══════════════════════════════════════════════════════════
-- 3. CATEGORY EXPLORATION
-- ═══════════════════════════════════════════════════════════

-- All pages in a category
SELECT p.page_title, p.page_len
FROM categorylinks cl
JOIN page p ON cl.cl_from = p.page_id
WHERE cl.cl_to = 'Physics'
  AND p.page_namespace = 0
ORDER BY p.page_len DESC
LIMIT 50;

-- Count of pages per category (top categories)
SELECT cl_to AS category, COUNT(*) AS page_count
FROM categorylinks
JOIN page ON cl_from = page_id
WHERE page_namespace = 0
GROUP BY cl_to
ORDER BY page_count DESC
LIMIT 50;

-- Subcategories of a given category
SELECT p.page_title AS subcategory
FROM categorylinks cl
JOIN page p ON cl.cl_from = p.page_id
WHERE cl.cl_to = 'Physics'
  AND p.page_namespace = 14  -- Category namespace
ORDER BY p.page_title;

-- Categories a specific page belongs to
SELECT cl_to AS category
FROM categorylinks
WHERE cl_from = (SELECT page_id FROM page WHERE page_title = 'Albert_Einstein' AND page_namespace = 0)
ORDER BY cl_to;

-- ═══════════════════════════════════════════════════════════
-- 4. PAGEVIEW DATA (via page_props)
-- ═══════════════════════════════════════════════════════════

-- Most viewed pages in a category
SELECT p.page_title, CAST(pp.pp_value AS UNSIGNED) AS avg_daily_views
FROM categorylinks cl
JOIN page p ON cl.cl_from = p.page_id
JOIN page_props pp ON pp.pp_page = p.page_id
WHERE cl.cl_to = 'Physics'
  AND p.page_namespace = 0
  AND pp.pp_propname = 'pageview_daily_average'
ORDER BY avg_daily_views DESC
LIMIT 25;

-- Most viewed pages overall across entire Wikipedia
SELECT p.page_title, CAST(pp.pp_value AS UNSIGNED) AS avg_daily_views
FROM page p
JOIN page_props pp ON pp.pp_page = p.page_id
WHERE p.page_namespace = 0
  AND p.page_is_redirect = 0
  AND pp.pp_propname = 'pageview_daily_average'
ORDER BY avg_daily_views DESC
LIMIT 100;

-- Pages with higher-than-average pageviews in a category
SELECT p.page_title, CAST(pp.pp_value AS UNSIGNED) AS avg_daily_views
FROM categorylinks cl
JOIN page p ON cl.cl_from = p.page_id
JOIN page_props pp ON pp.pp_page = p.page_id
WHERE cl.cl_to = 'Biology'
  AND p.page_namespace = 0
  AND pp.pp_propname = 'pageview_daily_average'
  AND CAST(pp.pp_value AS UNSIGNED) > 5000
ORDER BY avg_daily_views DESC;

-- ═══════════════════════════════════════════════════════════
-- 5. WIKIDATA INTEGRATION
-- ═══════════════════════════════════════════════════════════

-- Get Wikidata Q-IDs for pages in a category
SELECT p.page_title, pp.pp_value AS wikidata_qid
FROM categorylinks cl
JOIN page p ON cl.cl_from = p.page_id
JOIN page_props pp ON pp.pp_page = p.page_id
WHERE cl.cl_to = 'Physics'
  AND p.page_namespace = 0
  AND pp.pp_propname = 'wikibase_item'
ORDER BY p.page_title;

-- Pages that do NOT have a Wikidata item linked
SELECT p.page_title
FROM categorylinks cl
JOIN page p ON cl.cl_from = p.page_id
LEFT JOIN page_props pp ON pp.pp_page = p.page_id AND pp.pp_propname = 'wikibase_item'
WHERE cl.cl_to = 'Uncategorized_pages'
  AND p.page_namespace = 0
  AND pp.pp_page IS NULL
LIMIT 50;

-- ═══════════════════════════════════════════════════════════
-- 6. REVISION HISTORY
-- ═══════════════════════════════════════════════════════════

-- Most recently edited pages
SELECT p.page_title, MAX(r.rev_timestamp) AS last_edit
FROM revision r
JOIN page p ON r.rev_page = p.page_id
WHERE p.page_namespace = 0
GROUP BY p.page_title
ORDER BY last_edit DESC
LIMIT 25;

-- Pages with the most revisions (most frequently edited)
SELECT p.page_title, COUNT(*) AS revision_count
FROM revision r
JOIN page p ON r.rev_page = p.page_id
WHERE p.page_namespace = 0
GROUP BY p.page_title
ORDER BY revision_count DESC
LIMIT 25;

-- Pages that haven't been edited in the longest time
SELECT p.page_title, MAX(r.rev_timestamp) AS last_edit
FROM revision r
JOIN page p ON r.rev_page = p.page_id
WHERE p.page_namespace = 0 AND p.page_is_redirect = 0
GROUP BY p.page_title
HAVING last_edit < '20100101000000'
ORDER BY last_edit ASC
LIMIT 25;

-- ═══════════════════════════════════════════════════════════
-- 7. LINKS & BACKLINKS
-- ═══════════════════════════════════════════════════════════

-- Count of incoming links to a page
SELECT COUNT(*) AS incoming_links
FROM pagelinks
WHERE pl_title = 'Albert_Einstein' AND pl_namespace = 0;

-- Pages with the most incoming links (most linked-to)
SELECT pl_title AS page_title, COUNT(*) AS incoming_links
FROM pagelinks
WHERE pl_namespace = 0
GROUP BY pl_title
ORDER BY incoming_links DESC
LIMIT 25;

-- Orphaned pages: pages with no incoming links
SELECT p.page_title
FROM page p
LEFT JOIN pagelinks pl ON pl.pl_title = p.page_title AND pl.pl_namespace = 0
WHERE p.page_namespace = 0
  AND p.page_is_redirect = 0
  AND pl.pl_title IS NULL
LIMIT 25;

-- ═══════════════════════════════════════════════════════════
-- 8. CROSS-REFERENCE QUERIES
-- ═══════════════════════════════════════════════════════════

-- Most viewed pages that are in multiple categories
SELECT p.page_title,
       CAST(pp.pp_value AS UNSIGNED) AS avg_daily_views,
       COUNT(DISTINCT cl.cl_to) AS category_count
FROM page p
JOIN page_props pp ON pp.pp_page = p.page_id AND pp.pp_propname = 'pageview_daily_average'
JOIN categorylinks cl ON cl.cl_from = p.page_id
WHERE p.page_namespace = 0 AND p.page_is_redirect = 0
GROUP BY p.page_id
HAVING category_count > 5
ORDER BY avg_daily_views DESC
LIMIT 25;

-- Large articles with few pageviews (possibly neglected important topics)
SELECT p.page_title,
       p.page_len,
       CAST(pp.pp_value AS UNSIGNED) AS avg_daily_views
FROM page p
JOIN page_props pp ON pp.pp_page = p.page_id AND pp.pp_propname = 'pageview_daily_average'
WHERE p.page_namespace = 0
  AND p.page_is_redirect = 0
  AND p.page_len > 50000
ORDER BY avg_daily_views ASC
LIMIT 25;

-- ═══════════════════════════════════════════════════════════
-- 9. USER ACTIVITY
-- ═══════════════════════════════════════════════════════════

-- Most active editors on enwiki (last 30 days)
SELECT a.actor_name, COUNT(*) AS edits_last_30_days
FROM revision_userindex r
JOIN actor a ON r.rev_actor = a.actor_id
WHERE r.rev_timestamp >= DATE_FORMAT(DATE_SUB(NOW(), INTERVAL 30 DAY), '%Y%m%d%H%i%S')
GROUP BY a.actor_name
ORDER BY edits_last_30_days DESC
LIMIT 25;

-- ═══════════════════════════════════════════════════════════
-- 10. UTILITIES
-- ═══════════════════════════════════════════════════════════

-- Count total pages, articles, and redirects on enwiki
SELECT
  COUNT(*) AS total_pages,
  SUM(CASE WHEN page_namespace = 0 AND page_is_redirect = 0 THEN 1 ELSE 0 END) AS articles,
  SUM(CASE WHEN page_is_redirect = 1 THEN 1 ELSE 0 END) AS redirects
FROM page;

-- Database size info (approximate)
SELECT table_name, ROUND(((data_length + index_length) / 1024 / 1024), 2) AS size_mb
FROM information_schema.TABLES
WHERE table_schema = DATABASE()
ORDER BY size_mb DESC
LIMIT 20;
