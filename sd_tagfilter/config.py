"""태그 필터링 설정 관리

설정 파일 로드/저장 및 Pydantic 모델을 제공합니다.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, field_validator

from .base import AnyFilterRule, FilterType


class FilterRuleConfig(BaseModel):
    """필터 규칙 설정 모델"""

    filter_type: str
    pattern: str
    priority: int = 0
    replacement: Optional[str] = None
    enabled: bool = True
    description: Optional[str] = None

    @field_validator('filter_type')
    @classmethod
    def validate_filter_type(cls, v: str) -> str:
        """필터 타입 유효성 검증"""
        try:
            FilterType(v)
        except ValueError:
            raise ValueError(f'Invalid filter type: {v}')
        return v

    @field_validator('priority')
    @classmethod
    def validate_priority(cls, v: int) -> int:
        """우선순위 유효성 검증"""
        if v < 0:
            raise ValueError('Priority must be non-negative')
        return v

    def to_filter_rule(self):
        """FilterRule 객체로 변환"""
        from .base import FilterRule

        return FilterRule(
            filter_type=FilterType(self.filter_type),
            pattern=self.pattern,
            priority=self.priority,
            replacement=self.replacement,
            enabled=self.enabled,
            description=self.description,
        )


class GroupFilterRuleConfig(BaseModel):
    """그룹 필터 규칙 설정 모델"""

    filter_type: str = 'group'
    patterns: List[str]
    priority: int = 0
    enabled: bool = True
    description: Optional[str] = None

    @field_validator('filter_type')
    @classmethod
    def validate_filter_type(cls, v: str) -> str:
        """필터 타입 유효성 검증"""
        if v != 'group':
            raise ValueError("GroupFilterRuleConfig must have filter_type='group'")
        return v

    @field_validator('patterns')
    @classmethod
    def validate_patterns(cls, v: List[str]) -> List[str]:
        """패턴 목록 유효성 검증"""
        if not v:
            raise ValueError('Group filter must have at least one pattern')
        return v

    @field_validator('priority')
    @classmethod
    def validate_priority(cls, v: int) -> int:
        """우선순위 유효성 검증"""
        if v < 0:
            raise ValueError('Priority must be non-negative')
        return v

    def to_group_filter_rule(self):
        """GroupFilterRule 객체로 변환"""
        from .base import GroupFilterRule

        return GroupFilterRule.from_list(
            patterns=self.patterns,
            priority=self.priority,
            enabled=self.enabled,
            description=self.description,
        )


class TagFilterConfig(BaseModel):
    """태그 필터링 전체 설정"""

    version: str = '1.0'
    rules: List[FilterRuleConfig | GroupFilterRuleConfig]
    global_settings: Dict[str, Any] = Field(default_factory=dict)

    @field_validator('version')
    @classmethod
    def validate_version(cls, v: str) -> str:
        """버전 유효성 검증"""
        if not v:
            raise ValueError('Version cannot be empty')
        return v

    def to_filter_rules(self) -> List[AnyFilterRule]:
        """필터 규칙 객체 목록으로 변환"""
        filter_rules: List[AnyFilterRule] = []
        for rule_config in self.rules:
            if isinstance(rule_config, GroupFilterRuleConfig):
                filter_rules.append(rule_config.to_group_filter_rule())
            else:
                filter_rules.append(rule_config.to_filter_rule())
        return filter_rules

    def get_enabled_rules(self):
        """활성화된 규칙만 반환"""
        return [rule for rule in self.rules if rule.enabled]

    def get_rules_by_priority(self):
        """우선순위 순으로 정렬된 규칙 반환"""
        return sorted(self.rules, key=lambda r: r.priority, reverse=True)


class ConfigLoader:
    """설정 파일 로더"""

    @staticmethod
    def load_from_json(file_path: Union[str, Path]) -> TagFilterConfig:
        """JSON 파일에서 설정 로드

        Args:
            file_path: JSON 파일 경로

        Returns:
            태그 필터 설정

        Raises:
            FileNotFoundError: 파일이 존재하지 않음
            json.JSONDecodeError: JSON 파싱 오류
            ValueError: 설정 유효성 검증 오류
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f'Config file not found: {file_path}')

        with open(file_path, encoding='utf-8') as f:
            data = json.load(f)

        return ConfigLoader._parse_config_data(data)

    @staticmethod
    def load_from_yaml(file_path: Union[str, Path]) -> TagFilterConfig:
        """YAML 파일에서 설정 로드

        Args:
            file_path: YAML 파일 경로

        Returns:
            태그 필터 설정

        Raises:
            ImportError: PyYAML이 설치되지 않음
            FileNotFoundError: 파일이 존재하지 않음
            yaml.YAMLError: YAML 파싱 오류
            ValueError: 설정 유효성 검증 오류
        """
        try:
            import yaml
        except ImportError:
            raise ImportError('PyYAML is required for YAML support. Install with: pip install pyyaml')

        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f'Config file not found: {file_path}')

        with open(file_path, encoding='utf-8') as f:
            data = yaml.safe_load(f)

        return ConfigLoader._parse_config_data(data)

    @staticmethod
    def load_from_text(file_path: Union[str, Path], default_priority: int = 0) -> TagFilterConfig:
        """Plain text 파일에서 설정 로드

        라인별로 읽어서 다음 형식을 지원:
        - 일반: keyword
        - regex: /.*keyword/
        - 치환: keyword||replace

        Args:
            file_path: Plain text 파일 경로
            default_priority: 기본 우선순위

        Returns:
            태그 필터 설정

        Raises:
            FileNotFoundError: 파일이 존재하지 않음
            ValueError: 설정 유효성 검증 오류
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f'Config file not found: {file_path}')

        rules: List[Any] = []
        with open(file_path, encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()

                # 빈 줄이나 주석(#으로 시작) 무시
                if not line or line.startswith('#'):
                    continue

                try:
                    rule = ConfigLoader._parse_text_line(line, default_priority)
                    if rule:
                        rules.append(rule)
                except ValueError as e:
                    raise ValueError(f'Line {line_num}: {e}')

        return TagFilterConfig(
            version='1.0',
            rules=rules,
            global_settings={
                'source': 'text_file',
                'file_path': str(file_path),
                'default_priority': default_priority,
            },
        )

    @staticmethod
    def _parse_text_line(line: str, default_priority: int) -> Optional[FilterRuleConfig]:
        """텍스트 라인을 파싱하여 FilterRuleConfig 생성

        Args:
            line: 파싱할 라인
            default_priority: 기본 우선순위

        Returns:
            파싱된 FilterRuleConfig 또는 None

        Raises:
            ValueError: 파싱 오류
        """
        line = line.strip()
        if not line:
            return None

        # 치환 패턴: keyword||replace
        if '||' in line:
            parts = line.split('||', 1)
            if len(parts) != 2:
                raise ValueError(f'Invalid replacement format: {line}')

            pattern, replacement = parts[0].strip(), parts[1].strip()
            if not pattern or not replacement:
                raise ValueError(f'Empty pattern or replacement in: {line}')

            return FilterRuleConfig(
                filter_type='replace',
                pattern=pattern,
                replacement=replacement,
                priority=default_priority,
                description=f'Replace "{pattern}" with "{replacement}"',
            )

        # 정규식 패턴: /.*keyword/
        if line.startswith('/') and line.endswith('/') and len(line) >= 2:
            pattern = line[1:-1]  # 앞뒤 슬래시 제거
            if not pattern:
                raise ValueError(f'Empty regex pattern: {line}')

            return FilterRuleConfig(
                filter_type='regex', pattern=pattern, priority=default_priority, description=f'Regex pattern: {pattern}'
            )

        # 일반 키워드
        if line:
            return FilterRuleConfig(
                filter_type='plain_keyword',
                pattern=line,
                priority=default_priority,
                description=f'Plain keyword: {line}',
            )

        return None

    @staticmethod
    def _parse_config_data(data: Dict[str, Any]) -> TagFilterConfig:
        """설정 데이터를 파싱하여 TagFilterConfig 생성"""
        # 규칙 타입별로 분리하여 파싱
        parsed_rules: List[FilterRuleConfig | GroupFilterRuleConfig] = []
        for rule_data in data.get('rules', []):
            if rule_data.get('filter_type') == 'group':
                parsed_rules.append(GroupFilterRuleConfig(**rule_data))
            else:
                parsed_rules.append(FilterRuleConfig(**rule_data))

        data['rules'] = parsed_rules
        return TagFilterConfig(**data)

    @staticmethod
    def save_to_json(config: TagFilterConfig, file_path: Union[str, Path]):
        """설정을 JSON 파일로 저장

        Args:
            config: 저장할 설정
            file_path: 저장할 파일 경로
        """
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(config.model_dump(), f, indent=2, ensure_ascii=False)

    @staticmethod
    def save_to_yaml(config: TagFilterConfig, file_path: Union[str, Path]) -> None:
        """설정을 YAML 파일로 저장

        Args:
            config: 저장할 설정
            file_path: 저장할 파일 경로

        Raises:
            ImportError: PyYAML이 설치되지 않음
        """
        try:
            import yaml
        except ImportError:
            raise ImportError('PyYAML is required for YAML support. Install with: pip install pyyaml')

        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, 'w', encoding='utf-8') as f:
            yaml.dump(
                config.model_dump(),
                f,
                default_flow_style=False,
                allow_unicode=True,
                indent=2,
            )

    @staticmethod
    def create_sample_config() -> TagFilterConfig:
        """샘플 설정 생성

        Returns:
            샘플 태그 필터 설정
        """
        sample_rules = [
            GroupFilterRuleConfig(
                patterns=['steam', 'sweat', 'blush'],
                priority=100,
                description='NSFW 암시 조합 제거',
            ),
            FilterRuleConfig(
                filter_type='wildcard',
                pattern='*_hair',
                priority=50,
                description='모든 머리카락 태그 제거',
            ),
            FilterRuleConfig(
                filter_type='replace_capture',
                pattern='(.*)_hair||$1_bald',
                priority=30,
                enabled=False,
                description='머리카락을 대머리로 교체',
            ),
            FilterRuleConfig(
                filter_type='plain_keyword',
                pattern='nsfw',
                priority=80,
                description='NSFW 키워드 제거',
            ),
            FilterRuleConfig(
                filter_type='regex',
                pattern=r'\b(nude|naked)\b',
                priority=70,
                description='특정 단어 정확히 매칭하여 제거',
            ),
        ]

        return TagFilterConfig(
            version='1.0',
            rules=sample_rules,
            global_settings={
                'case_sensitive': False,
                'default_priority': 0,
                'max_rules': 100,
            },
        )


def load_config_from_file(file_path: Union[str, Path], default_priority: int = 0) -> TagFilterConfig:
    """파일 확장자에 따라 자동으로 설정 로드

    Args:
        file_path: 설정 파일 경로
        default_priority: 텍스트 파일의 기본 우선순위

    Returns:
        태그 필터 설정

    Raises:
        ValueError: 지원하지 않는 파일 형식
    """
    file_path = Path(file_path)
    suffix = file_path.suffix.lower()

    if suffix == '.json':
        return ConfigLoader.load_from_json(file_path)
    elif suffix in ['.yaml', '.yml']:
        return ConfigLoader.load_from_yaml(file_path)
    elif suffix == '.txt':
        return ConfigLoader.load_from_text(file_path, default_priority)
    else:
        raise ValueError(f'Unsupported file format: {suffix}. Supported formats: .json, .yaml, .yml, .txt')


def save_config_to_file(config: TagFilterConfig, file_path: Union[str, Path]) -> None:
    """파일 확장자에 따라 자동으로 설정 저장

    Args:
        config: 저장할 설정
        file_path: 저장할 파일 경로

    Raises:
        ValueError: 지원하지 않는 파일 형식
    """
    file_path = Path(file_path)
    suffix = file_path.suffix.lower()

    if suffix == '.json':
        ConfigLoader.save_to_json(config, file_path)
    elif suffix in ['.yaml', '.yml']:
        ConfigLoader.save_to_yaml(config, file_path)
    else:
        raise ValueError(f'Unsupported file format: {suffix}. Supported formats: .json, .yaml, .yml')
