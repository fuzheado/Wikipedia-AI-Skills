---
name: wikimedia-phabricator
description: Navigate Wikimedia's Phabricator instance — search tasks, interpret task status and project tags, file bug reports, and track WMF development priorities
license: MIT
compatibility: opencode
last_verified: 2026-06-12
---

> **When to use this skill:** A user asks why a Wikipedia feature behaves a certain way, whether a bug is known, whether something is being worked on, or wants to report a problem. **Phabricator is the canonical place to check** — it is the WMF's centralized task tracker for all software bugs, feature requests, and project planning across MediaWiki, Wikimedia apps, and Toolforge.

---

## SOP: What Phabricator Is

Wikimedia's **[Phabricator instance](https://phabricator.wikimedia.org)** is the project management and bug tracking system for the entire Wikimedia movement. Every software task — from a DiscussionTools bug to a Toolforge infrastructure request to a mobile app feature — lives here as a **task** (identified by `T` + number, e.g. `T409297`).

Key differences from MediaWiki wikis:
- Phabricator is NOT MediaWiki — it's a different platform with its own query language and interface
- Tasks are not "pages" you edit — they have structured fields (status, priority, project tags, subscribers)
- Anyone with a Wikimedia account can log in and comment, but filing good tasks follows conventions

---

## SOP: Searching Phabricator

### Basic Search (URL)

The quickest way to find a specific task is by URL:
```
https://phabricator.wikimedia.org/T12345
```

### Text Search (Top-right search box)

Accepts free-text queries and returns tasks whose title or description matches. Good for: "talk page usability improvements", "DiscussionTools mobile bug".

### Advanced Search (Maniphest)

Use the **Maniphest** search interface at `https://phabricator.wikimedia.org/maniphest/` for structured queries. Key query language:

| Pattern | Example | What It Finds |
|---------|---------|---------------|
| `project:(name)` | `project:(Editing-Talk)` | Tasks in a specific project |
| `is:open` | `is:open` | Open tasks (not Resolved/Closed) |
| `is:stalled` | `is:stalled` | Tasks blocked or waiting |
| `@username` | `@ppelberg` | Tasks assigned to or mentioned by a user |
| `#tag` | `#DiscussionTools` | Tasks tagged with a hashtag |
| `!project` | Tasks NOT in a project |
| `priority:high` | High-priority tasks |
| `subtype:epic` | Epic tasks (containers for sub-tasks) |

Combine them: `project:(Editing-Talk) is:open priority:high`

### Finding Tasks from a Phabricator URL Reference

When you have a task number like `T346108` from a skill or documentation page:
1. Navigate directly: `https://phabricator.wikimedia.org/T346108`
2. Read the task description for what the task is about
3. Check **status** (top of page)
4. Check **project tags** (right sidebar) for related work
5. Scroll to **comments** for discussion and status updates
6. Check **parent tasks** and **subtasks** (right sidebar) for task hierarchy

---

## SOP: Understanding Task Status

The task status tells you what stage a piece of work is in. This is the single most important thing to check when researching "is this being worked on?"

| Status | Meaning | When You See This |
|--------|---------|-------------------|
| **Open, Needs Triage** | Recently filed, not yet reviewed by the team | New bug reports, fresh feature requests |
| **Open, Needs Triage Public** | Visible to all (default for public tasks) | Same as above |
| **Open** | Reviewed and accepted — needs work | Someone is actively working on it or it's prioritized |
| **Stalled** | Blocked — waiting on another task, decision, or resource | Check comments for what's blocking it |
| **Resolved** | Work is complete | The fix/feature was delivered |
| **Closed** | No further action planned | May have been declined, superseded, or completed long ago |
| **Declined** | Decision not to do this | Check comments for the rationale |

### What "Open, Needs Triage" Actually Means

The project we looked at in this research, T409297 (English Wikipedia Phase 6 deployment), shows `Open, Needs Triage` — which means it's been created and acknowledged but hasn't yet been assigned or actively scheduled. This does NOT mean work has stopped; it means the task is waiting in the queue for the team to scope and schedule.

---

## SOP: Understanding Project Tags

Tasks are organized by **project tags** (shown in the right sidebar). These let you find related work.

### Common Project Tags

| Tag | Used By | Examples |
|-----|---------|----------|
| `#Editing-Talk` | Talk pages project, DiscussionTools | Reply Tool, Usability Improvements, Topic Subscriptions |
| `#DiscussionTools` | The DiscussionTools extension itself | Bug reports, feature requests for the tool |
| `#MediaWiki-General` | Core MediaWiki platform | API changes, infrastructure, performance |
| `#Toolforge` | Toolforge infrastructure | Tool hosting, database access, Kubernetes |
| `#Community-Health` | Anti-harassment, UCoC, moderation tools | Detox, incident reporting |
| `#Mobile-Web` | Mobile web experience | Mobile talk pages, mobile editing |
| `#StructuredDiscussions` | Flow / Structured Discussions (deprecating) | Migration tooling |
| `#WMDE-Engineering` | Wikimedia Deutschland engineering | Wikidata-related development |

### Finding Related Tasks

To find all tasks in a project: navigate to `https://phabricator.wikimedia.org/project/profile/N/` where N is the project ID, or use the search:

```
project:(Editing-Talk) is:open
```

### Task Hierarchy

Tasks can have relationships:

- **Parent task** (Epic): A larger project that contains sub-tasks. Epic tasks often have `subtype:epic` and a `#epic-` tag.
- **Subtasks**: Individual pieces of work within an epic. Each has its own T number and status.
- **Related tasks**: Tasks that are conceptually related but not hierarchical.
- **Depends on**: Task A cannot be completed until Task B is done.

When researching a project, always check the subtask list to understand scope. The epic task may be `Resolved` while individual subtasks are still `Open`.

---

## SOP: Filing a Bug Report

If a user reports a problem with a Wikimedia tool or feature, Phabricator is the right place to file it. But follow these conventions:

### Before Filing

1. **Search first** — Phabricator has a lot of duplicate tasks. Search for your issue before creating a new one
2. **Check if it's a known issue** — look for existing tasks with similar keywords
3. **If you find an existing task** — add a comment with your reproduction case rather than creating a duplicate

### What a Good Task Includes

```
**Title:** Short, specific description of the problem
**Example:** "Reply Tool inserts extra blank line when replying on mobile"

**Description:**
- **Steps to reproduce:** (numbered, starting from a known state)
  1. Open any article talk page on mobile web (e.g. Talk:Example)
  2. Click [ reply ] on the first comment
  3. Type a short message
  4. Click Publish

- **Expected behavior:** What should happen
  Comment appears with proper formatting, no extra blank lines.

- **Actual behavior:** What actually happens
  An extra blank line appears between the previous comment and the new one.

- **Environment:**  
  Browser/version: Chrome 125, iOS Safari 18  
  Skin: MinervaNeue (mobile)  
  Wiki: English Wikipedia  
  Account: Logged in

- **Screenshots/recordings:** (if applicable, attach to the task)

- **Related tasks:** (if you found anything similar)
```

### Project Tags

Tag the task with the relevant project so it reaches the right team. If unsure, add a comment asking for triage rather than guessing.

### Conventions to Know

| Rule | Why |
|------|-----|
| **No "me too" comments** | +1 comments without new information clutter the task. Instead, use the "Subscribe" button (subscribers are listed in the sidebar) |
| **Security issues go to security@** | Do NOT file security vulnerabilities as public tasks. Email `security@wikimedia.org` instead |
| **Bug reports on live tools may go elsewhere first** | For Toolforge-specific issues, check with the tool maintainer before filing a Phabricator task |
| **One issue per task** | Don't list multiple unrelated bugs in one task |
| **Use parent tasks for scope** | If filing a feature request that's part of a larger effort, link to the parent epic |

---

## SOP: Tracking What's in Development

To answer "is X being worked on?":

1. **Search** for tasks related to X (by keyword or project tag)
2. **Check status** of top results
3. **Look for epic tasks** with `subtype:epic` — these organize workstreams
4. **Check comments** on epic tasks — they often contain links to quarterly planning docs
5. **Check task dates** — tasks that went silent for 6+ months may be stalled even if not tagged as such

Example workflow (using the Talk pages research from this session):

```
Goal: Find out if section-level watchlisting is deployed

1. Search phabricator for "topic subscription" or "section watchlist"
2. Find T263820 (manual topic subscriptions) and T263819 (automatic)
3. Check status → both Resolved
4. Check parent epic → T263820 is subtask of #Editing-Talk
5. Conclusion: feature was built and deployed. Now check the talk page
   skill or mediawiki.org for end-user documentation.
```

---

## Relationship to Other Skills

- **wikimedia-toolforge** — Toolforge infrastructure tasks on Phabricator; this skill helps find them
- **wikipedia-error-handling** — Known API bugs and error conditions are tracked in Phabricator; this skill helps verify whether a 429/403 behavior is a known issue
- **wikimedia-api-access** — API feature requests and bug reports go through Phabricator
- **All skills that reference specific tasks** — Use this skill to look up referenced tasks and understand their current status (e.g. checking whether a deprecation noted in a skill is still in progress)

---

## Quick Reference Card

```
╔══════════════════════════════════════════════════════════════╗
║              Phabricator Quick Reference                     ║
╠══════════════════════════════════════════════════════════════╣
║ URL:         https://phabricator.wikimedia.org               ║
║ Task format: T12345                                          ║
║                                                              ║
║ SEARCH                                                        ║
║   project:(Editing-Talk) is:open      — open tasks in project ║
║   #DiscussionTools                    — hashtag search        ║
║   @username                           — user-related tasks   ║
║   subtype:epic                        — epic/umbrella tasks  ║
║   priority:high                       — priority filter      ║
║                                                              ║
║ TASK STATUSES                                                 ║
║   Needs Triage  →  Open  →  Resolved (work complete)          ║
║                        →  Stalled (blocked)                   ║
║                        →  Declined (won't do)                 ║
║                                                              ║
║ DO: search first, subscribe instead of +1                    ║
║ DON'T: file security bugs publicly, create duplicates        ║
╚══════════════════════════════════════════════════════════════╝
```
