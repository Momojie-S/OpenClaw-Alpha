# -*- coding: utf-8 -*-
"""信号文件存储和加载工具"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Optional


# 信号文件存储根目录
SIGNAL_ROOT = Path(".openclaw_alpha") / "signals"


def build_signal_id(signal_type: str, params: dict) -> str:
    """构建信号 ID

    Args:
        signal_type: 信号类型（如 ma_cross, rsi, bollinger）
        params: 参数字典

    Returns:
        信号 ID（如 ma_cross_5_20）
    """
    # 根据信号类型提取关键参数
    if signal_type == "ma_cross":
        return f"ma_cross_{params.get('fast', 5)}_{params.get('slow', 20)}"
    elif signal_type == "rsi":
        return f"rsi_{params.get('period', 14)}_{params.get('lower', 30)}_{params.get('upper', 70)}"
    elif signal_type == "bollinger":
        return f"bollinger_{params.get('period', 20)}_{params.get('std', 2)}"
    elif signal_type == "northbound_flow":
        return f"northbound_{params.get('days', 5)}d"
    elif signal_type == "rotation":
        return f"rotation_{params.get('threshold', 20)}"
    else:
        # 通用方式：拼接参数值
        param_str = "_".join(str(v) for v in params.values())
        return f"{signal_type}_{param_str}" if param_str else signal_type


def get_signal_path(
    signal_type: str,
    stock_code: str,
    signal_id: str,
) -> Path:
    """获取信号文件路径

    Args:
        signal_type: 信号类型
        stock_code: 股票代码
        signal_id: 信号 ID

    Returns:
        信号文件路径
    """
    # 按信号类型分类
    type_mapping = {
        "ma_cross": "technical",
        "rsi": "technical",
        "bollinger": "technical",
        "macd": "technical",
        "kdj": "technical",
        "northbound_flow": "flow",
        "main_flow": "flow",
        "rotation": "rotation",
        "fundamental": "fundamental",
        "sentiment": "sentiment",
    }

    category = type_mapping.get(signal_type, "other")
    path = SIGNAL_ROOT / category / stock_code / f"{signal_id}.json"
    path.parent.mkdir(parents=True, exist_ok=True)

    return path


def save_signal(signal_data: dict) -> Path:
    """保存信号文件

    Args:
        signal_data: 信号数据（包含 signal_type, stock_code, signal_id, signals 等字段）

    Returns:
        信号文件路径
    """
    signal_type = signal_data.get("signal_type", "unknown")
    stock_code = signal_data.get("stock_code", "unknown")
    signal_id = signal_data.get("signal_id", "unknown")

    path = get_signal_path(signal_type, stock_code, signal_id)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(signal_data, f, ensure_ascii=False, indent=2)

    return path


def load_signal(
    signal_type: str,
    stock_code: str,
    signal_id: str,
) -> Optional[dict]:
    """加载信号文件

    Args:
        signal_type: 信号类型
        stock_code: 股票代码
        signal_id: 信号 ID

    Returns:
        信号数据，不存在则返回 None
    """
    path = get_signal_path(signal_type, stock_code, signal_id)

    if not path.exists():
        return None

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_signal_by_path(path: str | Path) -> Optional[dict]:
    """按路径加载信号文件

    Args:
        path: 信号文件路径

    Returns:
        信号数据，不存在则返回 None
    """
    path = Path(path)

    if not path.exists():
        return None

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def list_signals(
    signal_type: Optional[str] = None,
    stock_code: Optional[str] = None,
) -> list[Path]:
    """列出信号文件

    Args:
        signal_type: 信号类型（可选）
        stock_code: 股票代码（可选）

    Returns:
        信号文件路径列表
    """
    if signal_type:
        # 信号类型到目录的映射
        type_mapping = {
            "ma_cross": "technical",
            "rsi": "technical",
            "bollinger": "technical",
            "northbound_flow": "flow",
            "rotation": "rotation",
        }
        category = type_mapping.get(signal_type, signal_type)

        if stock_code:
            pattern = SIGNAL_ROOT / category / stock_code / "*.json"
        else:
            pattern = SIGNAL_ROOT / category / "*" / "*.json"
    else:
        if stock_code:
            pattern = SIGNAL_ROOT / "*" / stock_code / "*.json"
        else:
            pattern = SIGNAL_ROOT / "*" / "*" / "*.json"

    return sorted(Path(".").glob(str(pattern)))


def build_signal_data(
    signal_type: str,
    stock_code: str,
    signal_id: str,
    signals: list[dict],
    params: Optional[dict] = None,
    date_range: Optional[dict] = None,
) -> dict:
    """构建信号文件数据

    Args:
        signal_type: 信号类型
        stock_code: 股票代码
        signal_id: 信号 ID
        signals: 信号列表
        params: 参数
        date_range: 日期范围

    Returns:
        信号文件数据
    """
    buy_signals = sum(1 for s in signals if s.get("action") == "buy")
    sell_signals = sum(1 for s in signals if s.get("action") == "sell")

    return {
        "signal_id": signal_id,
        "signal_type": signal_type,
        "stock_code": stock_code,
        "generated_at": datetime.now().isoformat(),
        "params": params or {},
        "signals": signals,
        "summary": {
            "total_signals": len(signals),
            "buy_signals": buy_signals,
            "sell_signals": sell_signals,
            "date_range": date_range or {},
        }
    }
