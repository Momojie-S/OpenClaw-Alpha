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
- 如果反馈被采纳且需要开发工作，由智能体输出 `next_steps` 中建议创建开发任务
- 开发任务在独立的开发流程中执行（参见 `development-workflow.md`）

---

## 目录结构

```
{project_root}/
└── workspace/
    └── feedback/
        ├── config.yaml           # 配置
        ├── new/                  # 待处理反馈
        │   └── {YYYY-MM-DD}-{hash}.json
        ├── done/                 # 已处理反馈
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
  "task_dir": "workspace/feedback/tasks/2026-03-17/abc123",
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
  "task_dir": "workspace/feedback/tasks/2026-03-17/abc123",
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
归档到 feedback/processed/
```

**详细说明**：
- **openclaw_alpha_feedback**：负责收集用户反馈，保存到 JSON 文件（见 [skill-design.md](./skill-design.md)）
- **Backend**：负责定时扫描、触发处理、发送结果消息、归档反馈
- **Agent**：负责分析反馈、做出决策、更新 JSON 文件

### 定时任务主流程

### 定时任务主流程

每 30 分钟执行一次：

1. **扫描反馈目录**：收集所有 `.json` 文件（排除 `processed/` 子目录）

2. **过滤待处理反馈**：筛选 `status == "pending"` 的反馈

3. **应用数量限制**：`limit > 0` 时只处理前 N 条，`limit == 0` 表示全部

4. **逐个处理**：对每条待处理反馈执行单条反馈处理流程

### 单条反馈处理流程

1. **更新状态为 processing**：设置 `status = "processing"`，写回 JSON 文件

2. **创建任务目录**：`workspace/feedback/tasks/{date}/{id}/`

3. **触发 Agent Session**：构造任务消息（包含反馈内容），提交 cron 任务

4. **轮询 Session 信息**：等待 session 创建（超时 300 秒），获取 `session_id`

5. **更新处理字段**：添加 `task_dir`、`job_id`、`session_id`、`context_path`、`context_path_deleted`、`started_at`，写回 JSON 文件

6. **等待处理完成**：轮询 JSON 文件（超时 300 秒），检测 `decision` 字段是否被填充

7. **更新完成状态**：设置 `status = "completed"`，添加 `completed_at`，写回 JSON 文件

8. **发送消息通知**：
   - 通过 `source_session` 发送结果消息给提出者
   - 通过 `delivery.recipients` 发送通知给维护者

9. **归档**：移动 JSON 文件到 `processed/` 目录

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
2. 将 JSON 文件移动到 `processed/` 目录

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

**配置位置**：`workspace/feedback/config.yaml`

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

**路径**：`workspace/feedback/config.yaml`

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
