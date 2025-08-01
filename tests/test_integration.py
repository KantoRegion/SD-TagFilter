"""
태그 필터링 시스템 통합 테스트

전체 시스템의 동작을 검증합니다.
"""

import pytest

from sd_tagfilter import (
    FilterRule,
    FilterType,
    GroupFilterRule,
    OptimizedTagFilterEngine,
    TagFilterEngine,
    create_engine,
)


class TestTagFilteringIntegration:
    """태그 필터링 시스템 통합 테스트"""

    def test_complete_filtering_workflow(self):
        """완전한 필터링 워크플로우 테스트"""
        # 다양한 필터 규칙 정의
        rules = [
            # 그룹 필터 (최고 우선순위)
            GroupFilterRule.from_list(
                patterns=['steam', 'sweat', 'blush'],
                priority=100,
                description='NSFW 암시 조합 제거',
            ),
            # 와일드카드 필터
            FilterRule(
                filter_type=FilterType.WILDCARD,
                pattern='*_hair',
                priority=50,
                description='모든 머리카락 태그 제거',
            ),
            # 정규식 필터
            FilterRule(
                filter_type=FilterType.REGEX,
                pattern=r'\b(nude|naked)\b',
                priority=70,
                description='특정 단어 정확히 매칭',
            ),
            # 플레인 키워드 필터
            FilterRule(
                filter_type=FilterType.PLAIN_KEYWORD,
                pattern='nsfw',
                priority=60,
                description='NSFW 키워드 제거',
            ),
            # 교체 필터
            FilterRule(
                filter_type=FilterType.REPLACE,
                pattern='bad_word||good_word',
                priority=40,
                description='단어 교체',
            ),
            # 캡처 교체 필터
            FilterRule(
                filter_type=FilterType.REPLACE_CAPTURE,
                pattern=r'(.*)_old||$1_new',
                priority=30,
                description='패턴 기반 교체',
            ),
        ]

        # 엔진 생성
        engine = TagFilterEngine(rules)

        # 테스트 태그 목록
        test_tags = [
            'red_hair',
            'blue_hair',
            'steam',
            'sweat',
            'blush',
            'smile',
            'nude',
            'nsfw_content',
            'bad_word',
            'something_old',
            'normal_tag',
        ]

        # 필터링 실행
        filtered_tags = engine.filter_tags(test_tags)

        # 결과 검증
        # 그룹 필터로 인해 steam, sweat, blush가 모두 제거되어야 함
        assert 'steam' not in filtered_tags
        assert 'sweat' not in filtered_tags
        assert 'blush' not in filtered_tags

        # 와일드카드 필터로 인해 *_hair 태그들이 제거되어야 함
        assert 'red_hair' not in filtered_tags
        assert 'blue_hair' not in filtered_tags

        # 정규식 필터로 인해 nude가 제거되어야 함
        assert 'nude' not in filtered_tags

        # 플레인 키워드 필터로 인해 nsfw가 포함된 태그가 제거되어야 함
        assert 'nsfw_content' not in filtered_tags

        # 교체 필터로 인해 bad_word가 good_word로 교체되어야 함
        assert 'bad_word' not in filtered_tags
        assert 'good_word' in filtered_tags

        # 캡처 교체 필터로 인해 something_old가 something_new로 교체되어야 함
        assert 'something_old' not in filtered_tags
        assert 'something_new' in filtered_tags

        # 필터링되지 않은 태그들은 유지되어야 함
        assert 'smile' in filtered_tags
        assert 'normal_tag' in filtered_tags

    def test_priority_ordering(self):
        """우선순위 순서 테스트"""
        rules = [
            FilterRule(
                filter_type=FilterType.PLAIN_KEYWORD,
                pattern='test',
                priority=10,
            ),
            FilterRule(
                filter_type=FilterType.WILDCARD,
                pattern='*test*',
                priority=20,
            ),
            GroupFilterRule.from_list(
                patterns=['test', 'group'],
                priority=30,
            ),
        ]

        engine = TagFilterEngine(rules)
        filters = engine.get_filters_by_priority()

        # 우선순위 순으로 정렬되어 있는지 확인
        priorities = [f.get_priority() for f in filters]
        assert priorities == [30, 20, 10]

    def test_disabled_rules_ignored(self):
        """비활성화된 규칙이 무시되는지 테스트"""
        rules = [
            FilterRule(
                filter_type=FilterType.PLAIN_KEYWORD,
                pattern='remove_me',
                enabled=True,
            ),
            FilterRule(
                filter_type=FilterType.PLAIN_KEYWORD,
                pattern='keep_me',
                enabled=False,  # 비활성화
            ),
        ]

        engine = TagFilterEngine(rules)
        test_tags = ['remove_me', 'keep_me', 'normal']

        filtered_tags = engine.filter_tags(test_tags)

        # 활성화된 규칙만 적용되어야 함
        assert 'remove_me' not in filtered_tags
        assert 'keep_me' in filtered_tags  # 비활성화된 규칙이므로 유지
        assert 'normal' in filtered_tags

    def test_empty_tags_handling(self):
        """빈 태그 목록 처리 테스트"""
        rules = [
            FilterRule(
                filter_type=FilterType.PLAIN_KEYWORD,
                pattern='test',
            ),
        ]

        engine = TagFilterEngine(rules)
        result = engine.filter_tags([])

        assert result == []

    def test_no_matching_rules(self):
        """매칭되는 규칙이 없는 경우 테스트"""
        rules = [
            FilterRule(
                filter_type=FilterType.PLAIN_KEYWORD,
                pattern='nonexistent',
            ),
        ]

        engine = TagFilterEngine(rules)
        test_tags = ['tag1', 'tag2', 'tag3']

        filtered_tags = engine.filter_tags(test_tags)

        # 모든 태그가 유지되어야 함
        assert filtered_tags == test_tags

    def test_engine_factory(self):
        """엔진 팩토리 함수 테스트"""
        rules = [
            FilterRule(
                filter_type=FilterType.PLAIN_KEYWORD,
                pattern='test',
            ),
        ]

        # 표준 엔진
        standard_engine = create_engine(rules, 'standard')
        assert isinstance(standard_engine, TagFilterEngine)
        assert not isinstance(standard_engine, OptimizedTagFilterEngine)

        # 최적화된 엔진
        optimized_engine = create_engine(rules, 'optimized', batch_size=500)
        assert isinstance(optimized_engine, OptimizedTagFilterEngine)
        assert optimized_engine.batch_size == 500

        # 메모리 효율적 엔진
        memory_engine = create_engine(rules, 'memory_efficient')
        assert memory_engine.__class__.__name__ == 'MemoryEfficientFilterEngine'

        # 잘못된 엔진 타입
        with pytest.raises(ValueError):
            create_engine(rules, 'invalid_type')

    def test_complex_group_filtering(self):
        """복잡한 그룹 필터링 테스트"""
        rules = [
            GroupFilterRule.from_list(
                patterns=['red', 'hot', 'fire'],
                priority=100,
            ),
            GroupFilterRule.from_list(
                patterns=['blue', 'cold', 'ice'],
                priority=90,
            ),
        ]

        engine = TagFilterEngine(rules)

        # 첫 번째 그룹이 모두 있는 경우
        tags1 = ['red', 'hot', 'fire', 'other']
        result1 = engine.filter_tags(tags1)
        assert 'red' not in result1
        assert 'hot' not in result1
        assert 'fire' not in result1
        assert 'other' in result1

        # 두 번째 그룹이 모두 있는 경우
        tags2 = ['blue', 'cold', 'ice', 'other']
        result2 = engine.filter_tags(tags2)
        assert 'blue' not in result2
        assert 'cold' not in result2
        assert 'ice' not in result2
        assert 'other' in result2

        # 그룹이 불완전한 경우 (일부만 있음)
        tags3 = ['red', 'hot', 'other']  # fire가 없음
        result3 = engine.filter_tags(tags3)
        assert 'red' in result3  # 그룹이 불완전하므로 유지
        assert 'hot' in result3
        assert 'other' in result3

    def test_replacement_filters_combination(self):
        """교체 필터들의 조합 테스트"""
        rules = [
            FilterRule(
                filter_type=FilterType.REPLACE,
                pattern='old||new',
                priority=20,
            ),
            FilterRule(
                filter_type=FilterType.REPLACE_CAPTURE,
                pattern=r'prefix_(.*)_suffix||middle_$1',
                priority=10,
            ),
        ]

        engine = TagFilterEngine(rules)
        test_tags = ['old', 'prefix_content_suffix', 'normal']

        filtered_tags = engine.filter_tags(test_tags)

        assert 'old' not in filtered_tags
        assert 'new' in filtered_tags
        assert 'prefix_content_suffix' not in filtered_tags
        assert 'middle_content' in filtered_tags
        assert 'normal' in filtered_tags

    def test_performance_with_large_tag_list(self):
        """대용량 태그 목록 성능 테스트"""
        rules = [
            FilterRule(
                filter_type=FilterType.WILDCARD,
                pattern='*_remove',
                priority=10,
            ),
        ]

        engine = OptimizedTagFilterEngine(rules)

        # 대용량 태그 목록 생성
        large_tag_list = [f'tag_{i}' for i in range(1000)]
        large_tag_list.extend([f'tag_{i}_remove' for i in range(100)])

        # 필터링 실행
        filtered_tags = engine.filter_tags(large_tag_list)

        # 결과 검증
        assert len(filtered_tags) == 1000  # _remove가 붙은 100개 태그가 제거됨
        assert all('_remove' not in tag for tag in filtered_tags)

        # 성능 통계 확인
        stats = engine.get_performance_stats()
        assert stats.total_processed == 1100
        assert stats.total_filtered == 100
        assert stats.filter_rate == 100 / 1100
        assert stats.processing_time > 0

    def test_rule_management(self):
        """규칙 관리 기능 테스트"""
        initial_rules = [
            FilterRule(
                filter_type=FilterType.PLAIN_KEYWORD,
                pattern='initial',
            ),
        ]

        engine = TagFilterEngine(initial_rules)
        assert engine.get_filter_count() == 1

        # 규칙 추가
        new_rule = FilterRule(
            filter_type=FilterType.WILDCARD,
            pattern='*_new',
        )
        engine.add_rule(new_rule)
        assert engine.get_filter_count() == 2

        # 규칙 제거
        engine.remove_rule(new_rule)
        assert engine.get_filter_count() == 1

        # 모든 규칙 제거
        engine.clear_rules()
        assert engine.get_filter_count() == 0
