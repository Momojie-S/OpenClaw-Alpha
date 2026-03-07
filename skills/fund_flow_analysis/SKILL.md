---
name: openclaw_alpha_fund_flow_analysis
description: "资金流向分析：查看行业和概念板块的资金流向排名。适用于：(1) 查看资金净流入最多的行业/概念，(2) 发现资金青睐的热点板块，(3) 多时间周期资金动向分析。不适用于：个股资金流向、实时推送、资金流向预测。"
metadata:
  openclaw:
    emoji: "💹"
    requires:
      bins: ["uv"]
---

# 资金流向分析

快速了解市场资金的流动方向，发现资金青睐的热点板块。

## 使用说明

### 脚本运行

```bash
# 查看今日行业资金流向 Top 10
uv run --env-file .env python -m skills.fund_flow_analysis.scripts.fund_flow_processor.fund_flow_processor

# 查看概念资金流向
uv run --env-file .env python -m skills.fund_flow_analysis.scripts.fund_flow_processor.fund_flow_processor --type concept

# 指定时间周期（今日/3日/5日/10日/20日）
uv run --env-file .env python -m skills.fund_flow_analysis.scripts.fund_flow_processor.fund_flow_processor --period 5日

# 按涨幅排序
uv run --env-file .env python -m skills.fund_flow_analysis.scripts.fund_flow_processor.fund_flow_processor --sort-by change

# 筛选净流入 > 10 亿的板块
uv run --env-file .env python -m skills.fund_flow_analysis.scripts.fund_flow_processor.fund_flow_processor --min-net 10

# 组合条件
uv run --env-file .env python -m skills.fund_flow_analysis.scripts.fund_flow_processor.fund_flow_processor \
    --type concept \
    --period 5日 \
    --sort-by net \
    --min-net 5 \
    --top-n 20
```

### 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--type` | 类型：industry(行业) / concept(概念) | industry |
| `--period` | 时间周期：今日/3日/5日/10日/20日 | 今日 |
| `--sort-by` | 排序：net(净额) / change(涨幅) / inflow(流入) | net |
| `--min-net` | 最小净额过滤(亿) | 不过滤 |
| `--top-n` | 返回数量 | 10 |

### 运行记录

输出文件保存在：`.openclaw_alpha/fund_flow_analysis/{日期}/fund_flow.json`

## 分析步骤

### Step 1: 查看今日资金流向

**输入**：无（使用默认参数）
**动作**：运行行业资金流向查询
**输出**：今日资金净流入 Top 10 行业

```bash
uv run --env-file .env python -m skills.fund_flow_analysis.scripts.fund_flow_processor.fund_flow_processor
```

### Step 2: 对比概念资金流向

**输入**：概念类型
**动作**：运行概念资金流向查询
**输出**：今日资金净流入 Top 10 概念

```bash
uv run --env-file .env python -m skills.fund_flow_analysis.scripts.fund_flow_processor.fund_flow_processor --type concept
```

### Step 3: 多周期对比

**输入**：不同时间周期
**动作**：分别查询 3日、5日、10日资金流向
**输出**：各周期资金持续流入的板块

```bash
uv run --env-file .env python -m skills.fund_flow_analysis.scripts.fund_flow_processor.fund_flow_processor --period 5日 --top-n 20
```

### Step 4: 筛选重点板块

**输入**：最小净额、排序方式
**动作**：筛选大额资金流入板块
**输出**：符合条件的板块列表

```bash
uv run --env-file .env python -m skills.fund_flow_analysis.scripts.fund_flow_processor.fund_flow_processor --min-net 20 --sort-by change
```

## 分析思路

1. **短期热点**：看今日资金流向，发现当日资金追捧的板块
2. **持续关注**：看 5日/10日资金流向，发现持续有资金流入的板块
3. **强弱对比**：对比行业和概念的资金流向，判断资金偏好
4. **趋势判断**：资金持续流入 + 涨幅居前 = 强势板块
5. **风险提示**：资金持续流出 + 涨幅居前 = 可能见顶

## 注意事项

- 数据来源：同花顺（稳定但可能有延迟）
- 资金净额单位：亿元
- 建议结合板块涨跌幅综合判断
- 大额资金流入不等于股价上涨，需综合分析
