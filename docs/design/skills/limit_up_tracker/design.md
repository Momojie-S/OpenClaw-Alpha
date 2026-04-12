# 设计文档 - 涨停追踪

## 一、技术方案

使用 AKShare 获取涨停股数据，支持多种涨停类型查询。

## 二、数据源

| 数据 | 来源 | 接口 | 积分要求 |
|------|------|------|---------|
| 涨停股 | AKShare | `stock_zt_pool_em()` | 免费 |
| 跌停股 | AKShare | `stock_zt_pool_dtgc_em()` | 免费 |
| 炸板股 | AKShare | `stock_zt_pool_zbgc_em()` | 免费 |
| 昨日涨停 | AKShare | `stock_zt_pool_previous_em()` | 免费 |

**备选（未实现）**：
- Tushare `limit_list_d` - 需要 5000 积分

## 三、模块划分

```
limit_up_tracker/
├── scripts/
│   └── limit_up_fetcher/
│       ├── limit_up_fetcher.py   # 入口类
│       ├── akshare.py            # AKShare 实现
│       └── models.py             # 数据模型
```

### 3.1 Fetcher 入口

- `LimitUpFetcher` - 调度可用数据源
- `fetch()` - 获取涨停数据

### 3.2 数据模型

```python
class LimitUpType(Enum):
    LIMIT_UP = "limit_up"      # 涨停
    LIMIT_DOWN = "limit_down"  # 跌停
    BROKEN = "broken"          # 炸板
    PREVIOUS = "previous"      # 昨日涨停

class LimitUpItem:
    code: str
    name: str
    continuous: int        # 连板数
    change_pct: float      # 涨跌幅
    first_limit_time: str  # 封板时间
    limit_times: int       # 炸板次数
    float_mv: float        # 流通市值（亿）
    industry: str          # 所属行业

class LimitUpResult:
    date: str
    limit_type: LimitUpType
    total: int
    items: list[LimitUpItem]
    continuous_stat: dict   # 连板统计
```

## 四、输出

- 控制台：格式化的涨停股列表
- 文件：`.openclaw_alpha/limit_up_tracker/{date}/{type}.json`
