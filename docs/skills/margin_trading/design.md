# 融资融券分析 - 设计文档

> 版本: v1.0
> 创建时间: 2026-03-08

---

## 技术选型

| 项目 | 选型 | 原因 |
|------|------|------|
| 数据源 | AKShare | 免费、稳定、接口完善 |
| 数据格式 | JSON | 与其他 skill 一致 |
| 命令方式 | 模块方式 | 统一格式 |

---

## 接口契约

### 市场汇总 Processor

**命令**：
```bash
uv run --env-file .env python -m skills.margin_trading.scripts.market_margin_processor.market_margin_processor
```

**参数**：
| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--date` | 查询日期 | 最新 |
| `--output` | text/json | text |

**输出**：
```json
{
  "date": "2026-03-05",
  "sh_market": {
    "financing_balance": 13466.9,
    "financing_buy": 1099.7,
    "change_pct": -0.28
  },
  "sz_market": {
    "financing_balance": 12910.4,
    "financing_buy": 1174.0,
    "change_pct": +0.43
  },
  "total_balance": 26377.3,
  "leverage_level": "正常"
}
```

### 个股明细 Processor

**命令**：
```bash
uv run --env-file .env python -m skills.margin_trading.scripts.stock_margin_processor.stock_margin_processor
```

**参数**：
| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--type` | financing/securities | financing |
| `--top-n` | 返回数量 | 20 |
| `--output` | text/json | text |

**输出**：
```json
{
  "date": "2026-03-05",
  "type": "financing",
  "stocks": [
    {
      "code": "600519",
      "name": "贵州茅台",
      "financing_balance": 125.3,
      "financing_buy": 5.2,
      "change_pct": +1.5
    }
  ]
}
```

---

## 数据源

### 市场汇总

| 接口 | 说明 |
|------|------|
| `ak.macro_china_market_margin_sh()` | 沪市汇总 |
| `ak.macro_china_market_margin_sz()` | 深市汇总 |

### 个股明细

| 接口 | 说明 |
|------|------|
| `ak.stock_margin_detail_sse(date)` | 沪市个股 |
| `ak.stock_margin_detail_szse(date)` | 深市个股 |

---

## 实现要点

1. **日期格式转换**：AKShare 使用 YYYYMMDD，需转换
2. **金额单位**：原始数据是元，转换为亿元便于阅读
3. **环比计算**：需要获取前一日数据进行对比
4. **数据合并**：个股明细需要合并沪深两市数据

---

## 目录结构

```
skills/margin_trading/
├── SKILL.md
└── scripts/
    ├── __init__.py
    ├── market_margin_processor/
    │   ├── __init__.py
    │   └── market_margin_processor.py
    └── stock_margin_processor/
        ├── __init__.py
        └── stock_margin_processor.py
```
