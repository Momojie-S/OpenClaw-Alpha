---
name: openclaw_alpha_watchlist_monitor
description: "自选股监控：维护自选股列表，批量获取行情，快速分析。适用于：(1) 维护关注股票列表，(2) 批量查看自选股行情，(3) 分析自选股整体表现。不适用于：实时推送、复杂技术分析、持仓盈亏计算。"
metadata:
  openclaw:
    emoji: "⭐"
    requires:
      bins: ["uv"]
---

# 自选股监控

维护自选股列表，快速获取批量行情和分析。

## 使用说明

### 脚本运行

```bash
uv run --env-file .env python -m openclaw_alpha.skills.watchlist_monitor.watchlist_processor.watchlist_processor [参数]
```

### 运行记录

运行记录保存在：
- 自选股数据：`.openclaw_alpha/watchlist-monitor/watchlist.json`

## 分析步骤

### Step 1: 管理自选股列表

**添加股票**：
```bash
# 添加单只或多只股票
uv run --env-file .env python -m openclaw_alpha.skills.watchlist_monitor.watchlist_processor.watchlist_processor --add "000001,600000,002475"

# 从文件添加（每行一个代码）
uv run --env-file .env python -m openclaw_alpha.skills.watchlist_monitor.watchlist_processor.watchlist_processor --add-file watchlist.txt
```

**查看列表**：
```bash
uv run --env-file .env python -m openclaw_alpha.skills.watchlist_monitor.watchlist_processor.watchlist_processor --list
```

**移除股票**：
```bash
uv run --env-file .env python -m openclaw_alpha.skills.watchlist_monitor.watchlist_processor.watchlist_processor --remove "000001"
```

**清空列表**：
```bash
uv run --env-file .env python -m openclaw_alpha.skills.watchlist_monitor.watchlist_processor.watchlist_processor --clear --yes
```

### Step 2: 查看行情

**批量获取行情**：
```bash
# 查看所有自选股行情
uv run --env-file .env python -m openclaw_alpha.skills.watchlist_monitor.watchlist_processor.watchlist_processor --watch

# 只显示前5只
uv run --env-file .env python -m openclaw_alpha.skills.watchlist_monitor.watchlist_processor.watchlist_processor --watch --top-n 5
```

输出示例：
```
自选股行情 (共 5 只)
============================================================
代码     名称        现价    涨跌幅   成交额(亿)  换手率
------------------------------------------------------------
000001  平安银行    12.50   +2.35%      15.6    3.20%
600000  浦发银行     8.20   -0.50%       8.2    1.50%
///.py
统计: 3涨 2跌 平均 +1.20%
```

### Step 3: 快速分析

**分析自选股表现**：
```bash
uv run --env-file .env python -m openclaw_alpha.skills.watchlist_monitor.watchlist_processor.watchlist_processor --analyze
```

输出示例：
```
自选股分析报告
========================================

市场统计:
  总数: 5
  上涨: 3 (60%)
  下跌: 2 (40%)
  平均涨跌幅: +1.20%

表现最好:
  平安银行(000001): +2.35%

表现最差:
  浦发银行(600000): -0.50%

异动提醒: 无
```

## 相关 Skill

- [stock_screener](../stock_screener/SKILL.md) - 选股筛选
- [stock_analysis](../stock_analysis/SKILL.md) - 个股深度分析
- [portfolio_analysis](../portfolio_analysis/SKILL.md) - 持仓分析
