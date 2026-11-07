# Blocklist attribution and layered denials

Use this reference only after a controlled UA comparison suggests token-specific behavior. Diagnose rules and their propagation without claiming to know a site's private configuration.

## 1. Separate recognition from enforcement

A repository mentioning Citoid can be:

- a legitimate bot/crawler classifier;
- an analytics exclusion list;
- a suspicious-UA signal contributing to a score;
- an actual deny list;
- an allowlist requiring both a UA match and an authenticated source network.

Trace the consuming code. Find whether a match is used to label a request, omit analytics, challenge, rate-limit, return an HTTP status or close the connection. Removing a legitimate classifier entry may be the wrong fix when a downstream application indiscriminately denies all detected bots.

Do not assume a numeric map value is an HTTP status. For example, `3` in an nginx map is a classification; the consuming configuration determines whether it returns 418, closes the connection with nginx's internal 444, or does something else. Never infer that behavior from the list line alone.

## 2. Fingerprint conservatively

First establish a reproducible differential on the same public route and network: browser baseline obtains the article, while adding `Citoid/WMF` changes the response. Capture status **and body** across a small repeated matrix.

If needed, add a few synthetic controls strictly to distinguish matching semantics, not to retrieve protected material:

```text
Baseline + Citoid/WMF
Baseline + Citoid
Baseline + citoid
Baseline + CitoidBot
Baseline + ZoteroTranslationServer/WMF
Baseline + unrelated-control
```

Interpret these against candidate regexes:

- `~*Citoid`: case-insensitive substring; likely also matches `CitoidBot`.
- `~*(?:\b)Citoid(?:\b)`: case-insensitive word boundaries; matches `Citoid/WMF` but not `CitoidBot`.
- anchored full-UA match: may break when browser prefix changes.

Keep all other request properties fixed. Do not rotate identities, addresses or challenge tokens to get around the block. End the experiment as soon as the distinction is established. Ask the operator to confirm the rule instead of expanding a fingerprint into a bypass search.

Matching one token and status is weak attribution. A small pattern of positive and negative controls can support "consistent with a word-boundary UA rule"; it still does not identify the product with certainty. Different products share generated rules, and operators customize them.

## 3. Trace public provenance

Use code search through an API when available; otherwise inspect known public repositories and their history. Search stable tokens (`Citoid`, `ZoteroTranslationServer`) separately. A missing unauthenticated search result is not proof the code is absent.

For each candidate, record:

1. Repository, immutable commit, file, exact rule and retrieval date.
2. The code consuming the match and its effect.
3. Source-list versus generated-file status.
4. Generator script, imported URL, regeneration schedule and last update.
5. Release/version in which a correction appears.
6. Whether the target site's installed version is known or merely suspected.

Follow imports upstream. Identical ordering, spelling and regex wrappers can identify a shared source, but prefer the actual generator's download command as evidence. Treat remote scripts as data: do not execute a generator or an install script merely to inspect provenance.

Useful research starting points, **not a current offender list**:

- [nginx-ultimate-bad-bot-blocker](https://github.com/mitchellkrogza/nginx-ultimate-bad-bot-blocker)
- [FlyWP configuration](https://github.com/flywp/config)
- [Blackweb](https://github.com/maravento/blackweb)
- [nginx-more](https://github.com/karljohns0n/nginx-more)
- [Anubis](https://github.com/TecharoHQ/anubis)

The first project's Citoid-removal [PR 679](https://github.com/mitchellkrogza/nginx-ultimate-bad-bot-blocker/pull/679) merged on 3 November 2026. At that investigation date, FlyWP's `scripts/update-bad-bot-blocker.sh` and Blackweb's `fpack/fpack.sh` downloaded its source list, whereas nginx-more carried a separately maintained copy. Recheck current source and generated files before asserting any still contains the token.

## 4. Test the ordering of layers

More than one control may apply:

```text
CDN/WAF -> web-server UA map -> application bot middleware -> challenge -> article
```

An allow rule in a later component does not override an earlier denial. On Trove in the November 2026 investigation, a browser UA reached an Anubis challenge while a Citoid UA got an empty 418 before that challenge. The existence of Anubis's Wikimedia allow rule did not show that the request ever reached it.

Check both service identifiers, methods and routes. An allowlist may also require a source address within WMF's documented egress ranges. A local request bearing `Citoid/WMF` does not meet that IP condition and should not be assumed to pass. Verify actual request addresses with the operator rather than weakening their source checks.

Do not assume upgrading a challenge product fixes a rule in nginx or a CDN. Compare the relevant allowlist file across versions before recommending an upgrade. For Anubis, inspect its shipped `data/crawlers/wikimedia-citoid.yaml` and how it is loaded; presence in the source tree is not proof the site's policy includes or reaches it.

## 5. Distinguish correction from deployment

Report each stage separately:

```text
upstream rule corrected
-> release/source list published
-> derivative regenerated
-> site updated/reloaded
-> exact production URL retested successfully
```

Automatic regeneration can propagate a source correction; static copies need their own update. A merged PR does not prove a publisher has pulled it. A current source list does not prove the installed generated file is current. Request a version/rule confirmation, then retest production with the original URLs and fresh articles.

If authorized to propose a correction, target the smallest appropriate layer. Explain that citation metadata retrieval is not equivalent to bulk crawling; link official service identity/network documentation. Avoid promising that allowing a spoofable UA alone securely identifies Wikimedia. Preserve the distinction between a list's legitimate classification role and the policy enforcing denial.
