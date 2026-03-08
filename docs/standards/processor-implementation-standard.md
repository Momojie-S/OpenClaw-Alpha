# Processor 实现规范

## 设计目标

- **双输出**：控制台输出精简结果给大模型，文件保存完整数据给后续处理
- **信号输出**：支持输出历史信号序列，供回测使用
- **独立可执行**：每个 Processor 是独立的脚本，可单独运行
- **数据传递**：多步分析时，通过文件传递中间结果

---

## 双输出设计

| 输出 | 内容 | 用途 |
|------|------|------|
| 控制台 | 精简结果（如 Top N） | 给大模型分析（节省 token） |
| 文件 | 完整数据 | 给后续 Processor 使用 |
| 信号文件 | 历史信号序列 | 给回测框架使用 |

**示例**：
```
Processor A: 计算板块热度
├── 控制台: Top 10 热门板块
├── 文件: 所有板块热度数据
└── 信号文件: 历史买卖信号（可选）

Processor B: 综合分析
├── 读取: Processor A 的文件输出
├── 控制台: Top 10 综合评分
└── 文件: 所有板块综合数据
```

**文件格式**：根据数据特点选择（JSON/CSV/Parquet），无强制约束。

---

## 信号输出（可选）

Processor 可选支持输出历史信号序列，供回测框架使用。

### 信号输出参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--save-signals` | false | 同时输出信号文件 |
| `--signal-only` | false | 只输出信号文件（不输出分析结果） |

### 使用示例

```bash
# 默认：当前时点分析
uv run ... indicator_processor.py 000001
→ 输出分析结果

# 同时输出信号文件
uv run ... indicator_processor.py 000001 --save-signals
→ 输出分析结果 + 信号文件

# 只输出信号（用于回测）
uv run ... indicator_processor.py 000001 --signal-only
→ 只输出信号文件
```

### 信号文件格式

**存储路径**：
```
.openclaw_alpha/signals/{signal_type}/{stock_code}/{signal_id}.json
```

**示例**：
```
.openclaw_alpha/signals/technical/000001/ma_cross_5_20.json
```

**文件内容**：
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

### 信号输出实现

在 Processor 中增加信号提取方法：

```python
from openclaw_alpha.core.signal_utils import (
    build_signal_id,
    build_signal_data,
    save_signal,
)


class MyProcessor:
    def __init__(self, ..., save_signals: bool = False, signal_only: bool = False):
        self.save_signals = save_signals
        self.signal_only = signal_only

    async def analyze(self, ...):
        # 获取数据
        self.df = await fetch_data(...)

        # 分析逻辑（现有）
        if not self.signal_only:
            result = self._analyze(...)
            self._save_result(result)

        # 信号输出（新增）
        if self.save_signals or self.signal_only:
            signals = self._extract_signals(...)
            self._save_signal_file("signal_type", params, signals)

    def _extract_signals(self, params: dict) -> list[dict]:
        """提取历史信号序列"""
        signals = []
        for i in range(1, len(self.df)):
            # 检测信号条件
            if self._check_buy_condition(i):
                signals.append({
                    "date": self.df.iloc[i]["date"],
                    "action": "buy",
                    "score": 1,
                    "reason": "买入原因",
                })
            elif self._check_sell_condition(i):
                signals.append({
                    "date": self.df.iloc[i]["date"],
                    "action": "sell",
                    "score": -1,
                    "reason": "卖出原因",
                })
        return signals

    def _save_signal_file(self, signal_type: str, params: dict, signals: list):
        """保存信号文件"""
        signal_id = build_signal_id(signal_type, params)
        signal_data = build_signal_data(
            signal_type=signal_type,
            stock_code=self.symbol,
            signal_id=signal_id,
            signals=signals,
            params=params,
        )
        path = save_signal(signal_data)
        print(f"信号文件: {path}")
```

---

## 文件保存

### 保存路径

```
{workspace}/.openclaw_alpha/{skill_name}/{YYYY-MM-DD}/{processor_name}.{ext}
```

**优点**：
- 进度文件、报告、中间数据在同一目录
- 按日期组织，历史可追溯

### 格式约定

- 格式按需选择（JSON、CSV、Parquet 等）
- 编码：UTF-8
- 命名：`{processor_name}.{ext}`

---

## 命令行参数

每个 Processor 按需定义参数，常见参数：

| 参数 | 说明 | 示例 |
|------|------|------|
| `--top-n` | 返回 Top N 结果 | `--top-n 10` |
| `--date` | 指定日期 | `--date 2026-03-06` |
| `--output` | 指定输出路径 | `--output .temp/xxx.json` |

**原则**：有合理默认值，参数语义清晰，支持 `--help`。

---

## 脚本结构

```python
# -*- coding: utf-8 -*-
"""概念热度 Processor"""

import argparse
import asyncio
import json
from datetime import datetime

from openclaw_alpha.core.processor_utils import get_output_path, load_output
from ..concept_fetcher import fetch  # Skill 内部用相对路径

SKILL_NAME = "industry_trend"
PROCESSOR_NAME = "concept_heat"


def parse_args():
    parser = argparse.ArgumentParser(description="计算概念板块热度")
    parser.add_argument("--date", default=datetime.now().strftime("%Y-%m-%d"))
    parser.add_argument("--top-n", type=int, default=10)
    return parser.parse_args()


async def process(date: str, top_n: int):
    # 1. 调用 Fetcher 获取数据
    concepts = await fetch(date)
    
    # 2. 读取上游 Processor 的数据（如有需要）
    prev_data = load_output(SKILL_NAME, "some_processor", date)

    # 3. 加工数据...

    # 4. 保存完整数据到文件
    output_path = get_output_path(SKILL_NAME, PROCESSOR_NAME, date, ext="json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    # ...保存逻辑...

    # 5. 返回精简结果（Top N）
    return all_data[:top_n]


def main():
    args = parse_args()
    result = asyncio.run(process(args.date, args.top_n))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
```

---

## 工具函数

**位置**：`src/openclaw_alpha/core/processor_utils.py`

**导入**：`from openclaw_alpha.core.processor_utils import get_output_path, load_output`

```python
def get_output_path(skill_name: str, processor_name: str, date: str = None, ext: str = "json") -> Path:
    """获取 Processor 输出文件路径"""
    pass


def load_output(skill_name: str, processor_name: str, date: str = None, ext: str = "json") -> Any:
    """读取 Processor 输出文件，不存在则返回 None"""
    pass
```

---

## 参考资料

- [开发规范](development-standard.md) - Python 编码、测试规范
- [Skill 实现规范](skill-implementation-standard.md) - 目录结构、命名规范、运行方式
