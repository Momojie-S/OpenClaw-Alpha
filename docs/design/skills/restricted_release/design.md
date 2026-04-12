# 设计文档 - 限售解禁风险监控

## 一、技术方案

使用 AKShare 的东方财富解禁数据接口。

## 二、数据源

| 数据 | 来源 | 接口 |
|------|------|------|
| 解禁日历 | AKShare | `stock_restricted_release_summary_em()` |
| 个股解禁 | AKShare | `stock_restricted_release_queue_em()` |

## 三、模块划分

```
restricted_release/scripts/
├── restricted_release_fetcher/   # 解禁数据获取
│   ├── restricted_release_fetcher.py
│   └── __init__.py
└── restricted_release_processor/ # 解禁分析处理
    ├── restricted_release_processor.py
    └── __init__.py
```

### restricted_release_fetcher

封装解禁数据获取逻辑。

### restricted_release_processor

提供三种分析模式：
- `upcoming`：查询即将解禁的股票
- `queue`：查询单只股票的解禁排期
- `high-risk`：筛选高解禁风险股票

## 四、命令行参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `action` | 模式：upcoming/queue/high-risk | - |
| `--days` | 天数（upcoming） | 7 |
| `--symbol` | 股票代码（queue） | - |
| `--min-ratio` | 最小比例（high-risk） | 0.1 |
| `--sort-by` | 排序字段：value/ratio | value |
| `--top-n` | 返回数量 | 20 |

## 五、输出设计

**即将解禁**：`.openclaw_alpha/restricted_release/{date}/upcoming.json`

**解禁排期**：`.openclaw_alpha/restricted_release/{date}/queue_{code}.json`

**高风险股票**：`.openclaw_alpha/restricted_release/{date}/high_risk.json`
