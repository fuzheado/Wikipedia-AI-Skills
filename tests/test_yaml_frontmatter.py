"""Validate YAML frontmatter in all skill SKILL.md files."""

import yaml
import pytest
from conftest import SKILL_NAMES, read_skill  # noqa: E402


def extract_yaml_frontmatter(text):
    """Extract YAML frontmatter from a SKILL.md file.

    Returns the parsed dict, or None if no valid frontmatter is found.
    """
    lines = text.split('\n')
    if not lines or lines[0].strip() != '---':
        return None
    end_idx = None
    for i in range(1, len(lines)):
        if lines[i].strip() == '---':
            end_idx = i
            break
    if end_idx is None:
        return None
    yaml_block = '\n'.join(lines[1:end_idx])
    return yaml.safe_load(yaml_block)


class TestYamlFrontmatter:
    """Every SKILL.md must have valid YAML frontmatter with required fields."""

    @pytest.mark.parametrize('skill_name', SKILL_NAMES)
    def test_frontmatter_exists(self, skill_name):
        """All skills must have YAML frontmatter."""
        text = read_skill(skill_name)
        frontmatter = extract_yaml_frontmatter(text)
        assert frontmatter is not None, (
            f"{skill_name}/SKILL.md is missing YAML frontmatter "
            f"(must start with '---')"
        )

    @pytest.mark.parametrize('skill_name', SKILL_NAMES)
    def test_required_fields(self, skill_name):
        """Frontmatter must contain name, description, license, compatibility, last_verified."""
        text = read_skill(skill_name)
        frontmatter = extract_yaml_frontmatter(text)
        assert frontmatter is not None

        for field in ('name', 'description', 'license', 'compatibility', 'last_verified'):
            assert field in frontmatter, (
                f"{skill_name}/SKILL.md frontmatter missing '{field}'"
            )
            assert frontmatter[field], (
                f"{skill_name}/SKILL.md frontmatter '{field}' is empty"
            )

    @pytest.mark.parametrize('skill_name', SKILL_NAMES)
    def test_last_verified_is_date(self, skill_name):
        """last_verified must be a valid ISO-8601 date."""
        import re
        text = read_skill(skill_name)
        frontmatter = extract_yaml_frontmatter(text)
        assert frontmatter is not None
        lv = frontmatter.get('last_verified', '')
        assert re.match(r'^\d{4}-\d{2}-\d{2}$', str(lv)), (
            f"{skill_name}/SKILL.md last_verified='{lv}' is not a valid ISO-8601 date"
        )

    @pytest.mark.parametrize('skill_name', SKILL_NAMES)
    def test_description_length(self, skill_name):
        """Description should be concise (< 400 chars) for agent discovery."""
        text = read_skill(skill_name)
        frontmatter = extract_yaml_frontmatter(text)
        desc = frontmatter.get('description', '')
        assert len(desc) < 400, (
            f"{skill_name}/SKILL.md description is {len(desc)} chars "
            f"(max 400)"
        )

    @pytest.mark.parametrize('skill_name', SKILL_NAMES)
    def test_license_is_mit(self, skill_name):
        """All skills should use the MIT license per project decision."""
        text = read_skill(skill_name)
        frontmatter = extract_yaml_frontmatter(text)
        assert frontmatter.get('license') == 'MIT', (
            f"{skill_name}/SKILL.md license should be 'MIT'"
        )

    @pytest.mark.parametrize('skill_name', SKILL_NAMES)
    def test_frontmatter_name_matches_directory(self, skill_name):
        """Frontmatter 'name' should match the skill directory name."""
        text = read_skill(skill_name)
        frontmatter = extract_yaml_frontmatter(text)
        assert frontmatter is not None
        assert frontmatter['name'] == skill_name, (
            f"frontmatter name '{frontmatter['name']}' doesn't match "
            f"directory '{skill_name}'"
        )
