# OpenClaw Cron 调研

> 更新日期：2026-03-11

---

## 命令概览

```bash
openclaw cron <command>

Commands:
  add       添加定时任务
  list      列出所有任务
  run       立即运行任务（调试）
  runs      查看任务运行历史
  edit      编辑任务（patch 字段）
  rm        删除任务
  enable    启用任务
  disable   禁用任务
  status    查看调度器状态
```

---

## 添加任务（cron add）

### 基本用法

```bash
openclaw cron add [options]
```

### 核心参数

| 参数 | 说明 | 示例 |
|------|------|------|
| `--name <name>` | 任务名称 | `--name "news-analysis"` |
| `--description <text>` | 任务描述 | `--description "分析新闻"` |

### 调度方式（三选一）

| 参数 | 说明 | 示例 |
|------|------|------|
| `--at <when>` | 一次性任务（ISO 时间或 duration） | `--at "2026-03-11T18:00:00"` / `--at "20m"` |
| `--every <duration>` | 间隔任务 | `--every "30m"` / `--every "1h"` |
| `--cron <expr>` | Cron 表达式（5 或 6 字段） | `--cron "0 9 * * 1-5"` |

**duration 格式**：`1m`（1 分钟）、`30s`（30 秒）、`1h`（1 小时）

**注意**：`--at` 使用 duration 时不需要 `+` 前缀（如 `1m` 而非 `+1m`）

**其他调度参数**：
- `--tz <iana>` - 时区（如 `Asia/Shanghai`）
- `--stagger <duration>` - 错峰窗口（如 `30s`、`5m`）
- `--exact` - 禁用错峰（stagger = 0）

### Session 相关（重要）

| 参数 | 说明 | 可选值 |
|------|------|--------|
| `--session <target>` | Session 目标 | `main` / `isolated` |
| `--session-key <key>` | Session 路由键 | `agent:my-agent:my-session` |
| `--agent <id>` | Agent ID | `alpha` / `work` |

**Session 目标说明**：
- `main`：主 session，用于系统事件
- `isolated`：隔离 session，用于独立任务（推荐用于分析任务）

**Session Key 格式**：
```
agent:{agent_id}:{session_label}
```

示例：
```bash
--session-key "agent:alpha:news-analysis-20260311-001"
```

### 任务类型（二选一）

#### 1. System Event（主 session）

```bash
--session main --system-event "text"
```

**用途**：向主 session 注入系统事件

**示例**：
```bash
openclaw cron add \
  --name "daily-report" \
  --session main \
  --system-event "生成每日市场报告" \
  --cron "0 20 * * 1-5"
```

#### 2. Agent Message（isolated session）

```bash
--session isolated --message "text"
```

**用途**：在隔离 session 中运行 agent 任务

**参数**：
- `--message <text>` - Agent 消息内容
- `--model <model>` - 模型覆盖（如 `zai/glm-5`）
- `--thinking <level>` - 思考级别（`off`/`minimal`/`low`/`medium`/`high`）
- `--timeout-seconds <n>` - 超时时间（秒）
- `--expect-final` - 等待最终响应
- `--light-context` - 使用轻量级上下文

**示例**：
```bash
openclaw cron add \
  --name "news-analysis" \
  --session isolated \
  --message "分析以下新闻：标题：{title}，链接：{link}" \
  --at "+5m" \
  --model "zai/glm-5" \
  --thinking "low"
```

### 一次性任务选项

| 参数 | 说明 |
|------|------|
| `--delete-after-run` | 成功后删除任务（默认 false） |
| `--keep-after-run` | 成功后保留任务（默认 false） |

**说明**：默认行为是保留任务

### 消息推送

| 参数 | 说明 | 示例 |
|------|------|------|
| `--announce` | 推送摘要到聊天（isolated session 默认） | `--announce` |
| `--channel <channel>` | 推送渠道 | `wecom` / `telegram` / `discord` |
| `--to <dest>` | 推送目标 | E.164 号码 / Telegram chatId / Discord channel |
| `--best-effort-deliver` | 推送失败不影响任务 | `--best-effort-deliver` |
| `--no-deliver` | 禁用推送 | `--no-deliver` |

**说明**：isolated session 任务默认会推送摘要，除非指定 `--no-deliver`

### 其他参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--disabled` | 创建时禁用 | false |
| `--timeout <ms>` | 超时时间（毫秒） | 30000 |
| `--json` | JSON 格式输出 | false |
| `--token <token>` | Gateway token（如需要） | - |
| `--url <url>` | Gateway WebSocket URL | 从配置读取 |

---

## 常见使用场景

### 1. 一次性分析任务（立即执行）

```bash
openclaw cron add \
  --name "news-analysis-$(date +%s)" \
  --session isolated \
  --message "分析新闻：{title}" \
  --at "1m" \
  --delete-after-run
```

### 2. 定时市场报告

```bash
openclaw cron add \
  --name "daily-report" \
  --session isolated \
  --message "生成每日市场报告" \
  --cron "0 20 * * 1-5" \
  --channel wecom \
  --announce
```

### 3. 间隔任务

```bash
openclaw cron add \
  --name "fetch-news" \
  --session isolated \
  --message "拉取最新新闻" \
  --every "30m" \
  --thinking "minimal"
```

### 4. 主 session 系统事件

```bash
openclaw cron add \
  --name "reminder" \
  --session main \
  --system-event "提醒：检查持仓风险" \
  --at "2026-03-11T18:00:00" \
  --tz "Asia/Shanghai"
```

---

## 任务管理

### 列出任务

```bash
# 列出所有任务
openclaw cron list

# JSON 格式输出
openclaw cron list --json
```

### 运行任务

```bash
# 立即运行（调试）
openclaw cron run <job_id>

# 查看运行历史
openclaw cron runs <job_id>
```

### 编辑任务

```bash
# 修改任务字段
openclaw cron edit <job_id> --message "新消息内容"

# 启用/禁用任务
openclaw cron enable <job_id>
openclaw cron disable <job_id>
```

### 删除任务

```bash
openclaw cron rm <job_id>
```

---

## Session 相关

### Session 目标

| 目标 | 说明 | 用途 |
|------|------|------|
| `main` | 主 session | 系统事件、提醒 |
| `isolated` | 隔离 session | 独立任务、分析任务 |

**推荐**：分析类任务使用 `isolated` session

### Session Key

**格式**：
```
agent:{agent_id}:{session_label}
```

**用途**：
- 路由任务到特定 session
- 追踪任务执行

**示例**：
```bash
--session-key "agent:alpha:news-analysis-20260311-001"
```

### Agent ID

**查看可用 agent**：
```bash
openclaw sessions --agent <id>
```

**默认 agent**：配置文件中的 `agents.defaults.id`

---

## 最佳实践

### 1. 任务命名

使用有意义的名称 + 时间戳：
```bash
--name "news-analysis-$(date +%Y%m%d-%H%M%S)"
```

### 2. 一次性任务

使用 `--delete-after-run` 自动清理：
```bash
--at "+5m" --delete-after-run
```

### 3. 错误处理

使用 `--best-effort-deliver` 避免推送失败影响任务：
```bash
--announce --best-effort-deliver
```

### 4. 超时设置

长时间任务设置超时：
```bash
--timeout-seconds 300  # 5 分钟
```

### 5. 模型选择

简单任务使用轻量模型：
```bash
--model "zai/glm-5" --thinking "low"
```

---

## 任务返回结果

### 添加任务（--json）

```bash
openclaw cron add \
  --name "news-analysis" \
  --session isolated \
  --message "分析新闻" \
  --at "1m" \
  --json
```

**返回结果**：
```json
{
  "id": "job-uuid",
  "name": "news-analysis",
  "status": "scheduled",
  "schedule": {
    "kind": "at",
    "at": "2026-03-11T18:05:00Z"
  },
  "payload": {
    "kind": "agentTurn",
    "message": "分析新闻"
  }
}
```

**关键字段**：
- `id` - 任务 ID（用于后续操作）
- `status` - 任务状态（`scheduled` / `running` / `completed` / `failed`）

### 运行任务（--json）

```bash
openclaw cron run --expect-final --timeout 60000 {job_id} --json
```

**返回结果**：
```json
{
  "status": "ok",
  "runId": "run-uuid",
  "jobId": "job-uuid"
}
```

### 查看运行结果（--json）

```bash
openclaw cron runs --id {job_id} --limit 1 --json
```

**返回结果**：
```json
{
  "sessionId": "session-uuid",
  "sessionKey": "agent:main:cron:{jobId}:run:{sessionId}",
  "status": "ok",
  "summary": "任务执行结果摘要",
  "durationMs": 16676,
  "timestamp": "2026-03-11T18:05:16Z"
}
```

**关键字段**：
- `sessionId` - Session ID（用于查询历史）
- `sessionKey` - Session Key（格式：`agent:{agent_id}:cron:{jobId}:run:{sessionId}`）
- `status` - 执行状态（`ok` / `failed` / `timeout`）
- `summary` - 执行结果摘要
- `durationMs` - 执行时长（毫秒）

### 查询 Session 历史

```bash
openclaw sessions history --session-key "{sessionKey}"
```

**用途**：查看完整的对话历史和执行细节

---

## 调试

### 查看任务状态

```bash
openclaw cron status
```

### 查看运行历史

```bash
openclaw cron runs <job_id>
```

### 立即运行

```bash
openclaw cron run <job_id>
```

### JSON 输出

```bash
openclaw cron list --json
openclaw cron runs <job_id> --json
```

---

## 参考链接

- [OpenClaw Cron 文档](https://docs.openclaw.ai/cli/cron)
- [OpenClaw Sessions 文档](https://docs.openclaw.ai/cli/sessions)
