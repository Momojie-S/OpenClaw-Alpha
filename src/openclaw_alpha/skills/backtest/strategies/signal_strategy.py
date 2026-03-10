# -*- coding: utf-8 -*-
"""信号驱动策略"""

import json
from pathlib import Path


from .base_strategy import BaseStrategy


class SignalStrategy(BaseStrategy):
    """信号驱动策略

    从信号文件读取买卖信号，执行交易。

    参数：
        signal_file: 信号文件路径
        printlog: 是否打印日志
    """

    params = (
        ("signal_file", None),
        ("printlog", True),
    )

    def __init__(self):
        """初始化策略"""
        super().__init__()

        # 加载信号文件
        if not self.p.signal_file:
            raise ValueError(
                "参数 signal_file 缺失（必填）。"
                "请提供信号文件路径，例如：--signal-file .openclaw_alpha/signals/xxx.json"
            )

        signal_path = Path(self.p.signal_file)
        if not signal_path.exists():
            raise FileNotFoundError(
                f"信号文件不存在: {signal_path}。"
                f"请检查文件路径是否正确，或先运行对应的 processor 生成信号文件"
            )

        with open(signal_path, "r", encoding="utf-8") as f:
            self.signal_data = json.load(f)

        # 构建日期 -> 信号映射
        self.signal_map = {}
        for signal in self.signal_data.get("signals", []):
            date_str = signal["date"]
            # 支持 YYYY-MM-DD 和 YYYYMMDD 格式
            if len(date_str) == 8:
                date_str = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
            self.signal_map[date_str] = signal

        # 记录信号统计
        self.signal_stats = {
            "total": len(self.signal_map),
            "buy": sum(1 for s in self.signal_map.values() if s.get("action") == "buy"),
            "sell": sum(1 for s in self.signal_map.values() if s.get("action") == "sell"),
        }

        if self.p.printlog:
            self.log(f"加载信号文件: {signal_path.name}")
            self.log(f"信号总数: {self.signal_stats['total']} (买入: {self.signal_stats['buy']}, 卖出: {self.signal_stats['sell']})")

    def next(self):
        """策略逻辑 - 每个交易日执行一次"""
        # 如果有待执行的订单，不操作
        if self.order:
            return

        # 获取当前日期
        current_date = self.datas[0].datetime.date(0).strftime("%Y-%m-%d")

        # 查找当前日期的信号
        signal = self.signal_map.get(current_date)

        if not signal:
            return

        action = signal.get("action")
        reason = signal.get("reason", "")

        if action == "buy" and not self.position:
            # 买入信号，且无持仓
            if self.p.printlog:
                self.log(f"买入信号: {reason} (日期: {current_date})")
            self.order = self.buy()

        elif action == "sell" and self.position:
            # 卖出信号，且有持仓
            if self.p.printlog:
                self.log(f"卖出信号: {reason} (日期: {current_date})")
            self.order = self.sell()
