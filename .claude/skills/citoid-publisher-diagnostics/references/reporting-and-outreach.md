# Reporting, outreach and authoritative references

## Compact diagnostic report

Lead with the answer to the user's actual question. Use this structure:

```text
Question: Is citation metadata accessible for the tested publisher articles?
Measured: [UTC start/end], [network locations], [endpoint and format]
Sample: [N real articles], [hosts/routes], [selection method]

Access verdict: non-Wayback metadata / archive-only / wrong-page response /
                failed / mixed / insufficient evidence
Freshness: new-article test / cache may remain / origin-log confirmation
Trigger: confirmed UA differential / network difference suspected / unresolved
Attribution: confirmed by operator / consistent with fingerprint / unknown
Confidence and limitations: [specific evidence, not a bare confidence score]

URL | production HTTP/error | provenance and returned article |
local baseline/Citoid/Zotero result | interpretation

Metadata quality (separate): [authors/date/type defects, if relevant]
Recommended next action: [smallest evidence-based fix or discriminating test]
Evidence artifacts: [reviewed relative paths]
```

Use confidence words precisely:

- **Observed:** a directly measured response under the recorded conditions.
- **Consistent with:** a hypothesis fits the measurements but alternatives remain.
- **Confirmed:** logs, a controlled change, or an operator identifies the cause.
- **Not established:** the available evidence cannot support the claim.

Avoid "blocked" as an unexplained catch-all. State "Citoid returned a load failure for 2/2 current articles; the responsible layer is unknown" when that is all the evidence shows.

For before/after reports, preserve both raw runs, endpoint format, exact inputs, archive provenance and controls. Explicitly distinguish code merged, configuration deployed and production retested. Include contradictory samples. Correct earlier findings in place rather than silently carrying a stale publisher-status list forward.

## Allowlisting facts

Read the current [official allowlisting guidance](https://wikitech.wikimedia.org/wiki/Citoid/Allowlisting) before drafting any request. As reviewed on **7 November 2026**, it documents:

| Property | Documented value |
|---|---|
| Stable UA identifier 1 | `Citoid/WMF` |
| Stable UA identifier 2 | `ZoteroTranslationServer/WMF` |
| IPv4 egress range | `208.80.152.0/22` |
| IPv6 egress range | `2620:0:860::/46` |
| Technical contact | `noc@wikimedia.org` |

Link the page rather than promising the ranges or browser prefix will never change. Do not substitute all Wikimedia AS ranges or Toolforge addresses. A local request bearing one of these identifiers is not authenticated Wikimedia traffic.

Recommend the publisher's documented, source-verified exception mechanism for the restrictive rule. Avoid prescribing a universal WAF expression or a bypass of all security checks. Ask for the UA and official source network to be considered together where the product supports that. The publisher should retain appropriate rate limits and unrelated protections.

Cloudflare/Akamai bot registration is normally a bot-operator activity; a publisher can still correct its own rule. Do not assert that registration guarantees access across every customer or that it explains any given success. A vendor header identifies infrastructure, not the decision that denied a request.

For forward-confirmed reverse DNS, verify the **actual request source**: PTR lookup followed by A/AAAA resolution back to the same address. Do not assume every unused IP within a published range has a PTR. Request operator confirmation when needed; do not turn a few sampled addresses into a guarantee for an entire pool.

## Outreach draft

Prepare but do not send without authorization. Replace bracketed fields, use only reviewed public evidence, and keep access and metadata-quality requests separate.

> Subject: Citation metadata requests failing for [publisher/host]
>
> Wikimedia's Citoid service retrieves citation metadata when editors add references. On [UTC date/time], requests for [two exact public article URLs] returned [precise production error or challenge]. [Describe a controlled differential only if measured.] The responsible rule is [unknown / confirmed by specific evidence]; use of a particular CDN alone does not identify it.
>
> Could your technical team check the corresponding request/WAF logs and confirm the rule and action? Please consult Wikimedia's current allowlisting documentation for both stable service identifiers, `Citoid/WMF` and `ZoteroTranslationServer/WMF`, and the published IPv4/IPv6 source ranges. The browser-looking portion can change, so matching a frozen full UA may be brittle. The Wikimedia technical contact is `noc@wikimedia.org`.
>
> We are asking for citation metadata access, not a subscription bypass. After a rule change, we can retest the same URLs and fresh articles, distinguishing live/non-Wayback metadata from archived or cached results.
>
> This message was drafted by an AI agent (OpenHands) on behalf of [name].

If source networking is only suspected, say so; request logs rather than declaring an IP block. Provide request IDs when available, but redact cookies, tokens and personal addresses. Do not include private correspondence or whole publisher pages in public reports.

## Public sources and where to verify claims

### Service behavior and identity

- [Citoid documentation](https://www.mediawiki.org/wiki/Citoid): service overview and links to the API.
- [Citoid API documentation](https://www.mediawiki.org/wiki/Citoid/API): citation endpoint and output formats.
- [Citoid/Allowlisting](https://wikitech.wikimedia.org/wiki/Citoid/Allowlisting): official stable identifiers, contact and egress ranges.
- [Citoid source](https://gerrit.wikimedia.org/r/plugins/gitiles/mediawiki/services/citoid/): inspect redirect discovery (`lib/utils/unshorten.js`), HTTP request helpers, cache and Wayback behavior at the revision under investigation.
- [Deployment charts](https://gerrit.wikimedia.org/r/plugins/gitiles/operations/deployment-charts/): inspect `charts/citoid/templates/_config.yaml`; a public mirror is also available on GitHub under `wikimedia/operations-deployment-charts`.
- [WMF Zotero service repository](https://gitlab.wikimedia.org/repos/mediawiki/services/zotero): inspect deployment-specific `config/production.json5` and release history rather than assuming the upstream default.
- [Citoid UA task T442971](https://phabricator.wikimedia.org/T442971): historical deployment-UA investigation; recheck current task/deployment state before citing it as unresolved.
- [Publisher outreach task T439327](https://phabricator.wikimedia.org/T439327): public coordination history, not a definitive live blocklist.

### Extraction versus access

- [Zotero translators](https://github.com/zotero/translators): check current targets, embedded metadata and site-specific extraction.
- [Zotero translation server](https://github.com/zotero/translation-server): distinguish server-side behavior from an interactive browser connector.

When a result has correct article metadata but missing/wrong fields, compare the raw source with the deployed translator and endpoint format. A local translator test or generic JSON-LD helper improvement does not prove that production Citoid has deployed it. Prefer fixing an existing translator or shared extractor when appropriate; do not create redundant site-specific code simply because JSON-LD exists.

### Attribution and change tracking

- [nginx blocklist PR 679](https://github.com/mitchellkrogza/nginx-ultimate-bad-bot-blocker/pull/679): historical source correction; check downstream regeneration and site deployment independently.
- [Anubis source](https://github.com/TecharoHQ/anubis): examine the relevant version's crawler policies and policy loading/order, not just the product's presence.

For future investigations, cite immutable revisions or dated raw responses for material technical claims. Keep the skill's methodology stable while refreshing dated facts only after verification. Do not publish a private evidence path as if readers can verify it; label a historical case as a summarized observation when its raw data is not public.
