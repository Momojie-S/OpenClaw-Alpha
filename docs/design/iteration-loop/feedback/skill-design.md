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

