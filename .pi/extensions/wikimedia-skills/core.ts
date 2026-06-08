/**
 * Core User-Agent injection logic for Wikimedia requests.
 *
 * Pure functions — no pi SDK dependency, easily testable.
 *
 * The Wikimedia Foundation User-Agent Policy requires all requests to
 * *.wikipedia.org, *.wikidata.org, *.wikimedia.org, and related domains
 * to include a descriptive User-Agent header. Requests without one, or
 * with generic agents (python-requests/x, curl/x), are blocked with
 * HTTP 403 or 429.
 *
 * @see https://foundation.wikimedia.org/wiki/Policy:Wikimedia_Foundation_User-Agent_Policy
 */

export const WIKIMEDIA_DOMAINS =
  /wikipedia\.org|wikidata\.org|wikimedia\.org|wmcloud\.org|toolforge\.org|tools\.wmflabs\.org/;

export const DEFAULT_USER_AGENT =
  "WikipediaAIAgent/1.0 (https://github.com/user/Wikipedia-AI-Skills; user@example.com) SkillsDemo";

export interface ExtensionConfig {
  userAgent: string;
  enabled: boolean;
  interceptCurl: boolean;
  interceptPython: boolean;
  interceptNode: boolean;
  interceptWget: boolean;
}

export const DEFAULT_CONFIG: ExtensionConfig = {
  userAgent: DEFAULT_USER_AGENT,
  enabled: true,
  interceptCurl: true,
  interceptPython: true,
  interceptNode: true,
  interceptWget: true,
};

/** Options passed to injectUserAgent */
export interface InjectOptions {
  userAgent: string;
  interceptCurl: boolean;
  interceptPython: boolean;
  interceptNode: boolean;
  interceptWget: boolean;
}

/**
 * Test whether a command string targets a Wikimedia domain.
 * Returns true if any Wikimedia domain appears in the command.
 */
export function targetsWikimedia(cmd: string): boolean {
  return WIKIMEDIA_DOMAINS.test(cmd);
}

/**
 * Check whether a User-Agent header is already set in a command.
 * Handles curl -H 'User-Agent: ...', wget --header='User-Agent: ...',
 * and env var WIKIMEDIA_USER_AGENT=... patterns.
 */
export function hasUserAgentAlready(cmd: string): boolean {
  // curl: -H 'User-Agent:' or -H"User-Agent:"
  if (/-H[= ]?['"]?User-Agent:/i.test(cmd)) return true;
  // wget: --header='User-Agent:' or --header="User-Agent:"
  if (/--header[= ]?['"]?User-Agent:/i.test(cmd)) return true;
  // Env var already exported
  if (/WIKIMEDIA_USER_AGENT=/.test(cmd)) return true;
  return false;
}

/**
 * Inject the WIKIMEDIA_USER_AGENT env var at the top of a shell command.
 * Used for python / node / any script-based commands.
 */
function prependEnvVar(cmd: string, ua: string): string {
  return `export WIKIMEDIA_USER_AGENT="${escapeShellArg(ua)}"\n${cmd}`;
}

/**
 * Escape a value for safe use in single-quoted shell strings.
 */
function escapeShellArg(val: string): string {
  return val.replace(/'/g, "'\\''");
}

/**
 * Interpret line continuations (trailing backslash) so piped multiline
 * commands are handled correctly.
 */
function normalizeContinuations(cmd: string): string {
  return cmd.replace(/\\\n/g, " ");
}

/**
 * Inject a User-Agent header into a command string.
 *
 * Strategies by tool type:
 *   - curl:  inject -H 'User-Agent: ...' right after 'curl'
 *   - wget:  inject --header='User-Agent: ...' right after 'wget'
 *   - python: prepend export WIKIMEDIA_USER_AGENT=...
 *   - node:   prepend export WIKIMEDIA_USER_AGENT=...
 *
 * Returns the modified command, or the original unchanged if already has a UA.
 */
export function injectUserAgent(cmd: string, opts: InjectOptions): string {
  const normalized = normalizeContinuations(cmd.trim());

  if (!targetsWikimedia(normalized)) return cmd;
  if (hasUserAgentAlready(normalized)) return cmd;
  if (!opts.userAgent) return cmd;

  const ua = opts.userAgent;

  // Strategy 1: curl
  if (opts.interceptCurl && /^curl\b/.test(normalized)) {
    return cmd.replace(/^curl\b/, `curl -H 'User-Agent: ${escapeShellArg(ua)}'`);
  }

  // Strategy 2: wget
  if (opts.interceptWget && /^wget\b/.test(normalized)) {
    return cmd.replace(
      /^wget\b/,
      `wget --header='User-Agent: ${escapeShellArg(ua)}'`,
    );
  }

  // Strategy 3: Python scripts
  if (
    opts.interceptPython &&
    /^python[23]?\b/.test(normalized)
  ) {
    return prependEnvVar(cmd, ua);
  }

  // Strategy 4: Node.js scripts
  if (
    opts.interceptNode &&
    /^node\b/.test(normalized) &&
    /fetch|axios|node:https/.test(normalized)
  ) {
    return prependEnvVar(cmd, ua);
  }

  // No pattern matched — return unchanged
  return cmd;
}
