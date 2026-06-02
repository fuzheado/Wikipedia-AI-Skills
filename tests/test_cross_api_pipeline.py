"""Tests for the cross-API pipeline script (newly added)."""

import sys
from unittest.mock import MagicMock, patch
from pathlib import Path

import pytest

# Add assets directory to path so we can import the module directly
_assets = Path(__file__).resolve().parent.parent / \
    '.claude/skills/wikimedia-api-access/assets'
sys.path.insert(0, str(_assets))
import cross_api_pipeline  # noqa: E402


class TestGetTopTitles:
    """Step 1: Pageviews Top endpoint."""

    @patch('cross_api_pipeline.SESSION.get')
    def test_returns_filtered_titles(self, mock_get):
        """Should filter out non-article namespaces and return (title, views) tuples."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'items': [{
                'articles': [
                    {'article': 'Main_Page', 'views': 7000000, 'rank': 1},
                    {'article': 'Special:Search', 'views': 1000000, 'rank': 2},
                    {'article': 'Donald_Trump', 'views': 500000, 'rank': 3},
                    {'article': 'Wikipedia:About', 'views': 300000, 'rank': 4},
                    {'article': 'Albert_Einstein', 'views': 200000, 'rank': 5},
                    {'article': 'Python_(programming_language)', 'views': 150000, 'rank': 6},
                ]
            }]
        }
        mock_get.return_value = mock_response

        result = cross_api_pipeline.get_top_titles(limit=10)

        assert len(result) == 3  # 6 total - 3 skipped (Main_Page, Special:Search, Wikipedia:About)
        assert result[0] == ('Donald_Trump', 500000)
        assert result[1] == ('Albert_Einstein', 200000)
        assert result[2] == ('Python_(programming_language)', 150000)

    @patch('cross_api_pipeline.SESSION.get')
    def test_respects_limit(self, mock_get):
        """Should return at most 'limit' results."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'items': [{
                'articles': [
                    {'article': 'Article_A', 'views': 100, 'rank': 1},
                    {'article': 'Article_B', 'views': 90, 'rank': 2},
                    {'article': 'Article_C', 'views': 80, 'rank': 3},
                ]
            }]
        }
        mock_get.return_value = mock_response

        result = cross_api_pipeline.get_top_titles(limit=2)
        assert len(result) == 2

    @patch('cross_api_pipeline.SESSION.get')
    def test_handles_api_error(self, mock_get):
        """Should return empty list on non-200 response."""
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.text = '{"detail": "Rate limited"}'
        mock_get.return_value = mock_response

        result = cross_api_pipeline.get_top_titles(limit=10)
        assert result == []


class TestGetWikidataIds:
    """Step 2: Wikidata ID resolution, with title normalization."""

    @patch('cross_api_pipeline.SESSION.get')
    def test_normalizes_underscores_to_spaces(self, mock_get):
        """The critical normalization: Pageviews underscores -> Action API spaces."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'query': {
                'pages': {
                    '123': {
                        'pageid': 123,
                        'ns': 0,
                        'title': 'Donald Trump',  # Action API returns spaces
                        'pageprops': {'wikibase_item': 'Q22686'},
                    }
                }
            }
        }
        mock_get.return_value = mock_response

        # Pageviews returns underscores, must be matched to space-keyed dict
        result = cross_api_pipeline.get_wikidata_ids([('Donald_Trump', 500000)])
        assert len(result) == 1
        assert result[0] == ('Donald_Trump', 500000, 'Q22686')

    @patch('cross_api_pipeline.SESSION.get')
    def test_skips_missing_items(self, mock_get):
        """Titles without a Wikidata item should be skipped."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'query': {
                'pages': {
                    '-1': {
                        'ns': 0,
                        'title': 'Nonexistent Page',
                        'missing': True,
                    }
                }
            }
        }
        mock_get.return_value = mock_response

        result = cross_api_pipeline.get_wikidata_ids([('Nonexistent_Page', 100)])
        assert result == []

    @patch('cross_api_pipeline.SESSION.get')
    def test_batches_by_50(self, mock_get):
        """Should split into batches of 50 and make multiple calls."""
        titles = [(f'Article_{i}', 100 - i) for i in range(75)]

        def side_effect(url, params=None, **kwargs):
            mock = MagicMock()
            mock.status_code = 200
            batch = params.get('titles', '').split('|')
            pages = {}
            for t in batch:
                pages[str(hash(t))] = {
                    'pageid': hash(t),
                    'ns': 0,
                    'title': t.replace('_', ' '),
                    'pageprops': {'wikibase_item': f'Q{abs(hash(t)) % 100000}'},
                }
            mock.json.return_value = {'query': {'pages': pages}}
            return mock

        mock_get.side_effect = side_effect
        result = cross_api_pipeline.get_wikidata_ids(titles)
        assert len(result) == 75
        assert mock_get.call_count == 2  # 75 titles = 2 batches (50 + 25)


class TestClassifyEntities:
    """Step 3: Entity classification via P31."""

    @patch('cross_api_pipeline.SESSION.get')
    def test_identifies_humans(self, mock_get):
        """Should detect instance of human (Q5)."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'entities': {
                'Q22686': {
                    'claims': {
                        'P31': [{
                            'mainsnak': {
                                'datavalue': {
                                    'value': {'id': 'Q5'},
                                    'type': 'wikibase-entityid',
                                }
                            }
                        }]
                    }
                }
            }
        }
        mock_get.return_value = mock_response

        result = cross_api_pipeline.classify_entities([('Donald_Trump', 500000, 'Q22686')])
        assert 'Q22686' in result
        assert 'human' in result['Q22686']

    @patch('cross_api_pipeline.SESSION.get')
    def test_multiple_types(self, mock_get):
        """An entity can have multiple P31 values."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'entities': {
                'Q123': {
                    'claims': {
                        'P31': [
                            {
                                'mainsnak': {
                                    'datavalue': {
                                        'value': {'id': 'Q515'},
                                        'type': 'wikibase-entityid',
                                    }
                                }
                            },
                            {
                                'mainsnak': {
                                    'datavalue': {
                                        'value': {'id': 'Q43229'},
                                        'type': 'wikibase-entityid',
                                    }
                                }
                            },
                        ]
                    }
                }
            }
        }
        mock_get.return_value = mock_response

        result = cross_api_pipeline.classify_entities([('Some_Place', 100, 'Q123')])
        assert 'Q123' in result
        assert 'city' in result['Q123']
        assert 'organization' in result['Q123']

    @patch('cross_api_pipeline.SESSION.get')
    def test_unknown_type_omitted(self, mock_get):
        """Entities without known P31 types should be absent from result."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'entities': {
                'Q999': {
                    'claims': {
                        'P31': [{
                            'mainsnak': {
                                'datavalue': {
                                    'value': {'id': 'Q1234567'},  # not in KNOWN_TYPES
                                    'type': 'wikibase-entityid',
                                }
                            }
                        }]
                    }
                }
            }
        }
        mock_get.return_value = mock_response

        result = cross_api_pipeline.classify_entities([('Obscure_Thing', 50, 'Q999')])
        assert 'Q999' not in result  # not a known type, excluded


class TestCountCitationNeeded:
    """Step 4: Content analysis via parse."""

    @patch('cross_api_pipeline.SESSION.get')
    def test_counts_cn_templates(self, mock_get):
        """Should count {{citation needed}} instances (case-insensitive)."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'parse': {
                'wikitext': {
                    '*': 'Some text{{citation needed}}. More text{{citation needed}}. And{{Citation needed|reason=foo}}.'
                }
            }
        }
        mock_get.return_value = mock_response

        count = cross_api_pipeline.count_citation_needed('Albert_Einstein')
        assert count == 3

    @patch('cross_api_pipeline.SESSION.get')
    def test_returns_zero_on_empty(self, mock_get):
        """Should return 0 when no citation needed templates exist."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'parse': {
                'wikitext': {'*': 'Clean article with no flags.'}
            }
        }
        mock_get.return_value = mock_response

        count = cross_api_pipeline.count_citation_needed('Perfect_Article')
        assert count == 0

    @patch('cross_api_pipeline.SESSION.get')
    def test_normalizes_title(self, mock_get):
        """Should pass space-normalized title to the parse API."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'parse': {'wikitext': {'*': ''}}
        }
        mock_get.return_value = mock_response

        cross_api_pipeline.count_citation_needed('Donald_Trump')
        # Verify the request used spaces, not underscores
        call_args = mock_get.call_args
        assert call_args is not None
        assert 'page=Donald Trump' in str(call_args) or 'Donald Trump' in str(call_args[1].get('params', {}))


class TestSkipPrefixes:
    """Namespace filtering configuration."""

    def test_common_prefixes_covered(self):
        """Should filter typical non-article namespaces."""
        prefixes = cross_api_pipeline.SKIP_PREFIXES
        assert 'Special:' in prefixes
        assert 'Wikipedia:' in prefixes
        assert 'Template:' in prefixes
        assert 'Category:' in prefixes
        assert 'Main_Page' in prefixes
        assert 'File:' in prefixes
        assert 'Help:' in prefixes
        assert 'Portal:' in prefixes


class TestKnownTypes:
    """P31 type mapping."""

    def test_key_types_present(self):
        """Should cover the most common entity types."""
        types = cross_api_pipeline.KNOWN_TYPES
        assert types['Q5'] == 'human'
        assert types['Q11424'] == 'film'
        assert types['Q515'] == 'city'
        assert types['Q16521'] == 'taxon/species'
        assert types['Q7889'] == 'video game'
        assert types['Q4830453'] == 'company'
        assert types['Q43229'] == 'organization'
        assert types['Q3918'] == 'university'
