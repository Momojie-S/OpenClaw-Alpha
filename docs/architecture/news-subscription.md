# 新闻订阅分析功能设计

> **注意**：此文档为旧版设计，新设计请参考：
> - 快速分析：[docs/design/news/quick-analysis.md](../design/news/quick-analysis.md)
> - 深度分析：[docs/design/news/deep-analysis.md](../design/news/deep-analysis.md)
> - 整体设计：[docs/design/news/overview.md](../design/news/overview.md)
>
> API 端点已更新为：
> - 快速分析：`POST /api/news/quick/trigger`
> - 深度分析：详见深度分析设计文档

## 目标

定时从 RSSHub 拉取新闻，识别未处理的新闻，触发一次性 isolated session 进行分析。

## 功能流程

```
RSSHub → 拉取新闻 → 对比已处理记录 → 新新闻 → 触发分析 session
           ↓
      记录处理状态（按路由+天）
```

## 目录结构

```
{project_root}/workspace/
├── news/                       # 新闻模块工作目录
│   ├── config.yaml             # 新闻模块配置
│   ├── cache/
│   │   └── rsshub/
│   │       └── {route_id}/
│   │           └── {YYYY-MM-DD}.json  # 新闻状态记录
│   └── analysis/               # 新闻分析任务目录
│       └── {YYYY-MM-DD}/
│           └── {news_id}/
│               ├── progress.md
│               └── report.md
└── logs/

src/openclaw_alpha/backend/news/
├── jobs.py                # 定时任务：拉取 + 触发分析
├── rss_fetcher.py         # RSS 拉取逻辑
├── state_manager.py       # 状态文件管理
├── task_executor.py       # 调用 openclaw cron
├── config.py              # 配置模型
└── models.py              # 数据模型
```

## 配置

**路径**：`workspace/news/config.yaml`

```yaml
enabled: true
interval_minutes: 30

# Agent 配置
agent_id: alpha
model: zai/glm-4.7

# 消息推送
delivery:
  channel: wecom
  to: Momojie

# Cron 任务配置
cron:
  # 轮询 session store 的超时时间（秒）
  # 用于等待任务 session 创建
  session_poll_timeout_seconds: 300

  # 等待 report.md 创建的超时时间（秒）
  # 用于追加系统运行信息到报告
  report_wait_timeout_seconds: 300
```

**RSS 源**（硬编码，按优先级）：
1. `/cls/telegraph` - 财联社电报快讯
2. `/jin10` - 金十数据快讯
3. `/wallstreetcn/news` - 华尔街见闻资讯
4. `/yicai/brief` - 第一财经简报

**RSSHub 实例**：自动尝试多个实例，失败自动切换

## 状态文件

**路径**：`workspace/news/cache/rsshub/{route_id}/{YYYY-MM-DD}.json`

**route_id**：URL path 第一段（如 `/cls/telegraph` → `cls`）

**字段**：
- `id`, `title`, `link`, `published` - 新闻信息
- `processed` - 是否已处理
- `processed_at`, `job_id`, `workspace_dir` - 处理记录

## 定时任务

**调度**：APScheduler，间隔可配置

**逻辑**：
1. 遍历 RSS 源（按优先级）
2. 拉取 RSS 内容（所有新闻）
3. **过滤出今天发布的新闻**（基于 `published` 字段）
4. 加载今日状态文件
5. 过滤未处理的新闻
6. 应用 limit 限制（如果指定）
7. 逐个触发分析（调用 `submit_analysis`）
8. 更新状态文件

**处理范围**：**今天发布且未处理的新闻**
- 定时任务使用 `limit=0`，处理全部
- 先按 `published` 日期过滤，再检查是否已处理
- 避免每天重复处理旧新闻

**"今天"的定义**：
- 使用 `date.today()` 获取当前日期（服务器本地时区）
- 比较新闻的 `published` 字段：`item.published.date() == today`
- 状态文件路径：`cache/news/rsshub/{route_id}/{YYYY-MM-DD}.json`
- 例如：`cache/news/rsshub/cls/2026-03-13.json`
- 时区：使用服务器本地时区（Asia/Shanghai）

**RSS 拉取说明**：
- 拉取所有新闻（不按日期过滤）
- **必须基于 `published` 字段过滤出今天的新闻**
- 避免每天重复处理历史新闻

**处理方式**：逐个处理（非并发）
- 确保资源消耗可控
- 避免并发冲突
- 等待当前分析完成后才处理下一条

## 分析任务执行

### 触发方式

`openclaw cron add --session isolated`

**cron 命令详解**：参见 [OpenClaw Cron 调研](../openclaw/cron.md)

### task_executor.py 职责

**函数**：`async submit_analysis(title, link, summary) -> (job_id, task_dir)`

**流程**：
1. 创建工作目录：`workspace/news/analysis/{date}/{news_id}/`
2. 构造任务消息（模板 + 参数 + 内容）
3. 提交 cron 任务（异步）
4. 轮询 session store 获取 session 信息（异步，超时可配置）
5. 等待 report.md 创建（异步，超时可配置）
6. 追加系统运行信息到 report.md
7. 返回 `(job_id, task_dir)`

**路径工具**：使用 `openclaw_alpha.core.path_utils`

### cron 参数

| 参数 | 值 | 说明 |
|------|---|---|
| `--session` | `isolated` | 使用隔离 session |
| `--at` | `now` | 立即触发 |
| `--delete-after-run` | - | **不使用此选项**（见下方说明） |
| `--thinking` | `low` | 降低推理消耗 |
| `--timeout-seconds` | `300`（5 分钟） | 任务超时时间 |
| `--announce` | 启用推送 | 推送结果到配置的渠道 |
| `--channel` | 从配置读取 | 推送渠道 |
| `--to` | 从配置读取 | 推送目标 |

### Session 生命周期调研

**问题**：OpenClaw 的 cron session 清理机制

**`deleteAfterRun` 参数的作用**：
- **直接作用**：控制 Cron Job 记录是否在执行后删除
- **连带影响**：影响 Session 文件的清理时机

| 配置 | Cron Job | Session 删除时机 |
|------|----------|---------------|
| `deleteAfterRun: true` | 从 jobs.json 删除 | **~0.5 秒**内删除 |
| `deleteAfterRun: false` (`--keep-after-run`) | 保留 (disabled) | **不删除**（由其他机制清理） |

**实测案例**：
```
test-lifecycle (deleteAfterRun: true):
  07:55:27.092 - 最后一条消息
  07:55:27.650 - Session 删除 (仅差 0.558 秒)

test-keep (deleteAfterRun: false):
  16:10:00 - 任务完成
  16:15+  - Session 仍然存在
```

**清理机制**：
- Session 删除后会重命名为 `.deleted.{timestamp}` 备份
- 例如：`7d28cad7-9e7e-4def-bef1-9b9a1d4b794a.jsonl.deleted.2026-03-13T07-55-27.650Z`

**本方案的处理**：
- 不使用 `--delete-after-run`
- 在 `append_system_info` 中，当 session 文件不存在时，自动查找并使用最新的 `.deleted` 备份
- 这样既能保留当天 session 用于追溯，又能在自然清理后仍有备份可用

### Async 说明

为了避免阻塞主线程，所有 `submit_cron_task` 和 `submit_analysis` 都改为 async 函数：

- 使用 `asyncio.to_thread` 执行阻塞的 subprocess 调用
- 使用 `asyncio.sleep` 进行异步等待
- 轮询 session store 时使用异步等待

**配置的超时时间**：
- `session_poll_timeout_seconds`：轮询 session store 的超时（默认 300 秒）
- `report_wait_timeout_seconds`：等待 report.md 创建的超时（默认 300 秒）

### jobs.py 集成

```python
job_id, workspace_dir = submit_analysis(
    title=item.title,
    link=item.link,
    summary=item.summary
)

if job_id:
    mark_processed(state, item, job_id, workspace_dir)
```

**失败处理**：返回 `None` 时不标记已处理，下次重试

## 错误处理

| 错误类型 | 处理方式 |
|---------|---------|
| RSS 拉取失败 | 跳过该源，继续下一个 |
| 状态文件损坏 | 备份后重建 |
| 分析任务失败 | 不标记，下次重试 |

## 清理策略

**状态文件**：
- 保留 7 天
- 每日凌晨自动清理
- 清理函数：`cleanup_old_states(keep_days=7)`

**清理逻辑**：
- 遍历 `cache/news/rsshub/{route_id}/` 下的所有状态文件
- 从文件名解析日期（`{YYYY-MM-DD}.json`）
- 删除超过 7 天的文件
- 例如：今天是 2026-03-13，则删除 2026-03-06 及更早的文件

**时区说明**：
- "今天"和清理日期都使用服务器本地时区（Asia/Shanghai）
- 如果服务器时区变更，需要手动调整或等待自然清理

## 任务模板

**文件**：`skills/news_driven_investment/tasks/quick-news-analysis.md`

**作用**：指导智能体如何分析新闻，是任务消息的核心部分。

**消息结构**：
```
[任务模板 - quick-news-analysis.md]

---

## 本次任务参数

- **任务目录**：{task_dir}
- **新闻标题**：{title}
- **新闻链接**：{link}

---

## 新闻内容

{content}
```

**设计原则**：
1. 专注指令，不介绍拼接内容
2. 讲目标，不给固定步骤
3. 不限制智能体发挥
4. 必需输出：`progress.md` + `report.md`

## 待办

- [ ] 实现核心模块
- [ ] 添加单元测试

## API 接口

### POST /api/news/trigger

**功能**：手动触发新闻拉取和分析任务

**主要用途**：调试

**说明**：
- API 调用的逻辑与定时任务完全相同，都是调用 `fetch_all_sources(limit)`
- 默认 limit=1，适合调试观察单条新闻的处理流程
- 生产环境不建议使用此接口，应依赖定时任务自动拉取

**请求参数**：
| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| limit | int | 否 | 1 | 全局最多处理多少条新闻，默认 1 用于调试 |

**请求示例**：
```bash
# 调试：只处理 1 条新闻（默认）
curl -X POST http://localhost:8000/api/news/trigger

# 调试：处理 3 条新闻
curl -X POST "http://localhost:8000/api/news/trigger?limit=3"

# 全量：处理所有新新闻
curl -X POST "http://localhost:8000/api/news/trigger?limit=0"
```

**响应示例**：
```json
{
  "success": true,
  "message": "新闻拉取任务已执行",
  "routes_processed": 4,
  "limit": 1
}
```

**处理流程**：
1. 拉取所有 RSS 路由（共 4 个），收集所有未处理新闻
2. 应用全局 limit 限制（默认 1，limit=0 表示全部）
3. **逐个**触发分析任务（等待当前完成再处理下一条）
4. 更新每个路由的状态文件

**注意事项**：
- **主要用途是调试**，观察单条新闻的完整处理流程
- 处理是逐个进行的，不是并发
- limit 是**全局限制**，不是每个路由的限制
  - 例如：limit=3 → 最多处理总共 3 条新闻（所有路由合并后）
  - 例如：limit=0 → 处理所有新新闻
- 即使分析失败也会标记为已处理，避免重复
- 生产环境应依赖定时任务（`config.enabled: true`），而非手动触发
