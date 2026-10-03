"""Guard for the tests that make real API calls (the ``slow`` marker in pytest.ini).

CI runners sit behind data-centre IPs that Wikimedia rate-limits far more
aggressively than a laptop does. On 2026-09-15 the ``tests`` job failed with
eight HTTP 429s in ``tests/test_templates.py``: the skill scripts were fine, the
API was throttling the runner. A rate limit is not a regression, so live tests
call :func:`run_live`, which

  * paces requests at least one second apart (Wikimedia API etiquette),
  * retries a transient failure with a linear backoff,
  * and then **skips** the test, quoting the API output in the skip reason.

Every other failure still fails normally — the transient signatures below are
deliberately narrow (they must appear *and* the command must have exited
non-zero). Set ``SKILLS_LIVE_STRICT=1`` to turn the skip into a failure, which
is what you want when you are deliberately testing a live API from this host.

The same class of failure resurfaced on 2026-09-20 as ``Error: Template
'Infobox person' not found on https://en.wikipedia.org``: the skill scripts were
*masking* an API refusal as a missing page, so this guard could not see it (and
neither could anyone reading the log). The wikipedia-templates scripts now report
``API returned HTTP <code>`` instead, and
:func:`is_transient_live_failure` treats 403/429/5xx/000 plus an unparseable API
response as transient — while a 404 stays a real failure.

Usage in a test file::

    from live_calls import run_live

    @pytest.mark.slow
    def test_scanner_real_page():
        result = run_live([sys.executable, str(SCANNER), 'Berlin'],
                          capture_output=True, text=True, timeout=30)
        assert result.returncode == 0, f"Failed: {result.stderr}"
"""

import os
import re
import subprocess
import time

import pytest

# HTTP rate limiting / WMF throttling responses.
RATE_LIMIT_SIGNATURES = (
    "429",
    "Too Many Requests",
    "Retry-After",
    "maxlag",
)

# DNS/TLS/socket failures that mean "no network from this host", not "bug".
NETWORK_SIGNATURES = (
    "Temporary failure in name resolution",
    "Name or service not known",
    "nodename nor servname",
    "Could not resolve host",
    "getaddrinfo failed",
    "Connection refused",
    "Connection reset by peer",
    "Max retries exceeded",
    "Remote end closed connection",
    "Read timed out",
)

# API refusals: the skill scripts report these as "API returned HTTP <code>" or
# "unexpected API response" once they stop masking failures (see the
# wikipedia-templates scripts). 403/429/5xx and 000 (no response at all) are
# environment conditions for a live test; a 404 is not.
API_STATUS_RE = re.compile(r"API returned HTTP (\d{3})")
TRANSIENT_API_STATUSES = frozenset({0, 403, 429, 500, 502, 503, 504})
API_REFUSAL_SIGNATURES = ("unexpected API response",)

TRANSIENT_SIGNATURES = (RATE_LIMIT_SIGNATURES + NETWORK_SIGNATURES
                        + API_REFUSAL_SIGNATURES)

STRICT_ENV = "SKILLS_LIVE_STRICT"
DEFAULT_MIN_INTERVAL = 1.0  # seconds; Wikimedia etiquette is >= 1s between calls

_last_live_call = 0.0


def is_transient_live_failure(output: str) -> bool:
    """True when *output* looks like rate limiting, an API refusal or a network drop.

    A 404/400 reported by a script is deliberately **not** transient: that is a
    real regression (wrong endpoint or wrong parameters), not a throttled runner.
    """
    if any(signature in output for signature in TRANSIENT_SIGNATURES):
        return True
    return any(
        int(match.group(1)) in TRANSIENT_API_STATUSES
        for match in API_STATUS_RE.finditer(output)
    )


def pace_live_call(min_interval: float = DEFAULT_MIN_INTERVAL) -> None:
    """Sleep as needed so consecutive live calls are >= *min_interval* apart."""
    global _last_live_call
    wait = _last_live_call + min_interval - time.monotonic()
    if wait > 0:
        time.sleep(wait)
    _last_live_call = time.monotonic()


def run_live(argv, *, attempts: int = 2, backoff: float = 3.0,
             min_interval: float = DEFAULT_MIN_INTERVAL, **kwargs):
    """Run a command that hits a live Wikimedia API, tolerating throttling.

    Paces calls, retries transient failures (:data:`TRANSIENT_SIGNATURES`) with
    a linear backoff, then skips the calling test with the API output in the
    skip reason. Returns the ``CompletedProcess`` otherwise — including for
    commands that are *expected* to fail (non-zero exit without a transient
    signature), so negative tests keep working.
    """
    proc = None
    for attempt in range(attempts):
        pace_live_call(min_interval)
        proc = subprocess.run(argv, **kwargs)
        output = (proc.stdout or "") + (proc.stderr or "")
        if proc.returncode == 0 or not is_transient_live_failure(output):
            return proc
        if attempt < attempts - 1:
            time.sleep(backoff * (attempt + 1))

    output = ((proc.stdout or "") + (proc.stderr or "")).strip()
    reason = (
        f"live API rate-limited the runner or dropped the connection after "
        f"{attempts} attempt(s) — not a code failure. Output: ...{output[-300:]}"
    )
    if os.environ.get(STRICT_ENV):
        raise AssertionError(
            f"{reason}\n[{STRICT_ENV} is set, so this is reported as a failure "
            f"instead of a skip]"
        )
    pytest.skip(reason)
