# -*- coding: utf-8 -*-
"""Iteration Loop jobs 测试"""

import pytest
from unittest.mock import AsyncMock


class TestDevTasksSwitchLogic:
    """测试 dev_tasks 开关逻辑（不依赖实际 jobs 模块）"""

    @pytest.mark.asyncio
    async def test_enabled_calls_process(self):
        """开启时调用 process"""
        from openclaw_alpha.backend.iteration_loop.config import IterationLoopConfig

        config = IterationLoopConfig(dev_tasks={"enabled": True})

        # 模拟 process 函数
        mock_process = AsyncMock(return_value=True)

        # 模拟 jobs.py 中的逻辑
        if config.dev_tasks.enabled:
            result = await mock_process()

        mock_process.assert_called_once()
        assert result is True

    @pytest.mark.asyncio
    async def test_disabled_skips_process(self):
        """禁用时不调用 process"""
        from openclaw_alpha.backend.iteration_loop.config import (
            IterationLoopConfig,
            DevTasksConfig,
        )

        config = IterationLoopConfig(dev_tasks=DevTasksConfig(enabled=False))

        # 模拟 process 函数
        mock_process = AsyncMock(return_value=True)

        # 模拟 jobs.py 中的逻辑
        if config.dev_tasks.enabled:
            await mock_process()

        mock_process.assert_not_called()

    @pytest.mark.asyncio
    async def test_disabled_feedback_still_works(self):
        """禁用 dev_tasks 不影响 feedback"""
        from openclaw_alpha.backend.iteration_loop.config import (
            IterationLoopConfig,
            DevTasksConfig,
        )

        config = IterationLoopConfig(dev_tasks=DevTasksConfig(enabled=False))

        # 模拟两个 process 函数
        mock_dev_process = AsyncMock(return_value=True)
        mock_feedback_process = AsyncMock(return_value=False)

        # 模拟 jobs.py 中的逻辑
        modules = []
        if config.dev_tasks.enabled:
            modules.append(("dev_tasks", mock_dev_process))
        modules.append(("feedback", mock_feedback_process))

        # 只有 feedback 在列表中
        assert len(modules) == 1
        assert modules[0][0] == "feedback"

        # 执行
        for name, process_fn in modules:
            await process_fn()

        mock_dev_process.assert_not_called()
        mock_feedback_process.assert_called_once()
