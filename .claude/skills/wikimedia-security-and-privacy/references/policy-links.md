# Wikimedia Security & Privacy — Policy References

Quick-reference links to official Wikimedia policies and guidelines relevant
to tool development.

---

## Core Policies

| Document | URL | Relevance |
|----------|-----|-----------|
| **Privacy Policy** | [wmf:Privacy policy](https://foundation.wikimedia.org/wiki/Policy:Privacy_policy) | Governs collection, use, and handling of user data by all tools and services |
| **Terms of Use** | [wmf:Terms of Use](https://foundation.wikimedia.org/wiki/Policy:Terms_of_Use) | Section 4 covers refraining from certain activities, including disclosure of personal information |
| **Data Retention Guidelines** | [meta:Data retention guidelines](https://meta.wikimedia.org/wiki/Data_retention_guidelines) | Specifies how long different data types should be retained (IPs: 90 days max, etc.) |
| **User-Agent Policy** | [foundation:User-Agent policy](https://foundation.wikimedia.org/wiki/Policy:Wikimedia_Foundation_User-Agent_Policy) | All API clients must send a descriptive User-Agent header |

## Security Guidelines

| Document | URL | Relevance |
|----------|-----|-----------|
| **Security for developers** | [wikitech:Security](https://wikitech.wikimedia.org/wiki/Security) | General security best practices for Wikimedia developers |
| **OAuth app guidelines** | [meta:OAuth app guidelines](https://meta.wikimedia.org/wiki/OAuth_app_guidelines) | Requirements for OAuth consumer registration and operation |
| **Bot policy** | [enwiki:Wikipedia:Bot policy](https://en.wikipedia.org/wiki/Wikipedia:Bot_policy) | Rules for automated editing, including permission requirements |
| **AbuseFilter** | [mw:Extension:AbuseFilter](https://www.mediawiki.org/wiki/Extension:AbuseFilter) | Documentation on how AbuseFilter rules work and what they return |

## Privacy Guidance

| Document | URL | Relevance |
|----------|-----|-----------|
| **Toolforge privacy policy** | [wikitech:Portal:Toolforge/Privacy](https://wikitech.wikimedia.org/wiki/Portal:Toolforge/Privacy) | Privacy requirements for tools hosted on Toolforge |
| **Access to nonpublic data** | [meta:Access to nonpublic personal data policy](https://meta.wikimedia.org/wiki/Access_to_nonpublic_personal_data_policy) | Who can access nonpublic data and under what conditions |
| **Suppression policy** | [meta:Suppression](https://meta.wikimedia.org/wiki/Suppression) | What suppressed revisions are and how they're handled |

## Technical References

| Document | URL | Relevance |
|----------|-----|-----------|
| **API:Deleted revisions** | [mw:API:Deletedrevisions](https://www.mediawiki.org/wiki/API:Deletedrevisions) | How to (and when not to) access deleted revisions |
| **API:Userinfo** | [mw:API:Userinfo](https://www.mediawiki.org/wiki/API:Userinfo) | Fields returned by the userinfo module — know which are sensitive |
| **API:Blocks** | [mw:API:Blocks](https://www.mediawiki.org/wiki/API:Blocks) | How to check block status and block information |
| **Manual:Revision delete** | [mw:Manual:RevisionDelete](https://www.mediawiki.org/wiki/Manual:RevisionDelete) | How revision visibility/deletion works internally |

---

## Quick Reference: What's Public vs Private

| Data Point | Public? | Notes |
|------------|---------|-------|
| Username | ✅ Public | Appears in page history, recent changes |
| Edit count | ✅ Public | Shown on user pages and API |
| User ID | ⚠️ Semi-public | Can be used to track users across renames |
| Registration date | ⚠️ Semi-public | Visible in preferences, available via API |
| Email address | ❌ Private | Only visible to users who have enabled email contact; never expose |
| Real name | ❌ Private | Only shown if user explicitly provided it; never expose |
| IP address | ❌ Private | Stored temporarily in toolforge logs; never store or expose |
| Block reason | ⚠️ Context-dependent | May contain private information; avoid exposing |
| Suppressed revision content | ❌ Private | Not visible to non-oversight users |
| Deleted revision content | ⚠️ Conditional | Visible to admins; must check visibility flags before display |
