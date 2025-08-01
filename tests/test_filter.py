import tempfile
from pathlib import Path

import pytest

from sd_tagfilter import (
    ConfigLoader,
    TagFilterConfig,
    TagFilterEngine,
)


@pytest.fixture
def text_config() -> str:
    return """
long_hair
dark_side
"""


@pytest.fixture
def tagFilterConfig(text_config: str):
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(text_config)
        f.flush()

        yield ConfigLoader.load_from_text(f.name)

        Path(f.name).unlink()


@pytest.fixture
def tags() -> list[str]:
    return [
        'long_hair',
        'Long_Hair',
        'Long_hair',
        'long hair',
        'Long Hair',
        'Long hair',
    ]


def test_case_sensitive(tagFilterConfig: TagFilterConfig, tags: list[str]):
    print(tagFilterConfig.rules)
    engine = TagFilterEngine(tagFilterConfig.rules)

    tags_filtered = engine.filter_tags(tags)

    print(f'{tags_filtered = }')

    assert tags_filtered == []
