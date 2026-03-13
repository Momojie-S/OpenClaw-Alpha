# OpenClaw 工具模块

> 更新日期：2026-03-12

OpenClaw 框架相关的 Python 工具模块。

---

## 位置

`src/openclaw_alpha/openclaw/`

---

## 模块列表

### path_utils - 路径工具

**位置**：`openclaw/path_utils.py`

#### 核心函数

| 函数 | 说明 | 返回值示例 |
|------|------|-----------|
| `get_openclaw_home()` | OpenClaw 主目录 | `~/.openclaw` |
| `get_openclaw_agents_dir()` | agents 目录 | `~/.openclaw/agents` |
| `get_openclaw_agent_dir(agent_id)` | 指定 agent 目录 | `~/.openclaw/agents/alpha` |
| `get_openclaw_sessions_dir(agent_id)` | 指定 agent 的 sessions 目录 | `~/.openclaw/agents/alpha/sessions` |
| `get_openclaw_session_file(agent_id, session_id)` | session 上下文文件 | `~/.openclaw/agents/alpha/sessions/{uuid}.jsonl` |
| `parse_agent_id_from_session_key(session_key)` | 从 sessionKey 解析 agent_id | `"alpha"` |

#### 使用示例

```python
from openclaw_alpha.openclaw import (
    get_openclaw_session_file,
    parse_agent_id_from_session_key,
)

# 从 sessionKey 解析 agent_id
session_key = "agent:alpha:cron:job-123:run:session-uuid"
agent_id = parse_agent_id_from_session_key(session_key)
# -> "alpha"

# 获取 session 上下文文件路径
session_id = "fab6e5fa-d029-4c68-9aa2-28eed6497ab2"
context_path = get_openclaw_session_file(agent_id, session_id)
# -> /home/user/.openclaw/agents/alpha/sessions/fab6e5fa-d029-4c68-9aa2-28eed6497ab2.jsonl
```

---

### cron_utils - Cron 工具

**位置**：`openclaw/cron_utils.py`

#### 核心函数

| 函数 | 说明 |
|------|------|
| `submit_cron_task(message, name, ...)` | 提交 OpenClaw cron 任务（同步等待完成） |
| `parse_cron_result(data)` | 解析 `openclaw cron add --expect-final` 的返回结果 |

#### CronResult 数据类

| 字段 | 类型 | 说明 |
|------|------|------|
| `job_id` | `str` | 任务 ID |
| `session_id` | `str \| None` | Session UUID |
| `session_key` | `str \| None` | Session Key |
| `agent_id` | `str` | Agent ID |
| `context_path` | `str \| None` | Session 上下文文件路径 |
| `success` | `bool` | 是否成功 |
| `error` | `str \| None` | 错误信息（如有） |

#### submit_cron_task 参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `message` | `str` | 必需 | 任务消息 |
| `name` | `str \| None` | `task-{timestamp}` | 任务名称 |
| `timeout_seconds` | `int` | `300` | 超时时间（秒） |
| `delete_after_run` | `bool` | `True` | 运行后删除任务 |
| `thinking` | `str` | `"low"` | 思考级别 |
| `agent_id` | `str` | `"alpha"` | Agent ID |

#### 使用示例

```python
from openclaw_alpha.openclaw import submit_cron_task

# 提交任务（同步等待完成）
result = submit_cron_task(
    message="分析新闻：XXX",
    name="news-analysis",
    timeout_seconds=300
)

if result.success:
    print(f"任务完成: {result.job_id}")
    print(f"上下文路径: {result.context_path}")
else:
    print(f"任务失败: {result.error}")
```

#### 底层命令

`submit_cron_task` 封装了以下命令：

```bash
openclaw cron add \
  --name "{name}" \
  --session isolated \
  --message "{message}" \
  --expect-final \
  --timeout-seconds {timeout_seconds} \
  --delete-after-run \
  --thinking {thinking} \
  --json
```

---

## 设计原则

1. **统一管理**：所有 OpenClaw 框架相关的工具集中在此包
2. **避免硬编码**：路径规则、解析逻辑集中维护
3. **类型安全**：使用 dataclass 和类型提示
