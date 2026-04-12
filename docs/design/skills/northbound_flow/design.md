# 设计文档 - northbound_flow

## 一、技术方案

使用 AKShare 和 Tushare 双数据源：
- AKShare：主数据源（免费、稳定）
- Tushare：备用数据源（数据更规范）

## 二、数据源

| 数据 | 来源 | 接口 | 积分要求 |
|------|------|------|----------|
| 北向资金 | AKShare | `stock_hsgt_north_net_flow_in_em()` | 免费 |
| 北向资金 | Tushare | `moneyflow_hsgt()` | 基础 |
| 个股持股 | AKShare | `stock_hsgt_hold_stock_em()` | 免费 |

## 三、模块划分

```
northbound_flow/
├── scripts/
│   ├── flow_fetcher/          # 北向资金获取
│   │   ├── flow_fetcher.py    # Fetcher 入口
│   │   ├── akshare_flow.py    # AKShare 实现
│   │   └── tushare_flow.py    # Tushare 实现
│   └── northbound_processor/  # 北向资金分析
│       └── northbound_processor.py
└── docs/
```

### flow_fetcher

**职责**：获取北向资金数据

**输出字段**：
- 每日净流入：date, total_flow, sh_flow, sz_flow
- 个股持股：code, name, hold_change, hold_ratio

### northbound_processor

**职责**：分析北向资金趋势

**支持动作**：
- `--action daily`：每日净流入
- `--action stock`：个股流向
- `--action trend`：资金趋势
- `--action signals`：信号输出

## 四、接口契约

```bash
uv run --env-file .env python skills/northbound_flow/scripts/northbound_processor/northbound_processor.py --action <daily|stock|trend|signals> [--days N] [--top-n 10]
```

| 参数 | 说明 | 默认值 |
|------|------|--------|
| --action | 动作类型 | daily |
| --days | 天数 | 5 |
| --top-n | Top N | 10 |

## 五、信号输出

**路径**：`.openclaw_alpha/signals/flow/MARKET/northbound_30d.json`

**信号类型**：northbound_flow
