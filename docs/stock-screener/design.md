# 选股筛选器 - 设计文档

## 一、技术选型

### 1.1 数据源选择

| 数据源 | 接口 | 优势 | 劣势 | 决策 |
|--------|------|------|------|------|
| AKShare | stock_zh_a_spot_em() | 免费、实时、数据全 | 网络不稳定 | **首选** |
| Tushare | daily() + basic() | 稳定、数据准 | 需要积分、字段有限 | 备选 |

**决策**：使用 AKShare 的 `stock_zh_a_spot_em()` 接口作为主要数据源，该接口返回 A 股所有股票的实时行情数据，包含涨跌幅、换手率、成交额、市值、价格等所需字段。

### 1.2 数据字段映射

| 业务字段 | AKShare 字段 | 说明 |
|----------|-------------|------|
| 股票代码 | 代码 | 6 位代码 |
| 股票名称 | 名称 | - |
| 涨跌幅 | 涨跌幅 | 百分比 |
| 换手率 | 换手率 | 百分比 |
| 成交额 | 成交额 | 元 |
| 最新价 | 最新价 | 元 |
| 总市值 | 总市值 | 元 |

## 二、架构设计

### 2.1 模块结构

```
skills/stock_screener/
├── SKILL.md
└── scripts/
    ├── __init__.py
    ├── stock_spot_fetcher/        # 全市场行情获取
    │   ├── __init__.py
    │   ├── stock_spot_fetcher.py  # 入口类
    │   └── akshare.py             # AKShare 实现
    └── screener_processor/        # 筛选处理器
        ├── __init__.py
        └── screener_processor.py
```

### 2.2 类设计

#### StockSpotFetcher

负责获取全市场股票行情数据。

```python
class StockSpotFetcher(Fetcher):
    """全市场股票行情 Fetcher"""
    name = "stock_spot"
    
    async def fetch(self) -> list[StockSpot]:
        """获取全市场股票行情"""
        pass

class StockSpot:
    """股票行情数据"""
    code: str        # 代码
    name: str        # 名称
    change_pct: float  # 涨跌幅（%）
    turnover_rate: float  # 换手率（%）
    amount: float    # 成交额（亿元）
    price: float     # 最新价（元）
    market_cap: float  # 总市值（亿元）
```

#### ScreenerProcessor

负责按条件筛选股票。

```python
class ScreenerProcessor:
    """选股筛选器"""
    
    def filter(self, spots: list[StockSpot], conditions: FilterConditions) -> list[StockSpot]:
        """按条件筛选"""
        pass
    
    def apply_strategy(self, spots: list[StockSpot], strategy: str) -> list[StockSpot]:
        """应用预设策略"""
        pass

class FilterConditions:
    """筛选条件"""
    change_min: float | None = None      # 涨幅下限
    change_max: float | None = None      # 涨幅上限
    turnover_min: float | None = None    # 换手下限
    turnover_max: float | None = None    # 换手上限
    amount_min: float | None = None      # 成交额下限（亿）
    amount_max: float | None = None      # 成交额上限（亿）
    cap_min: float | None = None         # 市值下限（亿）
    cap_max: float | None = None         # 市值上限（亿）
    price_min: float | None = None       # 价格下限
    price_max: float | None = None       # 价格上限
```

### 2.3 预设策略定义

```python
STRATEGIES = {
    "volume_breakout": FilterConditions(
        change_min=3.0,
        turnover_min=5.0,
        amount_min=2.0,
    ),
    "pullback": FilterConditions(
        change_min=-5.0,
        change_max=0.0,
        turnover_max=3.0,
    ),
    "leader": FilterConditions(
        change_min=5.0,
        amount_min=10.0,
        cap_min=100.0,
    ),
    "small_active": FilterConditions(
        turnover_min=8.0,
        cap_max=50.0,
    ),
    "blue_chip": FilterConditions(
        cap_min=500.0,
        turnover_max=2.0,
    ),
}
```

## 三、数据流

```
用户调用 screener_processor
        │
        ▼
StockSpotFetcher.fetch()  ──→  AKShare: stock_zh_a_spot_em()
        │
        ▼
数据转换（单位、格式）
        │
        ▼
ScreenerProcessor.filter(conditions) 或 apply_strategy(strategy)
        │
        ▼
排序、Top N 限制
        │
        ▼
输出结果（控制台 + 文件）
```

## 四、命令行接口

```bash
# 自定义筛选
uv run --env-file .env python skills/stock_screener/scripts/screener_processor/screener_processor.py \
    --change-min 3 \
    --turnover-min 5 \
    --amount-min 2 \
    --top-n 20

# 使用预设策略
uv run --env-file .env python skills/stock_screener/scripts/screener_processor/screener_processor.py \
    --strategy volume_breakout \
    --top-n 10

# 列出可用策略
uv run --env-file .env python skills/stock_screener/scripts/screener_processor/screener_processor.py \
    --list-strategies
```

## 五、输出格式

### 控制台输出

精简结果，给大模型分析：

```json
{
  "date": "2026-03-07",
  "strategy": "volume_breakout",
  "total_matched": 35,
  "results": [
    {
      "code": "300XXX",
      "name": "XXX科技",
      "change_pct": 5.23,
      "turnover_rate": 8.5,
      "amount": 3.2,
      "price": 25.6,
      "market_cap": 80.5
    }
  ]
}
```

### 文件输出

完整数据，保存到 `.openclaw_alpha/stock-screener/{date}/screen_result.json`

## 六、错误处理

| 异常情况 | 处理方式 |
|----------|----------|
| 网络超时 | 重试 3 次，指数退避 |
| 无数据 | 返回空列表，提示"非交易日或数据未更新" |
| 无效参数 | 参数校验，提示正确用法 |
| 筛选无结果 | 返回空列表，建议放宽条件 |

## 七、性能考虑

- 全市场 5000+ 股票数据量较大（约 2MB）
- 内存筛选性能足够（< 100ms）
- 可考虑后续增加缓存机制
