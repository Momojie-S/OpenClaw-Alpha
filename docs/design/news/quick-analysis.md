# 快速分析设计（简化版）

## 概述

快速分析是新闻分析系统的第一层，由 Backend 定时触发，对每条新闻进行快速分析，判断是否值得深入分析。

---

## 功能流程

```
┌─────────────────────────────────────────────────────────────┐
│                   Backend Cron 定时任务                      │
│                  (每30分钟自动执行)                           │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
    RSSHub 拉取新闻
    (按优先级: cls > jin10 > wallstreetcn)
         │
         ▼
    对比已处理记录
    (cache/rsshub/{route_id}/{date}.json)
         │
         ▼
    过滤未处理新闻
    (只处理今天发布的新闻)
         │
         ▼
    ┌─────────────────┐
    │ 逐个触发分析     │
    │ Agent Session   │
    └────────┬────────┘
             │
             ▼
    ┌─────────────────┐
    │ Agent 输出:     │
    │ analysis.json   │  ← 快速分析结果
    └────────┬────────┘
             │
             ▼
    ┌─────────────────┐
    │ Backend 读取:   │
    │ worth_deep_     │
    │ analysis 字段   │
    └────────┬────────┘
             │
             ├─ Yes ──→ 触发深度分析
             │
             └─ No ───→ 更新热度榜单
```

---

## 目录结构

### Backend 代码

```
src/openclaw_alpha/backend/news/
├── quick/                      # 快速分析模块
│   ├── jobs.py                 # 定时任务：拉取 + 触发分析
│   ├── rss_fetcher.py          # RSS 拉取逻辑
│   ├── state_manager.py        # 状态文件管理
│   ├── task_executor.py        # 触发 Agent Session
│   ├── deep_trigger.py         # 深度分析触发逻辑
│   ├── config.py               # 配置模型
│   └── models.py               # 数据模型
└── deep/                       # 深度分析模块（待实现）
    └── ...
```

### 工作目录

```
{project_root}/workspace/
├── news/                       # 新闻模块工作目录
│   ├── quick/                  # 快速分析
│   │   ├── config.yaml         # 配置文件
│   │   ├── tasks/              # 任务目录
│   │   │   └── {YYYY-MM-DD}/   # 按日期组织
│   │   │       └── {news_id}/  # 任务目录
│   │   │           ├── progress.md     # 任务进度
│   │   │           ├── analysis.json   # 分析结果
│   │   │           └── report.md       # 分析报告（可选）
│   │   └── cache/              # 缓存目录
│   │       └── rsshub/
│   │           └── {route_id}/
│   │               └── {YYYY-MM-DD}.json  # 新闻状态记录
│   └── deep/                   # 深度分析（待实现）
└── logs/
```

---

## 配置

**路径**：`workspace/news/quick/config.yaml`

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
  session_poll_timeout_seconds: 300
  report_wait_timeout_seconds: 300
```

**RSS 源**（硬编码，按优先级）：
1. `/cls/telegraph` - 财联社电报快讯
2. `/jin10` - 金十数据快讯
3. `/wallstreetcn/news` - 华尔街见闻资讯

---

## 状态管理

### 状态文件

**路径**：`workspace/news/quick/cache/rsshub/{route_id}/{YYYY-MM-DD}.json`

**作用**：记录哪些新闻已经被处理，避免重复分析

**结构**：
```json
{
  "date": "2026-03-14",
  "route_id": "cls",
  "items": [
    {
      "id": "news_id_123",
      "title": "新闻标题",
      "link": "https://...",
      "published": "2026-03-14T09:34:38+00:00",
      "processed": true,
      "processed_at": "2026-03-14T10:00:00+08:00",
      "job_id": "cron_job_id",
      "task_dir": "/path/to/task/dir"
    }
  ]
}
```

### 清理策略

- 保留 7 天
- 每日凌晨自动清理
- 清理函数：`cleanup_old_states(keep_days=7)`

---

## 定时任务逻辑

### jobs.py 核心流程

```python
async def fetch_and_analyze():
    """定时任务：拉取新闻并触发分析"""
    # 1. 遍历 RSS 源（按优先级）
    for route in RSS_ROUTES:
        # 2. 拉取 RSS 内容
        items = fetch_rss(route)
        
        # 3. 过滤出今天发布的新闻
        today_items = filter_today_items(items)
        
        # 4. 加载今日状态文件
        state = load_state(route, today)
        
        # 5. 过滤未处理的新闻
        unprocessed = filter_unprocessed(state, today_items)
        
        # 6. 应用 limit 限制（如果指定）
        if limit > 0:
            unprocessed = unprocessed[:limit]
        
        # 7. 逐个触发分析（非并发）
        for item in unprocessed:
            job_id, task_dir = await submit_analysis(item)
            
            # 8. 更新状态文件
            if job_id:
                mark_processed(state, item, job_id, task_dir)
```

### "今天"的定义

- 使用 `date.today()` 获取当前日期（服务器本地时区 Asia/Shanghai）
- 比较新闻的 `published` 字段：`item.published.date() == today`
- 状态文件路径：`cache/rsshub/{route_id}/{YYYY-MM-DD}.json`

### 处理方式

- **逐个处理**（非并发）
- 确保资源消耗可控
- 避免并发冲突
- 等待当前分析完成后才处理下一条

---

## 任务执行

### 触发方式

Backend 调用 `openclaw cron add --session isolated` 触发 Agent Session

### submit_analysis 函数

**职责**：提交单条新闻的分析任务

**流程**：
1. 创建工作目录：`workspace/news/quick/tasks/{date}/{news_id}/`
2. 构造任务消息（任务模板 + 参数 + 新闻内容）
3. 提交 cron 任务（异步）
4. 轮询 session store 获取 session 信息（超时 300 秒）
5. 等待 analysis.json 创建（超时 300 秒）
6. 读取 `worth_deep_analysis` 字段，判断是否触发深度分析
7. 如果存在 report.md，追加系统运行信息（包括 session 上下文路径）
8. 返回 `(job_id, task_dir)`

**追加系统运行信息**：
- Job ID
- Session ID
- Session 文件（原始路径）
- Session 备份路径（删除后，用于回溯）
- 实现函数：`append_system_info(task_dir, job_id, session_id, context_path, context_path_deleted)`
- 仅在 report.md 存在时追加

**与旧版代码的差异**：
- 旧版：等待 report.md 创建，必须存在
- 新版：等待 analysis.json 创建，report.md 可选
- 原因：新版设计要求输出结构化 JSON（analysis.json），report.md 仅作为可选的详细说明

### 任务模板

**文件**：`skills/news_driven_investment/tasks/quick-news-analysis.md`

**作用**：指导智能体如何分析新闻

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

### cron 参数

| 参数 | 值 | 说明 |
|------|---|------|
| `--session` | `isolated` | 使用隔离 session |
| `--at` | `now` | 立即触发 |
| `--delete-after-run` | - | **不使用**（保留 session 用于追溯） |
| `--thinking` | `low` | 降低推理消耗 |
| `--timeout-seconds` | `300`（5 分钟） | 任务超时时间 |
| `--announce` | 启用推送 | 推送结果到配置的渠道 |
| `--channel` | 从配置读取 | 推送渠道（wecom） |
| `--to` | 从配置读取 | 推送目标（Momojie） |

---

## 错误处理

| 错误类型 | 处理方式 |
|---------|---------|
| RSS 拉取失败 | 跳过该源，继续下一个 |
| 状态文件损坏 | 备份后重建 |
| 分析任务失败 | 不标记，下次重试 |
| analysis.json 不存在 | 不触发深度分析，记录警告 |
| worth_deep_analysis 字段缺失 | 默认 false，不触发深度分析 |

---

## 清理策略

**状态文件**：
- 保留 7 天
- 每日凌晨自动清理
- 清理函数：`cleanup_old_states(keep_days=7)`

**清理逻辑**：
- 遍历 `cache/rsshub/{route_id}/` 下的所有状态文件
- 从文件名解析日期（`{YYYY-MM-DD}.json`）
- 删除超过 7 天的文件

---

## 深度分析触发

Backend 读取 `analysis.json`，根据 `worth_deep_analysis` 字段决定是否触发深度分析：

```python
# 在 submit_analysis 函数中
analysis_json_path = os.path.join(task_dir, "analysis.json")

if os.path.exists(analysis_json_path):
    with open(analysis_json_path) as f:
        analysis = json.load(f)
    
    if analysis.get("worth_deep_analysis", False):
        # 触发深度分析
        trigger_deep_analysis(analysis, task_dir)
    else:
        # 仅更新热度榜单
        update_hotness_ranking(analysis)
```

**深度分析设计**：详见 [deep-analysis.md](deep-analysis.md)

---

## API 接口

### POST /api/news/quick/trigger

**功能**：手动触发快速新闻分析任务

**主要用途**：调试

**请求参数**：
| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| limit | int | 否 | 1 | 全局最多处理多少条新闻，默认 1 用于调试 |

**请求示例**：
```bash
# 调试：只处理 1 条新闻（默认）
curl -X POST http://localhost:8000/api/news/quick/trigger

# 调试：处理 3 条新闻
curl -X POST "http://localhost:8000/api/news/quick/trigger?limit=3"

# 全量：处理所有新新闻
curl -X POST "http://localhost:8000/api/news/quick/trigger?limit=0"
```

**响应示例**：
```json
{
  "success": true,
  "message": "快速新闻分析任务已执行",
  "routes_processed": 3,
  "total_news": 10,
  "processed": 3,
  "triggered_deep_analysis": 1
}
```

**处理流程**：
1. 拉取所有 RSS 路由（共 3 个），收集所有未处理新闻
2. 应用全局 limit 限制（默认 1，limit=0 表示全部）
3. 逐个触发快速分析任务
4. 读取 analysis.json，判断是否触发深度分析
5. 更新状态文件

**注意事项**：
- 主要用途是调试，观察单条新闻的完整处理流程
- 处理是逐个进行的，不是并发
- limit 是全局限制，不是每个路由的限制
- 只触发快速分析，深度分析由 Backend 自动判断是否触发

**深度分析 API**：详见 [deep-analysis.md](deep-analysis.md)

---

## 设计原则

1. **不限制取值**：不预设固定的事件类型、影响范围、确定性等字段取值
2. **流程引导**：引导智能体分析关键要素（板块、公司、影响程度）
3. **自主判断**：让智能体自己决定是否值得深入分析
4. **完整识别**：包括未上市公司的识别

---

## 输入

| 字段 | 类型 | 说明 |
|------|------|------|
| `task_dir` | string | 任务目录路径 |
| `title` | string | 新闻标题 |
| `link` | string | 新闻链接 |
| `content` | string | 新闻正文 |

---

## 输出结构

### 简单版

```json
{
  "related_sectors": ["板块1", "板块2"],
  "related_companies": [
    {
      "name": "比亚迪",
      "listed": true,
      "code": "002594"
    },
    {
      "name": "某未上市公司",
      "listed": false,
      "code": null
    }
  ],
  "impact_assessment": "自然语言描述：这件事对板块/公司有什么影响，影响程度如何",
  "worth_deep_analysis": true,
  "reason": "理由：为什么值得/不值得深入分析"
}
```

---

## 分析流程

智能体的分析流程详见任务模板：[quick-news-analysis.md](../../../skills/news_driven_investment/tasks/quick-news-analysis.md)

**核心要点**：
1. **相关板块**：哪些板块会受到影响？
2. **相关公司**：哪些公司会受到影响？（包括未上市）
3. **影响程度**：影响有多大？是正面还是负面？
4. **是否值得深入分析**：基于以上分析，判断是否需要深入

**重要**：执行分析的智能体拥有所有 `openclaw_alpha_*` skill 的能力，可以随时调用相关技能获取数据（如板块热度、资金流向等）。

---

## 输出示例

### 央行降准

**新闻**：央行宣布降准0.5个百分点，释放长期资金约1万亿元。此次降准旨在支持实体经济发展，降低银行资金成本。市场普遍认为此举将利好银行、地产等板块。

**输出**：
```json
{
  "related_sectors": ["银行", "地产", "券商", "基建", "消费"],
  "related_companies": [
    {"name": "工商银行", "listed": true, "code": "601398"},
    {"name": "中国平安", "listed": true, "code": "601318"},
    {"name": "万科A", "listed": true, "code": "000002"},
    {"name": "中信证券", "listed": true, "code": "600030"}
  ],
  "impact_assessment": "央行降准0.5个百分点，释放1万亿资金，将显著降低银行资金成本，提振市场信心。银行、地产、券商板块直接受益，基建、消费板块间接受益。影响强度为强烈正面，影响时效为中期。",
  "worth_deep_analysis": true,
  "reason": "影响全市场，涉及银行、地产、券商等多个重要板块，且有明确的投资机会和风险需要提示"
}
```

---

## Backend 处理逻辑

Backend Python 代码读取 `analysis.json`，根据 `worth_deep_analysis` 字段决定是否触发深度分析：

```python
if analysis["worth_deep_analysis"]:
    # 触发深度分析
    trigger_deep_analysis(analysis)
else:
    # 仅更新热度榜单
    update_hotness_ranking(analysis)
```

---

## Prompt 设计要点

1. **自由分析**：不限制字段取值，让智能体自由分析
2. **流程引导**：引导智能体按"板块 → 公司 → 影响 → 判断"的流程分析
3. **公司识别**：强调需要识别所有相关公司，包括未上市公司
4. **自然语言**：`impact_assessment` 和 `reason` 使用自然语言，不限制格式
5. **自主判断**：让智能体自己决定是否值得深入分析，不预设规则
6. **不列举可用 skill**：智能体已加载所有 `openclaw_alpha_*` skill，不需要在任务模板中列举可调用的 skill，由智能体自主决定是否调用
7. **不包含 Backend 逻辑**：任务模板只用于指引智能体完成分析，不包含任何与 Python 代码实现相关的内容（如追加系统信息等）

---

## 任务输出文件

### 1. progress.md

```markdown
# 任务进度

- [x] 读取新闻内容
- [ ] 分析相关板块
- [ ] 识别相关公司（包括未上市）
- [ ] 评估影响程度
- [ ] 判断是否值得深入分析
- [ ] 输出分析结果
```

### 2. analysis.json

```json
{
  "related_sectors": [...],
  "related_companies": [...],
  "impact_assessment": "...",
  "worth_deep_analysis": true/false,
  "reason": "..."
}
```

### 3. report.md（可选）

简要分析报告（如果需要更多说明）。

**重要**：任务完成后，Backend 会自动追加系统运行信息到 report.md，包括：
- Job ID
- Session ID
- Session 文件（原始路径）
- Session 备份路径（删除后，用于回溯）

这些信息用于复盘时查找 session 上下文。

---

## 优势

1. **灵活**：不限制字段取值，智能体可以自由发挥
2. **简单**：输出结构简单，只有5个字段
3. **完整**：包括未上市公司的识别
4. **可解释**：`reason` 字段让用户理解为什么值得/不值得深入分析
5. **易调整**：智能体可以根据实际情况调整判断标准

---

## 待办

- [x] 修改 task_executor.py：从等待 report.md 改为等待 analysis.json
- [x] 修改 task_executor.py：从 analysis.json 读取 worth_deep_analysis 字段
- [x] 修改 task_executor.py：仅在 report.md 存在时追加系统信息
- [x] 修改 jobs.py：处理新的返回值（包含 worth_deep_analysis）
- [ ] 实现 `trigger_deep_analysis` 函数（深度分析模块）
- [ ] 实现 `update_hotness_ranking` 函数
- [ ] 添加单元测试
- [ ] 测试真实新闻的分析效果

---

## 相关文档

- [overview.md](overview.md) - 新闻分析系统整体设计
- [../architecture/news-subscription.md](../architecture/news-subscription.md) - 新闻订阅功能技术架构
- [deep-analysis.md](deep-analysis.md) - 深度分析设计
- [hotness-ranking.md](hotness-ranking.md) - 热度榜单设计（待编写）
- [../../../skills/news_driven_investment/tasks/quick-news-analysis.md](../../../skills/news_driven_investment/tasks/quick-news-analysis.md) - 快速分析任务模板
