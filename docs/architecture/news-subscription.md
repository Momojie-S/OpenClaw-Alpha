# 新闻订阅分析功能设计

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
~/.openclaw_alpha/
├── config/
│   └── news.yaml              # 新闻模块配置
├── cache/
│   └── news/
│       └── rsshub/
│           └── {route_id}/
│               └── {YYYY-MM-DD}.json  # 新闻状态记录
└── logs/

src/openclaw_alpha/backend/news/
├── __init__.py
├── jobs.py                # 定时任务：拉取 + 触发分析
├── rss_fetcher.py         # RSS 拉取逻辑
├── state_manager.py       # 状态文件管理
├── task_executor.py       # 调用 openclaw cron
├── config.py              # 配置模型
└── models.py              # 数据模型
```

## 配置文件

**路径**：`~/.openclaw_alpha/config/news.yaml`

```yaml
enabled: true
interval_minutes: 30  # 拉取间隔（分钟）
```

**RSS 源**：硬编码在代码中（`src/openclaw_alpha/backend/news/config.py`）

**RSSHub 实例**：
- 自动尝试多个实例
- 按优先级排序
- 失败自动切换

**RSS 路由**（按优先级）：
1. `/cls/telegraph` - 财联社电报快讯
2. `/jin10` - 金十数据快讯
3. `/wallstreetcn/news` - 华尔街见闻资讯
4. `/yicai/brief` - 第一财经简报

## 状态文件

**路径**：`~/.openclaw_alpha/cache/news/rsshub/{route_id}/{YYYY-MM-DD}.json`

**route_id 定义**：从 RSSHub URL 中提取的路径第一段

| URL 示例 | route_id |
|---------|----------|
| `https://rsshub.app/36kr/newsflashes` | `36kr` |
| `https://rsshub.app/cls/telegraph` | `cls` |
| `https://rsshub.app/eastmoney/report` | `eastmoney` |

**提取规则**：取 URL path 的第一个非空段（去除域名后的第一部分）

**字段**：
- `date` - 日期
- `route` - 路由标识
- `items` - 新闻列表，每条包含：
  - `id` - 唯一标识（从 RSS item 提取或 link hash）
  - `title` - 标题
  - `link` - 链接
  - `published` - 发布时间
  - `processed` - 是否已处理
  - `processed_at` - 处理时间
  - `job_id` - 分析任务 ID
  - `workspace_dir` - 工作目录路径

**按天分文件**，便于管理和清理。

## 任务模板设计

### quick-news-analysis.md 用途

**文件路径**：`skills/news_driven_investment/tasks/quick-news-analysis.md`

**用途**：指示智能体如何分析新闻，是完整任务消息的一部分。

**消息结构**：
```
[任务模板 - quick-news-analysis.md]
    ↓
---
    ↓
## 本次任务参数（Python 生成）
- 任务目录
- 新闻标题
- 新闻链接
    ↓
---
    ↓
## 新闻内容（Python 生成）
[新闻正文/摘要]
```

### 编写原则

**1. 专注指令，不介绍拼接内容**
- ❌ 不写："保证消息中包含新闻内容"
- ❌ 不写："说明：summary 字段取决于数据源"
- ✅ 只写：智能体要做什么

**2. 讲目标，不给固定步骤**
- ❌ 不写：详细的检查清单
- ✅ 写：期望的输出和目标

**3. 不限制发挥**
- ❌ 不写：固定的分析维度
- ✅ 写：核心目标，让智能体自主发挥

**4. 必需的输出要求**
- 创建 `progress.md` 记录进度
- 创建 `report.md` 输出报告

### 模板结构

```markdown
# 任务名称

**目标**：一句话描述任务目标

---

## 输出要求

- 任务目录：{task_dir}
- 进度文件：{task_dir}/progress.md
- 报告文件：{task_dir}/report.md

---

## 报告格式

（期望的报告结构，不强制字段）
```

**注意**：
- 不需要"输入参数"说明（Python 会生成）
- 不需要"保证"、"说明"等描述性内容
- 不需要示例（限制智能体发挥）

## 定时任务

**调度方式**：APScheduler

**任务逻辑**：
1. 遍历 `rss_sources` 列表（按优先级顺序）
2. 拉取 RSS 内容
3. 加载今日状态文件
4. 过滤未处理的新闻
5. 触发分析（调用 `openclaw cron`）
6. 更新状态文件

**任务注册**：
- 单一定时任务，统一拉取所有源
- 间隔可配置（`interval_minutes`）

## 分析任务执行

**触发方式**：`openclaw cron add --session isolated`

**执行者**：OpenClaw 智能体（isolated session）

**实现模块**：`src/openclaw_alpha/backend/news/task_executor.py`

### 触发流程

```
发现新新闻
    ↓
构造分析任务
    ↓
调用 openclaw cron add
    ↓
返回 job_id
    ↓
更新状态文件（标记已处理）
```

### task_executor.py 职责

**主要功能**：
1. 构造 `openclaw cron add` 命令
2. 执行命令并捕获输出
3. 解析返回的 job_id
4. 提供任务模板

**输入**：
- `title` - 新闻标题
- `link` - 新闻链接
- `summary` - 新闻内容（可选）

**输出**：
- `job_id` - 任务 ID
- `command` - 执行的命令（用于调试）

### 命令模板

```bash
# 1. 添加任务
openclaw cron add \
  --name "news-analysis-{timestamp}" \
  --session isolated \
  --message "分析以下新闻：

标题：{title}
链接：{link}

要求：
1. 判断新闻对市场的影响（利好/利空/中性）
2. 识别相关的板块和股票
3. 评估影响程度和时效性" \
  --at "1m" \
  --delete-after-run \
  --thinking "low" \
  --timeout-seconds 120 \
  --json
```

**注意**：`--at` 格式为 `1m`（1 分钟后），不是 `+1m`

### 返回结果解析

**添加任务返回**：
```json
{
  "id": "job-uuid",
  "name": "news-analysis-1234567890",
  "status": "scheduled"
}
```

**关键字段**：
- `id` - 任务 ID（用于状态更新）

### task_executor.py 实现

**路径工具**：使用 `openclaw_alpha.core.path_utils` 统一管理路径

**详细文档**：[核心工具模块 - path_utils](core-utilities.md#path_utils---路径管理工具)

**主要功能**：
1. 使用 `get_news_analysis_task_dir()` 创建工作目录
2. 使用 `get_task_template_path()` 加载任务模板
3. 构造完整的任务消息（模板 + 参数）
4. 调用 `openclaw cron add` 提交任务
5. 返回 `(job_id, workspace_dir)`

**路径工具函数**：
```python
from openclaw_alpha.core.path_utils import (
    get_project_root,              # 项目根目录
    get_config_dir,                # ~/.openclaw_alpha
    get_cache_dir,                 # ~/.openclaw_alpha/cache
    get_news_analysis_task_dir,   # 新闻分析工作目录
    get_task_template_path,        # 任务模板路径
    ensure_dir,                    # 确保目录存在
)

# 示例
workspace_dir = get_news_analysis_task_dir("2026-03-11", "abc123")
# -> ~/workspace/news_analysis/2026-03-11/abc123/

template_path = get_task_template_path("news_driven_investment", "quick-news-analysis")
# -> {project_root}/skills/news_driven_investment/tasks/quick-news-analysis.md
```

**输入**：
- `title` - 新闻标题
- `link` - 新闻链接
- `summary` - 新闻内容（可选）

**输出**：
- `job_id` - 任务 ID（成功时）
- `workspace_dir` - 工作目录（成功时）
- `error` - 错误信息（失败时）

**工作目录命名**：`workspace/news_analysis/{date}/{news_id}/`
- `date` - 当天日期（YYYY-MM-DD）
- `news_id` - 新闻 ID（MD5(link)[:8]）

**工作目录结构**：
```
{workspace_dir}/
├── progress.md    # 任务进度
└── report.md      # 分析报告
```

**流程**：
```python
def submit_analysis(title: str, link: str, summary: str | None = None) -> tuple[str | None, str | None]:
    """
    提交新闻分析任务

    Returns:
        (job_id, workspace_dir) 成功时
        (None, None) 失败时
    """
    # 1. 创建工作目录
    date_str = datetime.now().strftime("%Y-%m-%d")
    news_id = generate_news_id(link)
    workspace_dir = get_news_analysis_task_dir(date_str, news_id)
    ensure_dir(workspace_dir)

    # 2. 构造任务消息（模板 + 参数）
    message = build_message(str(workspace_dir), title, link)

    # 3. 提交任务
    cmd = [
        "openclaw", "cron", "add",
        "--name", f"news-analysis-{int(time.time())}",
        "--session", "isolated",
        "--message", message,
        "--at", "1m",
        "--delete-after-run",
        "--thinking", "low",
        "--timeout-seconds", "120",
        "--json"
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        logger.error(f"添加任务失败: {result.stderr}")
        return (None, None)

    # 4. 解析返回
    data = json.loads(result.stdout)
    job_id = data["id"]
    return (job_id, str(workspace_dir))
```

**build_message() 实现**：
```python
def build_message(
    workspace_dir: str, title: str, link: str, content: str | None = None
) -> str:
    """构造分析任务消息（模板 + 参数 + 内容）"""
    template = load_task_template()

    message = f"""{template}

---

## 本次任务参数

- **工作目录**：{workspace_dir}
- **新闻标题**：{title}
- **新闻链接**：{link}
"""

    # 添加新闻内容（如果有）
    if content:
        message += f"""
---

## 新闻内容

{content}
"""

    return message
```

**submit_analysis() 实现**：
```python
def submit_analysis(
    title: str,
    link: str,
    summary: str | None = None,
) -> tuple[str | None, str | None]:
    """提交新闻分析任务"""
    # 1. 创建工作目录
    date_str = datetime.now().strftime("%Y-%m-%d")
    news_id = generate_news_id(link)
    workspace_dir = get_news_analysis_task_dir(date_str, news_id)
    ensure_dir(workspace_dir)

    # 2. 构造任务消息（包含摘要，减少 agent 获取新闻的调用）
    message = build_message(str(workspace_dir), title, link, summary)

    # 3. 提交任务
    cmd = [
        "openclaw", "cron", "add",
        "--name", f"news-analysis-{int(time.time())}",
        "--session", "isolated",
        "--message", message,
        "--at", "1m",
        "--delete-after-run",
        "--thinking", "low",
        "--timeout-seconds", "120",
        "--json"
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        logger.error(f"添加任务失败: {result.stderr}")
        return (None, None)

    # 4. 解析返回
    data = json.loads(result.stdout)
    job_id = data["id"]
    return (job_id, str(workspace_dir))
```

**优点**：
- ✅ 模板 + 参数 + 内容一次性传入，减少 agent 文件读取和新闻获取
- ✅ 如果提供了 summary，agent 无需再调用 web_fetch
- ✅ 消息长度测试：支持至少 100KB，新闻内容通常 < 10KB，完全够用
- ✅ 统一使用路径工具，避免硬编码

**错误处理**：
- 命令执行失败：记录日志，返回 `None`，**不标记已处理**
- JSON 解析失败：记录日志，返回 `None`，**不标记已处理**
- 返回 `None` 时，下次拉取会重试

### 参数说明

| 参数 | 值 | 说明 |
|------|---|------|
| `--name` | `news-analysis-{timestamp}` | 任务名称（包含时间戳） |
| `--session` | `isolated` | 使用隔离 session |
| `--message` | 分析任务描述 | 包含新闻标题、链接、要求 |
| `--at` | `1m` | 1 分钟后执行（避免立即执行） |
| `--delete-after-run` | - | 成功后自动删除 |
| `--thinking` | `low` | 低思考级别（节省成本） |
| `--timeout-seconds` | `120` | 2 分钟超时 |
| `--json` | - | JSON 格式输出（便于解析） |

### jobs.py 集成

在发现新新闻后调用 `submit_analysis()`：

```python
# jobs.py

from .task_executor import submit_analysis

async def fetch_and_process(route: str) -> None:
    # ... 拉取 RSS + 过滤新新闻 ...

    # 处理新新闻
    for item in new_items:
        # 提交分析任务
        job_id, workspace_dir = submit_analysis(
            title=item.title,
            link=item.link,
            summary=item.summary
        )

        if job_id:
            # 标记已处理，记录 job_id 和 workspace_dir
            mark_processed(state, item, job_id, workspace_dir)
            logger.info(f"新新闻已提交分析: {item.title} -> {workspace_dir}")
        else:
            # 失败，不标记已处理，下次重试
            logger.error(f"提交分析失败: {item.title}")
```

**状态文件更新**：
```json
{
  "id": "news-abc123",
  "title": "...",
  "processed": true,
  "processed_at": "2026-03-11T18:30:00",
  "job_id": "job-uuid",
  "workspace_dir": ".openclaw_alpha/news_analysis/2026-03-11/news-abc123/"
}
```

**详细文档**：[OpenClaw Cron 调研](../openclaw/cron.md)

## 错误处理

| 错误类型 | 处理方式 |
|---------|---------|
| RSS 拉取失败 | 记录日志，跳过该源，继续下一个 |
| 状态文件损坏 | 备份后重建，可能重复处理 |
| 分析任务失败 | 标记未处理，下次重试 |

## 清理策略

- **状态文件**：保留最近 7 天
- **清理任务**：每日凌晨自动清理过期文件

## 日志

使用统一日志模块，输出到 `~/.openclaw_alpha/logs/news.log`

## 待办

- [ ] 实现核心模块
- [ ] 添加单元测试

## 新闻分析任务流程

**任务流程文档**：`skills/news_driven_investment/tasks/quick-news-analysis.md`

### 分析目标

从投资角度快速评估新闻价值：
- 识别相关股票和板块
- 判断影响方向（利好/利空）
- 评估重要程度

### 触发方式

通过 `openclaw cron add` 创建 isolated session，传递任务描述：

```bash
openclaw cron add \
  --name "news-analysis-{timestamp}" \
  --session isolated \
  --message "阅读 skills/news_driven_investment/tasks/quick-news-analysis.md，按文档执行分析任务。

工作目录：{workspace_dir}
新闻标题：{title}
新闻链接：{link}" \
  --at "1m" \
  --delete-after-run \
  --thinking "low" \
  --timeout-seconds 120 \
  --json
```

**输入参数**：
- `工作目录` - 本次任务的专用目录（如 `.openclaw_alpha/news_analysis/2026-03-11/news-abc123/`）
- `新闻标题` - 新闻标题
- `新闻链接` - 新闻链接

### 执行流程

| Step | 内容 | 输出 |
|------|------|------|
| 1. 获取新闻内容 | web_fetch 获取正文 | 新闻正文 |
| 2. 分析新闻 | 提取股票、板块、影响 | 分析结论 |
| 3. 生成报告 | Markdown 格式 | 报告文件 |

### 输出路径

`.openclaw_alpha/news_analysis/{date}/{news_id}.md`

### 报告结构

```markdown
# {新闻标题}

## 基本信息
- 事件类型、影响方向、重要程度等

## 相关标的
- 股票代码、板块名称

## 核心内容
- 新闻要点

## 投资视角
- 从投资角度的简要分析
```
