# 资金流向分析 Skill - 设计文档

## 一、技术选型

### 1.1 数据源

| 数据 | 数据源 | 接口 | 稳定性 |
|------|--------|------|--------|
| 行业资金流 | 同花顺 | `stock_fund_flow_industry` | 稳定 |
| 概念资金流 | 同花顺 | `stock_fund_flow_concept` | 稳定 |

**为什么不选东方财富**：东方财富接口（`stock_individual_fund_flow_rank`、`stock_sector_fund_flow_rank`）网络不稳定，经常超时。

### 1.2 架构设计

简化架构：直接在 Processor 中调用 AKShare，不需要独立 Fetcher。

**理由**：
1. 逻辑简单，只有 2 个 API 调用
2. 无需数据转换（AKShare 返回的数据结构可直接使用）
3. 参考 `etf_analysis` 的成功实践

## 二、数据结构

### 2.1 行业/概念资金流数据

```python
@dataclass
class FundFlowData:
    """资金流向数据"""
    rank: int           # 排名
    name: str           # 行业/概念名称
    index_value: float  # 行业指数
    change_pct: float   # 涨跌幅(%)
    inflow: float       # 流入资金(亿)
    outflow: float      # 流出资金(亿)
    net_amount: float   # 净额(亿)
    company_count: int  # 公司家数
    leading_stock: str  # 领涨股
    leading_change: float  # 领涨股涨跌幅(%)
    current_price: float   # 当前价
```

## 三、接口设计

### 3.1 命令行参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--type` | str | industry | 类型：industry(行业) / concept(概念) |
| `--period` | str | 即时 | 时间周期：即时/3日排行/5日排行/10日排行/20日排行 |
| `--min-net` | float | None | 最小净额过滤(亿) |
| `--top-n` | int | 10 | 返回 Top N |
| `--sort-by` | str | net | 排序字段：net(净额) / change(涨幅) / inflow(流入) |
| `--output` | path | None | 输出文件路径 |

### 3.2 输出格式

**控制台（精简）**：
```
行业资金流向 (即时) - Top 10
=====================================
排名  行业        净额(亿)   涨幅(%)  领涨股
-------------------------------------
1    农化制品     30.95     +4.44   农大科技
2    化学原料     22.75     +3.78   江天化学
...
```

**文件（完整）**：JSON 格式，包含所有字段

## 四、流程设计

```
main()
  ↓
parse_args()      # 解析命令行参数
  ↓
fetch_fund_flow() # 调用 AKShare 获取数据
  ↓
process_data()    # 筛选、排序
  ↓
save_to_file()    # 保存完整数据
  ↓
print_result()    # 打印精简结果
```

## 五、错误处理

- 网络超时：重试 3 次，失败则报错
- 无数据：提示"暂无数据"
- 参数错误：显示帮助信息

## 六、文件结构

```
skills/fund_flow_analysis/
├── SKILL.md
└── scripts/
    ├── __init__.py
    └── fund_flow_processor/
        ├── __init__.py
        └── fund_flow_processor.py
```
