# EventStreams Schema Reference

Quick-field lookup for all available event streams. Schemas live at https://schema.wikimedia.org.

## `mediawiki/recentchange` (v1.0.1)

**Stream names:** `mediawiki.recentchange`, `recentchange`

| Field | Type | Description | Example |
|---|---|---|---|
| `$schema` | string | Schema URI | `/mediawiki/recentchange/1.0.1` |
| `meta.domain` | string | Domain of the wiki | `en.wikipedia.org` |
| `meta.dt` | string (ISO-8601) | Event timestamp | `2024-06-04T21:00:00Z` |
| `meta.id` | string | Unique event UUID | `a1b2c3d4-...` |
| `meta.stream` | string | Stream name | `mediawiki.recentchange` |
| `meta.uri` | string | Event URI | `https://en.wikipedia.org/wiki/Page` |
| `meta.partition` | integer | Kafka partition | `0` |
| `meta.offset` | integer | Kafka offset (or timestamp in multi-DC) | `4000957901` |
| `title` | string | Full page name (prefixed) | `Albert Einstein` |
| `type` | string | Event type: `edit`/`new`/`log`/`categorize`/`external` | `edit` |
| `bot` | boolean | Was this a bot edit? | `false` |
| `comment` | string | Edit summary / log comment | `/* lede */ fixed typo` |
| `id` | integer | Recentchanges ID (rcid) | `123456789` |
| `length.new` | integer | New page length in bytes | `84721` |
| `length.old` | integer | Old page length | `84650` |
| `minor` | boolean | Minor edit flag | `false` |
| `namespace` | integer | Namespace ID (-1 for Special) | `0` |
| `patrolled` | boolean | Is patrolled? (if patrol enabled) | `true` |
| `revision.new` | integer | New revision ID | `123456789` |
| `revision.old` | integer | Old revision ID | `123456788` |
| `server_name` | string | `$wgServerName` | `en.wikipedia.org` |
| `server_script_path` | string | `$wgScriptPath` | `/w` |
| `server_url` | string | `$wgCanonicalServer` | `https://en.wikipedia.org` |
| `timestamp` | integer | Unix timestamp | `1717540800` |
| `user` | string | Username or IP | `ExampleEditor` |
| `wiki` | string | wfWikiID | `enwiki` |
| `parsedcomment` | string | HTML-parsed comment (optional) | `<p>comment</p>` |
| `log_action` | string/null | Log action (type=`log`) | `delete` |
| `log_type` | string/null | Log type (type=`log`) | `delete` |
| `log_id` | integer/null | Log entry ID | `null` |

## `mediawiki/revision/create`

**Stream names:** `mediawiki.revision-create`, `revision-create`

| Field | Type | Description |
|---|---|---|
| `page_id` | integer | Page ID |
| `page_title` | string | Page title |
| `page_namespace` | integer | Namespace ID |
| `rev_id` | integer | Revision ID |
| `user` | string | Editor username |
| `bot` | boolean | Bot flag |
| `comment` | string | Edit summary |
| `meta` | object | Standard meta block (domain, dt, id, stream) |

## `mediawiki/page/delete`

**Stream names:** `mediawiki.page-delete`, `page-delete`

| Field | Type | Description |
|---|---|---|
| `page_id` | integer | Deleted page ID |
| `page_title` | string | Deleted page title |
| `page_namespace` | integer | Namespace ID |
| `rev_id` | integer | ID of last revision before deletion |
| `suppressed` | boolean | Was the deletion suppressed (oversight)? |
| `user` | string | Deleting user |
| `comment` | string | Deletion reason |
| `meta` | object | Standard meta block |

## `mediawiki/page/move`

**Stream names:** `mediawiki.page-move`, `page-move`

| Field | Type | Description |
|---|---|---|
| `page_id` | integer | Page ID |
| `page_title` | string | Old title |
| `page_namespace` | integer | Old namespace ID |
| `new_title` | string | New title |
| `new_namespace` | integer | New namespace ID |
| `suppressed_redirect` | boolean | Was redirect suppressed? |
| `user` | string | Moving user |
| `comment` | string | Move reason |
| `meta` | object | Standard meta block |

## `mediawiki/page/links-change`

**Stream names:** `mediawiki.page-links-change`, `page-links-change`

| Field | Type | Description |
|---|---|---|
| `page_id` | integer | Page ID |
| `page_title` | string | Page title |
| `page_namespace` | integer | Namespace ID |
| `added_links` | array | Array of {page_id, page_title, page_namespace} added |
| `removed_links` | array | Array of {page_id, page_title, page_namespace} removed |
| `meta` | object | Standard meta block |

## Machine Learning Prediction Streams

**Stream names:** `mediawiki.page_outlink_topic_prediction_change.v1`, `mediawiki.page_revert_risk_prediction_change.v1`, etc.

These carry ML model prediction scores for pages. The schema is `mediawiki/page/prediction_classification_change` and includes fields like `page_id`, `page_title`, `page_namespace`, `predictions` (map of label→score), and `model_name`.

## Common `wiki` Values for Filtering

| Wiki | `wiki` value | `server_name` |
|---|---|---|
| English Wikipedia | `enwiki` | `en.wikipedia.org` |
| Simple English Wikipedia | `simplewiki` | `simple.wikipedia.org` |
| German Wikipedia | `dewiki` | `de.wikipedia.org` |
| French Wikipedia | `frwiki` | `fr.wikipedia.org` |
| Spanish Wikipedia | `eswiki` | `es.wikipedia.org` |
| Japanese Wikipedia | `jawiki` | `ja.wikipedia.org` |
| Wikimedia Commons | `commonswiki` | `commons.wikimedia.org` |
| Wikidata | `wikidatawiki` | `www.wikidata.org` |
| MediaWiki wiki | `mediawikiwiki` | `www.mediawiki.org` |
| Meta-Wiki | `metawiki` | `meta.wikimedia.org` |
| Wikitech | `wikitech` | `wikitech.wikimedia.org` |

Pattern: `<language><project>wiki` for language-specific projects, `<project>wiki` for multi-language projects.
