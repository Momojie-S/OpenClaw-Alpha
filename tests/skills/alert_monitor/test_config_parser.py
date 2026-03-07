# -*- coding: utf-8 -*-
"""配置解析器测试"""

import tempfile
from pathlib import Path

import pytest

from skills.alert_monitor.scripts.config_parser import (
    AlertConfig,
    WatchlistItem,
    RiskAlertRule,
    RestrictedReleaseRule,
    NorthboundFlowRule,
    IndustryTrendRule,
    load_config,
    get_watchlist_symbols,
)


class TestConfigParser:
    """配置解析器测试"""

    def test_load_config_file_not_exist(self):
        """测试配置文件不存在时返回默认配置"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "not_exist.yaml"
            config = load_config(config_path)

            assert isinstance(config, AlertConfig)
            assert config.watchlist == []
            assert config.risk_alert.enabled is True
            assert config.restricted_release.enabled is True

    def test_load_config_empty_file(self):
        """测试空配置文件"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "empty.yaml"
            config_path.write_text("")

            config = load_config(config_path)

            assert config.watchlist == []

    def test_load_config_with_watchlist(self):
        """测试加载自选股列表"""
        yaml_content = """
watchlist:
  - symbol: "000001"
    name: "平安银行"
    cost_price: 12.50
    stop_loss: 11.00
  - symbol: "600000"
    name: "浦发银行"
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"
            config_path.write_text(yaml_content)

            config = load_config(config_path)

            assert len(config.watchlist) == 2
            assert config.watchlist[0].symbol == "000001"
            assert config.watchlist[0].name == "平安银行"
            assert config.watchlist[0].cost_price == 12.50
            assert config.watchlist[1].symbol == "600000"

    def test_load_config_with_rules(self):
        """测试加载预警规则"""
        yaml_content = """
watchlist: []

rules:
  risk_alert:
    enabled: false
    check_times: ["9:00", "15:00"]

  northbound_flow:
    enabled: true
    inflow_threshold: 100
    outflow_threshold: 50
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"
            config_path.write_text(yaml_content)

            config = load_config(config_path)

            assert config.risk_alert.enabled is False
            assert config.risk_alert.check_times == ["9:00", "15:00"]
            assert config.northbound_flow.inflow_threshold == 100.0
            assert config.northbound_flow.outflow_threshold == 50.0

    def test_get_watchlist_symbols(self):
        """测试获取自选股代码列表"""
        config = AlertConfig(
            watchlist=[
                WatchlistItem(symbol="000001", name="平安银行"),
                WatchlistItem(symbol="600000", name="浦发银行"),
            ]
        )

        symbols = get_watchlist_symbols(config)

        assert symbols == ["000001", "600000"]


class TestWatchlistItem:
    """自选股项测试"""

    def test_create_with_all_fields(self):
        """测试创建完整字段"""
        item = WatchlistItem(
            symbol="000001",
            name="平安银行",
            cost_price=12.50,
            stop_loss=11.00,
        )

        assert item.symbol == "000001"
        assert item.name == "平安银行"
        assert item.cost_price == 12.50
        assert item.stop_loss == 11.00

    def test_create_with_required_only(self):
        """测试仅必填字段"""
        item = WatchlistItem(symbol="000001")

        assert item.symbol == "000001"
        assert item.name == ""
        assert item.cost_price is None
        assert item.stop_loss is None


class TestRiskAlertRule:
    """风险预警规则测试"""

    def test_default_values(self):
        """测试默认值"""
        rule = RiskAlertRule()

        assert rule.enabled is True
        assert rule.check_times == ["9:15", "15:05"]


class TestNorthboundFlowRule:
    """北向资金规则测试"""

    def test_default_values(self):
        """测试默认值"""
        rule = NorthboundFlowRule()

        assert rule.enabled is True
        assert rule.inflow_threshold == 50.0
        assert rule.outflow_threshold == 30.0
