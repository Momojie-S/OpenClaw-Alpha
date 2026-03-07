# 涨停追踪 - 设计文档

## 技术选型

| 选型 | 原因 |
|------|------|
| 数据源 | AKShare（免费、无需 token） |
| 接口 | `stock_zt_pool_em` 系列（东方财富） |
| 存储 | 不存储，实时获取 |

## 数据流

```
用户请求
    ↓
Processor (limit_up_processor)
    ↓
Fetcher (limit_up_fetcher)
    ├── 涨停股池: stock_zt_pool_em
    ├── 炸板股池: stock_zt_pool_zbgc_em
    ├── 跌停股池: stock_zt_pool_dtgc_em
    └── 昨日涨停: stock_zt_pool_previous_em
    ↓
Processor 加工数据
    ↓
控制台输出 + 文件保存
```

## 接口设计

### LimitUpItem（涨停股数据）

```python
@dataclass
class LimitUpItem:
    """涨停股数据"""
    code: str              # 股票代码
    name: str              # 股票名称
    change_pct: float      # 涨跌幅 %
    price: float           # 最新价
    amount: float          # 成交额（亿）
    float_mv: float        # 流通市值（亿）
    total_mv: float        # 总市值（亿）
    turnover_rate: float   # 换手率 %
    first_limit_time: str  # 首次封板时间
    last_limit_time: str   # 最后封板时间
    limit_times: int       # 当日炸板次数
    limit_stat: str        # 涨停统计（如 '10/6'）
    continuous: int        # 连板数
    industry: str          # 所属行业
```

### Processor 参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--date` | 交易日期 | 今天 |
| `--type` | 类型：`limit_up`(涨停)、`limit_down`(跌停)、`broken`(炸板)、`previous`(昨日涨停) | limit_up |
| `--min-continuous` | 最小连板数 | 1 |
| `--top-n` | 返回数量 | 20 |

## 输出格式

### 控制台（精简）

```
涨停股池 (2026-03-07) - 共 45 只
========================================
连板统计: 首板 28 | 2板 12 | 3板 4 | 4+板 1

Top 10 连板股:
------------------------------------------------------------
代码     名称        连板  封板时间   炸板  封板资金(亿)  所属行业
------------------------------------------------------------
002475  立讯精密     4    09:32:15    0      15.6     消费电子
000001  平安银行     3    09:45:22    1       8.2     银行
...
```

### 文件（完整）

保存路径：`.openclaw_alpha/limit_up_tracker/{date}/limit_up.json`

## 目录结构

```
skills/limit_up_tracker/
├── SKILL.md
└── scripts/
    ├── __init__.py
    └── limit_up_fetcher/
        ├── __init__.py
        ├── limit_up_fetcher.py    # 入口
        └── akshare.py             # AKShare 实现
```

**注意**：这个 skill 只需要 Fetcher，不需要单独的 Processor。直接运行 fetcher 即可输出格式化结果。

## 参考资料

- [涨停板数据接口](../../references/api/akshare/limit_pool_apis.md)
