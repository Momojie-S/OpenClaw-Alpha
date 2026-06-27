# -*- coding: utf-8 -*-
"""QuickNewsConfig fetch_limit 测试"""

from openclaw_alpha.backend.quick_news.config import QuickNewsConfig


def test_fetch_limit_default():
    """默认值为 0（处理全部）"""
    config = QuickNewsConfig()
    assert config.fetch_limit == 0


def test_fetch_limit_positive():
    """正整数场景"""
    config = QuickNewsConfig(fetch_limit=10)
    assert config.fetch_limit == 10


def test_fetch_limit_from_dict():
    """从字典构造"""
    config = QuickNewsConfig(**{"fetch_limit": 5})
    assert config.fetch_limit == 5


def test_fetch_limit_zero_explicit():
    """显式设为 0"""
    config = QuickNewsConfig(fetch_limit=0)
    assert config.fetch_limit == 0
