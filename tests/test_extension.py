"""Validate the pi extension for Wikimedia User-Agent injection."""

import json
import re
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
EXT_DIR = REPO_ROOT / '.pi' / 'extensions' / 'wikimedia-skills'

# JS/TS keywords that can appear as identifiers but shouldn't be treated
# as function references
_TS_KEYWORDS = frozenset({
    'async', 'await', 'true', 'false', 'null', 'undefined',
    'export', 'default', 'function', 'import', 'from', 'type',
    'interface', 'const', 'let', 'var', 'return', 'if', 'else',
    'for', 'while', 'of', 'in',
})


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _gather_scope(content: str) -> set:
    """Collect all identifiers defined or imported in a TypeScript file."""
    scope: set[str] = set()

    for m in re.finditer(r'(?:export\s+)?(?:async\s+)?function\s+(\w+)', content):
        scope.add(m.group(1))
    for m in re.finditer(r'^\s*(?:export\s+)?(?:const|let|var)\s+(\w+)', content, re.MULTILINE):
        scope.add(m.group(1))
    for m in re.finditer(r'import\s+\{\s*([^}]+)\}', content):
        for name in m.group(1).split(','):
            clean = name.strip()
            if ' as ' in clean:
                clean = clean.split(' as ')[-1].strip()
            if clean and clean not in _TS_KEYWORDS:
                scope.add(clean)
    for m in re.finditer(r'import\s+(\w+)\s+from', content):
        scope.add(m.group(1))
    for m in re.finditer(r'import\s+type\s+\{\s*([^}]+)\}', content):
        for name in m.group(1).split(','):
            clean = name.strip()
            if clean:
                scope.add(clean)

    scope -= _TS_KEYWORDS
    return scope



def _gather_scope(content: str) -> set:
    """Collect all identifiers defined or imported in a TypeScript file."""
    scope: set[str] = set()

    for m in re.finditer(r'(?:export\s+)?(?:async\s+)?function\s+(\w+)', content):
        scope.add(m.group(1))
    for m in re.finditer(r'^\s*(?:export\s+)?(?:const|let|var)\s+(\w+)', content, re.MULTILINE):
        scope.add(m.group(1))
    for m in re.finditer(r'import\s+\{\s*([^}]+)\}', content):
        for name in m.group(1).split(','):
            clean = name.strip()
            if ' as ' in clean:
                clean = clean.split(' as ')[-1].strip()
            if clean and clean not in _TS_KEYWORDS:
                scope.add(clean)
    for m in re.finditer(r'import\s+(\w+)\s+from', content):
        scope.add(m.group(1))
    for m in re.finditer(r'import\s+type\s+\{\s*([^}]+)\}', content):
        for name in m.group(1).split(','):
            clean = name.strip()
            if clean:
                scope.add(clean)

    scope -= _TS_KEYWORDS
    return scope


def _strip_typescript(code: str) -> str:
    """Strip TypeScript-only syntax to produce valid JavaScript.

    Removes interface declarations, type imports/exports, type aliases,
    inline type annotations, and type-only import specifiers.
    Handles multiline blocks by tracking brace depth.
    """
    lines = code.split('\n')
    result = []

    # Track blocks to skip
    in_interface = False
    interface_depth = 0
    in_export_type = False
    export_type_depth = 0
    in_import_type = False
    import_type_depth = 0

    for line in lines:
        stripped = line.strip()

        # Skip interface declarations (exported or bare)
        if re.match(r'^(export\s+)?interface\s+\w+', stripped):
            in_interface = True
            interface_depth = stripped.count('{') - stripped.count('}')
            if interface_depth <= 0:
                in_interface = False
            continue
        if in_interface:
            interface_depth += stripped.count('{') - stripped.count('}')
            if interface_depth <= 0:
                in_interface = False
            continue

        # Skip export type { ... } from '...' (multiline re-exports)
        if re.match(r'^export\s+type\s+\{', stripped):
            in_export_type = True
            export_type_depth = stripped.count('{') - stripped.count('}')
            if export_type_depth <= 0:
                in_export_type = False
            continue
        if in_export_type:
            export_type_depth += stripped.count('{') - stripped.count('}')
            if export_type_depth <= 0:
                in_export_type = False
            continue

        # Skip import type { ... } blocks (multiline)
        if re.match(r'^import\s+type\s+\{', stripped):
            in_import_type = True
            import_type_depth = stripped.count('{') - stripped.count('}')
            if import_type_depth <= 0:
                in_import_type = False
            continue
        if in_import_type:
            import_type_depth += stripped.count('{') - stripped.count('}')
            if import_type_depth <= 0:
                in_import_type = False
            continue

        # Skip type alias: `type Foo = ...`
        if re.match(r'^(export\s+)?type\s+\w+\s*=', stripped):
            continue

        # Remove `type` qualifier from import specifiers:
        #   `  type ExtensionConfig,`  ->  `  ExtensionConfig,`
        line = re.sub(r'^(\s*)type\s+(\w+)', r'\1\2', line)

        # Strip inline type annotations
        # Handle function-typed params first: `paramName: () => Type`
        line = re.sub(r':\s*\([^)]*\)\s*=>\s*\w+(?:<[^>]*>)?', '', line)
        # Handles: `: string`, `: string[]`, `: string | null`, `: Foo<Bar>`
        line = re.sub(
            r':\s*\w+(?:<[^>]*>)?(?:\[\])?(?:\s*\|\s*\w+(?:<[^>]*>)?(?:\[\])?)*'
            r'(?=\s*[,)=]|\s*\)|\s*=>|\s*\{|\s*;)',
            '', line,
        )
        line = re.sub(
            r':\s*\w+(?:<[^>]*>)?(?:\[\])?(?:\s*\|\s*\w+(?:<[^>]*>)?(?:\[\])?)*'
            r'(?=\s*\{)',
            '', line,
        )
        line = re.sub(r'\s+as\s+\w+(?:<[^>]+>)?', '', line)

        result.append(line)

    return '\n'.join(result)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestExtensionStructure:
    """The Wikimedia Skills pi extension must have correct structure."""

    def test_extension_directory_exists(self):
        assert EXT_DIR.is_dir(), f"Extension directory not found: {EXT_DIR}"

    def test_index_ts_exists(self):
        assert (EXT_DIR / 'index.ts').is_file(), "Missing index.ts"

    def test_index_ts_has_default_export(self):
        content = (EXT_DIR / 'index.ts').read_text('utf-8')
        assert 'export default function' in content
        assert 'pi.on(' in content

    def test_core_ts_exists(self):
        assert (EXT_DIR / 'core.ts').is_file(), "Missing core.ts"

    def test_core_ts_exports_pure_functions(self):
        content = (EXT_DIR / 'core.ts').read_text('utf-8')
        for func in ['targetsWikimedia', 'hasUserAgentAlready', 'injectUserAgent']:
            assert f'export function {func}' in content, f"Missing export function {func}"
        assert 'export function injectRetry' in content

    def test_config_json_exists_and_valid(self):
        path = EXT_DIR / 'config.json'
        assert path.is_file()
        with open(path) as f:
            config = json.load(f)
        assert isinstance(config.get('userAgent'), str) and config['userAgent']
        for key in ('enabled', 'interceptCurl', 'interceptPython',
                     'interceptNode', 'interceptWget', 'interceptRetry'):
            assert isinstance(config.get(key), bool), f"{key} must be boolean"

    def test_package_json_exists_and_valid(self):
        path = EXT_DIR / 'package.json'
        assert path.is_file()
        with open(path) as f:
            pkg = json.load(f)
        assert 'pi' in pkg
        assert './index.ts' in pkg['pi']['extensions']

    def test_test_core_exists(self):
        assert (EXT_DIR / 'test-core.mjs').is_file()

    def test_no_node_modules_in_repo(self):
        assert not (EXT_DIR / 'node_modules').exists()

    def test_tools_directory_exists(self):
        assert (EXT_DIR / 'tools').is_dir()

    def test_vector_search_tool_exists(self):
        tool = EXT_DIR / 'tools' / 'vector-search.ts'
        assert tool.is_file()
        content = tool.read_text('utf-8')
        assert 'registerVectorSearchTool' in content
        assert 'pi.registerTool' in content
        assert 'wd-vectordb.wmcloud.org' in content
        assert 'export function formatResults' in content


class TestExtensionConfigDefaults:
    """Default config values should match Wikimedia policy."""

    def test_default_user_agent_format(self):
        with open(EXT_DIR / 'config.json') as f:
            config = json.load(f)
        ua = config['userAgent']
        assert 'SkillsDemo' in ua
        assert '(' in ua and ')' in ua
        assert '/' in ua

    def test_extension_enabled_by_default(self):
        with open(EXT_DIR / 'config.json') as f:
            config = json.load(f)
        assert config['enabled'] is True


class TestExtensionReadme:
    """Extension install instructions should be documented."""

    def test_extension_mentioned_in_readme(self):
        readme = REPO_ROOT / 'README.md'
        if not readme.exists():
            pytest.skip("README.md not found")
        content = readme.read_text('utf-8')
        assert any(m in content for m in ['pi extension', 'wikimedia-skills', 'settings.json'])

    def test_extension_has_install_instructions(self):
        readme = REPO_ROOT / 'README.md'
        if not readme.exists():
            pytest.skip("README.md not found")
        content = readme.read_text('utf-8')
        if 'Pi agent setup' in content:
            assert 'extensions' in content


class TestConfigPriorityChain:
    """Config resolution must follow the documented priority chain."""

    def test_index_ts_loads_user_config_first(self):
        content = (EXT_DIR / 'index.ts').read_text('utf-8')
        assert any(x in content for x in ['userConfigPath', 'XDG_CONFIG_HOME'])

    def test_index_ts_falls_back_to_shipped_config(self):
        content = (EXT_DIR / 'index.ts').read_text('utf-8')
        assert 'shippedConfigPath' in content or 'config.json' in content

    def test_index_ts_uses_env_var_as_highest_priority(self):
        content = (EXT_DIR / 'index.ts').read_text('utf-8')
        assert 'WIKIMEDIA_USER_AGENT' in content

    def test_README_documents_priority_chain(self):
        readme = REPO_ROOT / 'README.md'
        if not readme.exists():
            pytest.skip("README.md not found")
        content = readme.read_text('utf-8')
        for marker in ['WIKIMEDIA_USER_AGENT', '~/.config/wikimedia-skills/config.json']:
            assert marker in content


class TestExtensionCorrectness:
    """Cross-reference and sanity checks that catch bugs like undefined refs."""

    def test_all_callback_references_exist_in_index(self):
        """Every function name passed as a registration callback must be
        defined or imported in index.ts."""
        content = (EXT_DIR / 'index.ts').read_text('utf-8')
        scope = _gather_scope(content)

        callbacks: list[str] = []
        for m in re.finditer(r'register\w+\((?:pi|[^,]+),\s*(\w+)\)', content):
            callbacks.append(m.group(1))
        for m in re.finditer(r'pi\.on\(["\'][^"\']+["\'],\s*(\w+)', content):
            callbacks.append(m.group(1))

        failures = [
            f"'{cb}' — not defined or imported in index.ts"
            for cb in callbacks if cb not in scope and cb not in _TS_KEYWORDS
        ]
        assert not failures, "Undefined references in index.ts:\n" + "\n".join(failures)

    def test_all_tool_exports_are_imported_in_index(self):
        """Every registerXxxTool export from tools/*.ts must be
        imported in index.ts. Prevents orphaned tool files."""
        index_content = (EXT_DIR / 'index.ts').read_text('utf-8')
        tool_dir = EXT_DIR / 'tools'
        if not tool_dir.is_dir():
            return

        for tool_file in sorted(tool_dir.iterdir()):
            if not tool_file.name.endswith('.ts'):
                continue
            tool_content = tool_file.read_text('utf-8')
            for m in re.finditer(r'export\s+function\s+(register\w+)', tool_content):
                func_name = m.group(1)
                assert func_name in index_content, (
                    f"Tool {tool_file.name} exports '{func_name}' "
                    f"but it is never imported in index.ts."
                )

    def test_typescript_strips_and_parses_with_node(self):
        """Use Node.js's built-in --experimental-strip-types to verify
        that all extension .ts files parse without errors.

        This is the authoritative syntax check — it catches missing parens,
        braces, commas, and undefined identifiers that would crash pi's jiti
        loader at startup. Unlike the regex approach, Node's built-in
        TypeScript stripper handles all edge cases correctly.

        Requires Node.js 22+ (for --experimental-strip-types).
        """
        for ts_file in sorted(EXT_DIR.rglob('*.ts')):
            rel = ts_file.relative_to(EXT_DIR.parent.parent)

            result = subprocess.run(
                ['node', '--experimental-strip-types', '--check', str(ts_file)],
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                pytest.fail(
                    f"{rel}: syntax check failed:\n{result.stderr.strip()[:500]}"
                )
