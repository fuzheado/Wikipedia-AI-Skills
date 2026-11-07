# Branch, PR and review workflow
## Branch and identity hygiene
Locate the intended checkout and inspect status/remotes. Respect the user's designated development clone; another worktree can have stale helpers or be disconnected from their dev environment. Do not impose a personal machine's paths or create alternate translator versions.
For a new topic branch from the current upstream default branch (`master` in Zotero's translator repository); for an open PR use the current PR branch head. Fetch and compare before editing. Never blindly `reset --hard` to a remote or discard unrelated helper patches. If a branch is held by a worktree, resolve that deliberately without losing work.
Confirm the source/destination of each push: contribute through the authorized fork, not upstream master. Preserve configured author identity. Keep translator IDs and existing creator/license credit; add credit appropriately for substantive contributions.
## Focused submission
Before committing inspect git status, the complete diff and staged files. Include translator source, accurate embedded fixtures, timestamp and any justified ID retirement only. Exclude downloads, HAR files, cookies, browser profiles, local helper patches, dependencies and build artifacts. Ensure UTF-8/LF and no whole-file formatting churn.
If an ID is removed/replaced, update `deleted.txt` with the retired ID and reason, and increment its version header; verify current format. Renaming/reworking a translator while retaining the same ID does not retire it.
Create a PR only when authorized, one per topic. Check for an existing open PR before creating another. Include:
- the actual defect and representative supported page/layout/language types;
- a concise explanation of the extraction change and fallback precedence;
- exact commands, passing fixture counts and any verification limitations;
- no claim of deployed Citoid improvement until production is independently retested.
Prefer the service API/CLI for submission if authenticated. If authorization is missing, request it securely or provide a prepared compare link; do not expose tokens or misreport a pushed branch as an opened PR. Include a brief AI disclosure in AI-generated public PR text/comments.
## Review iteration
Evaluate suggestions for correctness and scope; do not blindly apply advice that loses authors, misclassifies types, changes an ID or broadens unsupported behavior. Apply sound changes to the existing file, bump the timestamp when warranted, then rerun lint and relevant fixtures.
Push only after confirming the PR remains open. Reply with the pushed commit and explain any intentionally declined suggestion. Resolve a thread after the fix is available, not before. API GraphQL review-thread queries can support replies/resolution when authorized; repository permissions and log visibility vary.
Do not embed a snapshot of current PR numbers or authentication failures in the reusable skill. Those belong in the task handoff or local memory. Keep the skill focused on repeatable procedure.
