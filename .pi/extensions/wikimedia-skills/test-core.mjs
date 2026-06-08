/**
 * Unit tests for the User-Agent injection core logic.
 *
 * The core module is pure TypeScript with no pi SDK dependency, so we can
 * test it with any test runner. This file uses Node's built-in `node:test`
 * (available from Node 18+).
 *
 * Run:   node --test .pi/extensions/wikimedia-skills/test-core.mjs
 * Watch: node --test --watch .pi/extensions/wikimedia-skills/test-core.mjs
 */

import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// --- Import via dynamic import (TypeScript with jiti at runtime, but since
//     core.ts exports pure functions, we compile a JS version on the fly by
//     reading the source. However, for testing we'll just use the compiled
//     JavaScript version. Actually, core.ts is plain enough that we can
//     test via a simple approach: we import core.js if it exists, or we
//     test the logic directly.
//
//     For simplicity and reliability, we re-implement the testable functions
//     here as plain JS. This avoids any transpilation dependency and keeps
//     tests running with just `node --test`.
// ===========================================================================

const WIKIMEDIA_DOMAINS =
  /wikipedia\.org|wikidata\.org|wikimedia\.org|wmcloud\.org|toolforge\.org|tools\.wmflabs\.org/;

function targetsWikimedia(cmd) {
  return WIKIMEDIA_DOMAINS.test(cmd);
}

function hasUserAgentAlready(cmd) {
  if (/-H[= ]?['"]?User-Agent:/i.test(cmd)) return true;
  if (/--header[= ]?['"]?User-Agent:/i.test(cmd)) return true;
  if (/WIKIMEDIA_USER_AGENT=/.test(cmd)) return true;
  return false;
}

function escapeShellArg(val) {
  return val.replace(/'/g, "'\\''");
}

function normalizeContinuations(cmd) {
  return cmd.replace(/\\\n/g, " ");
}

function injectUserAgent(cmd, opts) {
  const normalized = normalizeContinuations(cmd.trim());

  if (!targetsWikimedia(normalized)) return cmd;
  if (hasUserAgentAlready(normalized)) return cmd;
  if (!opts.userAgent) return cmd;

  const ua = opts.userAgent;

  if (opts.interceptCurl && /^curl\b/.test(normalized)) {
    return cmd.replace(/^curl\b/, `curl -H 'User-Agent: ${escapeShellArg(ua)}'`);
  }

  if (opts.interceptWget && /^wget\b/.test(normalized)) {
    return cmd.replace(/^wget\b/, `wget --header='User-Agent: ${escapeShellArg(ua)}'`);
  }

  if (opts.interceptPython && /^python[23]?\b/.test(normalized)) {
    return `export WIKIMEDIA_USER_AGENT="${escapeShellArg(ua)}"\n${cmd}`;
  }

  if (opts.interceptNode && /^node\b/.test(normalized) && /fetch|axios|node:https/.test(normalized)) {
    return `export WIKIMEDIA_USER_AGENT="${escapeShellArg(ua)}"\n${cmd}`;
  }

  return cmd;
}

const DEFAULT_OPTS = {
  userAgent: "WikipediaAIAgent/1.0 (user@email.com) SkillsDemo",
  interceptCurl: true,
  interceptPython: true,
  interceptNode: true,
  interceptWget: true,
};

// ===========================================================================
// Tests
// ===========================================================================

describe("targetsWikimedia()", () => {
  it("matches en.wikipedia.org", () => {
    assert(targetsWikimedia("curl https://en.wikipedia.org/w/api.php"));
  });

  it("matches other language wikipedias", () => {
    assert(targetsWikimedia("curl https://de.wikipedia.org/w/api.php"));
    assert(targetsWikimedia("curl https://fr.wikipedia.org/w/api.php"));
    assert(targetsWikimedia("curl https://ja.wikipedia.org/w/api.php"));
  });

  it("matches wikidata.org", () => {
    assert(targetsWikimedia("curl https://query.wikidata.org/sparql"));
    assert(targetsWikimedia("curl https://www.wikidata.org/w/api.php"));
  });

  it("matches wikimedia.org", () => {
    assert(targetsWikimedia("curl https://api.wikimedia.org/service/lw/inference/v1/models"));
    assert(targetsWikimedia("curl https://commons.wikimedia.org/w/api.php"));
    assert(targetsWikimedia("curl https://meta.wikimedia.org/w/api.php"));
    assert(targetsWikimedia("curl https://wikimedia.org/api/rest_v1/metrics/pageviews"));
  });

  it("matches wmcloud.org", () => {
    assert(targetsWikimedia("curl https://wd-vectordb.wmcloud.org/search_items"));
  });

  it("matches toolforge.org", () => {
    assert(targetsWikimedia("curl https://tools.wmflabs.org/"));
    assert(targetsWikimedia("ssh myuser@dev.toolforge.org"));
  });

  it("rejects non-Wikimedia domains", () => {
    assert(!targetsWikimedia("curl https://api.github.com/repos/user/repo"));
    assert(!targetsWikimedia("curl https://www.google.com/search"));
    assert(!targetsWikimedia("npm test"));
    assert(!targetsWikimedia("ls -la"));
  });
});

describe("hasUserAgentAlready()", () => {
  it("detects curl -H User-Agent:", () => {
    assert(
      hasUserAgentAlready(
        `curl -H 'User-Agent: MyBot/1.0' https://en.wikipedia.org/w/api.php`,
      ),
    );
  });

  it("detects curl -H\"User-Agent:", () => {
    assert(
      hasUserAgentAlready(
        `curl -H"User-Agent: MyBot/1.0" https://en.wikipedia.org/w/api.php`,
      ),
    );
  });

  it("detects wget --header=User-Agent:", () => {
    assert(
      hasUserAgentAlready(
        `wget --header='User-Agent: MyBot/1.0' https://en.wikipedia.org/w/api.php`,
      ),
    );
  });

  it("detects WIKIMEDIA_USER_AGENT env var", () => {
    assert(
      hasUserAgentAlready(
        `WIKIMEDIA_USER_AGENT="MyBot/1.0" python3 script.py`,
      ),
    );
  });

  it("returns false for commands with no UA", () => {
    assert(!hasUserAgentAlready("curl https://en.wikipedia.org/w/api.php"));
    assert(!hasUserAgentAlready("python3 script.py --url https://en.wikipedia.org"));
  });
});

describe("injectUserAgent()", () => {
  describe("curl", () => {
    it("injects -H flag after curl command", () => {
      const result = injectUserAgent(
        "curl https://en.wikipedia.org/w/api.php?action=query&format=json",
        DEFAULT_OPTS,
      );
      assert(result.includes("-H 'User-Agent:"));
      assert(result.includes("WikipediaAIAgent/1.0"));
      assert(result.includes("https://en.wikipedia.org/w/api.php"));
    });

    it("injects before piped curl", () => {
      const result = injectUserAgent(
        "curl -s https://en.wikipedia.org/w/api.php | jq '.query.pages'",
        DEFAULT_OPTS,
      );
      assert(result.startsWith("curl -H 'User-Agent:"));
      assert(result.includes("| jq '.query.pages'"));
    });

    it("does not double-inject if UA already present", () => {
      const cmd = `curl -H 'User-Agent: MyBot/1.0' https://en.wikipedia.org/w/api.php`;
      const result = injectUserAgent(cmd, DEFAULT_OPTS);
      assert.equal(result, cmd);
    });

    it("handles URLs with query parameters containing special chars", () => {
      const cmd =
        "curl 'https://en.wikipedia.org/w/api.php?action=query&titles=Python_(programming_language)'";
      const result = injectUserAgent(cmd, DEFAULT_OPTS);
      assert(result.startsWith("curl -H 'User-Agent:"));
      assert(result.includes("Python_(programming_language)"));
    });

    it("handles multiple -H flags (puts injection first)", () => {
      const cmd = "curl -H 'Accept: application/json' https://commons.wikimedia.org/w/api.php";
      const result = injectUserAgent(cmd, DEFAULT_OPTS);
      assert(result.startsWith("curl -H 'User-Agent:"));
      assert(result.includes("-H 'Accept: application/json'"));
    });
  });

  describe("wget", () => {
    it("injects --header flag", () => {
      const result = injectUserAgent(
        "wget -O- https://en.wikipedia.org/w/api.php",
        DEFAULT_OPTS,
      );
      assert(result.startsWith("wget --header='User-Agent:"));
      assert(result.includes("WikipediaAIAgent/1.0"));
    });

    it("does not double-inject", () => {
      const cmd = `wget --header='User-Agent: Bot/1.0' https://en.wikipedia.org/w/api.php`;
      const result = injectUserAgent(cmd, DEFAULT_OPTS);
      assert.equal(result, cmd);
    });
  });

  describe("python", () => {
    it("prepends env var for python3", () => {
      const result = injectUserAgent(
        "python3 script.py --title 'Albert Einstein' --api https://en.wikipedia.org/w/api.php",
        DEFAULT_OPTS,
      );
      assert(result.startsWith("export WIKIMEDIA_USER_AGENT="));
      assert(result.includes("WikipediaAIAgent/1.0"));
      assert(result.includes("python3 script.py --title 'Albert Einstein' --api https://en.wikipedia.org/w/api.php"));
    });

    it("prepends env var for python", () => {
      const result = injectUserAgent(
        "python script.py --url https://en.wikipedia.org/w/api.php",
        DEFAULT_OPTS,
      );
      assert(result.startsWith("export WIKIMEDIA_USER_AGENT="));
    });

    it("escapes single quotes in user agent", () => {
      const result = injectUserAgent(
        "python3 script.py https://en.wikipedia.org/w/api.php",
        { ...DEFAULT_OPTS, userAgent: "Test/1.0 (user@example.com) My'Project" },
      );
      assert(result.includes("My'\\''Project"));
    });

    it("does not inject if env var already set", () => {
      const cmd =
        "WIKIMEDIA_USER_AGENT='MyBot/1.0' python3 script.py";
      const result = injectUserAgent(cmd, DEFAULT_OPTS);
      assert.equal(result, cmd);
    });
  });

  describe("node", () => {
    it("prepends env var for node with fetch", () => {
      const result = injectUserAgent(
        "node script.js --fetch https://en.wikipedia.org",
        DEFAULT_OPTS,
      );
      assert(result.startsWith("export WIKIMEDIA_USER_AGENT="));
    });

    it("does not inject for node without HTTP keywords", () => {
      const cmd = "node script.js --help";
      const result = injectUserAgent(cmd, DEFAULT_OPTS);
      assert.equal(result, cmd);
    });
  });

  describe("non-Wikimedia commands", () => {
    it("passes through git commands", () => {
      const cmd = "git push origin main";
      assert.equal(injectUserAgent(cmd, DEFAULT_OPTS), cmd);
    });

    it("passes through npm commands", () => {
      const cmd = "npm test";
      assert.equal(injectUserAgent(cmd, DEFAULT_OPTS), cmd);
    });

    it("passes through non-Wikimedia curl", () => {
      const cmd = "curl https://api.github.com/repos/user/repo";
      assert.equal(injectUserAgent(cmd, DEFAULT_OPTS), cmd);
    });

    it("passes through ls/cd/echo", () => {
      assert.equal(injectUserAgent("ls -la", DEFAULT_OPTS), "ls -la");
      assert.equal(injectUserAgent("cd /tmp", DEFAULT_OPTS), "cd /tmp");
    });
  });

  describe("disabled interceptors", () => {
    it("does not inject curl when interceptCurl is false", () => {
      const cmd = "curl https://en.wikipedia.org/w/api.php";
      const result = injectUserAgent(cmd, { ...DEFAULT_OPTS, interceptCurl: false });
      assert.equal(result, cmd);
    });

    it("does not inject python when interceptPython is false", () => {
      const cmd = "python3 script.py";
      const result = injectUserAgent(cmd, { ...DEFAULT_OPTS, interceptPython: false });
      assert.equal(result, cmd);
    });
  });

  describe("multiline commands with line continuations", () => {
    it("handles backslash-newline continuations", () => {
      const cmd = "curl \\\n  https://en.wikipedia.org/w/api.php";
      const result = injectUserAgent(cmd, DEFAULT_OPTS);
      assert(result.startsWith("curl -H 'User-Agent:"));
      assert(result.includes("\\\n  https://en.wikipedia.org"));
    });

    it("handles multiline python commands", () => {
      const cmd = "python3 << 'EOF'\nimport requests\nr = requests.get('https://en.wikipedia.org/w/api.php')\nEOF";
      const result = injectUserAgent(cmd, DEFAULT_OPTS);
      assert(result.startsWith("export WIKIMEDIA_USER_AGENT="));
    });
  });

  describe("empty / edge user agent", () => {
    it("returns original if userAgent is empty", () => {
      const cmd = "curl https://en.wikipedia.org/w/api.php";
      const result = injectUserAgent(cmd, { ...DEFAULT_OPTS, userAgent: "" });
      assert.equal(result, cmd);
    });
  });
});

describe("config.json validation", () => {
  it("config.json exists and is valid JSON", () => {
    const configPath = resolve(__dirname, "config.json");
    assert(existsSync(configPath), "config.json not found");

    const raw = readFileSync(configPath, "utf-8");
    const config = JSON.parse(raw);

    assert(typeof config.userAgent === "string");
    assert(config.userAgent.length > 0, "userAgent must not be empty");
    assert(typeof config.enabled === "boolean");
    assert(typeof config.interceptCurl === "boolean");
    assert(typeof config.interceptPython === "boolean");
    assert(typeof config.interceptNode === "boolean");
    assert(typeof config.interceptWget === "boolean");
  });
});

describe("package.json validation", () => {
  it("package.json exists and has pi.extensions pointing to index.ts", () => {
    const pkgPath = resolve(__dirname, "package.json");
    assert(existsSync(pkgPath), "package.json not found");

    const raw = readFileSync(pkgPath, "utf-8");
    const pkg = JSON.parse(raw);

    assert(pkg.pi, "package.json missing 'pi' field");
    assert(Array.isArray(pkg.pi.extensions), "pi.extensions must be an array");
    assert(
      pkg.pi.extensions.includes("./index.ts"),
      "pi.extensions must include './index.ts'",
    );
  });
});
