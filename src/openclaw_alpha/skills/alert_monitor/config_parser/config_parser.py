# -*- coding: utf-8 -*-
"""预警配置解析器"""

import argparse
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml


@dataclass
class WatchlistItem:
    """自选股/持仓项"""
    symbol: str
    name: str = ""
    cost_price: Optional[float] = None
    stop_loss: Optional[float] = None


@dataclass
class RiskAlertRule:
    """风险预警规则"""
    enabled: bool = True
    check_times: list[str] = field(default_factory=lambda: ["9:15", "15:05"])


@dataclass
class RestrictedReleaseRule:
    """解禁风险规则"""
    enabled: bool = True
    threshold: float = 5.0  # 占流通市值比例


@dataclass
class NorthboundFlowRule:
    """北向资金规则"""
    enabled: bool = True
    inflow_threshold: float = 50.0  # 亿
    outflow_threshold: float = 30.0  # 亿


@dataclass
class IndustryTrendRule:
    """板块热度规则"""
    enabled: bool = True
    hot_threshold: float = 30.0  # 热度环比变化阈值
    cold_threshold: float = -30.0


@dataclass
class AlertConfig:
    """预警配置"""
    watchlist: list[WatchlistItem] = field(default_factory=list)
    risk_alert: RiskAlertRule = field(default_factory=RiskAlertRule)
    restricted_release: RestrictedReleaseRule = field(default_factory=RestrictedReleaseRule)
    northbound_flow: NorthboundFlowRule = field(default_factory=NorthboundFlowRule)
    industry_trend: IndustryTrendRule = field(default_factory=IndustryTrendRule)


def parse_watchlist(data: list) -> list[WatchlistItem]:
    """解析自选股列表"""
    items = []
    for item in data:
        if isinstance(item, str):
            items.append(WatchlistItem(symbol=item))
        elif isinstance(item, dict):
            items.append(WatchlistItem(
                symbol=item.get("symbol", ""),
                name=item.get("name", ""),
                cost_price=item.get("cost_price"),
                stop_loss=item.get("stop_loss"),
            ))
    return items


def load_config(config_path: Optional[Path] = None) -> AlertConfig:
    """加载配置文件

    Args:
        config_path: 配置文件路径，默认为 ~/.openclaw/workspace-alpha/alert_config.yaml

    Returns:
        AlertConfig 对象
    """
    if config_path is None:
        config_path = Path.home() / ".openclaw" / "workspace-alpha" / "alert_config.yaml"

    if not config_path.exists():
        return AlertConfig()

    with open(config_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    watchlist = parse_watchlist(data.get("watchlist", []))

    rules = data.get("rules", {})

    risk_alert_data = rules.get("risk_alert", {})
    risk_alert = RiskAlertRule(
        enabled=risk_alert_data.get("enabled", True),
        check_times=risk_alert_data.get("check_times", ["9:15", "15:05"]),
    )

    restricted_data = rules.get("restricted_release", {})
    restricted_release = RestrictedReleaseRule(
        enabled=restricted_data.get("enabled", True),
        threshold=restricted_data.get("threshold", 5.0),
    )

    northbound_data = rules.get("northbound_flow", {})
    northbound_flow = NorthboundFlowRule(
        enabled=northbound_data.get("enabled", True),
        inflow_threshold=northbound_data.get("inflow_threshold", 50.0),
        outflow_threshold=northbound_data.get("outflow_threshold", 30.0),
    )

    industry_data = rules.get("industry_trend", {})
    industry_trend = IndustryTrendRule(
        enabled=industry_data.get("enabled", True),
        hot_threshold=industry_data.get("hot_threshold", 30.0),
        cold_threshold=industry_data.get("cold_threshold", -30.0),
    )

    return AlertConfig(
        watchlist=watchlist,
        risk_alert=risk_alert,
        restricted_release=restricted_release,
        northbound_flow=northbound_flow,
        industry_trend=industry_trend,
    )


def get_watchlist_symbols(config: AlertConfig) -> list[str]:
    """获取自选股代码列表"""
    return [item.symbol for item in config.watchlist]


def main():
    parser = argparse.ArgumentParser(description="解析预警配置")
    parser.add_argument("--config", type=Path, help="配置文件路径")
    args = parser.parse_args()

    config = load_config(args.config)

    result = {
        "watchlist": [
            {
                "symbol": item.symbol,
                "name": item.name,
                "cost_price": item.cost_price,
                "stop_loss": item.stop_loss,
            }
            for item in config.watchlist
        ],
        "rules": {
            "risk_alert": {
                "enabled": config.risk_alert.enabled,
                "check_times": config.risk_alert.check_times,
            },
            "restricted_release": {
                "enabled": config.restricted_release.enabled,
                "threshold": config.restricted_release.threshold,
            },
            "northbound_flow": {
                "enabled": config.northbound_flow.enabled,
                "inflow_threshold": config.northbound_flow.inflow_threshold,
                "outflow_threshold": config.northbound_flow.outflow_threshold,
            },
            "industry_trend": {
                "enabled": config.industry_trend.enabled,
                "hot_threshold": config.industry_trend.hot_threshold,
                "cold_threshold": config.industry_trend.cold_threshold,
            },
        },
    }

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
