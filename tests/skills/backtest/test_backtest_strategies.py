# -*- coding: utf-8 -*-
"""回测策略测试"""

import pytest
import backtrader as bt

from skills.backtest.scripts.strategies.base_strategy import BaseStrategy
from skills.backtest.scripts.strategies.ma_cross_strategy import MACrossStrategy
from skills.backtest.scripts.strategies.rsi_strategy import RSIStrategy
from skills.backtest.scripts.strategies.bollinger_strategy import BollingerBandsStrategy
from skills.backtest.scripts.backtest_processor.backtest_processor import (
    STRATEGY_REGISTRY,
    BacktestEngine,
)


class TestStrategyRegistry:
    """测试策略注册表"""

    def test_registry_contains_strategies(self):
        """测试注册表包含所有策略"""
        assert "ma_cross" in STRATEGY_REGISTRY
        assert "rsi" in STRATEGY_REGISTRY
        assert "bollinger" in STRATEGY_REGISTRY

    def test_registry_strategy_classes(self):
        """测试注册的策略类正确"""
        assert STRATEGY_REGISTRY["ma_cross"] == MACrossStrategy
        assert STRATEGY_REGISTRY["rsi"] == RSIStrategy
        assert STRATEGY_REGISTRY["bollinger"] == BollingerBandsStrategy


class TestBaseStrategy:
    """测试策略基类"""

    def test_base_strategy_params(self):
        """测试基类参数"""
        assert hasattr(BaseStrategy, "params")

    def test_base_strategy_methods(self):
        """测试基类方法存在"""
        assert hasattr(BaseStrategy, "log")
        assert hasattr(BaseStrategy, "notify_order")
        assert hasattr(BaseStrategy, "notify_trade")
        assert hasattr(BaseStrategy, "next")


class TestMACrossStrategy:
    """测试均线交叉策略"""

    def test_strategy_params(self):
        """测试策略参数"""
        assert hasattr(MACrossStrategy, "params")

    def test_strategy_inherits_base(self):
        """测试策略继承基类"""
        assert issubclass(MACrossStrategy, BaseStrategy)


class TestRSIStrategy:
    """测试 RSI 策略"""

    def test_strategy_params(self):
        """测试策略参数"""
        assert hasattr(RSIStrategy, "params")

    def test_strategy_inherits_base(self):
        """测试策略继承基类"""
        assert issubclass(RSIStrategy, BaseStrategy)


class TestBollingerBandsStrategy:
    """测试布林带策略"""

    def test_strategy_params(self):
        """测试策略参数"""
        assert hasattr(BollingerBandsStrategy, "params")

    def test_strategy_inherits_base(self):
        """测试策略继承基类"""
        assert issubclass(BollingerBandsStrategy, BaseStrategy)


class TestBacktestEngine:
    """测试回测引擎"""

    def test_engine_initialization(self):
        """测试引擎初始化"""
        engine = BacktestEngine(
            strategy=MACrossStrategy,
            stock_code="000001",
            start_date="2026-01-01",
            end_date="2026-02-01",
            cash=100000.0,
            printlog=False,
        )

        assert engine.stock_code == "000001"
        assert engine.cash == 100000.0
        assert engine.strategy == MACrossStrategy

    def test_engine_params(self):
        """测试引擎参数"""
        engine = BacktestEngine(
            strategy=MACrossStrategy,
            stock_code="000001",
            start_date="2026-01-01",
            end_date="2026-02-01",
            cash=50000.0,
            commission=0.001,
            stamp_duty=0.001,
            printlog=False,
            strategy_params={"fast_period": 10, "slow_period": 30},
        )

        assert engine.cash == 50000.0
        assert engine.commission == 0.001
        assert engine.strategy_params == {"fast_period": 10, "slow_period": 30}

    def test_get_summary_before_run(self):
        """测试运行前获取摘要"""
        engine = BacktestEngine(
            strategy=MACrossStrategy,
            stock_code="000001",
            start_date="2026-01-01",
            end_date="2026-02-01",
            printlog=False,
        )

        summary = engine.get_summary()

        assert summary["stock_code"] == "000001"
        assert summary["strategy"] == "MACrossStrategy"
        assert "start_date" in summary
        assert "end_date" in summary
