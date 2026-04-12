# 设计文档 - index_analysis

## 一、技术方案

获取主要指数的日线行情，计算 MA5/MA20，判断趋势和市场温度。

## 二、数据源

| 数据 | 来源 | 说明 |
|------|------|------|
| 指数行情 | AKShare | 东方财富数据 |

### 覆盖指数

- 上证指数 (sh000001)
- 深证成指 (sz399001)
- 创业板指 (sz399006)
- 科创50 (sh000688)
- 沪深300 (sh000300)
- 中证500 (sh000905)

## 三、模块划分

```
index_analysis/
├── scripts/
│   └── index_processor/
│       ├── __init__.py
│       └── index_processor.py  # 入口脚本
└── docs/
```

### Processor

- **入口**：`index_processor.py`
- **参数**：
  - `--date`：分析日期
  - `--top-n`：返回数量

### 输出

- 控制台：精简的指数分析结果
- 文件：`.openclaw_alpha/index_analysis/{date}/index.json`
