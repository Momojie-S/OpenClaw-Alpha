# 设计文档 - 龙虎榜追踪

## 一、技术方案

采用单数据源方案，使用 AKShare 的东方财富龙虎榜接口。

## 二、数据源

| 数据 | 来源 | 接口 |
|------|------|------|
| 每日龙虎榜 | AKShare | `stock_lhb_detail_em()` |
| 个股龙虎榜 | AKShare | `stock_lhb_stock_detail_em()` |

## 三、模块划分

```
lhb_tracker/scripts/
├── lhb_fetcher/            # 龙虎榜数据获取
│   ├── __init__.py
│   └── akshare_lhb.py
└── lhb_processor/          # 龙虎榜分析处理
    └── lhb_processor.py
```

### lhb_fetcher

封装龙虎榜数据获取逻辑。

### lhb_processor

提供两种分析模式：
- `daily`：每日龙虎榜摘要
- `stock`：个股龙虎榜历史

## 四、命令行参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--action` | 模式：daily/stock | daily |
| `--symbol` | 股票代码（stock 模式） | - |
| `--days` | 天数（stock 模式） | 5 |
| `--top-n` | 返回数量 | 10 |

## 五、输出设计

**每日龙虎榜**：`.openclaw_alpha/lhb-tracker/{date}/lhb_daily.json`

**个股龙虎榜**：`.openclaw_alpha/lhb-tracker/{date}/lhb_stock_{code}.json`

## 六、Tushare 备选方案

如需更稳定的数据源，可使用 Tushare：

| 接口 | 积分要求 |
|------|---------|
| `top_list` | 2000 |

待积分足够后补充实现。
