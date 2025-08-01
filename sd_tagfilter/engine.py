"""태그 필터링 엔진

우선순위에 따라 필터링 규칙을 순차 적용하는 엔진을 제공합니다.
"""

import time
from collections.abc import Generator
from typing import List, Sequence

from pydantic import BaseModel

from .base import AnyFilter, AnyFilterRule, BaseFilter, FilterRule
from .filters import FilterFactory, ReplaceCaptureFilter, ReplaceFilter


class TagFilterEngine:
    """태그 필터링 엔진

    여러 필터 규칙을 우선순위에 따라 순차적으로 적용합니다.
    그룹 필터링이 개별 태그 필터링보다 우선적으로 처리됩니다.
    """

    def __init__(self, rules: Sequence[AnyFilterRule]):
        """필터링 엔진 초기화

        Args:
            rules: 필터링 규칙 목록
        """
        self.rules = list(rules)
        self.filters = self._create_filters(rules)
        self._sort_filters_by_priority()

    def _create_filters(self, rules: Sequence[AnyFilterRule]) -> List[AnyFilter]:
        """규칙들로부터 필터 인스턴스들을 생성"""
        filters: list[AnyFilter] = []
        for rule in rules:
            if rule.enabled:
                try:
                    filter_instance = FilterFactory.create_filter(rule)
                    filters.append(filter_instance)
                except ValueError as e:
                    # 알 수 없는 필터 타입은 무시하고 계속 진행
                    print(f'Warning: {e}')
        return filters

    def _sort_filters_by_priority(self):
        """필터들을 우선순위에 따라 정렬 (높은 우선순위부터)"""
        self.filters.sort(key=lambda f: f.get_priority(), reverse=True)

    def filter_tags(self, tags: List[str]) -> List[str]:
        """태그 목록에 모든 필터를 순차적으로 적용

        Args:
            tags: 필터링할 태그 목록

        Returns:
            필터링된 태그 목록
        """
        if not tags:
            return tags

        current_tags = tags.copy()

        # 우선순위에 따라 필터를 순차 적용
        for filter_instance in self.filters:
            if filter_instance.is_enabled():
                current_tags = filter_instance.apply(current_tags)
                # 태그가 모두 제거되면 조기 종료
                if not current_tags:
                    break

        return current_tags

    def get_filter_count(self) -> int:
        """활성화된 필터 개수 반환"""
        return len([f for f in self.filters if f.is_enabled()])

    def get_filters_by_priority(self) -> List[AnyFilter]:
        """우선순위 순으로 정렬된 필터 목록 반환"""
        return self.filters.copy()

    def add_rule(self, rule: AnyFilterRule):
        """새로운 규칙 추가"""
        if rule.enabled:
            try:
                filter_instance = FilterFactory.create_filter(rule)
                self.filters.append(filter_instance)
                self._sort_filters_by_priority()
                self.rules.append(rule)
            except ValueError as e:
                print(f'Warning: Failed to add rule: {e}')

    def remove_rule(self, rule: AnyFilterRule):
        """규칙 제거"""
        if rule in self.rules:
            self.rules.remove(rule)
            # 필터도 다시 생성
            self.filters = self._create_filters(self.rules)
            self._sort_filters_by_priority()

    def clear_rules(self):
        """모든 규칙 제거"""
        self.rules.clear()
        self.filters.clear()


class Stats(BaseModel):
    total_processed: int = 0
    total_filtered: int = 0
    processing_time: float = 0.0
    filter_rate: float = 0.0
    avg_processing_time: float = 0.0


class OptimizedTagFilterEngine(TagFilterEngine):
    """성능 최적화된 필터링 엔진

    배치 처리, 캐싱, 스트리밍 등의 최적화 기능을 제공합니다.
    """

    stats: Stats

    def __init__(self, rules: List[AnyFilterRule], batch_size: int = 1000):
        """최적화된 필터링 엔진 초기화

        Args:
            rules: 필터링 규칙 목록
            batch_size: 배치 처리 크기
        """
        super().__init__(rules)
        self.batch_size = batch_size
        self._precompile_patterns()
        self.stats: Stats = Stats()

    def _precompile_patterns(self):
        """모든 패턴을 미리 컴파일하여 성능 향상"""
        from .patterns import pattern_cache

        for rule in self.rules:
            if isinstance(rule, FilterRule):
                # 정규식 패턴들을 미리 컴파일
                try:
                    pattern_cache.get_compiled_pattern(rule.pattern)
                except Exception:
                    # 컴파일 실패는 무시 (런타임에서 처리)
                    pass
            # TODO: elif isinstance(rule,GroupFilterRule):

    def filter_tags(self, tags: List[str]) -> List[str]:
        """성능 측정과 함께 태그 필터링"""
        start_time = time.perf_counter()
        original_count = len(tags)

        result = super().filter_tags(tags)

        # 통계 업데이트
        end_time = time.perf_counter()
        self.stats.total_processed += original_count
        self.stats.total_filtered += original_count - len(result)
        self.stats.processing_time += end_time - start_time

        return result

    def filter_tags_batch(self, tag_batches: List[List[str]]) -> List[List[str]]:
        """배치 단위로 태그 필터링

        Args:
            tag_batches: 태그 배치 목록

        Returns:
            필터링된 태그 배치 목록
        """
        return [self.filter_tags(batch) for batch in tag_batches]

    def filter_tags_stream(self, tags: Generator[str, None, None]) -> Generator[str, None, None]:
        """스트리밍 방식으로 태그 필터링

        Args:
            tags: 태그 제너레이터

        Yields:
            필터링된 태그들
        """
        batch: List[str] = []
        for tag in tags:
            batch.append(tag)
            if len(batch) >= self.batch_size:
                filtered_batch = self.filter_tags(batch)
                for filtered_tag in filtered_batch:
                    yield filtered_tag
                batch = []

        # 남은 태그들 처리
        if batch:
            filtered_batch = self.filter_tags(batch)
            for filtered_tag in filtered_batch:
                yield filtered_tag

    def get_performance_stats(self) -> Stats:
        """성능 통계 반환"""
        stats = self.stats.model_copy()
        if stats.total_processed > 0:
            stats.filter_rate = stats.total_filtered / stats.total_processed
            stats.avg_processing_time = stats.processing_time / stats.total_processed
        else:
            stats.filter_rate = 0.0
            stats.avg_processing_time = 0.0
        return stats

    def reset_stats(self):
        """통계 초기화"""
        self.stats = Stats()


class MemoryEfficientFilterEngine(TagFilterEngine):
    """메모리 효율적인 스트리밍 필터링 엔진"""

    def filter_tags_stream(self, tags: Generator[str, None, None]) -> Generator[str, None, None]:
        """스트리밍 방식으로 태그 필터링 (메모리 효율적)

        Args:
            tags: 태그 제너레이터

        Yields:
            필터링된 태그들
        """
        for tag in tags:
            if self._should_keep_tag(tag):
                yield tag

    def _should_keep_tag(self, tag: str) -> bool:
        """개별 태그 유지 여부 판단

        Args:
            tag: 확인할 태그

        Returns:
            태그를 유지해야 하면 True
        """
        # 그룹 필터는 개별 태그로는 판단할 수 없으므로 제외
        for filter_instance in self.filters:
            if not filter_instance.is_enabled():
                continue
            # 그룹 필터가 아닌 경우에만 개별 태그 매칭 확인
            if isinstance(filter_instance, BaseFilter):
                if filter_instance.matches(tag):
                    # 교체 필터인 경우는 제거하지 않음
                    if isinstance(filter_instance, (ReplaceFilter, ReplaceCaptureFilter)):
                        return False
        return True


def create_engine(
    rules: List[AnyFilterRule], engine_type: str = 'standard', *, batch_size: int = 1000
) -> TagFilterEngine:
    """필터링 엔진 팩토리 함수

    Args:
        rules: 필터링 규칙 목록
        engine_type: 엔진 타입 ("standard", "optimized", "memory_efficient")
        추가 옵션
        batch_size: 배치 사이즈

    Returns:
        생성된 필터링 엔진

    Raises:
        ValueError: 알 수 없는 엔진 타입
    """
    if engine_type == 'standard':
        return TagFilterEngine(rules)
    elif engine_type == 'optimized':
        return OptimizedTagFilterEngine(rules, batch_size=batch_size)
    elif engine_type == 'memory_efficient':
        return MemoryEfficientFilterEngine(rules)
    else:
        raise ValueError(f'Unknown engine type: {engine_type}')
