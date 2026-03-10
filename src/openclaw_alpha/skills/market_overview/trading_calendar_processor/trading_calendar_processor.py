# -*- coding: utf-8 -*-
"""交易日历 Processor

提供完整的交易日历上下文信息，包括：
- 是否为交易日
- 是否为交易时段
- 市场状态（休市/盘前/集合竞价/早盘/午间休市/午盘/收盘）
- 建议使用的日期
- 上一个/下一个交易日
"""

import argparse
import asyncio
import json
from datetime import datetime
from pathlib import Path

# 添加项目根目录到 sys.path
import sys
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from openclaw_alpha.utils.trading_calendar import get_trading_calendar_context


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="获取交易日历上下文信息",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  # 获取当前时间的交易日历上下文
  uv run --env-file .env python trading_calendar_processor.py

  # 获取指定日期的交易日历上下文
  uv run --env-file .env python trading_calendar_processor.py --date 2026-03-10

  # 获取指定日期时间的交易日历上下文
  uv run --env-file .env python trading_calendar_processor.py --datetime "2026-03-10 10:30:00"
        """
    )
    parser.add_argument(
        "--date",
        type=str,
        help="指定日期（YYYY-MM-DD），默认今天"
    )
    parser.add_argument(
        "--datetime",
        type=str,
        help="指定日期时间（YYYY-MM-DD HH:MM:SS），默认当前时间"
    )
    return parser.parse_args()


def process(date: str | None = None, datetime_str: str | None = None) -> dict:
    """获取交易日历上下文

    Args:
        date: 指定日期（YYYY-MM-DD）
        datetime_str: 指定日期时间（YYYY-MM-DD HH:MM:SS）

    Returns:
        交易日历上下文字典
    """
    # 确定时间
    if datetime_str:
        time = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S")
    elif date:
        time = datetime.strptime(date, "%Y-%m-%d")
    else:
        time = datetime.now()

    # 获取交易日历上下文
    ctx = get_trading_calendar_context(time)

    # 转换为字典
    return {
        "current_time": ctx.current_time.strftime("%Y-%m-%d %H:%M:%S"),
        "is_trading_day": ctx.is_trading_day,
        "is_trading_time": ctx.is_trading_time,
        "market_status": ctx.market_status,
        "suggested_date": ctx.suggested_date,
        "previous_trading_day": ctx.previous_trading_day,
        "next_trading_day": ctx.next_trading_day,
    }


def main():
    """主入口"""
    args = parse_args()
    result = process(args.date, args.datetime)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
