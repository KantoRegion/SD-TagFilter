"""패턴 매칭 유틸리티

와일드카드 패턴을 정규식으로 변환하고, 정규식 컴파일 캐싱을 제공합니다.
"""

import re
from functools import lru_cache
from re import Pattern


class PatternCache:
    """정규식 패턴 캐싱 관리자"""

    def __init__(self, max_size: int = 1000):
        self.max_size = max_size

    @lru_cache(maxsize=1000)
    def get_compiled_pattern(self, pattern: str, flags: int = 0) -> Pattern[str]:
        """컴파일된 정규식 패턴 반환 (캐싱)

        Args:
            pattern: 정규식 패턴
            flags: 정규식 플래그

        Returns:
            컴파일된 정규식 패턴
        """
        return re.compile(pattern, flags)

    def clear_cache(self):
        """캐시 초기화"""
        self.get_compiled_pattern.cache_clear()


# 전역 패턴 캐시 인스턴스
pattern_cache = PatternCache()


def wildcard_to_regex(pattern: str) -> str:
    """와일드카드 패턴을 정규식으로 변환

    지원하는 와일드카드:
    - * : 0개 이상의 모든 문자
    - _ : 1개의 모든 문자
    - x? : x가 0번 또는 1번 나타남

    Args:
        pattern: 와일드카드 패턴

    Returns:
        정규식 패턴

    Examples:
        >>> wildcard_to_regex("*_hair")
        '.*_hair'
        >>> wildcard_to_regex("red_?")
        'red_.?'
        >>> wildcard_to_regex("test*ing")
        'test.*ing'
    """
    # 정규식 특수문자 이스케이프 (와일드카드 제외)
    escaped = re.escape(pattern)

    # 이스케이프된 와일드카드를 다시 정규식으로 변환
    # * -> .*
    escaped = escaped.replace(r'\*', '.*')
    # _ -> .
    escaped = escaped.replace(r'\_', '.')
    # x? -> x? (이미 정규식이므로 이스케이프 해제)
    escaped = re.sub(r'\\(.)\\\?', r'\1?', escaped)

    # 전체 문자열 매칭을 위해 앵커 추가
    return f'^{escaped}$'


def parse_replacement_pattern(pattern: str) -> tuple[str, str]:
    """교체 패턴을 파싱

    Args:
        pattern: "original||replacement" 형식의 패턴

    Returns:
        (원본 패턴, 교체 패턴) 튜플

    Raises:
        ValueError: 잘못된 교체 패턴 형식

    Examples:
        >>> parse_replacement_pattern("red_hair||blue_hair")
        ('red_hair', 'blue_hair')
        >>> parse_replacement_pattern("(.*)_hair||$1_bald")
        ('(.*)_hair', '$1_bald')
    """
    if '||' not in pattern:
        raise ValueError(f"Invalid replacement pattern: {pattern}. Expected format: 'original||replacement'")

    parts = pattern.split('||', 1)
    if len(parts) != 2:
        raise ValueError(f"Invalid replacement pattern: {pattern}. Expected format: 'original||replacement'")

    original, replacement = parts
    return original.strip(), replacement.strip()


def is_regex_pattern(pattern: str) -> bool:
    """문자열이 정규식 패턴인지 확인

    정규식 특수문자가 포함되어 있으면 정규식으로 간주합니다.

    Args:
        pattern: 확인할 패턴

    Returns:
        정규식 패턴이면 True

    Examples:
        >>> is_regex_pattern("simple_tag")
        False
        >>> is_regex_pattern(".*_hair")
        True
        >>> is_regex_pattern("tag[0-9]+")
        True
    """
    regex_chars = set(r'.*+?^${}[]|()')
    return any(char in pattern for char in regex_chars)


def validate_regex_pattern(pattern: str) -> bool:
    """정규식 패턴이 유효한지 검증

    Args:
        pattern: 검증할 정규식 패턴

    Returns:
        유효한 정규식이면 True
    """
    try:
        re.compile(pattern)
        return True
    except re.error:
        return False


def escape_for_literal_match(text: str) -> str:
    """리터럴 매칭을 위해 정규식 특수문자 이스케이프

    Args:
        text: 이스케이프할 텍스트

    Returns:
        이스케이프된 텍스트
    """
    return re.escape(text)


def create_case_insensitive_pattern(pattern: str) -> str:
    """대소문자 구분 없는 패턴 생성

    Args:
        pattern: 원본 패턴

    Returns:
        대소문자 구분 없는 패턴
    """
    return f'(?i){pattern}'


def match_with_wildcards(text: str, pattern: str, case_sensitive: bool = True) -> bool:
    """와일드카드 패턴으로 텍스트 매칭

    Args:
        text: 매칭할 텍스트
        pattern: 와일드카드 패턴
        case_sensitive: 대소문자 구분 여부

    Returns:
        패턴에 매칭되면 True

    Examples:
        >>> match_with_wildcards("red_hair", "*_hair")
        True
        >>> match_with_wildcards("blue_eyes", "*_hair")
        False
    """
    regex_pattern = wildcard_to_regex(pattern)
    if not case_sensitive:
        regex_pattern = create_case_insensitive_pattern(regex_pattern)

    flags = 0 if case_sensitive else re.IGNORECASE
    compiled_pattern = pattern_cache.get_compiled_pattern(regex_pattern, flags)
    return bool(compiled_pattern.match(text))


def substitute_with_capture(text: str, pattern: str, replacement: str) -> str:
    """정규식 캡처 그룹을 사용한 치환

    Args:
        text: 치환할 텍스트
        pattern: 정규식 패턴 (캡처 그룹 포함)
        replacement: 치환 문자열 ($1, $2 등 사용 가능)

    Returns:
        치환된 텍스트

    Examples:
        >>> substitute_with_capture("red_hair", r"(.*)_hair", r"$1_bald")
        'red_bald'
    """
    compiled_pattern = pattern_cache.get_compiled_pattern(pattern)
    # Python의 re.sub는 \1, \2 형식을 사용하므로 $1, $2를 변환
    python_replacement = replacement.replace('$', '\\')
    return compiled_pattern.sub(python_replacement, text)
