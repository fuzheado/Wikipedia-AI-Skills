# Interacting responsibly with Wikimedia Phabricator

Grounded in the primary policy pages (all read 2026-09-17). Load this **before any write action** on
phabricator.wikimedia.org — comment, task creation, status/priority change, file upload, or automation.

## 0. Default posture for this agent: READ-ONLY, unauthenticated

- **Never file, comment, edit, claim, assign, or re-prioritise a task on a user's behalf.** Produce the
  material (a draft task body, reproduction steps, evidence) and hand it over.
- Project convention: **many maintainers file their own Phabricator tasks** — hand over a draft as
  "inspiration only". Standing convention: no on-wiki/bot actions on anyone's behalf; agent work stays
  read-only and off-wiki.
- No Phabricator credential is available in this environment, and that is fine: **reading needs none** —
  plain task GETs and `/transactions/raw/{PHID}/` work anonymously. Anonymous Conduit returns
  `ERR-INVALID-SESSION: Session key is not present` (token-gated) — don't treat that as a bug.
- Automation that *does* write requires a **registered bot account** (see §5), never a personal account and
  never "just this once".

## 1. Who can do what (account model)

- Accounts connect to a **Wikimedia SUL (unified login)** or a **Wikimedia developer/LDAP account**; no
  separate Phabricator password. A valid, verified email is required and **is not visible** to others.
- **Connect only one SUL/developer account to a single Phabricator username** — mixing creates duplicate
  accounts that cannot be merged.
- Access-control fields on protected tasks are visible only to members of the **`#acl*security`** group.
- Public by default: assume everything you post is public, permanent, and attributable.

## 2. Etiquette (mw:**Bug management/Phabricator etiquette**)

The load-bearing rules, quoted:

- **"Act in public. Unless you are reporting a security issue or you were asked to email somebody with
  specific information, place all technical information relating to a bug report in the report itself."**
- **Search first**, then comment on the existing task with your reproduction case instead of filing a
  duplicate. One issue per task.
- **No "me too" / vote / "Fix this now" comments.** Subscribe (subscribers are in the sidebar) or use a
  mention if someone specifically needs to act.
- **"Only manually assign a task to someone if they have given their prior agreement."** It is up to
  developers and their product managers what they work on.
- **"Report status and priority fields summarise and *reflect* *reality* and do *not* cause it."** When in
  doubt **do not change** status/priority — add a comment suggesting the change instead.
- Priority-raising needs evidence of significant everyday-work impact; contrived or unlikely-circumstance
  problems are generally evidence for **low** priority.
- Fastest route to a fix is to **provide a patch**.
- **"Prefer using Phabricator usernames (e.g. @username) over a person's real name or other personal
  identifiers"**, for privacy and to avoid confusion.
- Use notification features (mentions, subscriptions, Herald rules) rather than mass-pinging.
- **AI/LLM-assisted reports:** *"Carefully review your AI- or LLM-assisted report. When creating and
  submitting a task or a comment, you are fully responsible for its content. Your text must be accurate,
  factually correct, and represent your own understanding of the topic."* — This is a written policy rule,
  not just good manners: verify every claim and every task ID before anything is posted.
- Handling others' breaches: contact them first (private email for minor cases, public for major to avoid
  ambiguity), "be informative" (what they did wrong, with evidence) and "be catalytic" (what to do
  instead). Persistent disregard → ping a Phabricator administrator in **#wikimedia-releng** on IRC.

## 3. Conduct policies that bind Phabricator

- **Code of Conduct for Wikimedia technical spaces** (approved 2017) explicitly covers
  `phabricator.wikimedia.org` (alongside wikitech, Gerrit, mailing lists, IRC, Etherpad). It commits to a
  "respectful and harassment-free experience for everyone".
- **Unacceptable behaviour includes**: harassment; "inappropriate or unwanted publication of private
  communication"; publishing personally identifying information; and **using the CoC system for purposes
  other than reporting genuine violations** (e.g. retaliating against a reporter).
- **Reporting**: contact the **Code of Conduct Committee at techconduct@wikimedia.org**, or a designated
  contact at an event. Reports may be a one-line notification with a link.
- The community code of conduct links both `mw:Code of Conduct` and `mw:Bug management/Phabricator
  etiquette` as the operative documents for Phabricator.

## 4. Privacy and data handling

- Don't paste confidential material into tasks, comments or pastes: no logs containing IP addresses,
  email addresses, access tokens, session data or credentials. `How to report a bug` says explicitly to
  make sure "no confidential data is included or shown" when attaching logs/screenshots.
- **Uploaded files are private until attached** — attaching them makes them visible to everyone who can
  see the task. Scrub *before* attaching; if a file needs real protection, use a more secure channel than
  Phabricator.
- Do not republish NDA/vetted material (internal analytics tables, private logs, data-lake extracts) in
  Phabricator. Cite the source and access route instead.
- For restricted tasks (`acl*security`, and the `PermanentlyPrivate` project which marks a task as never
  becoming public): don't screenshot or paraphrase restricted content into public spaces.

## 5. Security issues — never a public task

- Report via **security@wikimedia.org** or the **"Report Security Issue"** form
  (`phab:maniphest/task/edit/form/75/`). The project supports **coordinated/responsible disclosure** and
  expects "discretion and forbearance".
- Out of scope: plain source-code disclosures (our code is open source), unless a password/auth key.
- On the admin side: the **"Protect as security issue"** transform is the correct way to convert a normal
  task into a security task; only `acl*` projects may be used as access lists; adding a CC user to a
  protected task *grants them access* — so never do that casually.

## 6. Bot accounts (mw:**Phabricator/Bots**)

- Definition: Phabricator bots "are users in Phabricator for whom actions are automated or are a
  consequence of the actions of multiple users". Much of the general **Wikimedia bot policy** applies.
- **A personal account must not be used for repetitive/automated activity**: "in the human case they would
  almost universally be considered spam", and an account that looks like spam may be **disabled or
  deleted** — with no route to explain if it was also a personal account.
- Bot accounts are **created natively in Phabricator** (not tied to SUL/LDAP). Request one by creating a
  task in the **#Phabricator-Bot-Requests** project stating **name, purpose, a unique email (may be
  invalid), and the responsible user/organisation**.
- Admins then create the bot user, **add the human owner to the bot account description for transparency**,
  generate a **Conduit API token** and deliver it via a restricted paste (view policy = human owner +
  admin); the requester closes the task once it works. `arc` is configured with a `.arcrc` pointing at
  `https://phabricator.wikimedia.org/api/`.
- Practical consequence: an agent-driven automation needs a **registered bot with a named human owner** —
  not an API token borrowed from someone's personal account.

## 7. Read-side techniques that avoid auth entirely (verified in this environment)

1. `https://phabricator.wikimedia.org/T12345` — plain GET, no account (works for public tasks).
2. `https://phabricator.wikimedia.org/transactions/raw/{PHID}/` — comment text as plain text; PHIDs
   (`PHID-XACT-TASK-…`) are embedded in the task page's Javelin init data.
3. Phabricator's search UI is JS-only (public HTML contains **zero** task IDs), so for *finding* tasks use:
   browser automation, a web search, or Gerrit's `bug:T12345` reverse lookup; Conduit search is token-gated.
4. Set a descriptive `User-Agent` per the WMF UA policy and keep request rates low; prefer one bulk read
   over a crawl.

## 8. Pre-flight checklist before ANY Phabricator write

1. Is there already a task? (search — duplicates are the most common etiquette breach)
2. Is it a **security** issue? → email form/75, stop.
3. Does the body contain any confidential data, IPs, emails, tokens, or NDA material? → remove.
4. One issue per task? Title specific? Project tag correct or "please triage"?
5. Am I assigning or re-prioritising? → don't; comment instead.
6. If any part is AI/LLM-assisted: has every factual claim, task ID and number been verified, and does the
   text represent my own understanding? If not, it doesn't get posted.
7. Is this posted from the right identity (the human's own account, or a registered bot with a named
   owner) — and is the user's explicit request on record?

## 9. Automated access to Phabricator specifically (Wikitech **Robot policy**)

The Wikimedia [Robot policy](https://wikitech.wikimedia.org/wiki/Robot_policy) has a section
**"Rules for other resources: i.e. Gerrit, GitLab, Phabricator, and other wikimedia.org services"**:

- **Total concurrency of at most 1**, and **at least 1 second between requests.**
- **Pause crawling for at least 15 minutes if you receive a 5xx status code.**

The policy also states its general rules apply to "any activity on our websites", and that bots that
repeatedly circumvent these guidelines or threaten site stability **may be blocked**. Related practical
points: prefer dumps/offline collection over live requests; identify the client accurately via User-Agent
per the WMF UA policy; respect `429` + `Retry-After`; the limits are global across Wikimedia properties,
with **WMCS/Toolforge bots explicitly exempt** (though WMF reserves the right to throttle clients that
threaten stability). For genuinely high-volume needs the documented routes are OAuth 2.0 authentication
+ a community bot flag, WMCS hosting, Wikimedia Enterprise, or asking **bot-traffic@wikimedia.org**.

See also the `wikimedia-api-access` skill for the full rate-limit picture (gateway client classes,
per-surface concurrency, 429 flavours).
