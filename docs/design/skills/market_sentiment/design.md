# 设计文档 - market_sentiment

## 一、技术方案

多数据源混合：
- AKShare：涨停、炸板、资金流向、市场宽度
- Tushare：涨跌家数（需要 120 积分）

## 二、数据源

| 数据 | 来源 | 接口 |
|------|------|------|
| 涨停股池 | AKShare | `stock_zt_pool_em()` |
| 炸板股池 | AKShare | `stock_zt_pool_zbgc_em()` |
| 大盘资金流向 | AKShare | `stock_market_fund_flow()` |
| 涨跌家数 | Tushare | `daily()` + 统计 |
| 新高新低 | AKShare | `stock_zh_a_spot_em()` + 计算 |

## 三、模块划分

```
market_sentiment/
├── scripts/
│   ├── limit_fetcher/           # 涨跌停数据
│   ├── flow_fetcher/            # 资金流向数据
│   ├── breadth_fetcher/         # 市场宽度数据
│   ├── sentiment_processor/     # 市场情绪分析
│   ├── breadth_processor/       # 市场宽度分析
│   ├── timing_processor/        # 择时分析
│   └── equity_bond_ratio_processor/  # 股债性价比
└── docs/
```

### Processors

| Processor | 职责 |
|-----------|------|
| sentiment_processor | 市场温度、情绪状态 |
| breadth_processor | 市场宽度、健康度 |
| timing_processor | 择时信号（左侧+右侧）|
| equity_bond_ratio_processor | 股债性价比 |

## 四、接口契约

```bash
# 市场情绪
uv run ... sentiment_processor.py [--date YYYY-MM-DD]

# 市场宽度
uv run ... breadth_processor.py [--symbol all|sz50|hs300|zz500] [--days 30]

# 择时信号
uv run ... timing_processor.py [--date YYYY-MM-DD]

# 股债性价比
uv run ... equity_bond_ratio_processor.py [--lookback-days 252]
```

## 五、信号输出

**路径**：`.openclaw_alpha/signals/timing/MARKET/timing.json`

**信号类型**：timing
