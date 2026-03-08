---
name: openclaw_alpha_stock_fund_flow
description: "个股资金流向分析。适用于：(1) 查看单只股票的主力资金动向，(2) 分析资金流入/流出趋势，(3) 判断资金与价格的关联性。不适用于：板块资金流向（使用 fund_flow_analysis）、实时推送、资金预测。"
metadata:
  openclaw:
    emoji: "💰"
    requires:
      bins: ["uv"]
---

# 个股资金流向分析

分析单只股票的主力资金动向，判断资金趋势和价格关联。

## 使用说明

### 脚本运行

```bash
# 查看指定股票的资金流向
uv run --env-file .env python skills/stock_fund_flow/scripts/stock_fund_flow_processor/stock_fund_flow_processor.py <股票代码>

# 示例
uv run --env-file .env python skills/stock_fund_flow/scripts/stock_fund_flow_processor/stock_fund_flow_processor.py 000001
uv run --env-file .env python skills/stock_fund_flow/scripts/stock_fund_flow_processor/stock_fund_flow_processor.py 600519

# 指定汇总周期
uv run --env-file .env python skills/stock_fund_flow/scripts/stock_fund_flow_processor/stock_fund_flow_processor.py 000001 --periods 1 5 10

# 指定趋势分析回看天数
uv run --env-file .env python skills/stock_fund_flow/scripts/stock_fund_flow_processor/stock_fund_flow_processor.py 000001 --lookback 20

# JSON 输出
uv run --env-file .env python skills/stock_fund_flow/scripts/stock_fund_flow_processor/stock_fund_flow_processor.py 000001 --output json
```

### 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `股票代码` | 6 位股票代码 | 必填 |
| `--periods` | 汇总周期（今日/近5日/近10日/近20日） | 1 5 10 20 |
| `--lookback` | 趋势分析回看天数 | 10 |
| `--output` | 输出格式：text / json | text |

### 运行记录

输出文件保存在：`.openclaw_alpha/stock_fund_flow/{日期}/stock_fund_flow.json`

## 分析步骤

### Step 1: 查看资金流向汇总

**输入**：股票代码
**动作**：运行资金流向分析
**输出**：各周期主力资金净流入情况

```bash
uv run --env-file .env python skills/stock_fund_flow/scripts/stock_fund_flow_processor/stock_fund_flow_processor.py 000001
```

**输出示例**：
```
=== 000001 资金流向分析 ===
日期: 2026-03-06  收盘: 10.82  涨跌: +0.09%

--- 资金流向汇总 ---
今日: 主力净流入 -0.10亿 (-1.94%)
近5日: 主力净流入 -0.99亿 (-1.94%)
近10日: 主力净流入 -3.12亿 (-1.94%)
近20日: 主力净流入 -2.57亿 (-1.94%)

--- 资金趋势 ---
趋势: 持续流出
分析: 近10日中有7日主力资金净流出，资金持续撤离

--- 资金与价格关联 ---
关联性: 无明显关联
分析: 近10日资金与价格关联性一般
```

### Step 2: 深入分析趋势

**输入**：增加回看天数
**动作**：分析更长周期的资金趋势
**输出**：更全面的趋势判断

```bash
uv run --env-file .env python skills/stock_fund_flow/scripts/stock_fund_flow_processor/stock_fund_flow_processor.py 000001 --lookback 20
```

### Step 3: 结合其他分析

**建议搭配**：
- `stock_analysis` - 查看股票行情
- `technical_indicators` - 查看技术指标
- `fundamental_analysis` - 查看基本面

## 分析思路

### 资金趋势判断

| 趋势 | 判断条件 | 含义 |
|------|----------|------|
| 持续流入 | 近 N 日 70%+ 净流入 | 资金看好，可能上涨 |
| 持续流出 | 近 N 日 70%+ 净流出 | 资金撤离，可能下跌 |
| 震荡 | 流入流出各半 | 资金分歧，观望为主 |

### 资金与价格关联

| 关联性 | 判断条件 | 含义 |
|--------|----------|------|
| 资金推动 | 70%+ 同向 | 股价受资金推动明显 |
| 资金背离 | 30%- 同向 | 资金与价格背离，可能转折 |
| 无明显关联 | 30%-70% | 关联性一般 |

### 分析要点

1. **主力净流入**：大资金动向，影响股价趋势
2. **超大单净流入**：机构资金，更具参考价值
3. **连续流入/流出天数**：趋势强度
4. **资金与价格背离**：潜在转折信号

## 注意事项

- 数据来源：东方财富（稳定但有延迟）
- 数据范围：约 120 个交易日
- 主力资金包含超大单和大单
- 资金流向仅供参考，不构成投资建议
