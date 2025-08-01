"""텍스트 파일 설정 로딩 테스트"""

import tempfile
from pathlib import Path

import pytest

from sd_tagfilter.config import ConfigLoader, load_config_from_file


class TestTextConfigLoading:
    """텍스트 파일 설정 로딩 테스트"""

    def test_load_simple_keywords(self):
        """간단한 키워드 로딩 테스트"""
        content = """# 테스트 필터 규칙
nsfw
adult
explicit
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(content)
            f.flush()

            config = ConfigLoader.load_from_text(f.name)

            assert len(config.rules) == 3
            assert config.rules[0].filter_type == 'plain_keyword'
            assert config.rules[0].pattern == 'nsfw'
            assert config.rules[1].pattern == 'adult'
            assert config.rules[2].pattern == 'explicit'

            # 파일 정리
            Path(f.name).unlink()

    def test_load_regex_patterns(self):
        """정규식 패턴 로딩 테스트"""
        content = """/\\b(nude|naked)\\b/
/\\d{4}_\\d{2}_\\d{2}/
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(content)
            f.flush()

            config = ConfigLoader.load_from_text(f.name)

            assert len(config.rules) == 2
            assert config.rules[0].filter_type == 'regex'
            assert config.rules[0].pattern == '\\b(nude|naked)\\b'
            assert config.rules[1].filter_type == 'regex'
            assert config.rules[1].pattern == '\\d{4}_\\d{2}_\\d{2}'

            # 파일 정리
            Path(f.name).unlink()

    def test_load_replacement_patterns(self):
        """치환 패턴 로딩 테스트"""
        content = """bad_word||good_word
inappropriate||appropriate
old_style||new_style
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(content)
            f.flush()

            config = ConfigLoader.load_from_text(f.name)

            assert len(config.rules) == 3
            assert config.rules[0].filter_type == 'replace'
            assert config.rules[0].pattern == 'bad_word'
            assert config.rules[0].replacement == 'good_word'
            assert config.rules[1].pattern == 'inappropriate'
            assert config.rules[1].replacement == 'appropriate'

            # 파일 정리
            Path(f.name).unlink()

    def test_load_mixed_patterns(self):
        """혼합 패턴 로딩 테스트"""
        content = """# 혼합 패턴 테스트
nsfw
/\\b(nude|naked)\\b/
bad_word||good_word
adult
/\\d{4}_\\d{2}_\\d{2}/
inappropriate||appropriate
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(content)
            f.flush()

            config = ConfigLoader.load_from_text(f.name, default_priority=100)

            assert len(config.rules) == 6

            # 첫 번째 규칙: plain keyword
            assert config.rules[0].filter_type == 'plain_keyword'
            assert config.rules[0].pattern == 'nsfw'
            assert config.rules[0].priority == 100

            # 두 번째 규칙: regex
            assert config.rules[1].filter_type == 'regex'
            assert config.rules[1].pattern == '\\b(nude|naked)\\b'

            # 세 번째 규칙: replace
            assert config.rules[2].filter_type == 'replace'
            assert config.rules[2].pattern == 'bad_word'
            assert config.rules[2].replacement == 'good_word'

            # 글로벌 설정 확인
            assert config.global_settings['source'] == 'text_file'
            assert config.global_settings['default_priority'] == 100

            # 파일 정리
            Path(f.name).unlink()

    def test_ignore_comments_and_empty_lines(self):
        """주석과 빈 줄 무시 테스트"""
        content = """# 이것은 주석입니다

nsfw
# 또 다른 주석
adult

# 마지막 주석
explicit
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(content)
            f.flush()

            config = ConfigLoader.load_from_text(f.name)

            assert len(config.rules) == 3
            assert config.rules[0].pattern == 'nsfw'
            assert config.rules[1].pattern == 'adult'
            assert config.rules[2].pattern == 'explicit'

            # 파일 정리
            Path(f.name).unlink()

    def test_load_config_from_file_auto_detect(self):
        """파일 확장자 자동 감지 테스트"""
        content = """nsfw
adult
explicit
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(content)
            f.flush()

            config = load_config_from_file(f.name, default_priority=75)

            assert len(config.rules) == 3
            assert config.rules[0].priority == 75
            assert config.global_settings['default_priority'] == 75

            # 파일 정리
            Path(f.name).unlink()

    def test_invalid_replacement_format(self):
        """잘못된 치환 형식 테스트"""
        content = """bad_word||
||good_word
bad||word||good
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(content)
            f.flush()

            with pytest.raises(ValueError, match='Line 1'):
                ConfigLoader.load_from_text(f.name)

            # 파일 정리
            Path(f.name).unlink()

    def test_empty_regex_pattern(self):
        """빈 정규식 패턴 테스트"""
        content = """//
/valid_pattern/
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(content)
            f.flush()

            with pytest.raises(ValueError, match='Line 1'):
                ConfigLoader.load_from_text(f.name)

            # 파일 정리
            Path(f.name).unlink()

    def test_file_not_found(self):
        """파일이 존재하지 않는 경우 테스트"""
        with pytest.raises(FileNotFoundError):
            ConfigLoader.load_from_text('nonexistent_file.txt')

    def test_description_generation(self):
        """설명 자동 생성 테스트"""
        content = """nsfw
/\\b(nude|naked)\\b/
bad_word||good_word
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(content)
            f.flush()

            config = ConfigLoader.load_from_text(f.name)

            assert config.rules[0].description == 'Plain keyword: nsfw'
            assert config.rules[1].description == 'Regex pattern: \\b(nude|naked)\\b'
            assert config.rules[2].description == 'Replace "bad_word" with "good_word"'

            # 파일 정리
            Path(f.name).unlink()
