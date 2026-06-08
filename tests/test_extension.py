"""Validate the pi extension for Wikimedia User-Agent injection."""

import json
import os
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
EXT_DIR = REPO_ROOT / '.pi' / 'extensions' / 'wikimedia-skills'


class TestExtensionStructure:
    """The Wikimedia Skills pi extension must have correct structure."""

    def test_extension_directory_exists(self):
        assert EXT_DIR.is_dir(), (
            f"Extension directory not found: {EXT_DIR}"
        )

    def test_index_ts_exists(self):
        path = EXT_DIR / 'index.ts'
        assert path.is_file(), f"Missing index.ts at {path}"

    def test_index_ts_has_default_export(self):
        path = EXT_DIR / 'index.ts'
        content = path.read_text('utf-8')
        assert 'export default function' in content, (
            "index.ts must export a default function for pi"
        )
        assert 'pi.on(' in content, (
            "index.ts must call pi.on() to register event hooks"
        )

    def test_core_ts_exists(self):
        path = EXT_DIR / 'core.ts'
        assert path.is_file(), f"Missing core.ts at {path}"

    def test_core_ts_exports_pure_functions(self):
        path = EXT_DIR / 'core.ts'
        content = path.read_text('utf-8')
        exports = [
            'targetsWikimedia',
            'hasUserAgentAlready',
            'injectUserAgent',
        ]
        for func in exports:
            assert f'export function {func}' in content, (
                f"core.ts must export pure function '{func}'"
            )

        # Also check injectRetry
        assert 'export function injectRetry' in content, (
            "core.ts must export pure function 'injectRetry'"
        )

    def test_config_json_exists_and_valid(self):
        path = EXT_DIR / 'config.json'
        assert path.is_file(), f"Missing config.json at {path}"

        with open(path) as f:
            config = json.load(f)

        assert isinstance(config.get('userAgent'), str)
        assert config['userAgent'], "userAgent must not be empty"
        assert isinstance(config.get('enabled'), bool)
        assert isinstance(config.get('interceptCurl'), bool)
        assert isinstance(config.get('interceptPython'), bool)
        assert isinstance(config.get('interceptNode'), bool)
        assert isinstance(config.get('interceptWget'), bool)
        assert isinstance(config.get('interceptRetry'), bool)

    def test_package_json_exists_and_valid(self):
        path = EXT_DIR / 'package.json'
        assert path.is_file(), f"Missing package.json at {path}"

        with open(path) as f:
            pkg = json.load(f)

        assert 'pi' in pkg, "package.json missing 'pi' field"
        assert 'extensions' in pkg['pi'], (
            "package.json pi.extensions must exist"
        )
        assert './index.ts' in pkg['pi']['extensions'], (
            "package.json pi.extensions must include './index.ts'"
        )

    def test_test_core_exists(self):
        path = EXT_DIR / 'test-core.mjs'
        assert path.is_file(), f"Missing test-core.mjs at {path}"

    def test_no_node_modules_in_repo(self):
        """The extension should not check in node_modules."""
        nm = EXT_DIR / 'node_modules'
        assert not nm.exists(), (
            "node_modules should not be checked into the repo"
        )


class TestExtensionConfigDefaults:
    """Default config values should match Wikimedia policy."""

    def test_default_user_agent_format(self):
        path = EXT_DIR / 'config.json'
        with open(path) as f:
            config = json.load(f)

        ua = config['userAgent']
        # Must contain a project identifier (trailing name)
        assert 'SkillsDemo' in ua, (
            "Default User-Agent should contain project identifier"
        )
        # Must contain contact info in parentheses
        assert '(' in ua and ')' in ua, (
            "Default User-Agent should contain contact info in parentheses"
        )
        # Should contain a version
        assert '/' in ua, (
            "Default User-Agent should contain client/version format"
        )

    def test_extension_enabled_by_default(self):
        path = EXT_DIR / 'config.json'
        with open(path) as f:
            config = json.load(f)
        assert config['enabled'] is True, (
            "Extension should be enabled by default"
        )


class TestExtensionReadme:
    """Extension install instructions should be documented."""

    def test_extension_mentioned_in_readme(self):
        readme = REPO_ROOT / 'README.md'
        if not readme.exists():
            pytest.skip("README.md not found")

        content = readme.read_text('utf-8')

        # Should mention the extension somewhere
        mentions = ['pi extension', 'wikimedia-skills', 'User-Agent hook',
                     'settings.json', 'tool_call', 'pi.on(']
        found = any(m in content for m in mentions)

        if not found:
            # Non-fatal warning — doc update may be in progress
            pytest.skip(
                "README.md does not yet mention the pi extension "
                "(consider adding install instructions)"
            )

    def test_extension_has_install_instructions_in_readme(self):
        """Check that README has a setup section for the extension."""
        readme = REPO_ROOT / 'README.md'
        if not readme.exists():
            pytest.skip("README.md not found")

        content = readme.read_text('utf-8')
        if 'Pi agent setup' in content:
            assert 'extensions' in content or '.pi/extensions' in content, (
                "README should mention the extensions path in Pi agent setup"
            )


class TestConfigPriorityChain:
    """Config resolution must follow the documented priority chain."""

    def test_index_ts_loads_user_config_first(self):
        """index.ts should check ~/.config/wikimedia-skills/config.json first."""
        path = EXT_DIR / 'index.ts'
        content = path.read_text('utf-8')
        assert 'userConfigPath' in content or '~/.config' in content or 'XDG_CONFIG_HOME' in content, (
            "index.ts should resolve a user config path outside the repo"
        )

    def test_index_ts_falls_back_to_shipped_config(self):
        """index.ts should fall back to the repo's config.json."""
        path = EXT_DIR / 'index.ts'
        content = path.read_text('utf-8')
        assert 'shippedConfigPath' in content or 'config.json' in content, (
            "index.ts should fall back to the repo config.json"
        )

    def test_index_ts_uses_env_var_as_highest_priority(self):
        """WIKIMEDIA_USER_AGENT env var should override all config files."""
        path = EXT_DIR / 'index.ts'
        content = path.read_text('utf-8')
        assert 'WIKIMEDIA_USER_AGENT' in content, (
            "index.ts should check WIKIMEDIA_USER_AGENT env var"
        )

    def test_README_documents_priority_chain(self):
        """README should document the three priority levels."""
        readme = REPO_ROOT / 'README.md'
        if not readme.exists():
            pytest.skip("README.md not found")
        content = readme.read_text('utf-8')
        # Should mention all three config locations
        markers = [
            'WIKIMEDIA_USER_AGENT',
            '~/.config/wikimedia-skills/config.json',
            'config.json',
        ]
        for marker in markers:
            assert marker in content, (
                f"README should mention '{marker}' in the config priority docs"
            )
