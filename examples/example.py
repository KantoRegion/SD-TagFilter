"""태그 필터링 시스템 사용 예제

다양한 사용 방법과 패턴을 보여줍니다.
"""

from pathlib import Path

from sd_tagfilter.base import FilterRule, FilterType, GroupFilterRule
from sd_tagfilter.config import ConfigLoader, load_config_from_file
from sd_tagfilter.engine import OptimizedTagFilterEngine, TagFilterEngine, create_engine


def basic_usage_example():
    """기본 사용법 예제"""
    print('=== 기본 사용법 예제 ===')

    # 1. 규칙 정의
    rules = [
        # 플레인 키워드 필터
        FilterRule(
            filter_type=FilterType.PLAIN_KEYWORD,
            pattern='nsfw',
            priority=80,
            description='NSFW 키워드 제거',
        ),
        # 와일드카드 필터
        FilterRule(
            filter_type=FilterType.WILDCARD,
            pattern='*_hair',
            priority=50,
            description='모든 머리카락 태그 제거',
        ),
        # 그룹 필터
        GroupFilterRule.from_list(
            patterns=['steam', 'sweat', 'blush'],
            priority=100,
            description='NSFW 암시 조합 제거',
        ),
    ]

    # 2. 엔진 생성
    engine = TagFilterEngine(rules)

    # 3. 태그 필터링
    original_tags = [
        'red_hair',
        'blue_hair',
        'steam',
        'sweat',
        'blush',
        'smile',
        'nsfw_content',
        'normal_tag',
    ]

    filtered_tags = engine.filter_tags(original_tags)

    print(f'원본 태그: {original_tags}')
    print(f'필터링된 태그: {filtered_tags}')
    print(f'제거된 태그 수: {len(original_tags) - len(filtered_tags)}')
    print()


def advanced_filtering_example():
    """고급 필터링 예제"""
    print('=== 고급 필터링 예제 ===')

    rules = [
        # 정규식 필터
        FilterRule(
            filter_type=FilterType.REGEX,
            pattern=r'\b(nude|naked|explicit)\b',
            priority=90,
            description='명시적 NSFW 단어 정확 매칭',
        ),
        # 교체 필터
        FilterRule(
            filter_type=FilterType.REPLACE,
            pattern='bad_word||good_word',
            priority=40,
            description='부적절한 단어 교체',
        ),
        # 캡처 교체 필터
        FilterRule(
            filter_type=FilterType.REPLACE_CAPTURE,
            pattern=r'(.*)_old||$1_new',
            priority=30,
            description='패턴 기반 교체',
        ),
        # 복잡한 그룹 필터
        GroupFilterRule.from_list(
            patterns=['dark', 'shadow', 'mysterious'],
            priority=70,
            description='어두운 분위기 조합 제거',
        ),
    ]

    engine = TagFilterEngine(rules)

    test_tags = [
        'nude_art',
        'bad_word',
        'something_old',
        'dark',
        'shadow',
        'mysterious',
        'bright',
        'happy',
        'normal',
    ]

    filtered_tags = engine.filter_tags(test_tags)

    print(f'원본 태그: {test_tags}')
    print(f'필터링된 태그: {filtered_tags}')
    print()


def config_file_example():
    """설정 파일 사용 예제"""
    print('=== 설정 파일 사용 예제 ===')

    # 샘플 설정 생성 및 저장
    sample_config = ConfigLoader.create_sample_config()
    config_path = Path(__file__).parent / 'temp_config.json'

    try:
        # 설정 파일 저장
        ConfigLoader.save_to_json(sample_config, config_path)
        print(f'설정 파일 저장됨: {config_path}')

        # 설정 파일 로드
        loaded_config = load_config_from_file(config_path)
        print(f'설정 버전: {loaded_config.version}')
        print(f'규칙 수: {len(loaded_config.rules)}')
        print(f'활성화된 규칙 수: {len(loaded_config.get_enabled_rules())}')

        # 필터 규칙으로 변환
        filter_rules = loaded_config.to_filter_rules()
        engine = TagFilterEngine(filter_rules)

        # 테스트
        test_tags = [
            'red_hair',
            'steam',
            'sweat',
            'blush',
            'violence',
            'bad_word',
            'something_old',
            'temp_test',
            'debug',
            'normal',
        ]

        filtered_tags = engine.filter_tags(test_tags)

        print(f'원본 태그: {test_tags}')
        print(f'필터링된 태그: {filtered_tags}')

    finally:
        # 임시 파일 정리
        if config_path.exists():
            config_path.unlink()
            print(f'임시 파일 삭제됨: {config_path}')

    print()


def performance_example():
    """성능 최적화 예제"""
    print('=== 성능 최적화 예제 ===')

    rules = [
        FilterRule(
            filter_type=FilterType.WILDCARD,
            pattern='*_remove',
            priority=10,
        ),
        FilterRule(
            filter_type=FilterType.PLAIN_KEYWORD,
            pattern='filter_me',
            priority=20,
        ),
    ]

    # 최적화된 엔진 사용
    engine = OptimizedTagFilterEngine(rules, batch_size=500)

    # 대용량 태그 목록 생성
    large_tag_list = []
    for i in range(1000):
        large_tag_list.append(f'tag_{i}')
        if i % 10 == 0:
            large_tag_list.append(f'tag_{i}_remove')
        if i % 20 == 0:
            large_tag_list.append('filter_me')

    print(f'원본 태그 수: {len(large_tag_list)}')

    # 필터링 실행
    filtered_tags = engine.filter_tags(large_tag_list)

    print(f'필터링된 태그 수: {len(filtered_tags)}')

    # 성능 통계 출력
    stats = engine.get_performance_stats()
    print(f'처리된 태그 수: {stats["total_processed"]}')
    print(f'제거된 태그 수: {stats["total_filtered"]}')
    print(f'필터링 비율: {stats["filter_rate"]:.2%}')
    print(f'처리 시간: {stats["processing_time"]:.4f}초')
    print(f'평균 처리 시간: {stats["avg_processing_time"]:.6f}초/태그')
    print()


def engine_factory_example():
    """엔진 팩토리 사용 예제"""
    print('=== 엔진 팩토리 사용 예제 ===')

    rules = [
        FilterRule(
            filter_type=FilterType.PLAIN_KEYWORD,
            pattern='test',
            priority=10,
        ),
    ]

    # 다양한 엔진 타입 생성
    engines = {
        'standard': create_engine(rules, 'standard'),
        'optimized': create_engine(rules, 'optimized', batch_size=100),
        'memory_efficient': create_engine(rules, 'memory_efficient'),
    }

    test_tags = ['test', 'normal', 'another_test', 'keep_this']

    for engine_type, engine in engines.items():
        filtered_tags = engine.filter_tags(test_tags)
        print(f'{engine_type} 엔진: {len(test_tags)} -> {len(filtered_tags)} 태그')

    print()


def dynamic_rule_management_example():
    """동적 규칙 관리 예제"""
    print('=== 동적 규칙 관리 예제 ===')

    # 초기 규칙으로 엔진 생성
    initial_rules = [
        FilterRule(
            filter_type=FilterType.PLAIN_KEYWORD,
            pattern='remove_me',
            priority=10,
        ),
    ]

    engine = TagFilterEngine(initial_rules)
    print(f'초기 필터 수: {engine.get_filter_count()}')

    # 새 규칙 추가
    new_rule = FilterRule(
        filter_type=FilterType.WILDCARD,
        pattern='*_bad',
        priority=20,
    )
    engine.add_rule(new_rule)
    print(f'규칙 추가 후 필터 수: {engine.get_filter_count()}')

    # 테스트
    test_tags = ['remove_me', 'something_bad', 'good_tag']
    filtered_tags = engine.filter_tags(test_tags)
    print(f'필터링 결과: {test_tags} -> {filtered_tags}')

    # 규칙 제거
    engine.remove_rule(new_rule)
    print(f'규칙 제거 후 필터 수: {engine.get_filter_count()}')

    # 다시 테스트
    filtered_tags = engine.filter_tags(test_tags)
    print(f'규칙 제거 후 결과: {test_tags} -> {filtered_tags}')

    print()


def complex_scenario_example():
    """복잡한 시나리오 예제"""
    print('=== 복잡한 시나리오 예제 ===')

    # 실제 사용 시나리오를 모방한 복잡한 규칙 세트
    rules = [
        # 최고 우선순위: 위험한 조합 제거
        GroupFilterRule.from_list(
            patterns=['explicit', 'violence', 'gore'],
            priority=100,
            description='위험한 조합 완전 제거',
        ),
        # 높은 우선순위: NSFW 관련
        GroupFilterRule.from_list(
            patterns=['steam', 'sweat', 'blush'],
            priority=90,
            description='NSFW 암시 조합',
        ),
        # 정규식으로 정확한 매칭
        FilterRule(
            filter_type=FilterType.REGEX,
            pattern=r'\b(nsfw|adult|18\+)\b',
            priority=80,
            description='NSFW 키워드 정확 매칭',
        ),
        # 와일드카드로 패턴 매칭
        FilterRule(
            filter_type=FilterType.WILDCARD,
            pattern='*_inappropriate',
            priority=70,
            description='부적절한 태그 제거',
        ),
        # 교체 규칙들
        FilterRule(
            filter_type=FilterType.REPLACE_CAPTURE,
            pattern=r'old_(.*)_version||new_$1_version',
            priority=50,
            description='버전 업데이트',
        ),
        FilterRule(
            filter_type=FilterType.REPLACE,
            pattern='deprecated||updated',
            priority=40,
            description='deprecated 태그 업데이트',
        ),
        # 낮은 우선순위: 정리 작업
        FilterRule(
            filter_type=FilterType.WILDCARD,
            pattern='temp_*',
            priority=20,
            description='임시 태그 정리',
        ),
        FilterRule(
            filter_type=FilterType.PLAIN_KEYWORD,
            pattern='debug',
            priority=10,
            description='디버그 태그 제거',
        ),
    ]

    engine = TagFilterEngine(rules)

    # 복잡한 테스트 케이스
    complex_tags = [
        # 위험한 조합 (모두 제거되어야 함)
        'explicit',
        'violence',
        'gore',
        'other_tag',
        # NSFW 암시 조합 (모두 제거되어야 함)
        'steam',
        'sweat',
        'blush',
        'innocent_tag',
        # 개별 NSFW 키워드
        'nsfw_content',
        'adult_theme',
        '18+_rating',
        # 부적절한 태그
        'content_inappropriate',
        'theme_inappropriate',
        # 교체될 태그들
        'old_system_version',
        'deprecated',
        # 정리될 태그들
        'temp_file',
        'temp_data',
        'debug',
        # 유지될 태그들
        'normal',
        'safe',
        'appropriate',
        'good_content',
    ]

    print(f'원본 태그 수: {len(complex_tags)}')
    print(f'원본 태그: {complex_tags}')

    filtered_tags = engine.filter_tags(complex_tags)

    print(f'필터링된 태그 수: {len(filtered_tags)}')
    print(f'필터링된 태그: {filtered_tags}')
    print(f'제거/변경된 태그 수: {len(complex_tags) - len([t for t in complex_tags if t in filtered_tags])}')

    # 우선순위별 필터 정보 출력
    print('\n적용된 필터 (우선순위 순):')
    for i, filter_obj in enumerate(engine.get_filters_by_priority(), 1):
        print(f'{i}. {filter_obj} (우선순위: {filter_obj.get_priority()})')

    print()


def main():
    """모든 예제 실행"""
    print('태그 필터링 시스템 사용 예제')
    print('=' * 50)

    basic_usage_example()
    advanced_filtering_example()
    config_file_example()
    performance_example()
    engine_factory_example()
    dynamic_rule_management_example()
    complex_scenario_example()

    print('모든 예제 실행 완료!')


if __name__ == '__main__':
    main()
