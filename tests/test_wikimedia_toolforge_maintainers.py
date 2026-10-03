"""Mock-based tests for the Toolforge maintainer-audit script.

No network calls: `extract_maintainers` is exercised on inline HTML fixtures that
mirror the shape of a toolsadmin tool page, so the parsing contract is pinned
even when toolsadmin is unreachable.
"""

import importlib.util
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
        assert "HermesAgent" in cm.UA
        assert "http" in cm.UA


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
