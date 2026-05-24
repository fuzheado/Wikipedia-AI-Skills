-- Sample SQL Queries for Wikipedia Page Assessments
-- Run against enwiki_p (or any *_p replica with PageAssessments extension)
--
-- Usage:
--   mysql -h 127.0.0.1 -P 3307 -u u12345 -p enwiki_p < sample-queries.sql
-- Or use: ./scripts/query.sh "SELECT ..."

-- ═══════════════════════════════════════════════════════════
-- 1. PROJECT SUMMARIES
-- ═══════════════════════════════════════════════════════════

-- Quality distribution for a WikiProject
SELECT pa.pa_class, COUNT(*) AS article_count
FROM page_assessments pa
JOIN page_assessments_projects pap ON pa.pa_project_id = pap.pap_project_id
WHERE pap.pap_project_title = 'Chemistry'
GROUP BY pa.pa_class
ORDER BY FIELD(pa.pa_class, 'FA','GA','B','C','Start','Stub','List','FL','A','Book','Category','Disambig','File','Portal','Project','Redirect','Template','NA');

-- Importance distribution for a WikiProject
SELECT pa.pa_importance, COUNT(*) AS article_count
FROM page_assessments pa
JOIN page_assessments_projects pap ON pa.pa_project_id = pap.pap_project_id
WHERE pap.pap_project_title = 'Biology'
GROUP BY pa.pa_importance
ORDER BY FIELD(pa.pa_importance, 'Top','High','Mid','Low','NA','Unknown');

-- Combined quality × importance matrix
SELECT pa.pa_class, pa.pa_importance, COUNT(*) AS count
FROM page_assessments pa
JOIN page_assessments_projects pap ON pa.pa_project_id = pap.pap_project_id
WHERE pap.pap_project_title = 'Medicine'
GROUP BY pa.pa_class, pa.pa_importance
ORDER BY pa.pa_class, pa.pa_importance;

-- How many WikiProjects assess a typical article? (distribution)
SELECT assessments_per_article, COUNT(*) AS article_count
FROM (
    SELECT pa.pa_page_id, COUNT(*) AS assessments_per_article
    FROM page_assessments pa
    GROUP BY pa.pa_page_id
) AS sub
GROUP BY assessments_per_article
ORDER BY assessments_per_article;

-- ═══════════════════════════════════════════════════════════
-- 2. ARTICLE LOOKUPS
-- ═══════════════════════════════════════════════════════════

-- All assessments for a single article (with last revision timestamp)
SELECT pap.pap_project_title AS wikiproject,
       pa.pa_class,
       pa.pa_importance,
       rev.rev_timestamp AS last_assessed
FROM page_assessments pa
JOIN page_assessments_projects pap ON pa.pa_project_id = pap.pap_project_id
JOIN page p ON pa.pa_page_id = p.page_id
LEFT JOIN revision rev ON pa.pa_page_revision = rev.rev_id
WHERE p.page_title = 'Quantum_mechanics'
  AND p.page_namespace = 0;

-- Grouped: one row per article, all assessments concatenated
SELECT p.page_title,
       GROUP_CONCAT(
           DISTINCT CONCAT(pap.pap_project_title, ': ', pa.pa_class, ' / ', pa.pa_importance)
           ORDER BY pap.pap_project_title
           SEPARATOR '; '
       ) AS assessments
FROM page_assessments pa
JOIN page_assessments_projects pap ON pa.pa_project_id = pap.pap_project_id
JOIN page p ON pa.pa_page_id = p.page_id
WHERE p.page_namespace = 0
GROUP BY p.page_id, p.page_title
LIMIT 25;

-- ═══════════════════════════════════════════════════════════
-- 3. QUALITY GAPS (high-importance, low-quality)
-- ═══════════════════════════════════════════════════════════

-- Top-importance stubs that need urgent expansion
SELECT p.page_title,
       pa.pa_class,
       pa.pa_importance,
       p.page_len AS bytes
FROM page_assessments pa
JOIN page_assessments_projects pap ON pa.pa_project_id = pap.pap_project_id
JOIN page p ON pa.pa_page_id = p.page_id
WHERE pap.pap_project_title = 'Physics'
  AND p.page_namespace = 0
  AND p.page_is_redirect = 0
  AND pa.pa_class = 'Stub'
  AND pa.pa_importance = 'Top'
ORDER BY p.page_len ASC
LIMIT 20;

-- High-importance start/C-class articles (good improvement candidates)
SELECT p.page_title,
       pa.pa_class,
       pa.pa_importance,
       p.page_len AS bytes
FROM page_assessments pa
JOIN page_assessments_projects pap ON pa.pa_project_id = pap.pap_project_id
JOIN page p ON pa.pa_page_id = p.page_id
WHERE pap.pap_project_title = 'Engineering'
  AND p.page_namespace = 0
  AND p.page_is_redirect = 0
  AND pa.pa_class IN ('Start', 'C')
  AND pa.pa_importance IN ('Top', 'High')
ORDER BY pa.pa_class ASC, p.page_len ASC
LIMIT 30;

-- ═══════════════════════════════════════════════════════════
-- 4. IMPORTANCE DISTRIBUTION
-- ═══════════════════════════════════════════════════════════

-- All Top-importance articles in a project
SELECT p.page_title, pa.pa_class, pa.pa_importance
FROM page_assessments pa
JOIN page_assessments_projects pap ON pa.pa_project_id = pap.pap_project_id
JOIN page p ON pa.pa_page_id = p.page_id
WHERE pap.pap_project_title = 'History'
  AND p.page_namespace = 0
  AND p.page_is_redirect = 0
  AND pa.pa_importance = 'Top'
ORDER BY FIELD(pa.pa_class, 'FA','GA','B','C','Start','Stub') ASC
LIMIT 50;

-- ═══════════════════════════════════════════════════════════
-- 5. MULTI-PROJECT INTERSECTION
-- ═══════════════════════════════════════════════════════════

-- Articles assessed by BOTH Chemistry AND Physics WikiProjects
SELECT p.page_title
FROM page_assessments pa1
JOIN page_assessments pa2 ON pa1.pa_page_id = pa2.pa_page_id
JOIN page_assessments_projects pap1 ON pa1.pa_project_id = pap1.pap_project_id
JOIN page_assessments_projects pap2 ON pa2.pa_project_id = pap2.pap_project_id
JOIN page p ON pa1.pa_page_id = p.page_id
WHERE pap1.pap_project_title = 'Chemistry'
  AND pap2.pap_project_title = 'Physics'
  AND p.page_namespace = 0
LIMIT 25;

-- ═══════════════════════════════════════════════════════════
-- 6. MAINTENANCE & WORKFLOW
-- ═══════════════════════════════════════════════════════════

-- Articles not reassessed in over 5 years (potential quality drift)
-- Note: joins with revision table to get timestamp from pa_page_revision
SELECT p.page_title,
       pa.pa_class,
       pa.pa_importance,
       rev.rev_timestamp AS last_assessed
FROM page_assessments pa
JOIN page_assessments_projects pap ON pa.pa_project_id = pap.pap_project_id
JOIN page p ON pa.pa_page_id = p.page_id
LEFT JOIN revision rev ON pa.pa_page_revision = rev.rev_id
WHERE pap.pap_project_title = 'Computing'
  AND p.page_namespace = 0
  AND p.page_is_redirect = 0
  AND rev.rev_timestamp < '20210524000000'
ORDER BY rev.rev_timestamp ASC
LIMIT 30;

-- Articles without an assessment in a specific WikiProject
-- (Note: this requires category membership, not assessments table alone)
SELECT cl.cl_sortkey AS page_title
FROM categorylinks cl
JOIN page p ON cl.cl_from = p.page_id
LEFT JOIN page_assessments pa ON p.page_id = pa.pa_page_id
  AND pa.pa_project_id = (SELECT pap_project_id FROM page_assessments_projects WHERE pap_project_title = 'Biology')
WHERE cl.cl_to = 'WikiProject_Biology_articles'
  AND p.page_namespace = 0
  AND pa.pa_page_id IS NULL
LIMIT 25;
