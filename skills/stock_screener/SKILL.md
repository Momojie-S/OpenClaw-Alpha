---
name: openclaw_alpha_stock_screener
description: "选股筛选器，按条件快速筛选股票。适用于：(1) 按涨幅/换手率/市值等条件筛选，(2) 使用预设策略快速选股，(3) 寻找符合条件的投资标的。不适用于：技术指标筛选、财务指标筛选、回测验证。"
metadata:
  openclaw:
    emoji: "🔍"
    requires:
      bins: ["uv"]
---

# 选股筛选器

从 5000+ 只 A 股中快速筛选符合条件的股票。

## 使用说明

### 脚本运行

所有脚本需在项目根目录下运行，使用 `uv run --env-file .env` 加载环境变量：

```bash
uv run --env-file .env python -m skills.stock_screener.scripts.screener_processor.screener_processor [参数]
```

**如果脚本运行失败**：
1. 检查是否在项目根目录
2. 检查网络连接（需要访问东方财富接口）
3. 将错误信息记录到进度文件，不要丢失上下文

### 运行记录

**进度文件位置**：`.openclaw_alpha/stock-screener/{YYYY-MM-DD}/progress.md`

每次运行脚本后，记录：
- 运行时间
- 脚本命令
- 运行结果（成功/失败）
- 关键输出（筛选结果数、Top 3 股票）
- 错误信息（如有）

## 分析步骤

### Step 1: 使用预设策略筛选

**输入**：策略名称（可选 Top N）

**动作**：
```bash
# 放量突破策略
uv run --env-file .env python -m skills.stock_screener.scripts.screener_processor.screener_processor \
    --strategy volume_breakout --top-n 10

# 龙头股策略
uv run --env-file .env python -m skills.stock_screener.scripts.screener_processor.screener_processor \
    --strategy leader --top-n 20
```

**输出**：
- 控制台：筛选结果（JSON 格式）
- 文件：`.openclaw_alpha/stock-screener/{date}/screener.json`

**可用策略**：
| 策略 | 条件 |
|------|------|
| `volume_breakout` | 涨幅 > 3%，换手率 > 5%，成交额 > 2 亿 |
| `pullback` | 涨幅 -5% ~ 0%，换手率 < 3% |
| `leader` | 涨幅 > 5%，成交额 > 10 亿，市值 > 100 亿 |
| `small_active` | 换手率 > 8%，市值 < 50 亿 |
| `blue_chip` | 市值 > 500 亿，换手率 < 2% |

### Step 2: 自定义条件筛选

**输入**：各种筛选条件

**动作**：
```bash
# 自定义筛选：涨幅 > 5%，成交额 > 5 亿
uv run --env-file .env python -m skills.stock_screener.scripts.screener_processor.screener_processor \
    --change-min 5 --amount-min 5 --top-n 20

# 多条件组合
uv run --env-file .env python -m skills.stock_screener.scripts.screener_processor.screener_processor \
    --change-min 2 --change-max 9 \
    --turnover-min 3 --turnover-max 15 \
    --cap-min 50 --cap-max 500 \
    --top-n 30
```

**支持的筛选条件**：
| 参数 | 说明 | 单位 |
|------|------|------|
| `--change-min` | 涨幅下限 | % |
| `--change-max` | 涨幅上限 | % |
| `--turnover-min` | 换手下限 | % |
| `--turnover-max` | 换手上限 | % |
| `--amount-min` | 成交额下限 | 亿元 |
| `--amount-max` | 成交额上限 | 亿元 |
| `--cap-min` | 市值下限 | 亿元 |
| `--cap-max` | 市值上限 | 亿元 |
| `--price-min` | 价格下限 | 元 |
| `--price-max` | 价格上限 | 元 |

### Step 3: 查看可用策略

**动作**：
```bash
uv run --env-file .env python -m skills.stock_screener.scripts.screener_processor.screener_processor --list-strategies
```

## 输出说明

### 筛选结果

```json
{
  "date": "2026-03-07",
  "strategy": "volume_breakout",
  "total_matched": 35,
  "showing": 10,
  "results": [
    {
      "code": "300XXX",
      "name": "XXX科技",
      "change_pct": 8.52,
      "turnover_rate": 12.3,
      "amount": 5.6,
      "price": 35.2,
      "market_cap": 120.5
    }
  ]
}
```

### 字段说明

| 字段 | 说明 | 单位 |
|------|------|------|
| `code` | 股票代码 | - |
| `name` | 股票名称 | - |
| `change_pct` | 涨跌幅 | % |
| `turnover_rate` | 换手率 | % |
| `amount` | 成交额 | 亿元 |
| `price` | 最新价 | 元 |
| `market_cap` | 总市值 | 亿元 |

## 排序选项

| 参数 | 说明 |
|------|------|
| `--sort change` | 按涨跌幅排序（默认） |
| `--sort turnover` | 按换手率排序 |
| `--sort amount` | 按成交额排序 |
| `--sort cap` | 按市值排序 |
| `--asc` | 升序（默认降序） |

## 数据源

- **全市场行情**：AKShare（免费）
- 数据来源：东方财富

## 注意事项

1. **数据延迟**：盘中数据有延迟
2. **非交易日**：返回最近交易日数据
3. **筛选结果上限**：最多返回 100 只股票

## 使用建议

1. **策略组合**：先用预设策略快速筛选，再根据结果微调条件
2. **结合其他 skill**：
   - 筛选结果 → `stock_analysis` 深入分析个股
   - 筛选结果 → `industry_trend` 查看板块热度
   - 筛选结果 → `northbound_flow` 查看外资持仓

## 深入分析

筛选出股票后，使用其他 skill 进行深入分析：
- **stock_analysis**：分析个股行情和基本面
- **industry_trend**：查看股票所在板块的热度
- **lhb_tracker**：查看是否有游资/机构介入
