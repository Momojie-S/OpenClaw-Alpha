---
name: openclaw_alpha_margin_trading
description: "融资融券分析，监控市场杠杆水平。适用于：(1) 查看市场整体杠杆水平，(2) 发现融资/融券异动个股，(3) 判断市场风险状态。不适用于：实时推送、分时监控。"
metadata:
  openclaw:
    emoji: "⚖️"
    requires:
      bins: ["uv"]
---

# 融资融券分析

监控 A 股市场融资融券数据，分析市场杠杆水平和个股异动。

## 使用说明

### 市场汇总

查看沪深两市融资融券整体情况：

```bash
uv run --env-file .env python -m openclaw_alpha.skills.margin_trading.market_margin_processor.market_margin_processor
```

**参数**：
| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--date` | 查询日期 | 最新交易日 |
| `--output` | text/json | text |

### 个股融资 Top N

查看融资余额最高的个股：

```bash
uv run --env-file .env python -m openclaw_alpha.skills.margin_trading.stock_margin_processor.stock_margin_processor --top-n 20
```

**参数**：
| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--type` | financing(融资)/securities(融券) | financing |
| `--top-n` | 返回数量 | 20 |
| `--date` | 查询日期 | 最新交易日 |
| `--output` | text/json | text |

### 个股融券 Top N

查看融券余额最高的个股：

```bash
uv run --env-file .env python -m openclaw_alpha.skills.margin_trading.stock_margin_processor.stock_margin_processor --type securities
```

## 分析步骤

### Step 1: 查看市场杠杆水平

**输入**：无

**动作**：
```bash
uv run --env-file .env python -m openclaw_alpha.skills.margin_trading.market_margin_processor.market_margin_processor
```

**输出**：
- 沪深两市融资余额
- 融资余额环比变化
- 杠杆水平判断（高/正常/低）

### Step 2: 发现融资热门股

**输入**：市场杠杆水平正常或偏高

**动作**：
```bash
uv run --env-file .env python -m openclaw_alpha.skills.margin_trading.stock_margin_processor.stock_margin_processor
```

**输出**：融资余额 Top 20 个股

### Step 3: 发现做空标的

**输入**：需要判断市场做空力量

**动作**：
```bash
uv run --env-file .env python -m openclaw_alpha.skills.margin_trading.stock_margin_processor.stock_margin_processor --type securities
```

**输出**：融券余额 Top 20 个股

## 杠杆水平判断

| 水平 | 融资余额环比 | 含义 |
|------|-------------|------|
| **高** | > +2% | 杠杆增加，风险累积，注意回调风险 |
| **正常** | -2% ~ +2% | 正常波动，无特殊信号 |
| **低** | < -2% | 杠杆减少，情绪降温，可能见底 |

## 指标说明

| 指标 | 说明 | 多空含义 |
|------|------|----------|
| 融资余额 | 当前融资未还金额 | 余额↑ = 看多情绪强 |
| 融资买入额 | 当日融资买入金额 | 买入↑ = 新增多头 |
| 融券余量 | 当前融券未还股数 | 余量↑ = 做空增加 |
| 融券卖出量 | 当日融券卖出股数 | 卖出↑ = 新增空头 |

## 使用建议

1. **日常监控**：每天查看市场杠杆水平，关注异常波动
2. **选股参考**：融资余额高的股票通常是市场关注度高的大盘股
3. **风险预警**：杠杆水平持续走高时，注意市场回调风险
4. **做空监控**：关注融券余额变化，判断做空力量

## 注意事项

1. **数据延迟**：融资融券数据为 T 日晚间公布
2. **仅限标的**：只有融资融券标的股才有数据
3. **ETF 占比高**：融券标的中 ETF 占比较高，个股相对较少
4. **深市数据不稳定**：深市接口偶尔不稳定，可能只显示沪市数据
