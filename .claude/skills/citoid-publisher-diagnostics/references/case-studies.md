# Dated case studies: lessons, not current publisher status

These cases summarize October-November 2026 investigations. Use them to choose discriminating tests, not to assert that a publisher is still blocked. Recheck current behavior. Treat reconstructed hypotheses as weaker evidence than logs or controlled tests.

## Trove/NLA: two stacked gates, not one

**Observed, 3 November 2026:** repeated direct requests gave browser-like UAs HTTP 200 containing an Anubis "Making sure you're not a bot" challenge. Adding Citoid produced HTTP 418 with an empty body; the translation-server identifier reached the challenge. Citoid-looking token variants were consistent with a case-insensitive word-boundary rule rather than a simple substring rule.

**Interpretation:** a Citoid-specific denial precedes the challenge. Anubis's public Wikimedia rule also depends on WMF source networks; a local spoofed UA would not satisfy that condition. Presence of the allow rule therefore does not demonstrate that production reaches or passes it.

**Provenance:** public FlyWP/Blackweb generator scripts imported nginx-ultimate-bad-bot-blocker's UA source list. The nginx upstream removed Citoid in PR 679 on 3 November. This does not prove NLA's exact installed product or that its site regenerated/reloaded anything that day.

**Cache trap:** some old URLs returned metadata while novel URLs failed. The successful metadata did not establish fresh origin access; some was incomplete, and a challenge title had itself been extracted. An HTTP 200 from either endpoint could be misleading.

**Generalize:** inspect bodies and rule order; distinguish a fingerprint from installation proof; retest publisher deployment separately from upstream merges.

## People Inc.: network effects cannot be reduced to a UA story

**Observed, late October 2026:** People/EW examples returned real articles from the workstation with both browser and Citoid UAs, while production Citoid failed. A separate Toolforge run saw different responses again. Some large error bodies were initially overinterpreted as real pages and required inspection of actual article signals.

**Interpretation:** the local UA comparison did not demonstrate a UA-only denial. Source network, client behavior, and other request differences remained plausible. Toolforge and production were not interchangeable.

**Generalize:** request publisher-side logs and include official egress documentation in outreach; do not recommend only a token exception based on an unproven UA theory. Do not infer article access from body size, nor extend a few domains' findings to every brand in a publisher group.

## Roularta: a 200 login page is not successful retrieval

**Observed, 31 October 2026:** direct requests to Knack/Le Vif returned HTTP 200 with a small Onegini login page for multiple UAs. An earlier status-only interpretation had said there was no problem.

**Correction:** the returned page was not the requested publication content. The finding established a login/access wall, not its precise network or vendor trigger.

**Generalize:** compare final URL, title, canonical link, article heading and metadata. A status-only availability check is insufficient.

## Sveriges Radio: preserve the original failing paths

**Historical evidence located:** October records contained failing legacy `/cgi-bin/...` links; a 31 October production test failed for query-bearing `/ekot?cb=...` variants. A homepage had also succeeded in an earlier matrix, so access was never uniformly failing in the located evidence.

**Retest, 5-6 November investigation:** current `/artikel/...` routes and plain `/ekot` returned metadata, but the exact legacy links and exact earlier query-bearing URLs still failed using the same `zotero` endpoint format.

**Correction:** those observations do not demonstrate a clean same-URL blocked-to-working transition. They cannot date an unblock or attribute one to a CDN registration. Old routes, query handling, redirects, cache and path-specific rules remained possible distinctions. No September record was located; that is not proof none existed.

**Generalize:** use like-for-like comparisons; report missing evidence rather than inventing a transition date. Keep current article access separate from remaining author/date or translator-target issues.

## News UK and Telegraph: access and causality are separate questions

**News UK, 5 November 2026:** sampled current Times articles returned actual titles and other article metadata instead of the earlier "Verifying Device" interstitial. Many still lacked publication dates, while some Sun-family responses credited numeric identifiers rather than journalists.

**Interpretation:** access was available on the samples; date/byline extraction was a translator/generic-metadata concern, not a reason to keep asserting a publisher wall. Existing metadata fields can be present but wrong.

**Telegraph:** early-November records still showed failures; later samples returned article metadata. The publisher had been contacted directly and allowlisted Citoid. Do not reattribute that success to a separate Akamai registration merely because the site uses Akamai.

**Generalize:** separate observed change from cause. Preserve operator-confirmed interventions and do not infer causation from a broader vendor program or coincident date.

## Broad CDN-associated audit: headers do not establish a rule

**Observed, 5-6 November investigation:** dozens of domains associated with a CDN showed mixed results. Some current articles returned rich metadata; others failed; some old positives were Wayback fallback. A malformed Sky hostname and old ABS-CBN URLs returning a homepage needed exclusion from article-success claims.

**Interpretation:** neither CDN association nor a Citoid failure proved which component or rule caused denial. Domain-level link counts also did not equal affected citations or failing article counts.

**Generalize:** keep raw per-URL provenance and sample sizes; separate archived, wrong-page and non-Wayback outcomes. Treat publisher ownership, vendor relationship and actual rule attribution as independent evidence questions.

## Zenodo, DOI and metadata type: access can work while extraction is wrong

**Observed, 3 November 2026:** Zenodo record URLs returned titles, dates, abstracts and identifiers, but varied resource types were repeatedly classified as `journalArticle`. The DOI path returned different metadata. Some single-field creators were institutions, not lost personal names.

**Interpretation:** metadata quality/type handling required investigation; publisher bot blocking was not established. An identifier-based API path can work independently of HTML retrieval, and organization credits must not be judged using a personal-name parser.

**Generalize:** compare retrieval paths explicitly. Inspect existing translators and embedded metadata before proposing a new translator or an allowlist request.

## Service configuration: do not freeze a historical UA mismatch

**Observed, late October:** translation-server deployment moved to a newer Chrome-looking prefix while Citoid still used Chrome/110. An operator-visible request capture and public deployment configuration helped localize the difference. Searching only the Citoid application source had missed the value injected by the chart.

**Rechecked, 7 November 2026:** the official allowlisting page and public Citoid chart both document Chrome/156 for Citoid; the official page documents the same prefix for the translation server. The old mismatch must not be published as a current fact.

**Generalize:** trace application defaults, deployment charts and actual requests separately. Match stable `Citoid/WMF` and `ZoteroTranslationServer/WMF` identifiers for durable policy guidance; re-observe deployed prefixes when testing a version-dependent rule.
