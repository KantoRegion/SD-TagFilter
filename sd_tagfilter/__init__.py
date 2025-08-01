"""태그 필터링 시스템

이 모듈은 다양한 태그 필터링 기능을 제공합니다:
- 플레인 키워드 필터링
- 와일드카드 패턴 매칭
- 정규 표현식 지원
- 그룹 필터링 (태그 조합)
- 교체 기능
- 우선순위 시스템
"""

from .base import (
    BaseFilter,
    FilterInterface,
    FilterRule,
    FilterType,
    GroupFilterRule,
)
from .config import ConfigLoader, TagFilterConfig
from .engine import OptimizedTagFilterEngine, TagFilterEngine, create_engine
from .filters import FilterFactory

__all__ = [
    'FilterType',
    'FilterRule',
    'GroupFilterRule',
    'FilterInterface',
    'BaseFilter',
    'TagFilterEngine',
    'OptimizedTagFilterEngine',
    'FilterFactory',
    'TagFilterConfig',
    'ConfigLoader',
    'create_engine',
]
