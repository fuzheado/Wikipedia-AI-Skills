"""Mock-based tests for the Toolforge maintainer-audit script.

No network calls: `extract_maintainers` is exercised on inline HTML fixtures that
mirror the shape of a toolsadmin tool page, so the parsing contract is pinned
even when toolsadmin is unreachable.
"""

import importlib.util
import subprocess
import sys
import time
import urllib.error
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from conftest import read_skill  # noqa: E402

SCRIPT = (Path(__file__).resolve().parent.parent
          / ".claude" / "skills" / "wikimedia-toolforge" / "scripts" / "count-maintainers.py")


def _load_script():
    """Import the skill script by path (it is not an importable module)."""
    spec = importlib.util.spec_from_file_location("count_maintainers", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def cm():
    return _load_script()


class TestExtractMaintainers:
    """The maintainers table parser used by the solo-maintainer audit."""

    def test_missing_caption_returns_empty(self, cm):
        assert cm.extract_maintainers("<html><body><table><td>nope</td></table>") == []

    def test_single_maintainer(self, cm):
        html = ('<table><caption>Maintainers</caption><tbody>'
                '<tr><td><a href="/u/alice">alice</a></td></tr></tbody></table>')
        assert cm.extract_maintainers(html) == ["alice"]

    def test_two_maintainers_are_both_returned(self, cm):
        html = ('<table><caption>Maintainers</caption><tbody>'
                '<tr><td><a href="/u/alice">alice</a></td>'
                '<td><a href="/u/bob">bob</a></td></tr></tbody></table>')
        assert cm.extract_maintainers(html) == ["alice", "bob"]

    def test_entities_are_unescaped(self, cm):
        html = ('<table><caption>Maintainers</caption><tbody>'
                '<tr><td>A &amp; B</td></tr></tbody></table>')
        assert cm.extract_maintainers(html) == ["A & B"]

    def test_empty_cells_are_dropped(self, cm):
        html = ('<table><caption>Maintainers</caption><tbody>'
                '<tr><td></td><td>   </td><td>carol</td></tr></tbody></table>')
        assert cm.extract_maintainers(html) == ["carol"]

    def test_parse_stops_at_tbody_close(self, cm):
        """Cells after </tbody> belong to another table and must not leak in."""
        html = ('<table><caption>Maintainers</caption><tbody>'
                '<tr><td>alice</td></tr></tbody></table>'
                '<table><tbody><tr><td>toolsadmin-footer</td></tr></tbody></table>')
        assert cm.extract_maintainers(html) == ["alice"]

    def test_tool_link_regex_matches_toolsadmin_shape(self, cm):
        """The index scraper depends on this exact href shape."""
        html = '<a href="/tools/id/hay-directory">hay-directory</a>'
        assert cm.TOOL_RE.findall(html) == ["hay-directory"]

    def test_user_agent_is_descriptive(self, cm):
        """Wikimedia etiquette: UA must identify the agent and a contact URL."""
        assert "http" in cm.UA
        assert cm.UA.strip()

    def test_user_agent_is_not_the_private_client_name(self, cm):
        """The audit was published from a private working library; its UA must not
        travel with it (the value is also changeable by env var, see below).

        This assertion is the reason the private client name still appears in this
        file: it is here to keep the name out of the script.
        """
        assert "HermesAgent" not in cm.UA

    def test_user_agent_comes_from_the_environment(self, monkeypatch):
        """$WIKIMEDIA_USER_AGENT wins when set — the repo-wide convention."""
        monkeypatch.setenv("WIKIMEDIA_USER_AGENT",
                           "TestBot/9.9 (https://example.org; test@example.org)")
        assert _load_script().UA == "TestBot/9.9 (https://example.org; test@example.org)"

    def test_user_agent_falls_back_to_a_repo_default(self, monkeypatch):
        monkeypatch.delenv("WIKIMEDIA_USER_AGENT", raising=False)
        mod = _load_script()
        assert "Wikipedia-AI-Skills" in mod.UA
        assert "HermesAgent" not in mod.UA


class TestZeroArgumentGuard:
    """`guidelines/script-audit-guidelines.md` §1: bare invocation must not crawl.

    These run the script for real but exit before any request is made, so they
    are offline-safe (verified: the guard fires before the first `get()`).
    """

    def test_bare_invocation_prints_usage_and_exits_nonzero(self):
        p = subprocess.run([sys.executable, str(SCRIPT)], capture_output=True,
                           text=True, timeout=60)
        assert p.returncode != 0
        assert "--all" in p.stderr           # tells you the way forward
        assert "refusing" in p.stderr        # and why it stopped
        assert "delay" in p.stderr           # and what the crawl would cost

    def test_a_full_crawl_requires_all(self):
        """Without --all (and without a --max-page bound) it must refuse, not crawl."""
        p = subprocess.run([sys.executable, str(SCRIPT), "--json", "/dev/null"],
                           capture_output=True, text=True, timeout=60)
        assert p.returncode != 0
        assert "--all" in p.stderr


class TestPacing:
    """The Robot policy for non-wiki resources: >= 1s between requests."""

    def test_zero_delay_is_a_noop(self, cm):
        pacer = cm.Pacer(0)
        t0 = time.monotonic()
        for _ in range(5):
            pacer.wait()
        assert time.monotonic() - t0 < 0.1

    def test_delay_is_enforced_between_waits(self, cm):
        pacer = cm.Pacer(0.05)
        t0 = time.monotonic()
        for _ in range(3):
            pacer.wait()
        # 3 waits => 2 paced intervals => >= 0.10s, with slack for a loaded machine
        assert time.monotonic() - t0 >= 0.09

    def test_extra_workers_do_not_raise_the_rate(self, cm):
        """The pacer is global, so +threads removes idle time, not pacing."""
        import threading
        pacer = cm.Pacer(0.02)
        started = []
        lock = threading.Lock()

        def worker():
            pacer.wait()
            with lock:
                started.append(time.monotonic())

        threads = [threading.Thread(target=worker) for _ in range(4)]
        t0 = time.monotonic()
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert time.monotonic() - t0 >= 0.06   # 4 waits => 3 intervals of 0.02


class TestRetryAfter:
    """429 handling must honour Retry-After in both of its spellings."""

    def test_delta_seconds(self, cm):
        assert cm.parse_retry_after("7") == 7.0

    def test_zero(self, cm):
        assert cm.parse_retry_after("0") == 0.0

    def test_http_date(self, cm):
        when = datetime.now(timezone.utc) + timedelta(seconds=30)
        got = cm.parse_retry_after(when.strftime("%a, %d %b %Y %H:%M:%S GMT"))
        assert 25 <= got <= 31

    def test_past_http_date_clamps_to_zero(self, cm):
        when = datetime.now(timezone.utc) - timedelta(seconds=30)
        assert cm.parse_retry_after(when.strftime("%a, %d %b %Y %H:%M:%S GMT")) == 0.0

    def test_garbage_and_missing(self, cm):
        assert cm.parse_retry_after("soon") is None
        assert cm.parse_retry_after(None) is None

    def test_two_consecutive_429s_abort_the_run(self, cm):
        """After 2 consecutive 429s the script stops instead of pushing on."""
        assert cm.MAX_CONSECUTIVE_429 == 2
        assert issubclass(cm.RateLimited, RuntimeError)


class FakePacer:
    """Records waits instead of sleeping, so get() tests stay instant."""

    def __init__(self):
        self.waits = 0

    def wait(self):
        self.waits += 1


class FakeResponse:
    def __init__(self, body=b"ok", status=200):
        self.status = status
        self._body = body

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def http_error(code: int, retry_after: str | None = None):
    headers = {} if retry_after is None else {"Retry-After": retry_after}
    return urllib.error.HTTPError("https://toolsadmin.wikimedia.org/x", code,
                                  "err", headers, None)


def raise_(exc):
    """A urlopen stand-in that always raises."""
    def _fn(*a, **k):
        raise exc
    return _fn


class TestGet:
    """get() must pace every attempt, honour Retry-After, and stop when throttled."""

    def test_success_is_returned_and_paced(self, cm, monkeypatch):
        monkeypatch.setattr(cm.urllib.request, "urlopen",
                            lambda *a, **k: FakeResponse(body=b"<html>hi</html>"))
        pacer = FakePacer()
        assert cm.get("https://example.org", pacer) == (200, "<html>hi</html>")
        assert pacer.waits == 1, "the pacer must gate every request"

    def test_404_is_terminal_and_not_retried(self, cm, monkeypatch):
        calls = []

        def record(*a, **k):
            calls.append(1)
            raise http_error(404)

        monkeypatch.setattr(cm.urllib.request, "urlopen", record)
        assert cm.get("https://example.org", FakePacer()) == (404, "")
        assert len(calls) == 1, "404 is terminal, not retryable"

    def test_429_honours_retry_after_then_succeeds(self, cm, monkeypatch):
        calls = []

        def flaky(*a, **k):
            calls.append(1)
            if len(calls) == 1:
                raise http_error(429, retry_after="0")
            return FakeResponse()

        monkeypatch.setattr(cm.urllib.request, "urlopen", flaky)
        assert cm.get("https://example.org", FakePacer()) == (200, "ok")
        assert len(calls) == 2

    def test_two_consecutive_429s_stop_the_run(self, cm, monkeypatch):
        """The point of the fix: never retry straight through a throttle."""
        monkeypatch.setattr(cm.urllib.request, "urlopen",
                            raise_(http_error(429, retry_after="0")))
        with pytest.raises(cm.RateLimited):
            cm.get("https://example.org", FakePacer())

    def test_persistent_5xx_stops_the_run(self, cm, monkeypatch):
        monkeypatch.setattr(cm, "BACKOFF_START", 0)
        monkeypatch.setattr(cm.urllib.request, "urlopen", raise_(http_error(503)))
        with pytest.raises(cm.ServiceUnavailable):
            cm.get("https://example.org", FakePacer(), retries=1)

    def test_unrecoverable_transport_error_returns_minus_one(self, cm, monkeypatch):
        monkeypatch.setattr(cm.urllib.request, "urlopen",
                            raise_(OSError("connection reset by peer")))
        assert cm.get("https://example.org", FakePacer(), retries=1) == (-1, "")


class TestMaintainerAuditDocumentation:
    """The audit's numbers and method must be readable from the skill itself."""

    def test_reference_is_linked_from_the_skill(self):
        text = read_skill('wikimedia-toolforge')
        assert 'references/maintainer-audit.md' in text

    def test_reference_states_its_method(self):
        ref = (SCRIPT.parent.parent / "references" / "maintainer-audit.md")
        assert ref.exists(), "maintainer-audit.md must ship with the skill"
        body = ref.read_text()
        assert 'toolsadmin' in body.lower()
        assert len(body.splitlines()) > 20

    def test_reference_documents_the_robot_policy_pacing(self):
        """The audit must not re-teach the 12-thread anti-pattern it arrived with."""
        ref = (SCRIPT.parent.parent / "references" / "maintainer-audit.md")
        body = ref.read_text()
        assert "~12 threads" not in body
        assert "--all" in body
        assert "1 concurrent request" in body or "1 concurrent" in body
        assert "Retry-After" in body
