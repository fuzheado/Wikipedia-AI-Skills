# OAuth Grants and Scopes Reference

When registering an OAuth consumer or creating a bot password, you select
**grants** (permissions). Each grant grants one or more user rights. Be
minimal — only request what your tool actually needs.

---

## OAuth 2.0 Grant Types

These are the grant types selectable during consumer registration.
They map to one or more MediaWiki user rights.

### Basic / Identification

| Grant | Rights Granted | Use Case |
|-------|---------------|----------|
| `Basic rights` | `read` | Reading pages, searching. Minimal grant for tools that only read. |
| `User identity verification only` | None (identity only) | Tools that just need to know who the user is (via `/resource/profile`). Cannot make API calls that modify content. |

### Editing

| Grant | Rights Granted | Use Case |
|-------|---------------|----------|
| `Edit existing pages` | `edit`, `minoredit` | Editing existing articles. Most common edit grant. |
| `Create, edit, and move pages` | `createpage`, `createtalk`, `edit`, `minoredit`, `move`, `move-rootuserpages`, `move-subpages`, `move-categorypages`, `suppressredirect`, `noratelimit` | Full page creation and management. |
| `Delete pages, revisions` | `delete`, `bigdelete`, `deletedhistory`, `deletedtext`, `browsearchive`, `undelete` | Deleting and restoring pages. Requires elevated permissions. |
| `Protect pages` | `protect` | Changing protection levels. Requires elevated permissions. |

### Community / Moderation

| Grant | Rights Granted | Use Case |
|-------|---------------|----------|
| `Block users` | `block`, `unblockself`, `ipblock-exempt` | Blocking and unblocking users. Requires elevated permissions. |
| `Rollback edits` | `rollback` | Reverting vandalism. |
| `Patrol edits` | `patrol`, `autopatrol`, `patrolmarks` | Marking pages and edits as patrolled. |

### Uploads

| Grant | Rights Granted | Use Case |
|-------|---------------|----------|
| `Upload new files` | `upload`, `reupload`, `reupload-own`, `reupload-shared` | Uploading files to Commons or local wiki. |
| `Upload, replace, and move files` | `upload`, `reupload`, `reupload-own`, `reupload-shared`, `movefile` | Full file management. |

### Administration

| Grant | Rights Granted | Use Case |
|-------|---------------|----------|
| `Manage user rights` | `userrights` | Changing user group membership. Requires high-level permissions. |

### High-Volume

| Grant | Rights Granted | Use Case |
|-------|---------------|----------|
| `High-volume text querying` | `apihighlimits` | Higher API rate limits. Add this if your tool makes many API queries. |

### Web Actions

| Grant | Rights Granted | Use Case |
|-------|---------------|----------|
| `Send email` | `sendemail` | Sending emails through the wiki interface. |
| `View deleted history and text` | `deletedhistory`, `deletedtext` | Viewing deleted revisions. Requires elevated permissions. |

---

## Typical Grant Combinations

### Read-Only Tool

```
☐ High-volume text querying
→ Rights: read, apihighlimits
```

### Edit Bot

```
☑ Edit existing pages
☑ High-volume text querying
→ Rights: edit, minoredit, apihighlimits
```

### New Page Reviewer / Patroller

```
☑ Create, edit, and move pages
☑ Patrol edits
☑ High-volume text querying
→ Rights: createpage, edit, move, patrol, apihighlimits, ...
```

### Full Admin Tool

```
☑ Create, edit, and move pages
☑ Delete pages, revisions
☑ Protect pages
☑ Block users
☑ Rollback edits
☑ High-volume text querying
→ Rights: all admin-level rights + api high limits
```
