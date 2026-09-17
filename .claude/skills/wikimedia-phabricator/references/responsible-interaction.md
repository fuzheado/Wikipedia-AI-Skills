# Interacting responsibly with Wikimedia Phabricator

Every rule below comes from a primary policy page (listed under **Sources**, all read 2026-09-17). Read
this **before any write action** on `phabricator.wikimedia.org` — commenting, creating a task, changing
status or priority, attaching a file, or automating anything.

## 0. Default posture for an agent: READ-ONLY, unauthenticated

- **Do not file, comment, edit, claim, assign or re-prioritise a task on a person's behalf.** Produce the
  material — a draft task body, reproduction steps, evidence — and hand it over to the human, who posts it
  under their own account (or decides not to).
- **Reading needs no credential.** Plain task GETs and the raw-transaction pages work anonymously. Anonymous
  Conduit returns `ERR-INVALID-SESSION: Session key is not present` because it is token-gated — expected
  behaviour, not a fault to debug.
- **Writing needs an identity that owns the action**: the human's own account, or a registered bot account
  (§6). Never a borrowed API token, and never "just this once" from a personal account.
- Anything posted is **public, permanent and attributable**. Treat every field, comment and attachment as a
  public statement.

## 1. Who can do what (account model)

- A Phabricator account is linked to a **Wikimedia SUL (unified login)** or a **Wikimedia developer/LDAP
  account**; there is no separate Phabricator password. A valid, verified email address is required and is
  **not visible** to other users.
- **Connect only one SUL/developer account to a single Phabricator username** — mixing them creates
  duplicate accounts that cannot be merged.
- Access-control fields on protected tasks are editable only by members of the **`#acl*security`** group.
- When you link accounts, other users can see the connection between the account and your wiki identity:
  assume the linkage is public.

## 2. Etiquette

`Bug management/Phabricator etiquette` is the operative document. The load-bearing rules, quoted:

- **"Act in public. Unless you are reporting a security issue or you were asked to email somebody with
  specific information, place all technical information relating to a bug report in the report itself."**
- **Search first.** Duplicates are the most common etiquette breach. If a task exists, add your
  reproduction case as a comment instead of filing a new one. One issue per task.
- **No "me too" comments, no votes, no "Fix this now".** Subscribe to the task (subscribers are listed in
  the sidebar) or use a mention if a specific person has to act.
- **"Only manually assign a task to someone if they have given their prior agreement."** What gets worked
  on is the developers' and product managers' call.
- **"Report status and priority fields summarise and *reflect* *reality* and do *not* cause it."** When in
  doubt **do not change** status or priority — comment with your reasoning and let the owners decide.
- Raising a priority needs **evidence that it affects normal, everyday work significantly**. Contrived
  examples and unlikely-circumstance problems are generally evidence for **low** priority.
- The fastest route to a fix is to **provide a patch**.
- **"Prefer using Phabricator usernames (e.g. @username) over a person's real name or other personal
  identifiers"** — both for privacy and to avoid confusion.
- Use notification features (mentions, subscriptions, Herald rules) rather than pinging everyone.
- **AI/LLM-assisted reports:** *"Carefully review your AI- or LLM-assisted report. When creating and
  submitting a task or a comment, you are fully responsible for its content. Your text must be accurate,
  factually correct, and represent your own understanding of the topic."* This is a policy rule, not a
  stylistic preference: verify every claim, number and task ID before anything is posted.
- If someone else is breaching these guidelines: **contact them first** (private email for minor cases,
  in public for major ones, to avoid ambiguity), and be **informative** (say what they did and why it is a
  problem) and **catalytic** (say what to do instead). Persistent disregard → ping a Phabricator
  administrator in **#wikimedia-releng** on IRC.

## 3. Conduct policies that bind Phabricator

- The **Code of Conduct for Wikimedia technical spaces** (approved 2017) names `phabricator.wikimedia.org`
  explicitly, alongside Wikitech, Gerrit, the mailing lists, IRC and Etherpad. It commits to a
  "respectful and harassment-free experience for everyone".
- **Unacceptable behaviour includes**: harassment; "inappropriate or unwanted publication of private
  communication"; publishing personally identifying information; and **using the code-of-conduct system for
  anything other than reporting genuine violations** (for example retaliating against a reporter).
- **Reporting a problem**: contact the **Code of Conduct Committee at techconduct@wikimedia.org** (or a
  designated event contact). A report can be as short as a notification with a link.

## 4. Privacy and data handling

- Do **not** paste confidential material into tasks, comments or pastes: no logs containing IP addresses,
  email addresses, access tokens, session identifiers or credentials. `How to report a bug` says to make
  sure that "no confidential data is included or shown" when attaching logs or screenshots.
- **Uploaded files are private until they are attached** to a task; attaching makes them visible to
  everyone who can see that task. Scrub **before** attaching. If the material genuinely needs protection,
  Phabricator is the wrong channel.
- Do not republish material covered by a non-disclosure agreement (internal analytics tables, private logs,
  restricted data-lake extracts). Cite the source and the access route instead of pasting the data.
- Restricted tasks (`acl*security`, and the `PermanentlyPrivate` project which marks a task as never
  becoming public): do not screenshot, quote or paraphrase their contents into public spaces.

## 5. Security issues are never public tasks

- Report via **security@wikimedia.org** or the **"Report Security Issue"** form
  (`phab:maniphest/task/edit/form/75/`). Wikimedia supports **coordinated/responsible disclosure** and
  expects "discretion and forbearance".
- Out of scope: plain source-code disclosures (the code is open source) unless a password or auth key is
  involved.
- On the administration side: **"Protect as security issue"** is the correct transform for converting a
  normal task into a security task; only `acl*` projects may serve as access lists; and adding a CC user to
  a protected task **grants that user access** — never do it casually.

## 6. Bot accounts

`Phabricator/Bots` defines a bot as "users in Phabricator for whom actions are automated or are a
consequence of the actions of multiple users"; much of the general Wikimedia bot policy applies.

- **A personal account must not be used for repetitive or automated activity** — "in the human case they
  would almost universally be considered spam", and an account that looks like spam may be **disabled or
  deleted**. If that account was also someone's personal account, they lose the ability to explain.
- Bot accounts are **created natively in Phabricator** (they are not tied to SUL/LDAP). Request one by
  creating a task in the **#Phabricator-Bot-Requests** project stating: **name, purpose, a unique email
  address (it may be invalid, but must be unique), and the responsible user or organisation**.
- An administrator then creates the bot user, **adds the human owner to the bot account description for
  transparency**, generates a **Conduit API token** and delivers it in a **paste whose view policy is the
  human owner plus the admin**. The requester closes the request once it works. `arc` is configured with an
  `.arcrc` pointing at `phabricator.wikimedia.org/api/`.
- Practical consequence: agent-driven automation needs a **registered bot with a named human owner** — not
  a token minted from someone's personal account.

## 7. Read-side techniques that need no authentication

1. `https://phabricator.wikimedia.org/T12345` — plain GET; works for public tasks and their comments.
2. `phabricator.wikimedia.org/transactions/raw/{PHID}/` — returns comment text as plain text. PHIDs
   (`PHID-XACT-TASK-…`) are embedded in the task page's Javelin init data.
3. **The search UI is JavaScript-only** — the public HTML of `/maniphest/` and the global search contains
   **zero** task IDs, so HTML scraping finds nothing. To *find* tasks, use browser automation (rendered
   DOM), a general web search, or Gerrit's `bug:T12345` reverse lookup; Conduit search needs a token
   (§6).
4. Keep request rates low, identify the client with a descriptive `User-Agent` per the WMF User-Agent
   policy, and prefer one bulk read over a crawl — see the Robot policy limits in §9.

## 8. Pre-flight checklist before ANY write

1. Does a task for this already exist? (search first — duplicates are the commonest breach)
2. Is it a **security** issue? → email `security@wikimedia.org` or use form/75, and stop.
3. Does the text contain confidential data — IPs, emails, tokens, credentials, NDA material? → remove it.
4. One issue per task? Specific title? Correct project tag (or an explicit request for triage)?
5. Am I about to assign someone or change status/priority? → don't; comment with the case instead.
6. If any part is AI/LLM-assisted: has every factual claim, task ID and figure been verified, and does the
   text represent my own understanding? If not, it does not get posted.
7. Is this being posted from the right identity — the human's own account, or a registered bot with a named
   owner — with the human's explicit go-ahead on record?

## 9. Automated access to Phabricator specifically

The Wikimedia **Robot policy** covers "Gerrit, GitLab, Phabricator, and other wikimedia.org services":

- **Total concurrency of at most 1**, with **at least 1 second between requests**.
- **Pause crawling for at least 15 minutes if you receive a 5xx status code.**

Related rules that apply to any Wikimedia activity, Phabricator included: consider whether **dumps** are
more efficient than live requests; identify the client accurately via `User-Agent` per the WMF User-Agent
policy; honour `robots.txt`; respect `429` and its `Retry-After` header; the limits are **global across
Wikimedia properties** rather than per-domain, and bots in **Toolforge/WMCS are explicitly exempt** (WMF
still reserves the right to throttle anything that threatens stability). Bots that repeatedly work around
the guidelines or the limits **may be blocked**. For genuinely high-volume needs, the documented routes are
authenticating (OAuth 2.0 preferred) with a community bot flag, running in WMCS, using Wikimedia
Enterprise, or asking `bot-traffic@wikimedia.org`. See the **wikimedia-api-access** skill for the full
rate-limit picture.

## Sources

- Etiquette: `https://www.mediawiki.org/wiki/Bug_management/Phabricator_etiquette`
- Conduct (names Phabricator explicitly): `https://www.mediawiki.org/wiki/Code_of_Conduct`
- Security reporting and disclosure: `https://www.mediawiki.org/wiki/Reporting_security_bugs`
- Bot accounts: `https://www.mediawiki.org/wiki/Phabricator/Bots`
- Robot policy (incl. "other resources"): `https://wikitech.wikimedia.org/wiki/Robot_policy`
- Filing guidance and the confidential-data warning: `https://www.mediawiki.org/wiki/How_to_report_a_bug`
