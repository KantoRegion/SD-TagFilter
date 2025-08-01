# 태그 필터링 시스템

Python NamedTuple을 상속한 클래스들로 구현된 강력하고 유연한 태그 필터링 시스템입니다.

## 🎯 주요 기능

- **플레인 키워드 필터링**: 특정 단어가 포함된 태그 제거
- **와일드카드 패턴 매칭**: `*`, `_`, `?` 패턴 지원
- **정규 표현식 지원**: 복잡한 패턴 매칭
- **그룹 필터링**: 여러 태그 조합이 함께 나타날 때 전체 제거
- **교체 기능**: 태그를 다른 태그로 대체
- **캡처 그룹 교체**: 정규식 캡처 그룹을 활용한 동적 교체
- **우선순위 시스템**: 필터 규칙 간의 적용 순서 제어
- **설정 파일 지원**: JSON/YAML/텍스트 형식의 설정 파일
- **성능 최적화**: 배치 처리, 캐싱, 스트리밍 지원

## 📦 설치 및 의존성

이 시스템은 다음 패키지들을 사용합니다:

```python
# 필수 의존성
from typing import NamedTuple, List, Optional, Union, Pattern
from enum import Enum
from abc import ABC, abstractmethod
import re
from functools import lru_cache
from pathlib import Path
import json
import time

# Pydantic (프로젝트에 이미 포함됨)
from pydantic import BaseModel, Field, field_validator

# 선택적 의존성 (YAML 지원용)
# pip install pyyaml
```

## 🚀 빠른 시작

### 기본 사용법

```python
from app.utils.tag_filtering import (
    FilterRule, FilterType, GroupFilterRule, TagFilterEngine
)

# 1. 필터 규칙 정의
rules = [
    # 플레인 키워드 필터
    FilterRule(
        filter_type=FilterType.PLAIN_KEYWORD,
        pattern="nsfw",
        priority=80,
        description="NSFW 키워드 제거"
    ),
    
    # 와일드카드 필터
    FilterRule(
        filter_type=FilterType.WILDCARD,
        pattern="*_hair",
        priority=50,
        description="모든 머리카락 태그 제거"
    ),
    
    # 그룹 필터
    GroupFilterRule.from_list(
        patterns=["steam", "sweat", "blush"],
        priority=100,
        description="NSFW 암시 조합 제거"
    ),
]

# 2. 엔진 생성
engine = TagFilterEngine(rules)

# 3. 태그 필터링
original_tags = ["red_hair", "steam", "sweat", "blush", "smile", "nsfw_content"]
filtered_tags = engine.filter_tags(original_tags)

print(f"원본: {original_tags}")
print(f"필터링됨: {filtered_tags}")
# 출력: ['smile'] (나머지는 모두 필터링됨)
```

### 설정 파일 사용

```python
from app.utils.tag_filtering import load_config_from_file, TagFilterEngine

# 설정 파일에서 로드
config = load_config_from_file("config.json")
filter_rules = config.to_filter_rules()
engine = TagFilterEngine(filter_rules)

# 필터링 실행
filtered_tags = engine.filter_tags(your_tags)
```

## 📋 필터 타입별 상세 가이드

### 1. 플레인 키워드 (Plain Keyword)

특정 키워드가 포함된 태그를 제거합니다.

```python
FilterRule(
    filter_type=FilterType.PLAIN_KEYWORD,
    pattern="nsfw",
    priority=80
)
# "nsfw", "nsfw_content", "my_nsfw_tag" 등이 제거됨
```

### 2. 와일드카드 (Wildcard)

패턴 매칭을 통해 여러 태그를 한 번에 처리합니다.

```python
FilterRule(
    filter_type=FilterType.WILDCARD,
    pattern="*_hair",
    priority=50
)
# "red_hair", "blue_hair", "long_hair" 등이 제거됨

FilterRule(
    filter_type=FilterType.WILDCARD,
    pattern="temp_*",
    priority=30
)
# "temp_file", "temp_data" 등이 제거됨
```

**지원하는 와일드카드:**
- `*`: 0개 이상의 모든 문자
- `_`: 1개의 모든 문자
- `x?`: x가 0번 또는 1번 나타남

### 3. 정규 표현식 (Regex)

복잡한 패턴 매칭을 지원합니다.

```python
FilterRule(
    filter_type=FilterType.REGEX,
    pattern=r"\b(nude|naked|explicit)\b",
    priority=90
)
# 단어 경계를 고려한 정확한 매칭

FilterRule(
    filter_type=FilterType.REGEX,
    pattern=r"\d{4}_\d{2}_\d{2}",
    priority=20
)
# 날짜 형식 (YYYY_MM_DD) 태그 제거
```

### 4. 그룹 필터링 (Group)

여러 태그가 조합으로 나타날 때만 해당 그룹 전체를 제거합니다.

```python
GroupFilterRule.from_list(
    patterns=["steam", "sweat", "blush"],
    priority=100,
    description="NSFW 암시 조합 제거"
)
# 세 태그가 모두 있을 때만 전체 제거
# 일부만 있으면 제거하지 않음
```

### 5. 교체 (Replace)

특정 태그를 다른 태그로 대체합니다.

```python
FilterRule(
    filter_type=FilterType.REPLACE,
    pattern="bad_word||good_word",
    priority=40
)
# "bad_word"를 "good_word"로 교체
```

### 6. 캡처 교체 (Replace Capture)

정규식 캡처 그룹을 활용한 동적 교체입니다.

```python
FilterRule(
    filter_type=FilterType.REPLACE_CAPTURE,
    pattern=r"(.*)_old||$1_new",
    priority=30
)
# "something_old" → "something_new"
# "data_old" → "data_new"
```

## ⚙️ 고급 기능

### 우선순위 시스템

높은 우선순위 규칙이 먼저 적용됩니다. 그룹 필터링이 개별 태그 필터링보다 우선적으로 처리되도록 설계하는 것이 좋습니다.

```python
rules = [
    GroupFilterRule.from_list(patterns=["a", "b"], priority=100),  # 최우선
    FilterRule(filter_type=FilterType.REGEX, pattern=".*", priority=50),
    FilterRule(filter_type=FilterType.PLAIN_KEYWORD, pattern="test", priority=10),  # 최후순위
]
```

### 성능 최적화

대용량 태그 처리를 위한 최적화된 엔진을 사용할 수 있습니다.

```python
from app.utils.tag_filtering import OptimizedTagFilterEngine

engine = OptimizedTagFilterEngine(rules, batch_size=1000)
filtered_tags = engine.filter_tags(large_tag_list)

# 성능 통계 확인
stats = engine.get_performance_stats()
print(f"처리 시간: {stats['processing_time']:.4f}초")
print(f"필터링 비율: {stats['filter_rate']:.2%}")
```

### 엔진 팩토리

다양한 엔진 타입을 쉽게 생성할 수 있습니다.

```python
from app.utils.tag_filtering import create_engine

# 표준 엔진
engine = create_engine(rules, "standard")

# 최적화된 엔진
engine = create_engine(rules, "optimized", batch_size=500)

# 메모리 효율적 엔진
engine = create_engine(rules, "memory_efficient")
```

### 동적 규칙 관리

런타임에 규칙을 추가/제거할 수 있습니다.

```python
engine = TagFilterEngine(initial_rules)

# 규칙 추가
new_rule = FilterRule(filter_type=FilterType.WILDCARD, pattern="*_new")
engine.add_rule(new_rule)

# 규칙 제거
engine.remove_rule(new_rule)

# 모든 규칙 제거
engine.clear_rules()
```

## 📄 설정 파일 형식

### JSON 형식

```json
{
  "version": "1.0",
  "global_settings": {
    "case_sensitive": false,
    "default_priority": 0,
    "max_rules": 100
  },
  "rules": [
    {
      "filter_type": "group",
      "patterns": ["steam", "sweat", "blush"],
      "priority": 100,
      "enabled": true,
      "description": "NSFW 암시 조합 제거"
    },
    {
      "filter_type": "wildcard",
      "pattern": "*_hair",
      "priority": 50,
      "enabled": true,
      "description": "모든 머리카락 태그 제거"
    }
  ]
}
```

### YAML 형식

```yaml
version: "1.0"
global_settings:
  case_sensitive: false
  default_priority: 0
  max_rules: 100

rules:
  - filter_type: "group"
    patterns: ["steam", "sweat", "blush"]
    priority: 100
    enabled: true
    description: "NSFW 암시 조합 제거"
  
  - filter_type: "wildcard"
    pattern: "*_hair"
    priority: 50
    enabled: true
    description: "모든 머리카락 태그 제거"
```

### 텍스트 형식 (Plain Text)

간단한 필터 규칙을 위한 텍스트 파일 형식입니다. 라인별로 규칙을 정의하며, 다음 형식을 지원합니다:

```text
# 주석은 #으로 시작합니다
# 빈 줄은 무시됩니다

# 일반 키워드 (plain_keyword)
nsfw
adult
explicit

# 정규식 패턴 (regex) - 슬래시로 감쌉니다
/\b(nude|naked)\b/
/\d{4}_\d{2}_\d{2}/

# 치환 규칙 (replace) - ||로 구분합니다
bad_word||good_word
inappropriate||appropriate
old_style||new_style

# 기타 키워드들
violence
gore
debug
temp
```

**텍스트 파일 사용법:**

```python
from sd_tagfilter.config import load_config_from_file

# 텍스트 파일에서 로드 (기본 우선순위 50)
config = load_config_from_file("filters.txt", default_priority=50)
filter_rules = config.to_filter_rules()
engine = TagFilterEngine(filter_rules)
```

**지원하는 형식:**
- **일반 키워드**: `keyword` → `plain_keyword` 필터로 변환
- **정규식**: `/pattern/` → `regex` 필터로 변환
- **치환**: `original||replacement` → `replace` 필터로 변환
- **주석**: `#`으로 시작하는 줄은 무시
- **빈 줄**: 자동으로 무시

## 🧪 테스트

테스트를 실행하려면:

```bash
# 전체 테스트 실행
make test

# 커버리지와 함께 실행
make testcov
```

## 📚 예제 실행

포함된 예제를 실행해보세요:

```bash
cd examples/
python example.py
```

## 🏗️ 아키텍처

### 파일 구조

```
sd_tagfilter/
├── __init__.py          # 패키지 초기화 및 공개 API
├── base.py              # 기본 구조 (NamedTuple, 인터페이스)
├── patterns.py          # 패턴 매칭 유틸리티
├── filters.py           # 필터 구현체들
├── engine.py            # 필터링 엔진
└── config.py            # 설정 관리
```

### 클래스 다이어그램

```
FilterRule (NamedTuple)
├── filter_type: FilterType
├── pattern: str
├── priority: int
├── replacement: Optional[str]
├── enabled: bool
└── description: Optional[str]

GroupFilterRule (NamedTuple)
├── filter_type: FilterType
├── patterns: tuple[str, ...]
├── priority: int
├── enabled: bool
└── description: Optional[str]

BaseFilter (ABC)
├── PlainKeywordFilter
├── WildcardFilter
├── RegexFilter
├── ReplaceFilter
└── ReplaceCaptureFilter

BaseGroupFilter (ABC)
└── GroupFilter

TagFilterEngine
├── OptimizedTagFilterEngine
└── MemoryEfficientFilterEngine
```

## 🔧 확장성

### 새로운 필터 타입 추가

1. `FilterType` 열거형에 새 타입 추가
2. `BaseFilter`를 상속한 새 필터 클래스 구현
3. `FilterFactory`에 등록

```python
# 1. 새 필터 타입 정의
class FilterType(Enum):
    # ... 기존 타입들
    CUSTOM_FILTER = "custom_filter"

# 2. 새 필터 클래스 구현
class CustomFilter(BaseFilter):
    def apply(self, tags: List[str]) -> List[str]:
        # 커스텀 로직 구현
        pass
    
    def matches(self, tag: str) -> bool:
        # 매칭 로직 구현
        pass

# 3. 팩토리에 등록
FilterFactory.register_filter(FilterType.CUSTOM_FILTER, CustomFilter)
```

### 플러그인 시스템

향후 플러그인 시스템을 통해 외부 필터를 동적으로 로드할 수 있도록 설계되었습니다.

## 🚨 주의사항

1. **그룹 필터링 우선순위**: 그룹 필터는 항상 개별 태그 필터보다 높은 우선순위를 가져야 합니다.
2. **정규식 성능**: 복잡한 정규식은 성능에 영향을 줄 수 있으므로 주의하세요.
3. **교체 필터 순서**: 여러 교체 필터가 있을 때 우선순위를 신중히 설정하세요.
4. **메모리 사용량**: 대용량 태그 처리 시 메모리 효율적 엔진 사용을 고려하세요.

## 🤝 기여하기

1. 새로운 필터 타입이나 기능을 추가할 때는 테스트도 함께 작성해주세요.
2. 성능에 영향을 주는 변경사항은 벤치마크 결과를 포함해주세요.
3. 문서 업데이트도 함께 해주세요.

## 📝 라이선스

이 프로젝트는 프로젝트의 전체 라이선스를 따릅니다.

## 🔗 참고 자료

- [ComfyUI-LogicUtils FilterTagsNode](https://github.com/aria1th/ComfyUI-LogicUtils/blob/5992e91930b9e00c5afd687eb406f6795b0d198f/auxilary.py#L143) - 기본 필터링 로직 참고
- [Python NamedTuple 문서](https://docs.python.org/3/library/collections.html#collections.namedtuple)
- [Python 정규 표현식 문서](https://docs.python.org/3/library/re.html)
- [Pydantic 문서](https://docs.pydantic.dev/)
