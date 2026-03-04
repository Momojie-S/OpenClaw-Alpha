---
name: industry-trend
description: 产业热度追踪。当用户询问行业板块、概念板块、题材热点、市场热度、哪个板块领涨、申万行业时触发。
metadata:
  {
    "openclaw":
      {
        "emoji": "📈",
        "requires": { "bins": ["uv"], "env": ["TUSHARE_TOKEN"] }
      }
  }
---

# 产业热度追踪

追踪 A 股市场热度，识别热点和趋势。

**工作流程：数据脚本获取数据 → Echo 分析总结 → 输出报告**

## 数据脚本

| 脚本 | 功能 | 数据源 | 需要认证 |
|------|------|--------|----------|
| `sw_industry.py` | 申万行业指数 | Tushare | 是（120积分）|
| `board_concept.py` | 概念板块行情 | 东方财富 | 否 |

## 使用

### 申万行业（推荐）

```bash
uv run --env-file {baseDir}/../.env --directory {baseDir}/.. python src/openclaw_alpha/commands/sw_industry.py [--date DATE] [--level LEVEL] [--top N]
```

**参数**：
- `--date` - 交易日期 (YYYYMMDD)，默认当日
- `--level` - 行业层级 (L1/L2/L3)，默认 L3
- `--top` - 返回数量，默认 50

**注意**：必须使用 `--env-file .env` 加载 TUSHARE_TOKEN

### 概念板块

```bash
uv run --directory {baseDir}/.. python src/openclaw_alpha/commands/board_concept.py [--top N] [--sort FIELD]
```

**参数**：
- `--top` - 返回数量，默认 20
- `--sort` - 排序字段（change_pct/amount/turnover），默认 change_pct

## 输出格式

所有脚本返回统一 JSON 格式：

```json
{
  "success": true,
  "timestamp": "2026-03-03T10:00:00",
  "trade_date": "2026-03-03",
  "count": 20,
  "data_source": "Tushare",
  "data": [...]
}
```

## 字段说明

### 申万行业

| 字段 | 说明 |
|------|------|
| board_code | 指数代码 |
| board_name | 行业名称 |
| change_pct | 涨跌幅 |
| turnover_rate | 换手率（可计算）|
| amount | 成交额 |
| float_mv | 流通市值 |
| pe/pb | 估值指标 |

### 概念板块

| 字段 | 说明 |
|------|------|
| board_code | 板块代码 |
| board_name | 板块名称 |
| change_pct | 涨跌幅 |
| turnover_rate | 换手率 |
| up_count/down_count | 涨跌家数 |

## 工作流程

1. **获取数据** - 调用脚本获取结构化数据
2. **分析总结** - Echo 基于数据进行大模型分析
3. **输出报告** - 生成易读的热度报告

## 后续扩展

- [ ] 概念板块资金流向
- [ ] 股票热度排名
- [ ] SQLite 历史存储
- [ ] 热度趋势分析（环比）
