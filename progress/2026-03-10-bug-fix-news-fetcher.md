# 任务：修复 news_fetcher 数据源未注册问题

## 反馈来源
- **文件**：`feedback/2026-03-10-bug-news-driven-datasource.md`
- **用户**：Momojie
- **日期**：2026-03-10

## 问题描述
调用 `news_fetcher.py` 时报错：
```
NoAvailableMethodError: Fetcher 'news' 所有数据源均不可用:
  - akshare: 数据源未注册
```

## 根因分析
`news_fetcher.py` 缺少数据源注册导入：
```python
from openclaw_alpha.data_sources import registry  # noqa: F401
```

其他 fetcher 都有这行代码来确保数据源被注册到 `DataSourceRegistry`。

## 修复方案
在 `news_fetcher.py` 中添加数据源注册导入。

## 修复结果
- ✅ 已添加 `from openclaw_alpha.data_sources import registry  # noqa: F401`
- ✅ 测试通过：可以正常获取新闻

## 验证命令
```bash
uv run --env-file .env python skills/news_driven_investment/scripts/news_fetcher/news_fetcher.py --source cls_global --limit 3
```

## 状态
- **当前阶段**：完成
- **进度**：正常
- **优先级**：P0（Bug 修复）
- **下一步**：无
