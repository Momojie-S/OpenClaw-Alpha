# -*- coding: utf-8 -*-
"""Iteration Loop 配置测试"""

import pytest

from openclaw_alpha.backend.iteration_loop.config import (
    DevTasksConfig,
    IterationLoopConfig,
)


class TestDevTasksConfig:
    """DevTasksConfig 测试"""

    def test_default_enabled(self):
        """默认开启"""
        config = DevTasksConfig()
        assert config.enabled is True

    def test_disabled(self):
        """可以禁用"""
        config = DevTasksConfig(enabled=False)
        assert config.enabled is False


class TestIterationLoopConfig:
    """IterationLoopConfig 测试"""

    def test_default_values(self):
        """默认值"""
        config = IterationLoopConfig()
        assert config.enabled is True
        assert config.interval_minutes == 30
        assert config.dev_tasks.enabled is True

    def test_dev_tasks_disabled(self):
        """可以单独禁用 dev_tasks"""
        config = IterationLoopConfig(dev_tasks=DevTasksConfig(enabled=False))
        assert config.enabled is True
        assert config.dev_tasks.enabled is False

    def test_all_disabled(self):
        """可以全部禁用"""
        config = IterationLoopConfig(
            enabled=False,
            dev_tasks=DevTasksConfig(enabled=False),
        )
        assert config.enabled is False
        assert config.dev_tasks.enabled is False

    def test_custom_interval(self):
        """自定义间隔"""
        config = IterationLoopConfig(interval_minutes=15)
        assert config.interval_minutes == 15
