# Interacting responsibly with Wikimedia Phabricator

The rules that change what you *do* on `phabricator.wikimedia.org` — a gate, not a policy
anthology. Volatile policy text is linked, not copied. Read this before **any** write:
commenting, creating or editing a task, changing status/priority, attaching a file, or
automating anything.

## 0. Default: read-only, unauthenticated

- **Do not file, comment, edit, claim, assign or re-prioritise a task on someone's behalf.**
  Produce the draft — task body, reproduction steps, evidence — and hand it to the human, who
  posts it from their own account.
- Reading needs no credential: task GETs and `phabricator.wikimedia.org/transactions/raw/{PHID}/`
  work anonymously. Anonymous Conduit returning `ERR-INVALID-SESSION` is expected, not a bug.
- Writing needs an identity that owns the action: the human's own account, or a registered bot
  (§6) — never a borrowed token, and never "just this once" from a personal account.
- Everything posted is public, permanent and attributable.

## 1. Account model (only matters when a human sets one up)

One Phabricator username per Wikimedia SUL / developer (LDAP) account — mixing them creates
duplicate accounts that cannot be merged. Email is required and invisible; access-control
fields are visible only to members of `#acl*security`.

## 2. Etiquette: the rules that gate writes

- **AI/LLM-assisted reports:** *"Carefully review your AI- or LLM-assisted report. When creating
  and submitting a task or a comment, you are fully responsible for its content. Your text must
  be accurate, factually correct, and represent your own understanding of the topic."* Verify
  every claim, number and task ID before anything is posted.
- **"Only manually assign a task to someone if they have given their prior agreement."**
- **"Report status and priority fields summarise and *reflect* *reality* and do *not* cause
  it."** When in doubt, do not change them — comment with the case instead.
- **"Act in public"**: technical detail belongs in the task itself (security excepted).
- Search before filing; one issue per task; no "me too" comments — subscribe instead.
- Use `@username`s, not real names; prefer mentions/subscriptions/Herald over mass pings.
- If someone else breaches these: contact them first (be informative, be catalytic), and only
  then ping a Phabricator administrator in `#wikimedia-releng`.

## 3. Conduct

Phabricator is covered by the Code of Conduct for Wikimedia technical spaces (2017). Reports to
`techconduct@wikimedia.org`; using the CoC system for anything else — retaliation, for example —
is itself a violation.

## 4. Privacy

- No confidential material in tasks, comments or pastes: no IP addresses, emails, tokens, session
  data, credentials, or NDA-covered material — cite the source and the access route instead.
- **Uploaded files are private until they are attached** — attaching publishes them to everyone
  who can see the task. Scrub before attaching.
- Never quote, screenshot or paraphrase a restricted task (`acl*security`, `PermanentlyPrivate`)
  into a public space.

## 5. Security issues are never public tasks

Report via `security@wikimedia.org` or the "Report Security Issue" form
(`phab:maniphest/task/edit/form/75/`); Wikimedia expects coordinated disclosure. On the admin
side: "Protect as security issue" is the correct transform, only `acl*` projects may serve as
access lists, and **adding a CC user grants that user access**.

## 6. Bot accounts

Automation needs a **registered bot**, never a personal account used repetitively — "in the human
case they would almost universally be considered spam", and such an account can be disabled.
Request one in `#Phabricator-Bot-Requests` with a name, purpose, unique email and the responsible
user; an admin creates the bot, records the human owner in its description and hands over the
Conduit token in a restricted paste.

## 7. Two read-side traps worth knowing

- The **search UI is JavaScript-only**: the public HTML of `/maniphest/` and the global search
  contains **zero** task IDs, so scraping the HTML finds nothing. Use the rendered DOM, a general
  web search, or Gerrit's `bug:T12345` reverse lookup — Conduit search needs a token.
- `phabricator.wikimedia.org/transactions/raw/{PHID}/` returns comment text as plain text; the
  PHIDs (`PHID-XACT-TASK-…`) sit in the task page's Javelin init data.

Pacing and User-Agent requirements: see `wikimedia-api-access`.

## 8. Pre-flight checklist before ANY write

1. Does a task already exist? (search first — duplicates are the commonest breach)
2. Is it a **security** issue? → `security@wikimedia.org`, stop.
3. Any confidential data — IPs, emails, tokens, credentials, NDA material? → remove it.
4. One issue per task? Specific title? Correct project tag?
5. About to assign someone or change status/priority? → don't; comment with the case.
6. AI/LLM-assisted text: has every claim, figure and task ID been verified?
7. Posted from the right identity, with the human's go-ahead on record?

## 9. Automated access to Phabricator

Under the Robot policy's "other resources" rule (Gerrit, GitLab, Phabricator): **concurrency of at
most 1, at least 1 second between requests, and a pause of at least 15 minutes after any 5xx.**
The full policy picture — including the WMCS/Toolforge exemption and escalation routes — is in
`wikimedia-api-access`.

## Sources (all read 2026-09-17)

Etiquette `https://www.mediawiki.org/wiki/Bug_management/Phabricator_etiquette` · Conduct
`https://www.mediawiki.org/wiki/Code_of_Conduct` · Security
`https://www.mediawiki.org/wiki/Reporting_security_bugs` · Bots
`https://www.mediawiki.org/wiki/Phabricator/Bots` · Robot policy
`https://wikitech.wikimedia.org/wiki/Robot_policy` · Filing and confidential-data warning
`https://www.mediawiki.org/wiki/How_to_report_a_bug`
