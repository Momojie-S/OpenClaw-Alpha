# 设计文档 - stock_compare

## 一、技术方案

批量获取股票行情，计算四维度评分，加权得出综合评分并排名。

## 二、数据源

| 数据 | 来源 | 说明 |
|------|------|------|
| 实时行情 | AKShare | 东方财富数据 |

## 三、模块划分

```
stock_compare/
├── scripts/
│   └── compare_processor/
│       ├── __init__.py
│       └── compare_processor.py  # 入口脚本
└── docs/
```

### Processor

- **入口**：`compare_processor.py`
- **参数**：
  - `symbols`：股票代码（逗号分隔，2-10 只）
  - `--date`：对比日期
  - `--output`：保存结果到文件
  - `--json`：输出 JSON 格式

### 输出

- 控制台：表格形式的对比报告
- 文件：`.openclaw_alpha/stock_compare/{date}/compare_processor.json`
