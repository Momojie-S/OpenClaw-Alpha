---
name: industry-trend
description: 产业热度追踪。当用户询问行业板块、概念板块、题材热点、市场热度、哪个板块领涨时触发。
metadata:
  {
    "openclaw":
      {
        "emoji": "📈",
        "requires": { "bins": ["uv"] }
      }
  }
---

# 产业热度追踪

追踪 A 股市场行业/概念板块热度，识别热点和趋势。

## 数据脚本

| 脚本 | 功能 | 数据源 |
|------|------|--------|
| `board_industry.py` | 行业板块行情 | 同花顺 |
| `board_concept.py` | 概念板块行情 | 东方财富 |

*后续会持续增加更多数据接口*

## 使用

```bash
# 行业板块 Top 20
uv run --directory {baseDir}/.. python src/openclaw_alpha/commands/board_industry.py [--top N] [--sort FIELD]

# 概念板块 Top 20
uv run --directory {baseDir}/.. python src/openclaw_alpha/commands/board_concept.py [--top N] [--sort FIELD]
```

### 参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| --top | 20 | 返回前 N 个板块 |
| --sort | change_pct | 排序字段 |

## 输出格式

所有脚本返回统一 JSON 格式：

```json
{
  "success": true,
  "timestamp": "2026-03-02T15:00:00",
  "trade_date": "2026-03-02",
  "count": 20,
  "data_source": "数据源",
  "data": [...]
}
```

## 后续扩展

- 股票热度排名
- 资金流向
- 板块成分股
- 热度趋势分析

## 数据源

通过 AKShare，无需认证。
