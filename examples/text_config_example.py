#!/usr/bin/env python3
"""텍스트 파일에서 필터 설정을 로드하는 예제"""

import sys
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sd_tagfilter.config import load_config_from_file
from sd_tagfilter.engine import OptimizedTagFilterEngine


def main():
    """텍스트 파일 설정 로드 예제"""
    print('=== 텍스트 파일에서 필터 설정 로드 예제 ===\n')

    # 텍스트 파일 경로
    text_file_path = Path(__file__).parent / 'sample_filters.txt'

    try:
        # 텍스트 파일에서 설정 로드
        print(f'텍스트 파일 로드: {text_file_path}')
        config = load_config_from_file(text_file_path, default_priority=50)

        print(f'로드된 규칙 수: {len(config.rules)}')
        print(f'설정 버전: {config.version}')
        print(f'글로벌 설정: {config.global_settings}\n')

        # 각 규칙 출력
        print('=== 로드된 필터 규칙들 ===')
        for i, rule in enumerate(config.rules, 1):
            if hasattr(rule, 'pattern'):
                pattern = rule.pattern
            else:
                pattern = str(rule.patterns) if hasattr(rule, 'patterns') else 'N/A'

            print(f'{i:2d}. {rule.filter_type:15} | {pattern:20} | {rule.description}')

            if hasattr(rule, 'replacement') and rule.replacement:
                print(f'     -> 치환: {rule.replacement}')

        print('\n=== 필터 엔진으로 테스트 ===')

        # 필터 규칙을 실제 FilterRule 객체로 변환
        filter_rules = config.to_filter_rules()

        # 최적화된 엔진 생성 (성능 통계 기능 포함)
        engine = OptimizedTagFilterEngine(filter_rules)

        # 테스트 태그들
        test_tags = [
            'beautiful',
            'landscape',
            'nsfw',
            'adult',
            'explicit',
            'nude',
            'naked',
            'violence',
            'gore',
            'debug',
            'bad_word',
            'inappropriate',
            'old_style',
            'temp',
            '2024_01_15',
            'good_content',
            'art',
        ]

        print(f'원본 태그: {test_tags}')

        # 필터링 적용
        filtered_tags = engine.filter_tags(test_tags)

        print(f'필터링 후: {filtered_tags}')

        # 제거된 태그들
        removed_tags = set(test_tags) - set(filtered_tags)
        print(f'제거된 태그: {list(removed_tags)}')

        # 치환된 태그들 확인
        replaced_tags = set(filtered_tags) - set(test_tags)
        if replaced_tags:
            print(f'치환된 태그: {list(replaced_tags)}')

        # 성능 통계
        stats = engine.get_performance_stats()
        print(f'\n성능 통계: {stats}')

    except Exception as e:
        print(f'오류 발생: {e}')
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
