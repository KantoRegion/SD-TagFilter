"""태그 필터링 시스템의 기본 구조 정의

NamedTuple을 상속한 클래스들과 기본 인터페이스를 제공합니다.
"""

from abc import ABC, abstractmethod
from enum import StrEnum
from typing import List, NamedTuple, Optional, Protocol


class FilterType(StrEnum):
    """필터 타입 열거형"""

    PLAIN_KEYWORD = 'plain_keyword'
    WILDCARD = 'wildcard'
    REGEX = 'regex'
    GROUP = 'group'
    REPLACE = 'replace'
    REPLACE_CAPTURE = 'replace_capture'


class FilterRule(NamedTuple):
    """기본 필터 규칙

    NamedTuple을 상속하여 불변성과 성능을 보장합니다.
    """

    filter_type: FilterType
    pattern: str
    priority: int = 0
    replacement: Optional[str] = None
    enabled: bool = True
    description: Optional[str] = None

    def __str__(self) -> str:
        return f"FilterRule({self.filter_type.value}, '{self.pattern}', priority={self.priority})"


class GroupFilterRule(NamedTuple):
    """그룹 필터 규칙

    여러 태그가 조합으로 나타날 때 전체를 제거하는 규칙입니다.
    """

    filter_type: FilterType
    patterns: tuple[str, ...]  # 불변성을 위해 tuple 사용
    priority: int = 0
    enabled: bool = True
    description: Optional[str] = None

    def __str__(self) -> str:
        return f'GroupFilterRule({self.filter_type.value}, {list(self.patterns)}, priority={self.priority})'

    @classmethod
    def from_list(
        cls,
        patterns: List[str],
        priority: int = 0,
        enabled: bool = True,
        description: Optional[str] = None,
    ) -> 'GroupFilterRule':
        """리스트에서 GroupFilterRule 생성"""
        return cls(
            filter_type=FilterType.GROUP,
            patterns=tuple(patterns),
            priority=priority,
            enabled=enabled,
            description=description,
        )


class FilterInterface(Protocol):
    """필터 인터페이스 프로토콜"""

    def apply(self, tags: List[str]) -> List[str]:
        """태그 목록에 필터를 적용

        Args:
            tags: 필터링할 태그 목록

        Returns:
            필터링된 태그 목록
        """
        ...

    def matches(self, tag: str) -> bool:
        """개별 태그가 필터 조건에 맞는지 확인

        Args:
            tag: 확인할 태그

        Returns:
            필터 조건에 맞으면 True
        """
        ...


class BaseFilter(ABC):
    """기본 필터 추상 클래스"""

    def __init__(self, rule: FilterRule):
        self.rule = rule
        self._compiled_pattern = None

    @abstractmethod
    def apply(self, tags: List[str]) -> List[str]:
        """태그 목록에 필터를 적용"""
        pass

    @abstractmethod
    def matches(self, tag: str) -> bool:
        """개별 태그가 필터 조건에 맞는지 확인"""
        pass

    def is_enabled(self) -> bool:
        """필터가 활성화되어 있는지 확인"""
        return self.rule.enabled

    def get_priority(self) -> int:
        """필터의 우선순위 반환"""
        return self.rule.priority

    def __str__(self) -> str:
        return f'{self.__class__.__name__}({self.rule})'

    def __repr__(self) -> str:
        return self.__str__()


class BaseGroupFilter(ABC):
    """기본 그룹 필터 추상 클래스"""

    def __init__(self, rule: GroupFilterRule):
        self.rule = rule

    @abstractmethod
    def apply(self, tags: List[str]) -> List[str]:
        """태그 목록에 그룹 필터를 적용"""
        pass

    @abstractmethod
    def matches(self, tags: List[str]) -> bool:
        """태그 목록이 그룹 조건에 맞는지 확인"""
        pass

    def is_enabled(self) -> bool:
        """필터가 활성화되어 있는지 확인"""
        return self.rule.enabled

    def get_priority(self) -> int:
        """필터의 우선순위 반환"""
        return self.rule.priority

    def __str__(self) -> str:
        return f'{self.__class__.__name__}({self.rule})'

    def __repr__(self) -> str:
        return self.__str__()


# 타입 별칭
AnyFilterRule = FilterRule | GroupFilterRule
AnyFilter = BaseFilter | BaseGroupFilter
