# 任务：自选股监控 Skill (watchlist_monitor)

## 需求

实现一个自选股监控 skill，帮助用户维护关注列表，快速获取所有自选股的行情和分析。

## Phase 1: 需求
- [x] 编写需求文档
  - 位置：`docs/watchlist-monitor/spec.md`
  - 内容：自选股管理、行情监控、快速分析

## Phase 2: 设计
- [x] 调研技术方案，编写设计文档
  - 位置：`docs/watchlist-monitor/design.md`
  - 决策：复用 StockSpotFetcher，JSON 文件存储
- [x] 检查是否需要外部 API 调用
  - 复用 stock_screener 的 StockSpotFetcher，跳过 API 文档

## Phase 3: API 文档
- 跳过（复用已有 Fetcher）

## Phase 4: 开发
- [x] 创建 skill 目录结构
- [x] 实现 WatchlistManager（列表管理）
- [x] 实现 WatchlistProcessor（行情获取、分析）
- [x] 编写 SKILL.md

## Phase 5: 调试
- 跳过（复用已有 Fetcher，逻辑简单）

## Phase 6: 测试
- [x] 编写 WatchlistManager 测试 - 8 个测试
- [x] 编写 WatchlistProcessor 测试 - 16 个测试
- [x] 运行测试，确保全部通过 - 24/24 通过

## Phase 7: 文档合并
- [x] 文档已独立存放（docs/watchlist-monitor/），无需合并

## 完成总结

### 已完成

1. **需求文档** - `docs/watchlist-monitor/spec.md`
2. **设计文档** - `docs/watchlist-monitor/design.md`
3. **代码实现**
   - WatchlistManager（自选股列表管理）
   - WatchlistProcessor（行情获取、分析）
   - SKILL.md 文档
4. **测试** - 24/24 通过
   - WatchlistManager: 8 个测试
   - WatchlistProcessor: 16 个测试（筛选、排序、统计、格式化）

### 使用示例

```bash
# 添加自选股
uv run --env-file .env python skills/watchlist_monitor/scripts/watchlist_processor/watchlist_processor.py --add "000001,600000"

# 查看列表
uv run --env-file .env python skills/watchlist_monitor/scripts/watchlist_processor/watchlist_processor.py --list

# 获取行情
uv run --env-file .env python skills/watchlist_monitor/scripts/watchlist_processor/watchlist_processor.py --watch

# 快速分析
uv run --env-file .env python skills/watchlist_monitor/scripts/watchlist_processor/watchlist_processor.py --analyze
```

### 功能

| 功能 | 命令 |
|------|------|
| 添加股票 | `--add` |
| 从文件添加 | `--add-file` |
| 移除股票 | `--remove` |
| 查看列表 | `--list` |
| 清空列表 | `--clear` |
| 获取行情 | `--watch` |
| 快速分析 | `--analyze` |

## 备注
开始时间：2026-03-07 08:40
完成时间：2026-03-07 09:20
