"""
태그 필터링 기본 구조 테스트
"""

import pytest

from sd_tagfilter import (
    FilterRule,
    FilterType,
    GroupFilterRule,
)


class TestFilterType:
    """FilterType 열거형 테스트"""

    def test_filter_type_values(self):
        """필터 타입 값들이 올바른지 확인"""
        assert FilterType.PLAIN_KEYWORD.value == 'plain_keyword'
        assert FilterType.WILDCARD.value == 'wildcard'
        assert FilterType.REGEX.value == 'regex'
        assert FilterType.GROUP.value == 'group'
        assert FilterType.REPLACE.value == 'replace'
        assert FilterType.REPLACE_CAPTURE.value == 'replace_capture'


class TestFilterRule:
    """FilterRule NamedTuple 테스트"""

    def test_filter_rule_creation(self):
        """FilterRule 생성 테스트"""
        rule = FilterRule(
            filter_type=FilterType.PLAIN_KEYWORD,
            pattern='test_pattern',
            priority=10,
            replacement=None,
            enabled=True,
            description='Test rule',
        )

        assert rule.filter_type == FilterType.PLAIN_KEYWORD
        assert rule.pattern == 'test_pattern'
        assert rule.priority == 10
        assert rule.replacement is None
        assert rule.enabled is True
        assert rule.description == 'Test rule'

    def test_filter_rule_defaults(self):
        """FilterRule 기본값 테스트"""
        rule = FilterRule(
            filter_type=FilterType.WILDCARD,
            pattern='*_hair',
        )

        assert rule.filter_type == FilterType.WILDCARD
        assert rule.pattern == '*_hair'
        assert rule.priority == 0
        assert rule.replacement is None
        assert rule.enabled is True
        assert rule.description is None

    def test_filter_rule_immutability(self):
        """FilterRule 불변성 테스트"""
        rule = FilterRule(
            filter_type=FilterType.REGEX,
            pattern='test.*',
        )

        # NamedTuple은 불변이므로 속성 변경이 불가능해야 함
        with pytest.raises(AttributeError):
            rule.pattern = 'new_pattern'

    def test_filter_rule_str_representation(self):
        """FilterRule 문자열 표현 테스트"""
        rule = FilterRule(
            filter_type=FilterType.PLAIN_KEYWORD,
            pattern='test',
            priority=5,
        )

        str_repr = str(rule)
        assert 'FilterRule' in str_repr
        assert 'plain_keyword' in str_repr
        assert 'test' in str_repr
        assert 'priority=5' in str_repr


class TestGroupFilterRule:
    """GroupFilterRule NamedTuple 테스트"""

    def test_group_filter_rule_creation(self):
        """GroupFilterRule 생성 테스트"""
        rule = GroupFilterRule(
            filter_type=FilterType.GROUP,
            patterns=('steam', 'sweat', 'blush'),
            priority=100,
            enabled=True,
            description='NSFW group',
        )

        assert rule.filter_type == FilterType.GROUP
        assert rule.patterns == ('steam', 'sweat', 'blush')
        assert rule.priority == 100
        assert rule.enabled is True
        assert rule.description == 'NSFW group'

    def test_group_filter_rule_defaults(self):
        """GroupFilterRule 기본값 테스트"""
        rule = GroupFilterRule(
            filter_type=FilterType.GROUP,
            patterns=('tag1', 'tag2'),
        )

        assert rule.filter_type == FilterType.GROUP
        assert rule.patterns == ('tag1', 'tag2')
        assert rule.priority == 0
        assert rule.enabled is True
        assert rule.description is None

    def test_group_filter_rule_from_list(self):
        """from_list 클래스 메서드 테스트"""
        patterns = ['steam', 'sweat', 'blush']
        rule = GroupFilterRule.from_list(
            patterns=patterns,
            priority=50,
            enabled=False,
            description='Test group',
        )

        assert rule.filter_type == FilterType.GROUP
        assert rule.patterns == ('steam', 'sweat', 'blush')
        assert rule.priority == 50
        assert rule.enabled is False
        assert rule.description == 'Test group'

    def test_group_filter_rule_immutability(self):
        """GroupFilterRule 불변성 테스트"""
        rule = GroupFilterRule(
            filter_type=FilterType.GROUP,
            patterns=('tag1', 'tag2'),
        )

        # NamedTuple은 불변이므로 속성 변경이 불가능해야 함
        with pytest.raises(AttributeError):
            rule.patterns = ('new_tag1', 'new_tag2')

        # patterns는 tuple이므로 내용 변경도 불가능해야 함
        with pytest.raises(TypeError):
            rule.patterns[0] = 'new_tag'

    def test_group_filter_rule_str_representation(self):
        """GroupFilterRule 문자열 표현 테스트"""
        rule = GroupFilterRule(
            filter_type=FilterType.GROUP,
            patterns=('steam', 'sweat'),
            priority=10,
        )

        str_repr = str(rule)
        assert 'GroupFilterRule' in str_repr
        assert 'group' in str_repr
        assert 'steam' in str_repr
        assert 'sweat' in str_repr
        assert 'priority=10' in str_repr


class TestFilterRuleEquality:
    """FilterRule 동등성 테스트"""

    def test_filter_rule_equality(self):
        """FilterRule 동등성 비교"""
        rule1 = FilterRule(
            filter_type=FilterType.PLAIN_KEYWORD,
            pattern='test',
            priority=5,
        )
        rule2 = FilterRule(
            filter_type=FilterType.PLAIN_KEYWORD,
            pattern='test',
            priority=5,
        )
        rule3 = FilterRule(
            filter_type=FilterType.PLAIN_KEYWORD,
            pattern='different',
            priority=5,
        )

        assert rule1 == rule2
        assert rule1 != rule3

    def test_group_filter_rule_equality(self):
        """GroupFilterRule 동등성 비교"""
        rule1 = GroupFilterRule(
            filter_type=FilterType.GROUP,
            patterns=('steam', 'sweat'),
            priority=10,
        )
        rule2 = GroupFilterRule(
            filter_type=FilterType.GROUP,
            patterns=('steam', 'sweat'),
            priority=10,
        )
        rule3 = GroupFilterRule(
            filter_type=FilterType.GROUP,
            patterns=('different', 'tags'),
            priority=10,
        )

        assert rule1 == rule2
        assert rule1 != rule3


class TestFilterRuleHashing:
    """FilterRule 해싱 테스트"""

    def test_filter_rule_hashable(self):
        """FilterRule이 해시 가능한지 테스트"""
        rule = FilterRule(
            filter_type=FilterType.PLAIN_KEYWORD,
            pattern='test',
        )

        # 해시 가능하므로 set에 추가할 수 있어야 함
        rule_set = {rule}
        assert len(rule_set) == 1

        # 동일한 규칙을 추가해도 set 크기는 변하지 않아야 함
        rule_set.add(rule)
        assert len(rule_set) == 1

    def test_group_filter_rule_hashable(self):
        """GroupFilterRule이 해시 가능한지 테스트"""
        rule = GroupFilterRule(
            filter_type=FilterType.GROUP,
            patterns=('steam', 'sweat'),
        )

        # 해시 가능하므로 set에 추가할 수 있어야 함
        rule_set = {rule}
        assert len(rule_set) == 1

        # 동일한 규칙을 추가해도 set 크기는 변하지 않아야 함
        rule_set.add(rule)
        assert len(rule_set) == 1
