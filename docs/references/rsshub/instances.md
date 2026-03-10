# RSSHub 公共实例列表

> 更新日期：2026-03-10

---

## 可用实例（按速度排序）

| 实例 | 响应时间 | 上次可用 | 说明 |
|------|:--------:|:--------:|------|
| `rsshub-instance.zeabur.app` | 0.50s | 2026-03-10 | 速度最快 |
| `rsshub.liumingye.cn` | 0.73s | 2026-03-10 | 香港节点，国内访问友好 |
| `rsshub.rssforever.com` | 0.95s | 2026-03-10 | 稳定 |
| `rsshub.ktachibana.party` | 1.30s | 2026-03-10 | 美国节点 |
| `hub.slarker.me` | 1.47s | 2026-03-10 | - |
| `rsshub.pseudoyu.com` | 1.64s | 2026-03-10 | - |

---

## 不可用实例

| 实例 | 状态 | 说明 |
|------|:----:|------|
| `rsshub.feeded.xyz` | ❌ | 超时 |
| `rss.fatpandac.com` | ❌ | 超时 |
| `rsshub.app` | ❌ | 官方限制，仅用于测试 |

---

## 使用方式

```bash
# 获取财联社电报
curl -s "https://rsshub.ktachibana.party/cls/telegraph"

# 获取雪球今日话题
curl -s "https://rsshub.ktachibana.party/xueqiu/today"
```

---

## 维护说明

- **上次可用**：每次使用时更新，格式 `YYYY-MM-DD`
- **发现实例不可用**：移动到"不可用实例"表格
- **发现新实例**：先添加到"其他实例"，测试通过后移动到"推荐实例"
