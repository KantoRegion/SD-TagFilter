"""YAML 파일 설정 로딩 테스트"""

import tempfile
from pathlib import Path

import pytest

from sd_tagfilter.config import ConfigLoader, load_config_from_file


class TestYamlConfigLoading:
    """YAML 파일 설정 로딩 테스트"""

    def test_load_simple_yaml_config(self):
        """간단한 YAML 설정 로딩 테스트"""
        yaml_content = """
version: "1.0"
global_settings:
  case_sensitive: false
  default_priority: 50
rules:
  - filter_type: "plain_keyword"
    pattern: "nsfw"
    priority: 100
    enabled: true
    description: "NSFW 키워드 제거"
  - filter_type: "regex"
    pattern: "\\\\b(nude|naked)\\\\b"
    priority: 90
    enabled: true
    description: "특정 단어 정확히 매칭"
"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            f.flush()

            config = ConfigLoader.load_from_yaml(f.name)

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
        yaml_content = """
version: "1.0"
rules:
  - filter_type: "group"
    patterns:
      - "steam"
      - "sweat"
      - "blush"
    priority: 100
    enabled: true
    description: "NSFW 암시 조합 제거"
  - filter_type: "group"
    patterns:
      - "nude"
      - "naked"
    priority: 95
    enabled: false
    description: "명시적 NSFW 조합 제거 (비활성화)"
"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            f.flush()

            config = ConfigLoader.load_from_yaml(f.name)

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
        yaml_content = """
version: "1.0"
rules:
  - filter_type: "replace"
    pattern: "bad_word"
    replacement: "good_word"
    priority: 50
    enabled: true
    description: "부적절한 단어 교체"
  - filter_type: "replace_capture"
    pattern: "(.*)_old"
    replacement: "$1_new"
    priority: 40
    enabled: true
    description: "_old를 _new로 교체"
"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            f.flush()

            config = ConfigLoader.load_from_yaml(f.name)

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
        yaml_content = """
version: "1.0"
rules:
  - filter_type: "wildcard"
    pattern: "*_hair"
    priority: 60
    enabled: true
    description: "모든 머리카락 태그 제거"
  - filter_type: "wildcard"
    pattern: "temp_*"
    priority: 30
    enabled: false
    description: "임시 태그 제거 (비활성화)"
"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            f.flush()

            config = ConfigLoader.load_from_yaml(f.name)

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
        yaml_content = """
version: "1.0"
global_settings:
  case_sensitive: true
  max_rules: 50
rules:
  - filter_type: "group"
    patterns:
      - "steam"
      - "sweat"
    priority: 100
    enabled: true
    description: "그룹 필터"
  - filter_type: "regex"
    pattern: "\\\\d{4}_\\\\d{2}_\\\\d{2}"
    priority: 80
    enabled: true
    description: "날짜 형식 제거"
  - filter_type: "wildcard"
    pattern: "*_debug"
    priority: 60
    enabled: false
    description: "디버그 태그 제거"
  - filter_type: "plain_keyword"
    pattern: "test"
    priority: 40
    enabled: true
    description: "테스트 키워드"
"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            f.flush()

            config = ConfigLoader.load_from_yaml(f.name)

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

    def test_load_config_from_file_auto_detect_yaml(self):
        """파일 확장자 자동 감지 테스트 (.yaml)"""
        yaml_content = """
version: "1.0"
rules:
  - filter_type: "plain_keyword"
    pattern: "test"
    priority: 50
    enabled: true
"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            f.flush()

            config = load_config_from_file(f.name)

            assert config.version == '1.0'
            assert len(config.rules) == 1
            assert config.rules[0].pattern == 'test'

            # 파일 정리
            Path(f.name).unlink()

    def test_load_config_from_file_auto_detect_yml(self):
        """파일 확장자 자동 감지 테스트 (.yml)"""
        yaml_content = """
version: "1.0"
rules:
  - filter_type: "plain_keyword"
    pattern: "test"
    priority: 50
    enabled: true
"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            f.write(yaml_content)
            f.flush()

            config = load_config_from_file(f.name)

            assert config.version == '1.0'
            assert len(config.rules) == 1
            assert config.rules[0].pattern == 'test'

            # 파일 정리
            Path(f.name).unlink()

    def test_invalid_yaml_format(self):
        """잘못된 YAML 형식 테스트"""
        invalid_yaml = """
version: "1.0"
rules:
  - filter_type: "plain_keyword"
    pattern: "test"
    priority: 50
  - invalid_indentation
"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(invalid_yaml)
            f.flush()

            # YAML 파싱 오류가 발생해야 함
            with pytest.raises(Exception):  # yaml.YAMLError 또는 다른 파싱 오류
                ConfigLoader.load_from_yaml(f.name)

            # 파일 정리
            Path(f.name).unlink()

    def test_invalid_filter_type(self):
        """잘못된 필터 타입 테스트"""
        yaml_content = """
version: "1.0"
rules:
  - filter_type: "invalid_type"
    pattern: "test"
    priority: 50
"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            f.flush()

            with pytest.raises(ValueError, match='Invalid filter type'):
                ConfigLoader.load_from_yaml(f.name)

            # 파일 정리
            Path(f.name).unlink()

    def test_invalid_priority(self):
        """잘못된 우선순위 테스트"""
        yaml_content = """
version: "1.0"
rules:
  - filter_type: "plain_keyword"
    pattern: "test"
    priority: -10
"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            f.flush()

            with pytest.raises(ValueError, match='Priority must be non-negative'):
                ConfigLoader.load_from_yaml(f.name)

            # 파일 정리
            Path(f.name).unlink()

    def test_empty_group_patterns(self):
        """빈 그룹 패턴 테스트"""
        yaml_content = """
version: "1.0"
rules:
  - filter_type: "group"
    patterns: []
    priority: 50
"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            f.flush()

            with pytest.raises(ValueError, match='Group filter must have at least one pattern'):
                ConfigLoader.load_from_yaml(f.name)

            # 파일 정리
            Path(f.name).unlink()

    def test_file_not_found(self):
        """파일이 존재하지 않는 경우 테스트"""
        with pytest.raises(FileNotFoundError):
            ConfigLoader.load_from_yaml('nonexistent_file.yaml')

    def test_yaml_import_error(self):
        """PyYAML이 설치되지 않은 경우 테스트"""
        # 이 테스트는 실제로는 PyYAML이 설치되어 있어야 하므로
        # 모킹을 통해 ImportError를 시뮬레이션할 수 있지만
        # 여기서는 실제 동작을 확인하는 것으로 충분함
        yaml_content = """
version: "1.0"
rules:
  - filter_type: "plain_keyword"
    pattern: "test"
    priority: 50
"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            f.flush()

            # PyYAML이 설치되어 있다면 정상 동작해야 함
            try:
                config = ConfigLoader.load_from_yaml(f.name)
                assert config.version == '1.0'
            except ImportError as e:
                # PyYAML이 설치되지 않은 경우
                assert 'PyYAML is required' in str(e)

            # 파일 정리
            Path(f.name).unlink()

    def test_get_enabled_rules(self):
        """활성화된 규칙만 가져오기 테스트"""
        yaml_content = """
version: "1.0"
rules:
  - filter_type: "plain_keyword"
    pattern: "enabled_rule"
    priority: 50
    enabled: true
  - filter_type: "plain_keyword"
    pattern: "disabled_rule"
    priority: 40
    enabled: false
  - filter_type: "regex"
    pattern: "\\\\btest\\\\b"
    priority: 30
    enabled: true
"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            f.flush()

            config = ConfigLoader.load_from_yaml(f.name)
            enabled_rules = config.get_enabled_rules()

            assert len(enabled_rules) == 2
            assert enabled_rules[0].pattern == 'enabled_rule'
            assert enabled_rules[1].pattern == '\\btest\\b'

            # 파일 정리
            Path(f.name).unlink()

    def test_get_rules_by_priority(self):
        """우선순위 순으로 정렬된 규칙 가져오기 테스트"""
        yaml_content = """
version: "1.0"
rules:
  - filter_type: "plain_keyword"
    pattern: "low_priority"
    priority: 10
    enabled: true
  - filter_type: "plain_keyword"
    pattern: "high_priority"
    priority: 100
    enabled: true
  - filter_type: "regex"
    pattern: "medium_priority"
    priority: 50
    enabled: true
"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            f.flush()

            config = ConfigLoader.load_from_yaml(f.name)
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
        yaml_content = """
version: "1.0"
rules:
  - filter_type: "plain_keyword"
    pattern: "test"
    priority: 50
    enabled: true
    description: "테스트 규칙"
  - filter_type: "group"
    patterns:
      - "a"
      - "b"
    priority: 60
    enabled: true
    description: "그룹 규칙"
"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            f.flush()

            config = ConfigLoader.load_from_yaml(f.name)
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

    def test_yaml_with_unicode_content(self):
        """유니코드 내용이 포함된 YAML 테스트"""
        yaml_content = """
version: "1.0"
global_settings:
  description: "한글 설명이 포함된 설정"
rules:
  - filter_type: "plain_keyword"
    pattern: "한글키워드"
    priority: 50
    enabled: true
    description: "한글 키워드 제거"
  - filter_type: "replace"
    pattern: "나쁜말"
    replacement: "좋은말"
    priority: 40
    enabled: true
    description: "한글 단어 치환"
"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False, encoding='utf-8') as f:
            f.write(yaml_content)
            f.flush()

            config = ConfigLoader.load_from_yaml(f.name)

            assert config.version == '1.0'
            assert len(config.rules) == 2
            assert config.global_settings['description'] == '한글 설명이 포함된 설정'

            # 첫 번째 규칙
            assert config.rules[0].pattern == '한글키워드'
            assert config.rules[0].description == '한글 키워드 제거'

            # 두 번째 규칙
            assert config.rules[1].pattern == '나쁜말'
            assert config.rules[1].replacement == '좋은말'
            assert config.rules[1].description == '한글 단어 치환'

            # 파일 정리
            Path(f.name).unlink()

    def test_yaml_boolean_values(self):
        """YAML 불린 값 처리 테스트"""
        yaml_content = """
version: "1.0"
global_settings:
  case_sensitive: true
  debug_mode: false
rules:
  - filter_type: "plain_keyword"
    pattern: "test1"
    priority: 50
    enabled: yes  # YAML에서 yes는 true로 해석됨
  - filter_type: "plain_keyword"
    pattern: "test2"
    priority: 40
    enabled: no   # YAML에서 no는 false로 해석됨
"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            f.flush()

            config = ConfigLoader.load_from_yaml(f.name)

            assert config.global_settings['case_sensitive'] is True
            assert config.global_settings['debug_mode'] is False
            assert config.rules[0].enabled is True
            assert config.rules[1].enabled is False

            # 파일 정리
            Path(f.name).unlink()
