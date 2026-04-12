# 用户反馈处理系统设计

## 概述

用户反馈处理系统由 Backend 定时扫描 `feedback/` 目录，逐个触发 Agent Session 处理反馈。

**核心设计**：
- 每个反馈一个独立的 JSON 文件（用户直接提交）
- 全生命周期（提交 → 处理 → 结果）记录在同一文件
- 状态变化通过添加字段实现

---

## 模块定位

| 模块 | 职责 |
|------|------|
| **openclaw_alpha_feedback** | 收集用户反馈，保存到 JSON 文件（见 [skill-design.md](./skill-design.md)） |
| **Backend** | 扫描反馈目录、拼接任务消息、触发 Agent Session、提取结果、更新 JSON 文件、归档 |
| **feedback-workflow.md** | 智能体处理反馈的流程指引，不包含实现细节 |
| **智能体** | 拥有所有 `openclaw_alpha_xxx` skill，知悉 Alpha 项目规范文档，按流程处理反馈并输出结果 |

---

## 处理用户反馈流程的定位

**核心功能**：调研和思考，而非直接实现。

处理用户反馈的目的是：
1. 理解用户的真实需求
2. 评估技术可行性和是否符合项目规范
3. 做出处理决策
4. 如果需要修改，输出下一步行动建议

**不负责**：
- 直接修改 skill 或代码
- 立即实现功能

**后续行动**：
- 如果反馈被采纳且需要开发工作，由智能体输出 `next_steps` 中建议后续开发方向。

---

## 目录结构

```
{project_root}/
└── runtime/
    └── feedback/
        ├── config.yaml           # 配置
        ├── new/                  # 待处理反馈
        │   └── {YYYY-MM-DD}-{hash}.json
        ├── done/                 # 已处理反馈（归档）
        │   └── {YYYY-MM-DD}-{hash}.json
        └── tasks/                # 任务目录
            └── {YYYY-MM-DD}/
                └── {feedback_id}/
                    └── progress.md    # 处理进度
```

### Backend 代码

```
src/openclaw_alpha/backend/feedback/
├── __init__.py
├── config.py              # 配置模型
├── jobs.py                # 定时任务：扫描 pending 反馈
├── models.py              # 数据模型
├── task_executor.py       # 触发 Agent Session、等待完成、归档
└── submit_feedback.py     # 反馈提交接口
```

### Backend 代码

```
src/openclaw_alpha/backend/feedback/
├── __init__.py
├── config.py              # 配置模型
├── jobs.py                # 定时任务：扫描 + 触发处理
├── task_executor.py       # 触发 Agent Session
└── models.py              # 数据模型
```

---

## 反馈 JSON 结构

每个反馈一个独立的 JSON 文件，处理过程中逐步添加字段。

### 提交时

```json
{
  "id": "abc123",
  "source_user": "Momojie",
  "source_channel": "wecom",
  "submitted_at": "2026-03-10T10:00:00+08:00",
  "content": "反馈原文内容...",
  "status": "pending"
}
```

### 处理中

添加处理相关字段：

```json
{
  "id": "abc123",
  "source_user": "Momojie",
  "source_channel": "wecom",
  "submitted_at": "2026-03-10T10:00:00+08:00",
  "content": "反馈原文内容...",
  "status": "processing",
  "task_dir": "runtime/feedback/tasks/2026-03-17/abc123",
  "job_id": "cron_job_id",
  "session_id": "xxx",
  "context_path": "/path/to/session/file.jsonl",
  "context_path_deleted": "/path/to/session/file.deleted.*",
  "started_at": "2026-03-17T10:00:00+08:00"
}
```

### 处理完成

添加结果字段：

```json
{
  "id": "abc123",
  "source_user": "Momojie",
  "source_channel": "wecom",
  "submitted_at": "2026-03-10T10:00:00+08:00",
  "content": "反馈原文内容...",
  "status": "completed",
  "task_dir": "runtime/feedback/tasks/2026-03-17/abc123",
  "job_id": "cron_job_id",
  "session_id": "xxx",
  "context_path": "/path/to/session/file.jsonl",
  "context_path_deleted": "/path/to/session/file.deleted.*",
  "started_at": "2026-03-17T10:00:00+08:00",
  "decision": "采纳",
  "reason": "决策理由",
  "completed_at": "2026-03-17T10:05:00+08:00"
}
```

### 字段说明

| 字段 | 说明 | 写入时机 |
|------|------|---------|
| `id` | 反馈 ID（content hash） | 提交时 |
| `source_user` | 提交用户 | 提交时 |
| `source_channel` | 提交渠道 | 提交时 |
| `source_session` | 来源 session key（处理完成后用于发送结果消息） | 提交时 |
| `submitted_at` | 提交时间 | 提交时 |
| `content` | 反馈原文 | 提交时 |
| `status` | 状态：pending / processing / completed | 处理过程中 |
| `task_dir` | 任务目录（存放 progress.md） | 开始处理时 |
| `job_id` | Cron 任务 ID | 开始处理时 |
| `session_id` | Session ID | 开始处理时 |
| `context_path` | Session 文件原始路径（.jsonl） | 开始处理时 |
| `context_path_deleted` | Session 备份路径模式（.deleted.*） | 开始处理时 |
| `started_at` | 开始处理时间 | 开始处理时 |
| `decision` | 决策结果 | 处理完成时 |
| `reason` | 决策理由 | 处理完成时 |
| `completed_at` | 完成时间 | 处理完成时 |

**Session 路径说明**：

- `context_path`：OpenClaw 上下文存储路径（session file，.jsonl 格式）
- `context_path_deleted`：Session 备份文件路径模式（.deleted.*），用于 session 被删除后回溯

**用途**：
- 原始 Session 文件可能已被 OpenClaw 清理
- 复盘时先查看 `context_path`，如不存在则用 `context_path_deleted` 进行 glob 匹配查找最新的 `.deleted` 文件

**decision 取值**：
- `采纳`：用户方案完全符合规范，直接实施
- `调整后采纳`：需求合理但方案需调整，或需用其他方式实现
- `不采纳`：不符合项目规范或不可行
- `待讨论`：信息不足或需要进一步沟通

---

## 处理流程

### 完整流程图

```
用户提出反馈
    ↓
openclaw_alpha_feedback skill（收集反馈）
    ↓
保存到 feedback/{YYYY-MM-DD}-{hash}.json
    ↓
Backend 定时扫描（jobs.py）
    ↓
触发 Agent Session（feedback-workflow.md）
    ↓
处理反馈并更新 JSON 文件
    ↓
发送消息通知
    ├─ 给提出者（通过 source_session）
    └─ 给维护者（通过 delivery.recipients）
    ↓
归档到 feedback/done/
```

**详细说明**：
- **openclaw_alpha_feedback**：负责收集用户反馈，保存到 JSON 文件（见 [skill-design.md](./skill-design.md)）
- **Backend**：负责定时扫描、触发处理、发送结果消息、归档反馈
- **Agent**：负责分析反馈、做出决策、更新 JSON 文件

### 定时任务主流程

### 定时任务主流程

每 30 分钟执行一次：

1. **扫描反馈目录**：收集 `new/` 目录下所有 `.json` 文件

2. **过滤待处理反馈**：筛选 `status == "pending"` 的反馈

3. **应用数量限制**：`limit > 0` 时只处理前 N 条，`limit == 0` 表示全部

4. **逐个处理**：对每条待处理反馈执行单条反馈处理流程

### 单条反馈处理流程

1. **更新状态为 processing**：设置 `status = "processing"`，写回 JSON 文件

2. **创建任务目录**：`runtime/feedback/tasks/{date}/{id}/`

3. **触发 Agent Session**：构造任务消息（包含反馈内容），提交 cron 任务

4. **轮询 Session 信息**：等待 session 创建（超时 300 秒），获取 `session_id`

5. **更新处理字段**：添加 `task_dir`、`job_id`、`session_id`、`context_path`、`context_path_deleted`、`started_at`，写回 JSON 文件

6. **等待处理完成**：轮询 JSON 文件（超时 300 秒），检测 `decision` 字段是否被填充

7. **更新完成状态**：设置 `status = "completed"`，添加 `completed_at`，写回 JSON 文件

8. **发送消息通知**：
   - 通过 `source_session` 发送结果消息给提出者
   - 通过 `delivery.recipients` 发送通知给维护者

9. **归档**：移动 JSON 文件到 `done/` 目录

### 失败处理

如果任一步骤失败，重置 `status = "pending"`，写回 JSON 文件，下次定时任务会重试。

---

## 任务执行

### 智能体能力

执行反馈处理的智能体拥有以下能力：
- 所有 `openclaw_alpha_xxx` skill（市场分析、个股分析、技术指标等）
- 知悉 Alpha 项目规范文档（架构规范、开发规范、数据源策略等）

### 任务消息构造

Backend 负责拼接任务消息，包含：
1. 任务模板：`docs/workflow/feedback-workflow.md` 的完整内容
2. 任务参数：task_dir、json_path
3. 反馈内容：从 JSON 文件读取的 content 字段

最终消息格式为：

```
[feedback-workflow.md 内容]

---

## 本次任务参数

- **任务目录**：<task_dir>
- **反馈 JSON**：<json_path>

---

## 反馈内容

<实际反馈内容>
```

### Agent 输出

Agent 在 `task_dir` 下生成 `progress.md` 记录处理进度和详细分析内容。

处理完成后，Agent 直接更新 JSON 文件，添加以下字段：
- `decision` - 决策结果
- `reason` - 决策理由
- `completed_at` - 完成时间
- `status` - 改为 `completed`

其他内容（表面需求、真实需求、技术评估、下一步行动等）记录在 `progress.md` 中，需要时再查看。

Backend 轮询检测 JSON 文件的 `status` 是否变为 `completed`。

---

## 归档

处理完成后：
1. 发送消息通知（提出者和维护者）
2. 将 JSON 文件移动到 `done/` 目录

---

## 消息通知

处理完成后有两类消息需要发送：

### 1. 发给提出者

**渠道**：通过 `source_session` 发送（记录在反馈 JSON 里）

**时机**：处理完成后

**内容**：
- 处理结果（采纳/调整后采纳/不采纳/待讨论）
- 决策理由（简要）
- 后续行动（如有）

### 2. 发给项目维护者

**渠道**：通过配置文件的 `delivery.recipients` 发送

**时机**：
- 新反馈到达时
- 反馈处理完成时

**配置位置**：`runtime/feedback/config.yaml`

```yaml
delivery:
  recipients:
    - name: Momojie
      agent_id: notify
      channel: wecom
```

---

## 错误处理

| 错误类型 | 处理方式 |
|---------|---------|
| 反馈目录不存在 | 跳过，记录警告 |
| JSON 文件损坏 | 记录错误，跳过该文件 |
| 提交任务失败 | 状态重置为 pending，下次重试 |
| Session 超时 | 状态重置为 pending，下次重试 |
| decision 字段未填充 | decision 默认为"待讨论" |

---

## API 接口

### POST /api/feedback/trigger

手动触发反馈扫描，主要用于调试。

**请求参数**：

| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| limit | int | 否 | 1 | 最多处理多少条反馈，0 表示全部 |

**请求示例**：

```bash
# 调试：只处理 1 条
curl -X POST http://localhost:8000/api/feedback/trigger

# 调试：处理 3 条
curl -X POST "http://localhost:8000/api/feedback/trigger?limit=3"

# 全量处理
curl -X POST "http://localhost:8000/api/feedback/trigger?limit=0"
```

**响应示例**：

```json
{
  "success": true,
  "message": "反馈扫描已执行",
  "total_feedback": 5,
  "processed": 3
}
```

---

## 配置

**路径**：`runtime/feedback/config.yaml`

```yaml
enabled: true
interval_minutes: 30

# Agent 配置
agent_id: alpha
model: null  # 使用默认

# 消息推送
delivery:
  recipients:
    - name: Momojie
      agent_id: notify
      channel: wecom

# Cron 任务配置
cron:
  session_poll_timeout_seconds: 300
  result_wait_timeout_seconds: 300
```

---

## 相关文档

- [../../../../workflow/feedback-workflow.md](../../../../workflow/feedback-workflow.md) - 反馈处理流程模板（Agent 任务指引）
- [./skill-design.md](./skill-design.md) - openclaw_alpha_feedback Skill 设计
- [../overview.md](../overview.md) - Iteration Loop 总览
# openclaw_alpha_feedback 设计

## 概述

**Skill 名称**：`openclaw_alpha_feedback`

**作用**：在使用 `openclaw_alpha_xxx` skill 时，收集用户反馈并按指定格式保存到 `feedback/` 目录。

**使用场景**：
- 用户在使用市场分析、个股分析等 skill 时，提出改进建议
- 用户发现 skill 的 bug 或异常行为
- 用户希望新增某个功能或调整现有功能

**核心原则**：被动触发，不主动询问用户是否有反馈。

**位置**：`src/openclaw_alpha/backend/feedback/`（与反馈处理系统放在一起，而非 skills package）

---

## 功能定位

在用户反馈处理系统中的位置：

```
用户提出反馈
    ↓
openclaw_alpha_feedback（收集反馈）
    ↓
保存到 feedback/{YYYY-MM-DD}-{hash}.json
    ↓
Backend 定时扫描（jobs.py）
    ↓
触发 Agent Session（feedback-workflow.md）
    ↓
处理反馈并更新 JSON 文件
    ↓
发送消息通知
    ├─ 给提出者（通过 source_session）
    └─ 给维护者（通过 delivery.recipients）
    ↓
归档到 feedback/processed/
```

**职责边界**：

| 模块 | 职责 |
|------|------|
| **openclaw_alpha_feedback** | 收集用户反馈，保存到 JSON 文件 |
| **Backend** | 扫描反馈目录，触发 Agent Session |
| **feedback-workflow.md** | Agent 处理反馈的流程指引 |
| **Agent** | 分析反馈，做出决策，更新 JSON 文件 |

**不负责**：
- 分析反馈内容（由 Agent 负责）
- 触发处理流程（由 Backend 负责）
- 直接修改 skill 或代码（由后续开发任务负责）

---

## 使用流程

### 触发条件

用户提出反馈的常见表达：
- "我觉得这个功能可以改进一下：xxx"
- "这个结果不对，应该是 xxx"
- "希望能增加 xxx 功能"
- "这个输出格式不太清晰，能否调整"
- "使用时遇到了问题：xxx"

### 使用方式

智能体识别到用户反馈后，执行脚本提交反馈：

**脚本命令**：
```bash
uv run --env-file .env python -m openclaw_alpha.backend.feedback.submit_feedback \
  --content "反馈内容" \
  --source-user "用户名" \
  --source-channel "渠道" \
  --source-session "session:key"
```

**参数**：
| 参数 | 必需 | 说明 |
|------|------|------|
| `--content` | ✅ | 反馈原文内容 |
| `--source-user` | ✅ | 提交用户（从 inbound metadata 获取） |
| `--source-channel` | ✅ | 提交渠道（wecom、telegram 等） |
| `--source-session` | ✅ | 来源 session key（处理完成后用于发送结果消息） |

**调用示例**：
```bash
uv run --env-file .env python -m openclaw_alpha.backend.feedback.submit_feedback \
  --content "这个分析结果缺少换手率指标，建议增加" \
  --source-user "Momojie" \
  --source-channel "wecom" \
  --source-session "wecom-agent:alpha:user:Momojie"
```

**输出**：
```
✅ 反馈已保存
  ID: abc123...
  路径: feedback/2026-03-17-abc123.json
```

### 智能体职责

**智能体只需做**：
- 识别用户是否在提出反馈
- 提取反馈原文（`content`）
- 提取背景简述（`background`，可选）
- 获取用户信息（`source_user`、`source_channel`，可选）
- 获取当前会话的 session key（`source_session`，可选）
- 执行脚本命令

**系统自动处理**：
- 生成反馈 ID（content hash）
- 生成提交时间戳
- 构造完整 JSON 结构
- 保存到指定路径

### 执行流程

```
智能体识别用户反馈
    ↓
提取 content、background（可选）、source_user（可选）、source_channel（可选）、source_session（可选）
    ↓
执行脚本 submit_feedback
    ↓
脚本计算 hash、生成 ID、构造 JSON、保存文件
    ↓
返回反馈 ID 和保存路径
    ↓
（后续）Backend 处理完成后，通过 source_session 发送结果消息给提出者（如有）
```

---

## JSON 格式规范

### 提交时的 JSON 结构

```json
{
  "id": "abc123",
  "source_user": "Momojie",
  "source_channel": "wecom",
  "source_session": "wecom-agent:alpha:user:Momojie",
  "submitted_at": "2026-03-10T10:00:00+08:00",
  "background": "触发场景：分析小龙虾概念股时，获取概念板块热度",
  "content": "概念板块数据全部返回 0，功能不可用",
  "status": "pending"
}
```

### 字段说明

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `id` | string | ✅ | 反馈 ID，使用 content hash（SHA256 hex） |
| `source_user` | string | 可选 | 提交用户名（从 inbound metadata 获取） |
| `source_channel` | string | 可选 | 提交渠道（wecom、telegram 等） |
| `source_session` | string | 可选 | 来源 session key（处理完成后用于发送结果消息给提出者） |
| `submitted_at` | string | ✅ | 提交时间（ISO 8601，时区为 Asia/Shanghai） |
| `background` | string | 可选 | 背景简述（触发场景、问题描述、技术上下文等） |
| `content` | string | ✅ | 提出者的反馈原文 |
| `status` | string | ✅ | 固定为 `"pending"`（Backend 会更新为 processing/completed） |

### 文件命名

格式：`{YYYY-MM-DD}-{hash}.json`

示例：`2026-03-17-a1b2c3d4e5f6.json`

**规则**：
- 日期：提交当天的日期
- hash：content hash 的前 12 位（用于文件名可读性）
- 完整 ID 存储在 JSON 的 `id` 字段中

---

## 技术实现

### 目录结构

```
src/openclaw_alpha/backend/feedback/
├── __init__.py
├── config.py              # 配置模型
├── jobs.py                # 定时任务：扫描 + 触发处理
├── task_executor.py       # 触发 Agent Session
├── models.py              # 数据模型
└── submit_feedback.py     # 提交反馈脚本（本功能）
```

## Skill SKILL.md 结构

```markdown
---
name: openclaw_alpha_feedback
description: "用户反馈收集。适用于：在使用 openclaw_alpha_xxx skill 时提交改进建议、报告 bug、提出新功能需求。不适用于：实时反馈、紧急问题、技术讨论。"
metadata:
  openclaw:
    emoji: "💬"
    requires:
      bins: []
---

# 用户反馈收集

收集用户对 OpenClaw-Alpha 技能的反馈意见。

## 使用说明

### 触发方式

**显式调用**：
```
提交反馈：{反馈内容}
```

**隐式识别**：
用户提出反馈性建议时自动触发。

### 脚本运行

```bash
uv run --env-file .env python -m openclaw_alpha.backend.feedback.submit_feedback \
  --content "反馈内容" \
  --source-user "用户名" \
  --source-channel "渠道" \
  --source-session "session:key"
```

### 输出

```
✅ 反馈已保存
  ID: abc123...
  路径: feedback/2026-03-17-abc123.json
```

## 反馈 JSON 格式

```json
{
  "id": "abc123",
  "source_user": "Momojie",
  "source_channel": "wecom",
  "source_session": "wecom-agent:alpha:user:Momojie",
  "submitted_at": "2026-03-10T10:00:00+08:00",
  "content": "反馈原文内容...",
  "status": "pending"
}
```

## 后续处理

- Backend 每 30 分钟扫描一次 `feedback/` 目录
- 自动触发 Agent Session 处理反馈
- 处理结果会更新到 JSON 文件
- **处理完成后，通过 source_session 发送结果消息给提出者**

## 注意事项

- 反馈会记录用户身份、来源 session 和内容
- source_session 用于处理完成后发送结果消息
- 处理过程可能需要数小时到数天
- 处理结果会更新到反馈文件并通过 session 发送给用户
```

---

## 消息通知

处理完成后有两类消息需要发送：

### 1. 发给提出者

**渠道**：通过 `source_session` 发送

**时机**：Backend 处理完成后

**内容**：
- 反馈处理结果（采纳/调整后采纳/不采纳/待讨论）
- 决策理由（简要）
- 后续行动（如有）

**示例**：
```
📊 您的反馈已处理

反馈：这个分析结果缺少换手率指标，建议增加
结果：✅ 采纳
理由：符合项目规范，需求合理
后续：已创建开发任务，预计近期实现
```

### 2. 发给项目维护者

**渠道**：通过配置文件的 `delivery.recipients` 发送

**时机**：
- 新反馈到达时
- 反馈处理完成时

**配置位置**：`runtime/feedback/config.yaml`

```yaml
delivery:
  recipients:
    - name: Momojie
      agent_id: notify
      channel: wecom
```

**示例（新反馈到达）**：
```
💬 收到新反馈

来源：Momojie (wecom)
内容：这个分析结果缺少换手率指标，建议增加
ID：abc123...
```

**示例（处理完成）**：
```
📊 反馈处理完成

ID：abc123...
来源：Momojie
结果：✅ 采纳
理由：符合项目规范，需求合理
后续：已创建开发任务
```

---

## 与其他模块的交互

**触发场景**：
- 用户在聊天中提出反馈时，Agent 调用此功能
- 用户明确说"提交反馈"时，Agent 调用此功能

**返回信息**：
- 反馈 ID
- 保存路径
- 后续处理说明

### 与 Backend 的交互

**数据流**：
1. 收集反馈，保存 JSON 文件到 `feedback/`
2. Backend 定时扫描目录
3. Backend 更新 JSON 文件状态（pending → processing → completed）
4. **Backend 处理完成后，通过 source_session 发送结果消息给提出者**
5. Backend 归档到 `feedback/processed/`

**无直接调用**：和 Backend 是解耦的，通过文件系统交互。

---

## 错误处理

| 错误类型 | 处理方式 |
|---------|---------|
| 反馈目录不存在 | 自动创建目录 |
| 文件写入失败 | 提示用户稍后重试，记录错误日志 |
| content 为空 | 提示用户提供反馈内容 |
| 重复内容 | 不去重，允许保存相同反馈（可能代表重复需求） |

---

## 测试用例

### 基础功能

1. 提交简单反馈，验证 JSON 格式
2. 验证 ID 生成（相同 content 生成相同 ID）
3. 验证文件命名（日期 + hash 前缀）

### 边界情况

1. 空内容提示用户
2. 超长内容（> 10KB）是否截断或拒绝
3. 特殊字符处理（emoji、换行、引号）
4. 反馈目录不存在时自动创建

### 并发场景

1. 同时提交多个反馈，验证文件写入正常
2. 验证原子写入机制（避免文件损坏）

