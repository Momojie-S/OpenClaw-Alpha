# 设计文档 - watchlist_monitor

## 一、技术方案

本地存储自选股列表，批量获取行情并展示统计。

**性能优化**（2026-03-11）：
- 根据自选股数量动态选择数据源
- <= 50 只：使用个股行情 API（2-28 秒）
- > 50 只：使用全市场行情 API（58 秒）

## 二、数据源

| 数据 | 来源 | 说明 |
|------|------|------|
| 实时行情（全市场） | AKShare `stock_zh_a_spot_em()` | 5000+ 只，约 58 秒 |
| 实时行情（个股） | AKShare `stock_individual_spot_xq()` | 单只约 0.5 秒 |

**选择策略**：
- 自选股 <= 50 只：使用个股接口
- 自选股 > 50 只：使用全市场接口

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

**性能优化逻辑**（`watch()` 方法）：
1. 读取自选股列表
2. 判断数量是否 <= 50
3. 选择合适的 Fetcher 获取数据
4. 对用户透明，接口不变

### 存储

- 自选股列表：`.openclaw_alpha/watchlist-monitor/watchlist.json`

## 四、注意事项

- 自选股数量建议不超过 50 只（性能考虑）
- 数据为最新交易日行情
- 个股接口需要雪球格式代码（自动转换）
