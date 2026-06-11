# OAuth Endpoints Reference

All Wikimedia OAuth endpoints, organized by authentication method.

---

## OAuth 2.0 Endpoints

OAuth 2.0 endpoints live under the wiki's REST API (`rest.php`).

| Endpoint | URL | Method | Purpose |
|----------|-----|--------|---------|
| Authorize | `https://meta.wikimedia.org/rest.php/oauth2/authorize` | GET | Redirect user here for authorization |
| Access Token | `https://meta.wikimedia.org/rest.php/oauth2/access_token` | POST | Exchange code for token, or refresh token |
| Profile | `https://meta.wikimedia.org/rest.php/oauth2/resource/profile` | GET | Get authenticated user's identity |

### Per-Wiki Endpoints

Replace `meta.wikimedia.org` with any wiki's domain for wiki-specific consumers.
Most public tools use **meta** (central) consumers so they work across all wikis.

| Wiki | REST Base |
|------|-----------|
| Meta (central) | `https://meta.wikimedia.org/rest.php/oauth2` |
| English Wikipedia | `https://en.wikipedia.org/rest.php/oauth2` |
| Commons | `https://commons.wikimedia.org/rest.php/oauth2` |
| Wikidata | `https://www.wikidata.org/rest.php/oauth2` |
| Beta cluster | `https://meta.wikimedia.beta.wmflabs.org/rest.php/oauth2` |

### Access Token Response

```json
{
    "access_token": "eyJhbGciOiJSUzI1NiIs...",
    "token_type": "Bearer",
    "expires_in": 3600,
    "refresh_token": "rft_abc123def456..."
}
```

### Profile Response

```json
{
    "sub": 12345,
    "username": "ExampleUser",
    "editcount": 1500,
    "confirmed_email": true,
    "blocked": false,
    "registered": "2020-01-15T00:00:00Z",
    "groups": ["*", "user", "autoconfirmed"],
    "rights": ["read", "edit", "createpage", "upload", "move"],
    "realname": "Example",
    "email": "user@example.com"
}
```

The `realname` and `email` fields only appear if the consumer was granted
those permissions and the user authorized them.

---

## OAuth 1.0a Endpoints

OAuth 1.0a endpoints are wiki pages under `Special:OAuth`.

| Purpose | URL | Method | Signed? | Signed With |
|---------|-----|--------|---------|-------------|
| Initiate (request token) | `https://meta.wikimedia.org/w/index.php?title=Special:OAuth/initiate` | GET | ✅ Yes | Consumer token/secret only |
| Authorize (user redirect) | `https://meta.wikimedia.org/w/index.php?title=Special:OAuth/authorize` | GET | ❌ No | Query params (oauth_consumer_key, oauth_token) |
| Token (access token) | `https://meta.wikimedia.org/w/index.php?title=Special:OAuth/token` | GET | ✅ Yes | Consumer + request token/secret |
| Identify (JWT) | `https://meta.wikimedia.org/w/index.php?title=Special:OAuth/identify` | GET | ✅ Yes | Consumer + access token/secret |

**Important:** All signed OAuth 1.0a requests to `Special:OAuth/*` must include
`title` as a signed parameter (e.g., `title=Special:OAuth/initiate`).

---

## Bot Password Endpoints

Bot passwords use the standard `action=login` API, **not** OAuth endpoints.

| Purpose | URL | Method |
|---------|-----|--------|
| Login token | `https://en.wikipedia.org/w/api.php?action=query&meta=tokens&type=login` | GET |
| Login | `https://en.wikipedia.org/w/api.php?action=login` | POST |
| CSRF token | `https://en.wikipedia.org/w/api.php?action=query&meta=tokens&type=csrf` | GET |
| Edit | `https://en.wikipedia.org/w/api.php?action=edit` | POST |

---

## Consumer Registration

| Purpose | URL |
|---------|-----|
| Propose new consumer | `https://meta.wikimedia.org/wiki/Special:OAuthConsumerRegistration/propose` |
| List consumers | `https://meta.wikimedia.org/wiki/Special:OAuthListConsumers` |
| Manage my consumers | `https://meta.wikimedia.org/wiki/Special:OAuthManageMyConsumers` |
| Bot passwords (per wiki) | `https://en.wikipedia.org/wiki/Special:BotPasswords` |

---

## Rate Limits by Auth Method

| Auth Method | Anonymous | Logged In | Bot Flag |
|-------------|-----------|-----------|----------|
| No auth (read-only) | 500 req/s per IP | — | — |
| `action=login` (user) | — | Standard user limit | — |
| Bot password | — | Standard user limit | ✅ Higher limit |
| OAuth (any version) | — | OAuth flag | ✅ Higher limit |

Bot passwords and OAuth consumers automatically get bot-like rate limits when
created with grants that include `High-volume text querying` or similar.

---

## Testing on Beta

Before deploying to production, test OAuth flows on the beta cluster:

| Resource | URL |
|----------|-----|
| Beta meta | `https://meta.wikimedia.beta.wmflabs.org` |
| Beta consumer registration | `https://meta.wikimedia.beta.wmflabs.org/wiki/Special:OAuthConsumerRegistration/propose` |
| Beta Wikipedia | `https://en.wikipedia.beta.wmflabs.org` |
