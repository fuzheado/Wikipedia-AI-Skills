"""Offline tests for the live-API guard in tests/live_calls.py.

The guard exists because CI runners get HTTP 429 from Wikimedia far more often
than laptops do (see the module docstring). Its own behaviour is tested with
stub commands, so these tests need no network.
"""

import sys
import time

import pytest

import live_calls
from live_calls import is_transient_live_failure, pace_live_call, run_live


def stub(body):
    """A ``python -c`` command stub with the given behaviour."""
    return [sys.executable, "-c", body]


# ─── signature detection ────────────────────────────────────────────────


def test_detects_rate_limit_traceback():
    output = (
        "Traceback (most recent call last):\n"
        '  File "template-scanner.py", line 114, in api_call\n'
        "urllib.error.HTTPError: HTTP Error 429: Too Many Requests\n"
    )
    assert is_transient_live_failure(output)


def test_detects_maxlag_and_retry_after():
    assert is_transient_live_failure("error: maxlag exceeded")
    assert is_transient_live_failure("403 forbidden; Retry-After: 30")


def test_detects_network_drop():
    assert is_transient_live_failure(
        "socket.gaierror: [Errno -3] Temporary failure in name resolution"
    )
    assert is_transient_live_failure("Connection reset by peer")


def test_real_failures_are_not_transient():
    """A script bug or an expected 'not found' must never be swallowed."""
    assert not is_transient_live_failure("Template:NoSuchThing does not exist")
    assert not is_transient_live_failure("KeyError: 'parameters'")
    assert not is_transient_live_failure("")


def test_detects_api_refusal_statuses():
    """403/429/5xx and 000 (no response) are environment, not regressions."""
    for status in (403, 429, 500, 502, 503, 504, 0):
        output = f"Error: API returned HTTP {status:03d} from https://en.wikipedia.org/w/api.php"
        assert is_transient_live_failure(output), status


def test_api_404_is_not_transient():
    """A 404 means the endpoint/parameters are wrong — that is a real bug."""
    output = "Error: API returned HTTP 404 from https://en.wikipedia.org/w/api.php"
    assert not is_transient_live_failure(output)


def test_detects_unexpected_api_response():
    """An unparseable body is typically an edge/proxy block page."""
    assert is_transient_live_failure(
        "Error: unexpected API response from https://en.wikipedia.org/w/api.php "
        "(not JSON, or an API error object)"
    )


def test_detects_curl_dns_failure():
    assert is_transient_live_failure("curl: (6) Could not resolve host: en.wikipedia.invalid")


# ─── run_live behaviour ─────────────────────────────────────────────────


def test_returns_successful_process():
    proc = run_live(stub("print('Page: Albert Einstein')"),
                    capture_output=True, text=True)
    assert proc.returncode == 0
    assert "Albert Einstein" in proc.stdout


def test_returns_expected_failure_without_skipping():
    """Negative tests keep working: a real non-zero exit is returned."""
    proc = run_live(stub("import sys; print('does not exist'); sys.exit(1)"),
                    capture_output=True, text=True, min_interval=0)
    assert proc.returncode == 1
    assert "does not exist" in proc.stdout


def test_skips_on_rate_limit():
    with pytest.raises(pytest.skip.Exception) as excinfo:
        run_live(stub("import sys; print('HTTP Error 429: Too Many Requests');"
                      " sys.exit(1)"),
                 capture_output=True, text=True, min_interval=0, backoff=0)
    assert "429" in str(excinfo.value)


def test_skips_on_network_drop():
    with pytest.raises(pytest.skip.Exception):
        run_live(stub("import sys; print('Temporary failure in name resolution');"
                      " sys.exit(1)"),
                 capture_output=True, text=True, min_interval=0, backoff=0)


def test_retries_then_succeeds(tmp_path):
    """A single throttled attempt is retried instead of skipping the test."""
    counter = tmp_path / "attempts"
    body = (
        "from pathlib import Path\n"
        f"p = Path({str(counter)!r})\n"
        "n = int(p.read_text()) if p.exists() else 0\n"
        "p.write_text(str(n + 1))\n"
        "print('HTTP Error 429: Too Many Requests') if n == 0 else print('Page: Berlin')\n"
        "raise SystemExit(429 if n == 0 else 0)\n"
    )
    proc = run_live(stub(body), capture_output=True, text=True,
                    min_interval=0, backoff=0)
    assert proc.returncode == 0
    assert "Berlin" in proc.stdout
    assert counter.read_text() == "2"


def test_skips_after_all_attempts():
    with pytest.raises(pytest.skip.Exception) as excinfo:
        run_live(stub("import sys; print('Too Many Requests'); sys.exit(1)"),
                 capture_output=True, text=True, min_interval=0, backoff=0,
                 attempts=3)
    assert "3 attempt(s)" in str(excinfo.value)


def test_strict_mode_raises_instead_of_skipping(monkeypatch):
    monkeypatch.setenv(live_calls.STRICT_ENV, "1")
    with pytest.raises(AssertionError) as excinfo:
        run_live(stub("import sys; print('HTTP Error 429'); sys.exit(1)"),
                 capture_output=True, text=True, min_interval=0, backoff=0)
    assert live_calls.STRICT_ENV in str(excinfo.value)


def test_paces_consecutive_calls():
    pace_live_call(min_interval=0)
    start = time.monotonic()
    pace_live_call(min_interval=0.15)
    assert time.monotonic() - start >= 0.14


def test_command_failure_still_raises_for_missing_binary():
    """Only transient API conditions are tolerated — not broken test setups."""
    with pytest.raises(FileNotFoundError):
        run_live(["/nonexistent/binary"], min_interval=0)
