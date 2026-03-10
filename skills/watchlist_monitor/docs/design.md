# 设计文档 - watchlist_monitor

## 一、技术方案

本地存储自选股列表，批量获取行情并展示统计。

## 二、数据源

| 数据 | 来源 | 说明 |
|------|------|------|
| 实时行情 | AKShare | 东方财富数据 |

## 三、模块划分

```
watchlist_monitor/
├── scripts/
│   └── watchlist_processor/
│       ├── __init__.py
│       └── watchlist_processor.py  # 入口脚本
└── docs/
```

### Processor

- **入口**：`watchlist_processor.py`
- **参数**：
  - `--add`：添加股票（逗号分隔）
  - `--add-file`：从文件添加
  - `--remove`：移除股票
  - `--clear`：清空列表（需 `--yes`）
  - `--list`：查看列表
  - `--watch`：查看行情
  - `--analyze`：分析表现
  - `--top-n`：显示数量

### 存储

- 自选股列表：`.openclaw_alpha/watchlist-monitor/watchlist.json`

## 四、注意事项

- 自选股数量建议不超过 50 只
- 数据为最新交易日行情
