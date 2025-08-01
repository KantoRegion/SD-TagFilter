"""태그 필터링 구현체들

다양한 필터링 방식을 구현한 클래스들을 제공합니다.
"""

from typing import List

from .base import (
    AnyFilter,
    AnyFilterRule,
    BaseFilter,
    BaseGroupFilter,
    FilterRule,
    FilterType,
)
from .patterns import (
    match_with_wildcards,
    parse_replacement_pattern,
    pattern_cache,
    substitute_with_capture,
    wildcard_to_regex,
)


def normalize_tag(tag: str) -> str:
    """태그를 정규화"""
    return tag.strip().lower().replace(' ', '_')


class PlainKeywordFilter(BaseFilter):
    """플레인 키워드 필터

    특정 키워드가 포함된 태그를 제거합니다.
    ComfyUI-LogicUtils의 FilterTagsNode와 유사한 기능입니다.
    """

    def apply(self, tags: List[str]) -> List[str]:
        """태그 목록에서 키워드가 포함된 태그들을 제거"""
        if not self.is_enabled():
            return tags

        return [tag for tag in tags if not self.matches(tag)]

    def matches(self, tag: str) -> bool:
        """태그에 키워드가 포함되어 있는지 확인"""
        normalized_tag = normalize_tag(tag)

        return self.rule.pattern in normalized_tag


class WildcardFilter(BaseFilter):
    """와일드카드 필터

    와일드카드 패턴(*, _, ?)을 사용한 태그 필터링을 제공합니다.
    """

    def __init__(self, rule: FilterRule):
        super().__init__(rule)
        self._regex_pattern = wildcard_to_regex(rule.pattern)

    def apply(self, tags: List[str]) -> List[str]:
        """태그 목록에서 와일드카드 패턴에 매칭되는 태그들을 제거"""
        if not self.is_enabled():
            return tags

        return [tag for tag in tags if not self.matches(tag)]

    def matches(self, tag: str) -> bool:
        """태그가 와일드카드 패턴에 매칭되는지 확인"""
        return match_with_wildcards(tag, self.rule.pattern)


class RegexFilter(BaseFilter):
    """정규 표현식 필터

    정규 표현식을 사용한 고급 태그 필터링을 제공합니다.
    """

    def __init__(self, rule: FilterRule):
        super().__init__(rule)
        self._compiled_pattern = pattern_cache.get_compiled_pattern(rule.pattern)

    def apply(self, tags: List[str]) -> List[str]:
        """태그 목록에서 정규식에 매칭되는 태그들을 제거"""
        if not self.is_enabled():
            return tags

        return [tag for tag in tags if not self.matches(tag)]

    def matches(self, tag: str) -> bool:
        """태그가 정규식 패턴에 매칭되는지 확인"""
        return bool(self._compiled_pattern.search(tag))


class GroupFilter(BaseGroupFilter):
    """그룹 필터

    여러 태그가 조합으로 나타날 때 해당 그룹 전체를 제거합니다.
    예: steam, sweat, blush가 모두 있으면 세 태그 모두 제거
    """

    def apply(self, tags: List[str]) -> List[str]:
        """태그 목록에서 그룹 조건에 맞는 태그들을 제거"""
        if not self.is_enabled():
            return tags

        if not self.matches(tags):
            return tags

        # 그룹의 모든 패턴에 매칭되는 태그들을 제거
        filtered_tags: List[str] = []
        for tag in tags:
            should_remove = False
            for pattern in self.rule.patterns:
                if self._matches_pattern(tag, pattern):
                    should_remove = True
                    break
            if not should_remove:
                filtered_tags.append(tag)

        return filtered_tags

    def matches(self, tags: List[str]) -> bool:
        """태그 목록이 그룹 조건에 맞는지 확인"""
        # 모든 패턴이 태그 목록에 존재하는지 확인
        for pattern in self.rule.patterns:
            pattern_found = False
            for tag in tags:
                if self._matches_pattern(tag, pattern):
                    pattern_found = True
                    break
            if not pattern_found:
                return False
        return True

    def _matches_pattern(self, tag: str, pattern: str) -> bool:
        """태그가 패턴에 매칭되는지 확인 (플레인 키워드 매칭)"""
        normalized_tag = normalize_tag(tag)
        return pattern in normalized_tag


class ReplaceFilter(BaseFilter):
    """교체 필터

    특정 태그를 다른 태그로 교체합니다.
    패턴 형식: "original_tag||replacement_tag"
    """

    def __init__(self, rule: FilterRule):
        super().__init__(rule)
        self.original_pattern, self.replacement = parse_replacement_pattern(rule.pattern)

    def apply(self, tags: List[str]) -> List[str]:
        """태그 목록에서 매칭되는 태그들을 교체"""
        if not self.is_enabled():
            return tags

        result: List[str] = []
        for tag in tags:
            if self.matches(tag):
                result.append(self.replacement)
            else:
                result.append(tag)
        return result

    def matches(self, tag: str) -> bool:
        """태그가 교체 대상인지 확인"""
        return tag == self.original_pattern


class ReplaceCaptureFilter(BaseFilter):
    """캡처를 이용한 교체 필터

    정규 표현식의 캡처 그룹을 활용한 동적 태그 교체를 지원합니다.
    패턴 형식: "(.*)_hair||$1_bald"
    """

    def __init__(self, rule: FilterRule):
        super().__init__(rule)
        self.original_pattern, self.replacement = parse_replacement_pattern(rule.pattern)
        self._compiled_pattern = pattern_cache.get_compiled_pattern(self.original_pattern)

    def apply(self, tags: List[str]) -> List[str]:
        """태그 목록에서 매칭되는 태그들을 캡처 그룹을 이용해 교체"""
        if not self.is_enabled():
            return tags

        result: List[str] = []
        for tag in tags:
            if self.matches(tag):
                replaced = substitute_with_capture(tag, self.original_pattern, self.replacement)
                result.append(replaced)
            else:
                result.append(tag)
        return result

    def matches(self, tag: str) -> bool:
        """태그가 정규식 패턴에 매칭되는지 확인"""
        return bool(self._compiled_pattern.search(tag))


class FilterFactory:
    """필터 생성 팩토리"""

    _filter_registry = {
        FilterType.PLAIN_KEYWORD: PlainKeywordFilter,
        FilterType.WILDCARD: WildcardFilter,
        FilterType.REGEX: RegexFilter,
        FilterType.GROUP: GroupFilter,
        FilterType.REPLACE: ReplaceFilter,
        FilterType.REPLACE_CAPTURE: ReplaceCaptureFilter,
    }

    @classmethod
    def register_filter(cls, filter_type: FilterType, filter_class: type):
        """새로운 필터 타입 등록"""
        cls._filter_registry[filter_type] = filter_class

    @classmethod
    def create_filter(cls, rule: AnyFilterRule) -> AnyFilter:
        """규칙에 따라 필터 생성

        Args:
            rule: 필터 규칙

        Returns:
            생성된 필터 인스턴스

        Raises:
            ValueError: 알 수 없는 필터 타입
        """
        filter_class = cls._filter_registry.get(rule.filter_type)
        if not filter_class:
            raise ValueError(f'Unknown filter type: {rule.filter_type}')
        return filter_class(rule)

    @classmethod
    def get_supported_types(cls) -> List[FilterType]:
        """지원하는 필터 타입 목록 반환"""
        return list(cls._filter_registry.keys())

    @classmethod
    def is_supported(cls, filter_type: FilterType) -> bool:
        """필터 타입이 지원되는지 확인"""
        return filter_type in cls._filter_registry
