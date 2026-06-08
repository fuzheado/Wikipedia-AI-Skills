/**
 * Wikimedia AI Skills — Pi Extension
 *
 * Layer 1 (Event Hooks) of the three-layer agent integration strategy.
 * Automatically injects descriptive User-Agent headers into all bash
 * tool calls that target Wikimedia servers (Wikipedia, Wikidata, Commons,
 * Toolforge, etc.), preventing the HTTP 403/429 errors that Wikimedia
 * returns for requests with missing or generic User-Agents.
 *
 * The injection is invisible to the LLM — it runs in the background before
 * every bash tool call.
 *
 * @see https://foundation.wikimedia.org/wiki/Policy:Wikimedia_Foundation_User-Agent_Policy
 * @see ../AGENT-INTEGRATION-STRATEGY.md
 */

import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { existsSync, readFileSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";

// Resolve __dirname for ESM-compatible access to config.json
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

export type {
  ExtensionConfig,
  InjectOptions,
} from "./core";
export {
  DEFAULT_USER_AGENT,
  DEFAULT_CONFIG,
  WIKIMEDIA_DOMAINS,
  targetsWikimedia,
  hasUserAgentAlready,
  injectUserAgent,
} from "./core";

import {
  DEFAULT_CONFIG,
  type ExtensionConfig,
  targetsWikimedia,
  injectUserAgent,
  type InjectOptions,
} from "./core";

// ---------------------------------------------------------------------------
// Configuration
// ---------------------------------------------------------------------------

/**
 * Config priority chain (highest to lowest):
 *   1. WIKIMEDIA_USER_AGENT environment variable
 *   2. ~/.config/wikimedia-skills/config.json   (user's global config — survives git pull)
 *   3. <this-extension-dir>/config.json          (shipped default template)
 */

const HOME_CONFIG_DIR = [process.env["XDG_CONFIG_HOME"] ?? resolve(process.env["HOME"] ?? "~", ".config"), "wikimedia-skills"].join("/");

/** Resolve the repo's shipped config.json. */
function shippedConfigPath(): string {
  return resolve(__dirname, "config.json");
}

/** Resolve the user's global config at ~/.config/wikimedia-skills/config.json. */
function userConfigPath(): string {
  return resolve(HOME_CONFIG_DIR, "config.json");
}

/** Try to parse a config file, returning null on failure. */
function tryParseConfig(filePath: string): ExtensionConfig | null {
  try {
    if (!existsSync(filePath)) return null;
    const raw = readFileSync(filePath, "utf-8");
    const parsed = JSON.parse(raw) as Partial<ExtensionConfig>;
    return {
      userAgent: parsed.userAgent ?? DEFAULT_CONFIG.userAgent,
      enabled: parsed.enabled ?? DEFAULT_CONFIG.enabled,
      interceptCurl: parsed.interceptCurl ?? DEFAULT_CONFIG.interceptCurl,
      interceptPython: parsed.interceptPython ?? DEFAULT_CONFIG.interceptPython,
      interceptNode: parsed.interceptNode ?? DEFAULT_CONFIG.interceptNode,
      interceptWget: parsed.interceptWget ?? DEFAULT_CONFIG.interceptWget,
    };
  } catch {
    return null;
  }
}

/**
 * Load the extension configuration using the priority chain:
 *   user config (~/.config/) > shipped config (repo) > defaults
 */
function loadConfig(): ExtensionConfig {
  return tryParseConfig(userConfigPath())
    ?? tryParseConfig(shippedConfigPath())
    ?? { ...DEFAULT_CONFIG };
}

/** Cache the config so we don't read the file on every tool_call. */
let _config: ExtensionConfig | null = null;

function getConfig(): ExtensionConfig {
  if (!_config) {
    _config = loadConfig();
  }
  return _config;
}

/**
 * Reload config from disk. Called on session_start so config changes
 * take effect without restarting pi.
 */
function reloadConfig(): void {
  _config = null;
}

// ---------------------------------------------------------------------------
// User-Agent injection
// ---------------------------------------------------------------------------

/** Resolve the User-Agent string: env var > config.json > default. */
function resolveUserAgent(): string {
  // Env var takes highest priority so users can override at the shell level
  const envUA = process.env["WIKIMEDIA_USER_AGENT"];
  if (envUA && envUA.trim()) return envUA.trim();

  return getConfig().userAgent;
}

/**
 * Build the InjectOptions from current config, resolving the user agent
 * from env var or config.
 */
function buildInjectOptions(): InjectOptions {
  const cfg = getConfig();
  return {
    userAgent: resolveUserAgent(),
    interceptCurl: cfg.interceptCurl,
    interceptPython: cfg.interceptPython,
    interceptNode: cfg.interceptNode,
    interceptWget: cfg.interceptWget,
  };
}

// ---------------------------------------------------------------------------
// Extension entry point
// ---------------------------------------------------------------------------

export default function (pi: ExtensionAPI) {
  // Reload config on session start so changes to config.json take effect
  pi.on("session_start", async () => {
    reloadConfig();
  });

  // Intercept every bash tool call and inject User-Agent when targeting Wikimedia
  pi.on("tool_call", async (event, ctx) => {
    if (event.toolName !== "bash") return;
    if (!getConfig().enabled) return;

    const cmd: string = event.input.command;

    // Fast path: skip commands that don't mention any Wikimedia domain
    if (!targetsWikimedia(cmd)) return;

    const opts = buildInjectOptions();
    const modified = injectUserAgent(cmd, opts);

    if (modified !== cmd) {
      event.input.command = modified;
    }
  });
}
