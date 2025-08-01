"""JSON 파일 설정 로딩 테스트"""

import json
import tempfile
from pathlib import Path

import pytest

from sd_tagfilter.config import ConfigLoader, load_config_from_file


class TestJsonConfigLoading:
    """JSON 파일 설정 로딩 테스트"""

    def test_load_simple_json_config(self):
        """간단한 JSON 설정 로딩 테스트"""
        config_data = {
            'version': '1.0',
            'global_settings': {'case_sensitive': False, 'default_priority': 50},
            'rules': [
                {
                    'filter_type': 'plain_keyword',
                    'pattern': 'nsfw',
                    'priority': 100,
                    'enabled': True,
                    'description': 'NSFW 키워드 제거',
                },
                {
                    'filter_type': 'regex',
                    'pattern': '\\b(nude|naked)\\b',
                    'priority': 90,
                    'enabled': True,
                    'description': '특정 단어 정확히 매칭',
                },
            ],
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f, indent=2)
            f.flush()

            config = ConfigLoader.load_from_json(f.name)

            assert config.version == '1.0'
            assert len(config.rules) == 2
            assert config.global_settings['case_sensitive'] is False
            assert config.global_settings['default_priority'] == 50

            # 첫 번째 규칙 검증
            assert config.rules[0].filter_type == 'plain_keyword'
            assert config.rules[0].pattern == 'nsfw'
            assert config.rules[0].priority == 100
            assert config.rules[0].enabled is True
            assert config.rules[0].description == 'NSFW 키워드 제거'

            # 두 번째 규칙 검증
            assert config.rules[1].filter_type == 'regex'
            assert config.rules[1].pattern == '\\b(nude|naked)\\b'
            assert config.rules[1].priority == 90

            # 파일 정리
            Path(f.name).unlink()

    def test_load_group_filter_rules(self):
        """그룹 필터 규칙 로딩 테스트"""
        config_data = {
            'version': '1.0',
            'rules': [
                {
                    'filter_type': 'group',
                    'patterns': ['steam', 'sweat', 'blush'],
                    'priority': 100,
                    'enabled': True,
                    'description': 'NSFW 암시 조합 제거',
                },
                {
                    'filter_type': 'group',
                    'patterns': ['nude', 'naked'],
                    'priority': 95,
                    'enabled': False,
                    'description': '명시적 NSFW 조합 제거 (비활성화)',
                },
            ],
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f, indent=2)
            f.flush()

            config = ConfigLoader.load_from_json(f.name)

            assert len(config.rules) == 2

            # 첫 번째 그룹 규칙
            assert config.rules[0].filter_type == 'group'
            assert config.rules[0].patterns == ['steam', 'sweat', 'blush']
            assert config.rules[0].priority == 100
            assert config.rules[0].enabled is True

            # 두 번째 그룹 규칙
            assert config.rules[1].filter_type == 'group'
            assert config.rules[1].patterns == ['nude', 'naked']
            assert config.rules[1].priority == 95
            assert config.rules[1].enabled is False

            # 파일 정리
            Path(f.name).unlink()

    def test_load_replacement_rules(self):
        """치환 규칙 로딩 테스트"""
        config_data = {
            'version': '1.0',
            'rules': [
                {
                    'filter_type': 'replace',
                    'pattern': 'bad_word',
                    'replacement': 'good_word',
                    'priority': 50,
                    'enabled': True,
                    'description': '부적절한 단어 교체',
                },
                {
                    'filter_type': 'replace_capture',
                    'pattern': '(.*)_old',
                    'replacement': '$1_new',
                    'priority': 40,
                    'enabled': True,
                    'description': '_old를 _new로 교체',
                },
            ],
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f, indent=2)
            f.flush()

            config = ConfigLoader.load_from_json(f.name)

            assert len(config.rules) == 2

            # 첫 번째 치환 규칙
            assert config.rules[0].filter_type == 'replace'
            assert config.rules[0].pattern == 'bad_word'
            assert config.rules[0].replacement == 'good_word'
            assert config.rules[0].priority == 50

            # 두 번째 치환 규칙
            assert config.rules[1].filter_type == 'replace_capture'
            assert config.rules[1].pattern == '(.*)_old'
            assert config.rules[1].replacement == '$1_new'
            assert config.rules[1].priority == 40

            # 파일 정리
            Path(f.name).unlink()

    def test_load_wildcard_rules(self):
        """와일드카드 규칙 로딩 테스트"""
        config_data = {
            'version': '1.0',
            'rules': [
                {
                    'filter_type': 'wildcard',
                    'pattern': '*_hair',
                    'priority': 60,
                    'enabled': True,
                    'description': '모든 머리카락 태그 제거',
                },
                {
                    'filter_type': 'wildcard',
                    'pattern': 'temp_*',
                    'priority': 30,
                    'enabled': False,
                    'description': '임시 태그 제거 (비활성화)',
                },
            ],
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f, indent=2)
            f.flush()

            config = ConfigLoader.load_from_json(f.name)

            assert len(config.rules) == 2

            # 첫 번째 와일드카드 규칙
            assert config.rules[0].filter_type == 'wildcard'
            assert config.rules[0].pattern == '*_hair'
            assert config.rules[0].priority == 60
            assert config.rules[0].enabled is True

            # 두 번째 와일드카드 규칙
            assert config.rules[1].filter_type == 'wildcard'
            assert config.rules[1].pattern == 'temp_*'
            assert config.rules[1].priority == 30
            assert config.rules[1].enabled is False

            # 파일 정리
            Path(f.name).unlink()

    def test_load_mixed_rules(self):
        """혼합 규칙 로딩 테스트"""
        config_data = {
            'version': '1.0',
            'global_settings': {'case_sensitive': True, 'max_rules': 50},
            'rules': [
                {
                    'filter_type': 'group',
                    'patterns': ['steam', 'sweat'],
                    'priority': 100,
                    'enabled': True,
                    'description': '그룹 필터',
                },
                {
                    'filter_type': 'regex',
                    'pattern': '\\d{4}_\\d{2}_\\d{2}',
                    'priority': 80,
                    'enabled': True,
                    'description': '날짜 형식 제거',
                },
                {
                    'filter_type': 'wildcard',
                    'pattern': '*_debug',
                    'priority': 60,
                    'enabled': False,
                    'description': '디버그 태그 제거',
                },
                {
                    'filter_type': 'plain_keyword',
                    'pattern': 'test',
                    'priority': 40,
                    'enabled': True,
                    'description': '테스트 키워드',
                },
            ],
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f, indent=2)
            f.flush()

            config = ConfigLoader.load_from_json(f.name)

            assert config.version == '1.0'
            assert len(config.rules) == 4
            assert config.global_settings['case_sensitive'] is True
            assert config.global_settings['max_rules'] == 50

            # 규칙 타입별 검증
            assert config.rules[0].filter_type == 'group'
            assert config.rules[1].filter_type == 'regex'
            assert config.rules[2].filter_type == 'wildcard'
            assert config.rules[3].filter_type == 'plain_keyword'

            # 파일 정리
            Path(f.name).unlink()

    def test_load_config_from_file_auto_detect(self):
        """파일 확장자 자동 감지 테스트"""
        config_data = {
            'version': '1.0',
            'rules': [{'filter_type': 'plain_keyword', 'pattern': 'test', 'priority': 50, 'enabled': True}],
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f, indent=2)
            f.flush()

            config = load_config_from_file(f.name)

            assert config.version == '1.0'
            assert len(config.rules) == 1
            assert config.rules[0].pattern == 'test'

            # 파일 정리
            Path(f.name).unlink()

    def test_invalid_json_format(self):
        """잘못된 JSON 형식 테스트"""
        invalid_json = '{"version": "1.0", "rules": [{'

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write(invalid_json)
            f.flush()

            with pytest.raises(json.JSONDecodeError):
                ConfigLoader.load_from_json(f.name)

            # 파일 정리
            Path(f.name).unlink()

    def test_invalid_filter_type(self):
        """잘못된 필터 타입 테스트"""
        config_data = {'version': '1.0', 'rules': [{'filter_type': 'invalid_type', 'pattern': 'test', 'priority': 50}]}

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f, indent=2)
            f.flush()

            with pytest.raises(ValueError, match='Invalid filter type'):
                ConfigLoader.load_from_json(f.name)

            # 파일 정리
            Path(f.name).unlink()

    def test_invalid_priority(self):
        """잘못된 우선순위 테스트"""
        config_data = {
            'version': '1.0',
            'rules': [{'filter_type': 'plain_keyword', 'pattern': 'test', 'priority': -10}],
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f, indent=2)
            f.flush()

            with pytest.raises(ValueError, match='Priority must be non-negative'):
                ConfigLoader.load_from_json(f.name)

            # 파일 정리
            Path(f.name).unlink()

    def test_empty_group_patterns(self):
        """빈 그룹 패턴 테스트"""
        config_data = {'version': '1.0', 'rules': [{'filter_type': 'group', 'patterns': [], 'priority': 50}]}

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f, indent=2)
            f.flush()

            with pytest.raises(ValueError, match='Group filter must have at least one pattern'):
                ConfigLoader.load_from_json(f.name)

            # 파일 정리
            Path(f.name).unlink()

    def test_file_not_found(self):
        """파일이 존재하지 않는 경우 테스트"""
        with pytest.raises(FileNotFoundError):
            ConfigLoader.load_from_json('nonexistent_file.json')

    def test_get_enabled_rules(self):
        """활성화된 규칙만 가져오기 테스트"""
        config_data = {
            'version': '1.0',
            'rules': [
                {'filter_type': 'plain_keyword', 'pattern': 'enabled_rule', 'priority': 50, 'enabled': True},
                {'filter_type': 'plain_keyword', 'pattern': 'disabled_rule', 'priority': 40, 'enabled': False},
                {'filter_type': 'regex', 'pattern': '\\btest\\b', 'priority': 30, 'enabled': True},
            ],
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f, indent=2)
            f.flush()

            config = ConfigLoader.load_from_json(f.name)
            enabled_rules = config.get_enabled_rules()

            assert len(enabled_rules) == 2
            assert enabled_rules[0].pattern == 'enabled_rule'
            assert enabled_rules[1].pattern == '\\btest\\b'

            # 파일 정리
            Path(f.name).unlink()

    def test_get_rules_by_priority(self):
        """우선순위 순으로 정렬된 규칙 가져오기 테스트"""
        config_data = {
            'version': '1.0',
            'rules': [
                {'filter_type': 'plain_keyword', 'pattern': 'low_priority', 'priority': 10, 'enabled': True},
                {'filter_type': 'plain_keyword', 'pattern': 'high_priority', 'priority': 100, 'enabled': True},
                {'filter_type': 'regex', 'pattern': 'medium_priority', 'priority': 50, 'enabled': True},
            ],
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f, indent=2)
            f.flush()

            config = ConfigLoader.load_from_json(f.name)
            sorted_rules = config.get_rules_by_priority()

            assert len(sorted_rules) == 3
            assert sorted_rules[0].pattern == 'high_priority'
            assert sorted_rules[0].priority == 100
            assert sorted_rules[1].pattern == 'medium_priority'
            assert sorted_rules[1].priority == 50
            assert sorted_rules[2].pattern == 'low_priority'
            assert sorted_rules[2].priority == 10

            # 파일 정리
            Path(f.name).unlink()

    def test_to_filter_rules_conversion(self):
        """FilterRule 객체로 변환 테스트"""
        config_data = {
            'version': '1.0',
            'rules': [
                {
                    'filter_type': 'plain_keyword',
                    'pattern': 'test',
                    'priority': 50,
                    'enabled': True,
                    'description': '테스트 규칙',
                },
                {
                    'filter_type': 'group',
                    'patterns': ['a', 'b'],
                    'priority': 60,
                    'enabled': True,
                    'description': '그룹 규칙',
                },
            ],
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f, indent=2)
            f.flush()

            config = ConfigLoader.load_from_json(f.name)
            filter_rules = config.to_filter_rules()

            assert len(filter_rules) == 2

            # 첫 번째 규칙은 FilterRule
            from sd_tagfilter.base import FilterRule

            assert isinstance(filter_rules[0], FilterRule)
            assert filter_rules[0].pattern == 'test'

            # 두 번째 규칙은 GroupFilterRule
            from sd_tagfilter.base import GroupFilterRule

            assert isinstance(filter_rules[1], GroupFilterRule)

            # 파일 정리
            Path(f.name).unlink()
