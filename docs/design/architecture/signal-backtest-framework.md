# 信号驱动回测框架设计

> 版本: v1.0
> 创建日期: 2026-03-08

---

## 一、问题背景

### 1.1 现状

| Skill | 能力 | 问题 |
|-------|------|------|
| technical_indicators | 计算 MA/RSI/布林带等指标，输出**当前时点**信号 | 无法输出历史信号序列 |
| backtest | 执行回测，评估策略表现 | 策略逻辑**重复实现**，不复用现有 skill |
| industry_trend | 计算板块热度，判断轮动机会 | 无法用于回测验证 |

### 1.2 问题

1. **重复造轮子**：backtest 自己实现 MA/RSI 策略，不复用 technical_indicators
2. **无法验证**：其他 skill 的分析逻辑无法回测验证有效性
3. **难以组合**：无法组合多个 skill 的信号形成复合策略

### 1.3 目标

设计**信号驱动回测框架**，实现：
1. 信号生产与消费解耦
2. 信号标准化，可复用、可组合
3. backtest 专注交易执行，不关心策略逻辑

---

## 二、核心设计

### 2.1 架构概览

```
┌─────────────────────────────────────────────────────────────┐
│                     信号生产层                               │
│                                                              │
│  各 Skill 输出标准化信号文件                                  │
│                                                              │
│  technical_indicators                                        │
│  ├── ma_signal_processor.py                                 │
│  ├── rsi_signal_processor.py                                │
│  └── bollinger_signal_processor.py                          │
│                                                              │
│  industry_trend                                              │
│  └── rotation_signal_processor.py                           │
│                                                              │
│  northbound_flow                                             │
│  └── flow_signal_processor.py                               │
└─────────────────────────────────────────────────────────────┘
                           │
                           │ 信号文件 (.json)
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                     回测消费层                               │
│                                                              │
│  backtest                                                    │
│  └── signal_backtest_processor.py                           │
│      ├── 读取信号文件                                        │
│      ├── 转换为 backtrader 策略                              │
│      └── 执行回测                                            │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 信号文件标准

**文件路径**：
```
.openclaw_alpha/signals/{signal_type}/{stock_code}/{signal_id}.json
```

**示例**：
```
.openclaw_alpha/signals/technical/000001/ma_cross_5_20.json
.openclaw_alpha/signals/technical/000001/rsi_14_30_70.json
.openclaw_alpha/signals/flow/000001/northbound_5d.json
```

**文件格式**：
```json
{
  "signal_id": "ma_cross_5_20",
  "signal_type": "technical",
  "stock_code": "000001",
  "generated_at": "2026-03-08T12:00:00",
  "params": {
    "fast_period": 5,
    "slow_period": 20
  },
  "signals": [
    {
      "date": "2025-03-10",
      "action": "buy",
      "score": 1,
      "reason": "金叉",
      "metadata": {
        "fast_ma": 12.50,
        "slow_ma": 12.30
      }
    },
    {
      "date": "2025-04-15",
      "action": "sell",
      "score": -1,
      "reason": "死叉",
      "metadata": {
        "fast_ma": 11.80,
        "slow_ma": 12.00
      }
    }
  ],
  "summary": {
    "total_signals": 12,
    "buy_signals": 6,
    "sell_signals": 6,
    "date_range": {
      "start": "2025-01-01",
      "end": "2026-03-08"
    }
  }
}
```

### 2.3 字段定义

**信号文件顶层**：

| 字段 | 类型 | 必需 | 说明 |
|------|------|:----:|------|
| signal_id | string | ✅ | 信号唯一标识（如 `ma_cross_5_20`） |
| signal_type | string | ✅ | 信号类型（technical/flow/rotation/fundamental） |
| stock_code | string | ✅ | 股票代码 |
| generated_at | string | ✅ | 生成时间（ISO 8601） |
| params | object | ❌ | 信号参数 |
| signals | array | ✅ | 信号列表 |
| summary | object | ❌ | 统计摘要 |

**信号项**：

| 字段 | 类型 | 必需 | 说明 |
|------|------|:----:|------|
| date | string | ✅ | 交易日期（YYYY-MM-DD） |
| action | string | ✅ | 动作：buy / sell / hold |
| score | number | ✅ | 信号强度：-2 ~ +2 |
| reason | string | ❌ | 信号原因 |
| metadata | object | ❌ | 附加信息 |

**action 枚举**：

| 值 | 含义 |
|----|------|
| buy | 买入信号 |
| sell | 卖出信号 |
| hold | 持有（无操作） |

**score 范围**：

| 分值 | 含义 |
|------|------|
| +2 | 强烈买入 |
| +1 | 买入 |
| 0 | 中性 |
| -1 | 卖出 |
| -2 | 强烈卖出 |

---

## 三、信号生产规范

### 3.1 设计原则：一个 Processor 支持两种输出

**核心思路**：现有 processor 在计算时已遍历所有历史数据，可**顺便输出信号文件**，无需维护两份代码。

```
indicator_processor.py
    ↓
计算历史数据 + 技术指标（现有逻辑）
    ↓
├── 输出 1: 当前分析结果（默认）
│   → .openclaw_alpha/technical_indicators/{date}/indicator_analysis.json
│
└── 输出 2: 历史信号序列（可选）
    → .openclaw_alpha/signals/technical/{stock}/ma_cross_5_20.json
```

### 3.2 命令行参数

```bash
# 默认：当前时点分析（现有功能）
uv run ... indicator_processor.py 000001
→ 输出分析结果

# 同时输出信号文件
uv run ... indicator_processor.py 000001 --save-signals
→ 输出分析结果 + 信号文件

# 只输出信号（用于回测）
uv run ... indicator_processor.py 000001 --signal-only
→ 只输出信号文件
```

### 3.3 参数说明

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--save-signals` | false | 同时输出信号文件 |
| `--signal-only` | false | 只输出信号文件（不输出分析结果） |
| `--signal-type` | auto | 信号类型（ma_cross/rsi/bollinger/auto） |

### 3.4 实现模板

在现有 processor 中增加信号输出逻辑：

```python
# -*- coding: utf-8 -*-
"""技术指标分析 Processor"""

import argparse
import asyncio
import json
from datetime import datetime
from typing import Any

from openclaw_alpha.core.processor_utils import get_output_path
from openclaw_alpha.core.signal_utils import save_signal, build_signal_id

from ..history_fetcher import fetch as fetch_history


class IndicatorProcessor:
    """技术指标分析处理器"""

    def __init__(
        self,
        symbol: str,
        days: int = 60,
        save_signals: bool = False,
        signal_only: bool = False,
    ):
        self.symbol = symbol
        self.days = days
        self.save_signals = save_signals
        self.signal_only = signal_only
        self.df = None

    async def analyze(self, indicators: list[str] = None, params: dict = None) -> dict:
        """分析技术指标

        Args:
            indicators: 指标列表
            params: 指标参数

        Returns:
            分析结果
        """
        # 1. 获取历史数据（现有逻辑）
        self.df = await fetch_history(self.symbol, days=self.days)

        if self.df.empty:
            return {"error": "无法获取历史数据"}

        # 2. 计算指标（现有逻辑）
        indicator_values = {}
        signals = []  # 用于信号输出

        if "macd" in indicators:
            macd_result = self._calculate_macd(params["macd"])
            indicator_values["macd"] = macd_result
            
            # 现有：单点信号
            signal, score = self._judge_macd_signal(macd_result)
            
            # 新增：提取历史信号序列
            if self.save_signals or self.signal_only:
                macd_signals = self._extract_macd_signals(params["macd"])
                signals.extend(macd_signals)

        # ... 其他指标类似 ...

        # 3. 输出分析结果（现有功能，signal_only 时跳过）
        if not self.signal_only:
            analysis_result = self._build_analysis_result(indicator_values)
            self._save_analysis(analysis_result)

        # 4. 输出信号文件（新增功能）
        if self.save_signals or self.signal_only:
            signal_data = self._build_signal_data(signals, params)
            signal_path = save_signal(signal_data)
            print(f"信号文件: {signal_path}")

        return analysis_result if not self.signal_only else {"signals": len(signals)}

    def _extract_ma_cross_signals(self, params: dict) -> list[dict]:
        """提取均线交叉历史信号

        Args:
            params: {"fast": 5, "slow": 20}

        Returns:
            信号列表
        """
        fast = params["fast"]
        slow = params["slow"]

        # 计算均线
        self.df["fast_ma"] = self.df["close"].rolling(fast).mean()
        self.df["slow_ma"] = self.df["close"].rolling(slow).mean()

        signals = []
        for i in range(1, len(self.df)):
            prev = self.df.iloc[i - 1]
            curr = self.df.iloc[i]

            # 金叉
            if prev["fast_ma"] <= prev["slow_ma"] and curr["fast_ma"] > curr["slow_ma"]:
                signals.append({
                    "date": curr["trade_date"],
                    "action": "buy",
                    "score": 1,
                    "reason": "金叉",
                    "metadata": {
                        "fast_ma": round(curr["fast_ma"], 2),
                        "slow_ma": round(curr["slow_ma"], 2),
                    }
                })
            # 死叉
            elif prev["fast_ma"] >= prev["slow_ma"] and curr["fast_ma"] < curr["slow_ma"]:
                signals.append({
                    "date": curr["trade_date"],
                    "action": "sell",
                    "score": -1,
                    "reason": "死叉",
                    "metadata": {
                        "fast_ma": round(curr["fast_ma"], 2),
                        "slow_ma": round(curr["slow_ma"], 2),
                    }
                })

        return signals

    def _build_signal_data(self, signals: list[dict], params: dict) -> dict:
        """构建信号文件数据

        Args:
            signals: 信号列表
            params: 参数

        Returns:
            信号文件内容
        """
        signal_id = build_signal_id("ma_cross", params)

        return {
            "signal_id": signal_id,
            "signal_type": "technical",
            "stock_code": self.symbol,
            "generated_at": datetime.now().isoformat(),
            "params": params,
            "signals": signals,
            "summary": {
                "total_signals": len(signals),
                "buy_signals": sum(1 for s in signals if s["action"] == "buy"),
                "sell_signals": sum(1 for s in signals if s["action"] == "sell"),
                "date_range": {
                    "start": self.df["trade_date"].iloc[0],
                    "end": self.df["trade_date"].iloc[-1],
                }
            }
        }


def parse_args():
    parser = argparse.ArgumentParser(description="技术指标分析")
    parser.add_argument("symbol", help="股票代码")
    parser.add_argument("--days", type=int, default=60, help="历史天数")
    # 新增参数
    parser.add_argument("--save-signals", action="store_true", help="同时输出信号文件")
    parser.add_argument("--signal-only", action="store_true", help="只输出信号文件")
    return parser.parse_args()


async def main():
    args = parse_args()

    processor = IndicatorProcessor(
        symbol=args.symbol,
        days=args.days,
        save_signals=args.save_signals,
        signal_only=args.signal_only,
    )

    await processor.analyze()


if __name__ == "__main__":
    asyncio.run(main())
```

### 3.5 需要改造的 Processor

| signal_type | 来源 Skill | 说明 |
|-------------|-----------|------|
| technical | technical_indicators | 技术指标信号 |
| flow | northbound_flow, stock_fund_flow | 资金流向信号 |
| rotation | industry_trend | 板块轮动信号 |
| fundamental | fundamental_analysis | 基本面信号 |
| sentiment | market_sentiment | 市场情绪信号 |
| event | news_driven_investment, announcement_analysis | 事件驱动信号 |

---

## 四、回测消费层改造

### 4.1 信号策略适配器

新增 `SignalStrategy`，将信号文件转换为 backtrader 策略。

```python
# skills/backtest/scripts/strategies/signal_strategy.py

class SignalStrategy(BaseStrategy):
    """信号驱动策略
    
    从信号文件读取买卖信号，执行交易
    """
    
    params = (
        ("signal_file", None),      # 信号文件路径
        ("printlog", True),
    )
    
    def __init__(self):
        super().__init__()
        
        # 加载信号
        with open(self.p.signal_file, "r") as f:
            self.signal_data = json.load(f)
        
        # 构建日期 -> 信号映射
        self.signal_map = {
            s["date"]: s for s in self.signal_data["signals"]
        }
    
    def next(self):
        if self.order:
            return
        
        current_date = self.datas[0].datetime.date(0).strftime("%Y-%m-%d")
        signal = self.signal_map.get(current_date)
        
        if not signal:
            return
        
        if signal["action"] == "buy" and not self.position:
            if self.p.printlog:
                self.log(f"买入信号: {signal['reason']}")
            self.order = self.buy()
        
        elif signal["action"] == "sell" and self.position:
            if self.p.printlog:
                self.log(f"卖出信号: {signal['reason']}")
            self.order = self.sell()
```

### 4.2 信号回测处理器

```python
# skills/backtest/scripts/signal_backtest_processor/signal_backtest_processor.py

async def run_backtest(
    stock_code: str,
    signal_files: list[str],
    combine_mode: str = "single",
    cash: float = 100000.0,
    start_date: str = None,
    end_date: str = None,
) -> dict:
    """基于信号文件运行回测

    Args:
        stock_code: 股票代码
        signal_files: 信号文件列表
        combine_mode: 组合模式（single/and/or/majority）
        cash: 初始资金
        start_date: 开始日期
        end_date: 结束日期

    Returns:
        回测结果
    """
    # 加载所有信号
    signals_list = []
    for path in signal_files:
        with open(path, "r") as f:
            signals_list.append(json.load(f))
    
    # 根据组合模式合并信号
    if len(signals_list) == 1:
        combined_signals = signals_list[0]
    else:
        combined_signals = combine_signals(signals_list, combine_mode)
    
    # 保存合并后的信号文件
    merged_path = get_output_path("backtest", "merged_signals", ext="json")
    with open(merged_path, "w") as f:
        json.dump(combined_signals, f)
    
    # 运行回测
    engine = BacktestEngine(
        strategy=SignalStrategy,
        stock_code=stock_code,
        start_date=start_date,
        end_date=end_date,
        cash=cash,
        strategy_params={"signal_file": str(merged_path)},
    )
    
    return engine.run()
```

### 4.3 信号组合模式

| 模式 | 逻辑 | 使用场景 |
|------|------|---------|
| single | 单信号 | 单策略回测 |
| and | 所有信号一致才执行 | 严格筛选 |
| or | 任一信号触发即执行 | 宽松筛选 |
| majority | 多数信号一致才执行 | 投票机制 |
| weighted | 加权得分 | 综合评分 |

**示例**：
```bash
# 单信号
--signals ma_signals.json

# AND 组合（MA + RSI 都买入才买）
--signals ma_signals.json,rsi_signals.json --combine and

# 加权组合
--signals ma_signals.json:0.5,rsi_signals.json:0.3,flow_signals.json:0.2 --combine weighted
```

---

## 五、使用示例

### 5.1 单信号回测

```bash
# Step 1: 生成信号（使用现有 processor + --signal-only）
uv run --env-file .env python skills/technical_indicators/scripts/indicator_processor/indicator_processor.py \
    000001 --signal-only

# 输出: .openclaw_alpha/signals/technical/000001/ma_cross_5_20.json

# Step 2: 回测
uv run --env-file .env python skills/backtest/scripts/signal_backtest_processor/signal_backtest_processor.py \
    --stock 000001 \
    --signals .openclaw_alpha/signals/technical/000001/ma_cross_5_20.json
```

### 5.2 同时输出分析和信号

```bash
# 一次运行，两种输出
uv run --env-file .env python skills/technical_indicators/scripts/indicator_processor/indicator_processor.py \
    000001 --save-signals

# 输出:
#   1. 分析结果: .openclaw_alpha/technical_indicators/{date}/indicator_analysis.json
#   2. 信号文件: .openclaw_alpha/signals/technical/000001/ma_cross_5_20.json
```

### 5.3 多信号组合回测

```bash
# Step 1: 生成多个信号
uv run --env-file .env python skills/technical_indicators/scripts/indicator_processor/indicator_processor.py 000001 --signal-only
uv run --env-file .env python skills/northbound_flow/scripts/northbound_processor/northbound_processor.py 000001 --signal-only

# Step 2: 组合回测（AND 模式）
uv run --env-file .env python skills/backtest/scripts/signal_backtest_processor/signal_backtest_processor.py \
    --stock 000001 \
    --signals \
        .openclaw_alpha/signals/technical/000001/ma_cross_5_20.json,\
        .openclaw_alpha/signals/flow/000001/northbound_5d.json \
    --combine and
```
uv run --env-file .env python skills/backtest/scripts/signal_backtest_processor/signal_backtest_processor.py \
    --stock 000001 \
    --signals .openclaw_alpha/signals/technical/000001/ma_cross_5_20.json
```

---

## 六、实现计划
  for slow in 20 30 60; do
    uv run --env-file .env python ...ma_signal_processor.py 000001 --fast $fast --slow $slow
  done
done

# 批量回测对比
uv run --env-file .env python skills/backtest/scripts/batch_backtest_processor/batch_backtest_processor.py \
    --stock 000001 \
    --signals-dir .openclaw_alpha/signals/technical/000001/ \
    --output .temp/batch_backtest_result.json
```

---

## 六、实现计划

### 6.1 Phase 1: 基础框架

| 任务 | 说明 | 工作量 |
|------|------|--------|
| 信号文件标准 | 定义 JSON Schema | 1h |
| 信号存储工具 | `save_signal()`, `load_signal()` | 1h |
| indicator_processor 改造 | 增加 `--save-signals` 支持 | 2h |
| SignalStrategy 适配器 | 消费信号文件 | 2h |
| signal_backtest_processor | 命令行入口 | 2h |
| 测试 | 单元测试 + 集成测试 | 2h |
| **小计** | | **10h** |

### 6.2 Phase 2: 扩展信号源

| 任务 | 说明 | 工作量 |
|------|------|--------|
| indicator_processor 完整改造 | RSI、布林带信号 | 1h |
| northbound_processor 改造 | 北向资金信号 | 2h |
| industry_trend_processor 改造 | 轮动信号 | 2h |
| **小计** | | **5h** |

### 6.3 Phase 3: 组合策略

| 任务 | 说明 | 工作量 |
|------|------|--------|
| 信号组合逻辑 | and/or/majority/weighted | 2h |
| 批量回测 | 参数对比 | 2h |
| 回测报告 | 多信号对比报告 | 2h |
| **小计** | | **6h** |

**总计：22 小时**

---

## 七、与现有框架的关系

### 7.1 不改动现有代码

- 现有 processor（indicator_processor 等）保持不变
- 新增 signal_processor 作为独立模块
- 现有 backtest 策略保持不变，新增 signal_strategy

### 7.2 渐进式迁移

```
现状:
  backtest/strategies/ma_cross_strategy.py  (自己实现 MA 计算)

迁移后:
  technical_indicators/ma_signal_processor.py  (复用 MA 计算)
      ↓
  backtest/strategies/signal_strategy.py       (消费信号)
  
保留:
  backtest/strategies/ma_cross_strategy.py     (向后兼容)
```

### 7.3 目录结构

```
OpenClaw-Alpha/
├── src/openclaw_alpha/core/
│   └── signal_utils.py           # 新增：信号存储/加载工具
│
├── skills/technical_indicators/scripts/
│   ├── indicator_processor/       # 现有：单点分析
│   └── ma_signal_processor/       # 新增：信号序列生成
│
├── skills/backtest/scripts/
│   ├── strategies/
│   │   ├── ma_cross_strategy.py   # 现有：保留
│   │   └── signal_strategy.py     # 新增：信号驱动
│   ├── backtest_processor/        # 现有：基于策略类
│   └── signal_backtest_processor/ # 新增：基于信号文件
│
└── .openclaw_alpha/signals/       # 新增：信号存储目录
    ├── technical/
    ├── flow/
    └── rotation/
```

---

## 八、收益与风险

### 8.1 收益

| 收益 | 说明 |
|------|------|
| 复用现有能力 | 不重复实现 MA/RSI 等指标 |
| 可验证性 | 所有分析逻辑都可回测验证 |
| 可组合性 | 多信号组合形成复合策略 |
| 可追溯性 | 信号文件保存，便于复盘 |
| 扩展性 | 新增信号源只需实现 signal_processor |

### 8.2 风险

| 风险 | 缓解措施 |
|------|---------|
| 信号文件管理 | 使用统一存储路径，定期清理 |
| 信号一致性问题 | 信号文件包含生成时间、参数，可追溯 |
| 组合逻辑复杂 | 从简单模式开始（single/and），逐步扩展 |

---

## 九、总结

信号驱动回测框架的核心思想：

1. **解耦**：信号生产与消费分离
2. **标准化**：统一的信号文件格式
3. **复用**：各 skill 输出信号，backtest 消费信号
4. **组合**：支持多信号组合策略

**第一步**：实现均线信号处理器 + 信号策略适配器，验证框架可行性。
