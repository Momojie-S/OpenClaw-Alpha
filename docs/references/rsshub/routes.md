# RSSHub 投资相关路由

> 更新日期：2026-03-10

---

## 财经快讯

| 路由 | source 值 | 说明 |
|------|----------|------|
| `/cls/telegraph` | `cls_telegraph` | 财联社电报快讯 |
| `/cls/telegraph/{keyword}` | - | 财联社电报关键词筛选（暂不支持） |
| `/jin10` | `jin10` | 金十数据快讯 |

## 财经媒体

| 路由 | source 值 | 说明 |
|------|----------|------|
| `/yicai/brief` | `yicai_brief` | 第一财经简报 |

## 社区资讯（已失效）

| 路由 | source 值 | 说明 | 状态 |
|------|----------|------|------|
| `/xueqiu/today` | `xueqiu_today` | 雪球今日话题 | ❌ 已失效（HTTP 503） |

---

## 使用方式

```bash
# 通过 news_fetcher 使用
uv run ... news_fetcher.py --source cls_telegraph --limit 10
uv run ... news_fetcher.py --source jin10 --limit 10
uv run ... news_fetcher.py --source yicai_brief --limit 10

# 直接访问 RSSHub API
curl "https://rsshub.liumingye.cn/cls/telegraph?format=json"
```

---

## 维护说明

- **新增路由**：在 `rsshub.py` 的 `RSSHUB_ROUTES` 中添加映射
- **更新文档**：同步更新此文件
- **路由失效**：标记为"已失效"并注明原因
